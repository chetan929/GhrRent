import base64
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

logger = logging.getLogger(__name__)


class EmailReminderService:
    """Email service for rent reminders and notifications."""

    @staticmethod
    def _build_gmail_message(email_dict):
        """Build a Gmail API message payload from a normal email dictionary."""
        recipients = email_dict.get("to") or []
        if not recipients:
            raise ValueError("Email recipient list is empty.")

        message = MIMEMultipart("alternative")
        message["To"] = ", ".join(recipients)
        message["From"] = email_dict.get("from_email") or settings.DEFAULT_FROM_EMAIL
        message["Subject"] = email_dict["subject"]

        if email_dict.get("body"):
            message.attach(MIMEText(email_dict["body"], "plain", "utf-8"))
        if email_dict.get("html_body"):
            message.attach(MIMEText(email_dict["html_body"], "html", "utf-8"))

        encoded = base64.urlsafe_b64encode(message.as_bytes()).decode("ascii")
        return {"raw": encoded}

    @staticmethod
    def _refresh_gmail_token_if_needed(gmail_credential):
        """Refresh the Gmail access token if it has expired or will expire soon.

        Returns True if credentials are valid/refreshed successfully.
        Returns False if refresh_token missing, token refresh failed, or credentials invalid.
        """
        from datetime import timedelta
        from django.utils import timezone

        if not gmail_credential:
            return False

        # Return False if no refresh token (cannot refresh)
        if not gmail_credential.refresh_token:
            logger.warning(
                "No refresh token available for user %s. Cannot refresh access token.",
                gmail_credential.user.username,
            )
            return False

        # Check if token might be expired or will expire soon (within 5 minutes)
        if gmail_credential.token_expiry:
            time_to_expiry = gmail_credential.token_expiry - timezone.now()
            if time_to_expiry < timedelta(minutes=5):
                try:
                    from google.oauth2.credentials import Credentials
                    from google.auth.transport.requests import Request

                    credentials = Credentials(
                        token=gmail_credential.access_token,
                        refresh_token=gmail_credential.refresh_token,
                        token_uri="https://oauth2.googleapis.com/token",
                        client_id=settings.GOOGLE_CLIENT_ID,
                        client_secret=settings.GOOGLE_CLIENT_SECRET,
                        scopes=["https://www.googleapis.com/auth/gmail.send"],
                    )

                    request = Request()
                    credentials.refresh(request)

                    # Update the stored credentials
                    gmail_credential.access_token = credentials.token
                    if credentials.refresh_token:
                        gmail_credential.refresh_token = credentials.refresh_token
                    gmail_credential.token_expiry = credentials.expiry
                    gmail_credential.save()

                    logger.info(
                        "Gmail token refreshed successfully for user %s",
                        gmail_credential.user.username,
                    )
                    return True
                except Exception as e:
                    error_msg = str(e)
                    if "invalid_grant" in error_msg:
                        # Refresh token was revoked
                        logger.error(
                            "Gmail refresh token revoked for user %s. Credentials must be reconnected.",
                            gmail_credential.user.username,
                        )
                    else:
                        logger.error(
                            "Failed to refresh Gmail token for user %s: %s",
                            gmail_credential.user.username,
                            type(e).__name__,
                        )
                    return False

        return True  # Token is still valid

    @staticmethod
    def _send_via_gmail_api(user, email_dict):
        """Send email using the user's connected Gmail account via the Gmail API."""
        if user is None:
            raise RuntimeError("A Django user is required for Gmail API sending.")

        gmail_credential = getattr(user, "gmail_credential", None)
        if not gmail_credential:
            raise RuntimeError(
                "❌ No Gmail account connected. Please connect your Gmail account in settings to send email reminders."
            )

        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise RuntimeError(
                "❌ Google OAuth credentials not configured. Contact support."
            )

        # Attempt to refresh token if needed
        refresh_success = EmailReminderService._refresh_gmail_token_if_needed(
            gmail_credential
        )
        if not refresh_success:
            raise RuntimeError(
                "❌ Your Gmail session has expired. Please reconnect your Gmail account."
            )

        try:
            credentials = Credentials(
                token=gmail_credential.access_token,
                refresh_token=gmail_credential.refresh_token,
                token_uri="https://oauth2.googleapis.com/token",
                client_id=settings.GOOGLE_CLIENT_ID,
                client_secret=settings.GOOGLE_CLIENT_SECRET,
                scopes=["https://www.googleapis.com/auth/gmail.send"],
            )

            service = build("gmail", "v1", credentials=credentials)
            payload = EmailReminderService._build_gmail_message(email_dict)
            result = (
                service.users().messages().send(userId="me", body=payload).execute()
            )
            logger.info(
                "✅ Gmail API sent email for user %s to recipients: %s (message_id=%s)",
                user.username,
                email_dict.get("to"),
                result.get("id"),
            )
            return True
        except Exception as e:
            error_msg = str(e)

            # Check for various forms of invalid/revoked credentials
            if any(
                x in error_msg
                for x in [
                    "invalidCredentials",
                    "invalid_grant",
                    "unauthorized",
                    "credentials revoked",
                ]
            ):
                # Credentials are revoked or expired - mark for re-connection
                logger.error(
                    "Gmail credentials invalid/revoked for user %s. Deleting credential record.",
                    user.username,
                )
                try:
                    gmail_credential.delete()
                except Exception:
                    pass
                raise RuntimeError(
                    "❌ Your Gmail credentials have been revoked or expired. Please reconnect your Gmail account."
                )
            elif "rateLimitExceeded" in error_msg:
                logger.warning(
                    "Gmail API rate limit exceeded for user %s. Request will be retried later.",
                    user.username,
                )
                raise RuntimeError(
                    "❌ Gmail API rate limit exceeded. Please try again in a few minutes."
                )
            elif (
                "insufficient" in error_msg.lower() or "permission" in error_msg.lower()
            ):
                logger.error(
                    "Gmail insufficient permissions for user %s: %s",
                    user.username,
                    error_msg,
                )
                raise RuntimeError(
                    "❌ Insufficient permissions. Please reconnect your Gmail account with proper permissions."
                )
            else:
                logger.error(
                    "Gmail API error for user %s [%s]: %s",
                    user.username,
                    type(e).__name__,
                    error_msg,
                )
                raise RuntimeError(
                    "❌ Failed to send email via Gmail API. Please try again."
                )

    @staticmethod
    def _send_email_message(email_dict):
        """Send a composed email through Django's SMTP backend and return True only on real SMTP success."""
        recipients = email_dict.get("to") or []
        if not recipients:
            logger.error("❌ Cannot send email: recipient list is empty")
            raise ValueError("Email recipient list is empty.")

        smtp_user = getattr(settings, "EMAIL_HOST_USER", "") or ""
        smtp_password = getattr(settings, "EMAIL_HOST_PASSWORD", "") or ""
        if not smtp_user or not smtp_password:
            logger.error(
                "❌ SMTP send failed: missing credentials. EMAIL_HOST_USER='%s' EMAIL_HOST_PASSWORD=***",
                smtp_user,
            )
            raise RuntimeError(
                "SMTP credentials missing. Set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD."
            )

        logger.info(
            "Sending email via SMTP to %s using EMAIL_HOST_USER=%s, EMAIL_HOST=%s:%s",
            recipients,
            smtp_user,
            settings.EMAIL_HOST,
            settings.EMAIL_PORT,
        )

        msg = EmailMultiAlternatives(
            subject=email_dict["subject"],
            body=email_dict["body"],
            from_email=(settings.DEFAULT_FROM_EMAIL or smtp_user),
            to=recipients,
        )
        if email_dict.get("html_body"):
            msg.attach_alternative(email_dict["html_body"], "text/html")

        try:
            sent_count = msg.send(fail_silently=False)
            logger.info(
                "✅ SMTP accepted email: to=%s sent_count=%s",
                recipients,
                sent_count,
            )
            return sent_count > 0
        except Exception as e:
            logger.exception(
                "❌ SMTP send failed for recipients %s: %s", recipients, str(e)
            )
            raise

    @staticmethod
    def _format_due_date(due_date):
        """Return a readable date string from ISO or plain date value."""
        if not due_date:
            return "Due date not set"

        try:
            from datetime import datetime

            if isinstance(due_date, str):
                parsed = datetime.fromisoformat(due_date)
            else:
                parsed = due_date
            return parsed.strftime("%d %b %Y")
        except Exception:
            return str(due_date)

    @staticmethod
    def build_reminder_email(
        tenant_name,
        tenant_email,
        rent_amount,
        pending_amount,
        due_date=None,
        language="english",
    ):
        """Build a rent reminder email with formatted content and language options."""
        total_payable = float(rent_amount) + float(pending_amount)
        due_date_label = EmailReminderService._format_due_date(due_date)
        language = (language or "english").lower()

        if language == "hindi":
            subject = f"{tenant_name} के लिए rent reminder - GharRent"
            greeting = f"नमस्ते {tenant_name},"
            intro = "यह GharRent की ओर से एक औपचारिक rent reminder है। कृपया नीचे विवरण देखें।"
            monthly_label = "मासिक rent"
            previous_label = "पिछला बकाया"
            total_label = "कुल देय राशि"
            due_label = "नियत तिथि"
            footer = (
                "कृपया भुगतान समय पर करें ताकि देय राशि का निपटान सही समय पर हो सके।"
            )
            thanks = "धन्यवाद।"
            signoff = "सादर,\nGharRent - Property Management System"
            html_title = "Rent Payment Reminder"
            gentle_line = "Dear"
            note_line = "यदि आपने भुगतान पहले ही कर दिया है, तो कृपया इस संदेश को नजरअंदाज कर दें।"
            small_text = "यह GharRent - Property Management System की ओर से स्वचालित संदेश है। कृपया इस ईमेल का उत्तर न दें।"
        else:
            subject = f"Rent Reminder for {tenant_name} - GharRent"
            greeting = f"Hello {tenant_name},"
            intro = "This is a formal rent reminder from GharRent. Please review the details below."
            monthly_label = "Monthly Rent"
            previous_label = "Previous Outstanding"
            total_label = "Total Payable"
            due_label = "Due Date"
            footer = "Please ensure the payment is made on time to avoid any late payment issues."
            thanks = "Thank you for your prompt attention."
            signoff = "Best regards,\nGharRent - Property Management System"
            html_title = "Rent Payment Reminder"
            gentle_line = "Dear"
            note_line = (
                "If you have already made the payment, please ignore this message."
            )
            small_text = "This is an automated message from GharRent - Property Management System. Please do not reply to this email."

        # Plain text version
        body = (
            f"{greeting}\n\n"
            f"{intro}\n\n"
            f"{monthly_label}: ₹{float(rent_amount):,.0f}\n"
            f"{previous_label}: ₹{float(pending_amount):,.0f}\n"
            f"{due_label}: {due_date_label}\n"
            f"{total_label}: ₹{total_payable:,.0f}\n\n"
            f"{footer}\n\n"
            f"{thanks}\n\n"
            f"{signoff}"
        )

        # HTML version for better formatting
        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px; margin: 0;">
                <div style="max-width: 560px; margin: 0 auto; background-color: #ffffff; padding: 32px 28px; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.08); border: 1px solid #eceaf7;">
                    <h2 style="margin: 0 0 20px 0; font-size: 30px; line-height: 1.2; color: #1f2937; text-align: center; font-weight: 700;">{html_title}</h2>

                    <p style="margin: 0 0 12px 0; font-size: 18px; color: #1f2937;">{gentle_line} <strong>{tenant_name}</strong>,</p>
                    <p style="margin: 0 0 22px 0; font-size: 15px; line-height: 1.7; color: #374151;">{intro}</p>

                    <div style="background-color: #f8f8fb; border-left: 4px solid #5b4ef7; padding: 18px 18px 16px 18px; border-radius: 8px; margin-bottom: 20px;">
                        <p style="margin: 0 0 12px 0; font-size: 18px; font-weight: 700; color: #1f2937;"><strong>{monthly_label}:</strong> <span style="color: #5b4ef7;">₹{float(rent_amount):,.0f}</span></p>
                        <p style="margin: 0 0 12px 0; font-size: 18px; font-weight: 700; color: #1f2937;"><strong>{previous_label}:</strong> <span style="color: #1f2937;">₹{float(pending_amount):,.0f}</span></p>
                        <p style="margin: 0 0 12px 0; font-size: 18px; font-weight: 700; color: #1f2937;"><strong>{due_label}:</strong> <span style="color: #1f2937;">{due_date_label}</span></p>
                        <hr style="border: none; border-top: 1px solid #dfe3f1; margin: 16px 0;">
                        <p style="margin: 0; font-size: 22px; font-weight: 800; color: #1f2937;"><strong>{total_label}:</strong> <span style="color: #5b4ef7;">₹{total_payable:,.0f}</span></p>
                    </div>

                    <p style="margin: 0 0 10px 0; font-size: 15px; line-height: 1.7; color: #374151;">{footer}</p>
                    <p style="margin: 0 0 18px 0; font-size: 15px; line-height: 1.7; color: #374151;">{note_line}</p>

                    <p style="margin: 0; font-size: 12px; color: #6b7280; line-height: 1.6;">{small_text}</p>
                </div>
            </body>
        </html>
        """

        return {
            "to": [tenant_email] if tenant_email else [],
            "subject": subject,
            "body": body,
            "html_body": html_body,
        }

    @staticmethod
    def send_email_reminder(
        tenant_name,
        tenant_email,
        rent_amount,
        pending_amount,
        due_date=None,
        language="english",
        user=None,
    ):
        """Send a rent reminder email using the user's connected Gmail account.

        Production Requirement: Each GharRent client must use their own connected Gmail account.
        No fallback to shared SMTP is allowed to ensure proper email sender identification.
        """
        logger.info(
            "Email reminder requested for tenant %s by user %s",
            tenant_name,
            user.username if user else "Anonymous",
        )

        if not user:
            logger.error("send_email_reminder called without authenticated user")
            return {
                "success": False,
                "status": "Failed",
                "message": "❌ No authenticated user provided.",
            }

        if not tenant_email:
            logger.warning(
                "Cannot send reminder to tenant %s: no email address provided",
                tenant_name,
            )
            return {
                "success": False,
                "status": "Skipped",
                "message": "❌ Tenant email address not provided.",
            }

        # Check if user has Gmail connected
        gmail_credential = getattr(user, "gmail_credential", None)
        if not gmail_credential:
            logger.warning(
                "User %s attempted to send reminder without Gmail connected",
                user.username,
            )
            return {
                "success": False,
                "status": "Failed",
                "message": "❌ Please connect your Gmail account before sending email reminders. Go to Settings → Gmail Integration.",
            }

        # Build the email
        email = EmailReminderService.build_reminder_email(
            tenant_name=tenant_name,
            tenant_email=tenant_email,
            rent_amount=rent_amount,
            pending_amount=pending_amount,
            due_date=due_date,
            language=language,
        )

        try:
            email["from_email"] = gmail_credential.gmail_email
            sent = EmailReminderService._send_via_gmail_api(user, email)
            logger.info(
                "✅ Email reminder sent successfully for user %s to %s",
                user.username,
                tenant_email,
            )
            return {
                "success": sent,
                "status": "Sent",
                "message": f"✅ Email reminder sent from {gmail_credential.gmail_email}",
            }

        except RuntimeError as e:
            # Error messages already user-friendly from _send_via_gmail_api
            logger.error(
                "Email reminder failed for user %s: %s",
                user.username,
                str(e),
            )
            return {
                "success": False,
                "status": "Failed",
                "message": str(e),
            }
        except Exception as e:
            logger.exception(
                "Unexpected error sending reminder for user %s: %s",
                user.username,
                str(e),
            )
            return {
                "success": False,
                "status": "Failed",
                "message": "❌ An unexpected error occurred. Please try again.",
            }

    @staticmethod
    def send_welcome_email(user_email, user_name):
        """Send welcome email and return True only when SMTP accepts it."""
        subject = "Welcome to GharRent!"
        body = f"""
Hello {user_name},

Welcome to GharRent - Your Property Management System!

Your account has been successfully created. You can now log in and start managing your properties and tenants.

To get started:
1. Log in with your credentials
2. Add your properties and tenants
3. Set up automated rent reminders
4. Track payments and maintenance requests

If you need any assistance, please visit our help section.

Best regards,
GharRent Team
"""

        html_body = f"""
        <html>
            <body style="font-family: Arial, sans-serif; background-color: #f5f5f5; padding: 20px;">
                <div style="max-width: 500px; margin: 0 auto; background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1);">
                    <h1 style="color: #4f46e5; text-align: center;">Welcome to GharRent!</h1>
                    <p>Hello <strong>{user_name}</strong>,</p>
                    <p>Your account has been successfully created. You can now log in and start managing your properties and tenants.</p>

                    <div style="background-color: #f0f4ff; padding: 20px; border-radius: 5px; margin: 20px 0;">
                        <h3 style="color: #4f46e5; margin-top: 0;">Get Started:</h3>
                        <ol style="color: #333;">
                            <li>Log in with your credentials</li>
                            <li>Add your properties and tenants</li>
                            <li>Set up automated rent reminders</li>
                            <li>Track payments and maintenance requests</li>
                        </ol>
                    </div>

                    <p>If you need any assistance, please visit our help section or contact support.</p>

                    <p style="color: #666; font-size: 12px; margin-top: 30px;">
                        This is an automated message from GharRent.<br>
                        Please do not reply to this email.
                    </p>
                </div>
            </body>
        </html>
        """

        try:
            smtp_user = getattr(settings, "EMAIL_HOST_USER", "") or ""
            smtp_password = getattr(settings, "EMAIL_HOST_PASSWORD", "") or ""
            if not smtp_user or not smtp_password:
                logger.warning(
                    "Welcome email not sent to %s: SMTP credentials missing. EMAIL_HOST_USER=%s EMAIL_HOST_PASSWORD=%s",
                    user_email,
                    bool(smtp_user),
                    bool(smtp_password),
                )
                return False

            email_dict = {
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "to": [user_email],
            }

            sent = EmailReminderService._send_email_message(email_dict)
            logger.info(
                "Welcome email delivery result for %s: success=%s", user_email, sent
            )
            return sent

        except Exception as e:
            logger.exception(
                "❌ Failed to send welcome email to %s: %s", user_email, str(e)
            )
            return False
