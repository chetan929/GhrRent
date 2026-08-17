# GharRent Gmail OAuth Implementation Guide

**Status**: Production-Ready  
**Date**: 2026-08-17  
**Deployment Target**: Render (https://ghrrent.onrender.com)

---

## Overview

This document describes the production-ready Gmail OAuth implementation for GharRent. Each GharRent client can now connect their own Gmail account and send rent reminder emails directly from their connected Gmail account using the Gmail API.

### Key Features

✅ **User-Owned Gmail Accounts**: Each client connects their own Gmail account, not a shared mailbox  
✅ **Token Refresh**: Automatic token refresh when access_token expires  
✅ **Error Handling**: Comprehensive error messages for common OAuth issues  
✅ **Security**: No token exposure in logs, CSRF/state protection, HTTPS enforcement  
✅ **Production-Only Email**: Gmail connection required; no SMTP fallback for production  
✅ **Scope Minimal**: Only `gmail.send` scope required (respects user's "send emails" permission)

---

## Files Changed

### 1. **[gharrent/settings.py](gharrent/settings.py)**
- Updated `GOOGLE_REDIRECT_URI` to use environment variable with proper default for local development
- Production: Must set `GOOGLE_REDIRECT_URI=https://ghrrent.onrender.com/gmail/callback/` in Render

**Changes**:
```python
# Before:
GOOGLE_REDIRECT_URI = config(
    "GOOGLE_REDIRECT_URI", default="http://localhost:8000/gmail/callback/"
)

# After:
GOOGLE_REDIRECT_URI = config(
    "GOOGLE_REDIRECT_URI",
    default="http://127.0.0.1:8000/gmail/callback/",
)
# Production: Set GOOGLE_REDIRECT_URI=https://ghrrent.onrender.com/gmail/callback/
```

---

### 2. **[core/views.py](core/views.py)**
- Added `logger` initialization for secure logging
- Enhanced `gmail_connect()` with better error handling
- Enhanced `gmail_callback()` with:
  - OAuth error detection (access_denied, invalid_grant, redirect_uri_mismatch)
  - State/CSRF validation
  - Authorization code validation
  - Specific error messages for user-friendly feedback
  - Token expiry tracking
- Enhanced `gmail_disconnect()` with proper logging

**Key Changes**:
- All error messages are user-friendly and don't expose sensitive info
- Logging uses `logger` instead of print statements
- State validation prevents CSRF attacks
- Authorization code errors are caught and handled gracefully

---

### 3. **[core/email_service.py](core/email_service.py)**
- Added `_refresh_gmail_token_if_needed()` for automatic token refresh
- Enhanced `_send_via_gmail_api()` with:
  - Token refresh before sending
  - Revoked credential detection
  - Rate limit handling
  - Specific error messages (not exposing raw API errors)
- **Completely rewrote `send_email_reminder()`**:
  - **No SMTP fallback** (production requirement)
  - **Requires Gmail connection** to send email reminders
  - Returns clear error message if Gmail not connected
  - User must connect Gmail before sending any email

**Key Changes**:

```python
# New behavior:
# 1. If user has Gmail connected → send via Gmail API
# 2. If user doesn't have Gmail → return error message
# 3. Never fall back to SMTP
```

---

## Migration Status

✅ **No new migration needed!**

The `GmailCredential` model already exists in migration `0005_maintenancecomplaint_user_notification_user_and_more.py`.

---

## Environment Variables Required (Render)

Add these to Render environment variables in the dashboard:

```bash
# Google OAuth (existing)
GOOGLE_CLIENT_ID=your_client_id_here
GOOGLE_CLIENT_SECRET=your_client_secret_here

# NEW: Production OAuth Redirect URI
GOOGLE_REDIRECT_URI=https://ghrrent.onrender.com/gmail/callback/
```

**Steps to add in Render**:
1. Go to Render Dashboard → GharRent Service
2. Click "Environment" tab
3. Add/Update these 3 variables
4. Click "Save"
5. Render will auto-deploy with new environment variables

---

## Google Cloud Configuration Required

### Already Configured (per your setup):
✅ Gmail API enabled  
✅ OAuth Consent Screen configured  
✅ Gmail scope added: `https://www.googleapis.com/auth/gmail.send`  
✅ Google OAuth Web Application client created  

### Verify These Settings:

1. **Authorized Redirect URIs** in Google Cloud Console:
   - Go to: APIs & Services → Credentials → OAuth 2.0 Client IDs (Web Application)
   - **Authorized redirect URIs** section must include:
     ```
     http://127.0.0.1:8000/gmail/callback/
     http://localhost:8000/gmail/callback/
     https://ghrrent.onrender.com/gmail/callback/
     ```
   - Click "Save"

2. **Scopes** (already configured):
   - OAuth Consent Screen → Scopes → Verify `gmail.send` is added
   - This scope is sufficient to send emails on behalf of the user

3. **OAuth Consent Screen**:
   - User-facing name: "GharRent"
   - User support email: your_email@gmail.com
   - Developer contact: your_email@gmail.com
   - Status: **Published** (not in development)

---

## Implementation Details

### User Flow

```
1. User logs into GharRent
2. Clicks "Connect Gmail" in Settings → Gmail Integration
3. Redirected to Google OAuth consent screen
4. User grants "Send email on your behalf" permission
5. Google redirects to: https://ghrrent.onrender.com/gmail/callback/
6. Django exchanges authorization code for tokens
7. Access token + Refresh token saved to GmailCredential
8. User sees "Gmail Connected: user@gmail.com"
9. Can now send rent reminders
10. Emails are sent FROM user's connected Gmail
```

### Token Refresh Logic

```python
# Automatic token refresh happens when:
1. User initiates sending a reminder
2. EmailReminderService checks if token expires within 5 minutes
3. If yes, refresh token is used to get new access_token
4. New tokens saved to database
5. Email sent with fresh credentials
```

### Error Handling

| Error | User Message | Action |
|-------|--------------|--------|
| No Gmail connected | "Please connect your Gmail account" | Redirect to Settings |
| Credentials revoked | "Gmail credentials expired. Please reconnect" | Credential deleted, user must reconnect |
| OAuth state mismatch | "OAuth session expired. Try again" | Redirect to Settings |
| User denies permission | "You denied Gmail access. Please grant permission" | Redirect to Settings |
| Rate limit exceeded | "Gmail API rate limit. Try again later" | User retries |
| Tenant has no email | "Cannot send: tenant email missing" | User adds tenant email |
| No user authenticated | Error (should not happen) | System error |

---

## Production Testing Checklist

### Before Going Live:

#### 1. **Local Testing**
```bash
# Clone the repo and set up locally
python manage.py migrate

# Set environment variables (create .env file)
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret
GOOGLE_REDIRECT_URI=http://127.0.0.1:8000/gmail/callback/

# Run server
python manage.py runserver

# Test flow:
- Register new user
- Go to Settings → Gmail Integration
- Click "Connect Gmail"
- Verify it redirects to Google consent screen
- Verify after consent, redirects back and shows "Gmail Connected: your_email@gmail.com"
- Add a tenant with email
- Click "Send Reminder" → Should send email from connected Gmail
```

#### 2. **Test Token Refresh**
- Connect Gmail
- Wait for access token to be about to expire (or modify token_expiry in DB)
- Send a reminder email
- Verify in logs: "Gmail token refreshed successfully"
- Verify email still sent successfully

#### 3. **Test Error Scenarios**

**Scenario A: No Gmail Connected**
- Create user
- Try to send reminder without connecting Gmail
- Should show: "Please connect your Gmail account..."

**Scenario B: Tenant has no email**
- Add tenant without email
- Try to send reminder
- Should show: "Cannot send: tenant email missing"

**Scenario C: Gmail disconnected**
- Connect Gmail
- Delete Gmail credential from Django admin (simulate revocation)
- Try to send reminder
- Should show: "Please connect your Gmail account..."

**Scenario D: Revoked credentials**
- Connect Gmail
- In Django admin, set `access_token` to invalid value
- Try to send reminder
- Should show: "Gmail credentials expired. Please reconnect"

#### 4. **Test on Render Staging** (if available)
```bash
# Deploy to Render
git push origin main

# Wait for deployment
# Go to: https://ghrrent.onrender.com

# Test full flow as above
# Verify GOOGLE_REDIRECT_URI in Render environment matches deployed URL
```

#### 5. **Production Deployment**

```bash
# 1. Ensure Render environment variables are set:
GOOGLE_CLIENT_ID=xxx
GOOGLE_CLIENT_SECRET=xxx
GOOGLE_REDIRECT_URI=https://ghrrent.onrender.com/gmail/callback/

# 2. Google Cloud: Add to Authorized Redirect URIs:
https://ghrrent.onrender.com/gmail/callback/

# 3. Deploy code
git push origin main

# 4. Verify on production:
https://ghrrent.onrender.com/
```

---

## Database Schema (GmailCredential)

```python
class GmailCredential(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="gmail_credential")
    gmail_email = models.EmailField()  # The Gmail address connected
    access_token = models.TextField()  # OAuth access token (short-lived)
    refresh_token = models.TextField(blank=True, null=True)  # Refresh token (long-lived)
    token_expiry = models.DateTimeField(null=True, blank=True)  # When access_token expires
    connected_at = models.DateTimeField(auto_now_add=True)  # When connected
    updated_at = models.DateTimeField(auto_now=True)  # Last updated
```

---

## Security Considerations

### ✅ What We Do Right

1. **No Token Exposure**
   - Tokens NEVER appear in logs
   - Tokens NEVER sent to frontend/JavaScript
   - Tokens only used server-side

2. **CSRF Protection**
   - OAuth state parameter validated
   - Session-based protection
   - Django CSRF middleware active

3. **HTTPS Enforcement**
   - Production uses HTTPS only
   - Redirect URIs validated
   - Secure cookies in production

4. **One Token Per User**
   - OneToOneField prevents duplicate credentials
   - Each user can only have one connected Gmail
   - Reconnecting updates existing credential

5. **Scope Minimization**
   - Only request `gmail.send` scope
   - User must explicitly grant in consent screen
   - No access to other Gmail data

### ⚠️ What You Must Ensure

1. **Environment Variables**
   - Store `GOOGLE_CLIENT_SECRET` only in Render
   - Never commit to GitHub
   - Rotate regularly

2. **HTTPS in Production**
   - Render provides HTTPS automatically
   - Ensure `SECURE_SSL_REDIRECT = True` in production settings

3. **Google Cloud Permissions**
   - Limit API access to IP ranges if possible
   - Monitor API quota usage
   - Set up alerts for suspicious activity

4. **User Privacy**
   - Inform users what emails you're sending
   - Provide clear disconnect option
   - Don't reuse Gmail for other purposes

---

## Troubleshooting

### 1. "redirect_uri_mismatch" Error

**Cause**: GOOGLE_REDIRECT_URI in Django doesn't match Google Cloud Authorized URIs

**Fix**:
- Google Cloud Console → APIs & Services → Credentials → OAuth 2.0 Client
- Check Authorized Redirect URIs exactly matches:
  - Development: `http://127.0.0.1:8000/gmail/callback/`
  - Production: `https://ghrrent.onrender.com/gmail/callback/`

### 2. "Email Failed: No Gmail Account Connected"

**Cause**: User hasn't connected Gmail yet

**Fix**: Direct user to Settings → Gmail Integration → Connect Gmail

### 3. "Gmail credentials expired. Please reconnect"

**Cause**: Refresh token was revoked by user in Google Account settings

**Fix**: User must disconnect and reconnect Gmail in Settings

### 4. "Invalid authorization code"

**Cause**: Code already used or expired (>10 minutes old)

**Fix**: User should try connecting Gmail again

### 5. Emails not sending but no error

**Cause**: Gmail API quota exceeded or rate limited

**Fix**: Check Google Cloud Console → APIs & Services → Quota → Gmail API

---

## Monitoring & Logging

### Important Log Entries

```python
# Success
logger.info("Gmail credential connected for user %s with email %s")
logger.info("✅ Email reminder sent successfully for user %s to %s")

# Errors
logger.error("Gmail credentials revoked/invalid for user %s")
logger.warning("User %s attempted to send reminder without Gmail connected")
logger.error("Failed to refresh Gmail token for user %s")
```

### Recommended Monitoring

1. **Track Email Success Rate**
   - Monitor ReminderLog table
   - Alert if failure rate > 10%

2. **Track Token Refresh Failures**
   - Monitor logs for "Failed to refresh Gmail token"
   - Alert if > 5 per day

3. **Track Revoked Credentials**
   - Monitor logs for "Gmail credentials revoked"
   - Send notification to user to reconnect

---

## Rollback Plan

If you need to rollback to SMTP:

1. In `email_service.py`, modify `send_email_reminder()`:
   ```python
   # Comment out the Gmail check
   # if not gmail_credential:
   #     return {"success": False, ...}
   
   # Add SMTP fallback back
   # if not gmail_credential:
   #     # Use SMTP
   ```

2. But **NOT RECOMMENDED** because:
   - Different clients would send from your email
   - Violates project requirements
   - Could cause deliverability issues

---

## FAQ

### Q: Can users change their connected Gmail?
**A**: Yes. They disconnect the old one and connect a new one. The system uses `update_or_create()` so it replaces the old credential.

### Q: What happens if a user's Gmail account is deleted?
**A**: Their access_token becomes invalid. Next time they try to send email, they'll see "Please reconnect Gmail" and can connect a different Gmail.

### Q: Is the refresh token stored securely?
**A**: It's stored in the Django database as plain text. For production, consider encrypting the database field using django-encrypted-model-fields.

### Q: Can users send from multiple Gmail accounts?
**A**: No. GmailCredential uses OneToOneField. If they try to connect a second Gmail, it replaces the first.

### Q: Do we have access to user's emails?
**A**: No. We only have permission to `gmail.send`. We cannot read user's emails.

### Q: What if the user revokes Gmail permission?
**A**: Our access_token becomes invalid. We detect this and ask them to reconnect. Their credential is deleted.

### Q: How long do tokens last?
**A**: Access tokens last ~1 hour. We refresh automatically 5 minutes before expiry. Refresh tokens are permanent unless user revokes.

---

## API Endpoints

| Endpoint | Method | Action |
|----------|--------|--------|
| `/gmail/connect/` | GET | Start OAuth flow |
| `/gmail/callback/` | GET | Handle OAuth callback |
| `/gmail/disconnect/` | GET | Remove Gmail connection |
| `/profile/` | GET | View profile + Gmail status |
| `/send-email-reminder/<tenant_id>/` | GET | Send reminder (requires Gmail) |

---

## Next Steps

1. ✅ **Code Review**: Review changes in this document
2. ✅ **Local Testing**: Test locally before production
3. ✅ **Google Cloud**: Verify authorized redirect URIs
4. ✅ **Render Deploy**: Push code and environment variables
5. ✅ **Production Testing**: Follow testing checklist
6. ✅ **Monitor**: Watch logs for errors
7. ✅ **User Communication**: Inform clients about Gmail connection requirement

---

## Support

For issues or questions:
1. Check troubleshooting section above
2. Review logs in Render dashboard
3. Check Google Cloud API usage
4. Contact development team

---

**Implementation Complete** ✅
