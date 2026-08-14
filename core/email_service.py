from django.core.mail import send_mail
from django.conf import settings
import logging
import threading

logger = logging.getLogger(__name__)


class EmailReminderService:
    """Email service for rent reminders and notifications."""

    @staticmethod
    def _send_email_in_background(email_dict):
        """Helper method to send email in a background thread (non-blocking)."""
        try:
            from django.core.mail import EmailMultiAlternatives

            msg = EmailMultiAlternatives(
                subject=email_dict["subject"],
                body=email_dict["body"],
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=email_dict["to"],
            )
            msg.attach_alternative(email_dict["html_body"], "text/html")
            msg.send(fail_silently=False)
            logger.info(f"✅ Email sent to {email_dict['to']}")
        except Exception as e:
            logger.error(f"❌ Failed to send email: {str(e)}")

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
    ):
        """Send email reminder to tenant."""
        email = EmailReminderService.build_reminder_email(
            tenant_name=tenant_name,
            tenant_email=tenant_email,
            rent_amount=rent_amount,
            pending_amount=pending_amount,
            due_date=due_date,
            language=language,
        )
        if not email["to"]:
            return {
                "success": False,
                "status": "Skipped",
                "message": "Tenant email not provided.",
            }

        try:
            # Check if email is configured
            if not settings.EMAIL_HOST_USER:
                logger.warning(
                    f"Email not sent to {tenant_email}: SMTP not configured. "
                    f"Set EMAIL_HOST_USER in .env"
                )
                return {
                    "success": True,
                    "status": "Queued",
                    "message": "Email queued (SMTP not configured - set EMAIL_HOST_USER in .env)",
                    "email": email,
                }

            # Send email in background thread (non-blocking) for instant response
            thread = threading.Thread(
                target=EmailReminderService._send_email_in_background,
                args=(email,),
                daemon=True,
            )
            thread.start()

            logger.info(f"Email reminder queued for {tenant_email} for {tenant_name}")
            return {
                "success": True,
                "status": "Sent",
                "message": "Email reminder queued successfully.",
                "email": email,
            }

        except Exception as e:
            logger.error(f"Failed to queue email reminder to {tenant_email}: {str(e)}")
            return {
                "success": False,
                "status": "Failed",
                "message": f"Email sending failed: {str(e)}",
            }

    @staticmethod
    def send_welcome_email(user_email, user_name):
        """Send welcome email to new user."""
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
            if not settings.EMAIL_HOST_USER:
                logger.warning(
                    f"Welcome email not sent to {user_email}: SMTP not configured"
                )
                return False

            email_dict = {
                "subject": subject,
                "body": body,
                "html_body": html_body,
                "to": [user_email],
            }

            # Send welcome email in background thread (non-blocking)
            thread = threading.Thread(
                target=EmailReminderService._send_email_in_background,
                args=(email_dict,),
                daemon=True,
            )
            thread.start()

            logger.info(f"Welcome email queued for {user_email}")
            return True

        except Exception as e:
            logger.error(f"Failed to send welcome email to {user_email}: {str(e)}")
            return False
