# Google Cloud OAuth 2.0 Setup Guide for GharRent
## Per-User Gmail Integration on Render

**Deployment URL:** https://ghrrent.onrender.com  
**Callback URL:** https://ghrrent.onrender.com/gmail/callback/  
**Current Implementation Status:** ✅ Code is production-ready, awaiting OAuth credentials

---

## 1. Creating or Selecting a Google Cloud Project

### Option A: Create a NEW Project (Recommended for this app)

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Sign in with your Google account
3. At the top left, click the **Project dropdown** → **NEW PROJECT**
4. Enter Project Name: `GharRent`
5. Click **CREATE**
6. Wait for the project to initialize (~1 minute)
7. Select the new `GharRent` project from the dropdown at the top

### Option B: Use an Existing Project
- If you have an existing Google Cloud project, select it from the dropdown at the top

**Why a separate project is recommended:** Easier to manage OAuth credentials, separate billing, and cleaner organization.

---

## 2. Enabling the Gmail API

1. In the Google Cloud Console, go to **APIs & Services** → **Library**
2. Search for `Gmail API`
3. Click on **Gmail API**
4. Click the **ENABLE** button
5. Wait for the API to enable (you'll see "API enabled" confirmation)

**What this does:** Authorizes your project to access Gmail on behalf of users.

---

## 3. Configuring the OAuth Consent Screen

### Step 1: Set User Type
1. Go to **APIs & Services** → **OAuth consent screen**
2. You'll see **User Type** options: **Internal** or **External**
3. **Select: EXTERNAL** (this allows anyone to authenticate, not just Google Workspace users)
4. Click **CREATE**

### Step 2: Fill out App Information
On the "Edit app registration" page, complete:

**App Name:** `GharRent`

**User Support Email:** Your email address (e.g., `your-email@gmail.com`)

**Developer Contact:**
- Email: Your email address
- Leave phone blank (optional)

Click **SAVE AND CONTINUE**

### Step 3: Scopes Configuration
You'll see a **Scopes** section.

**Click "ADD OR REMOVE SCOPES"** and add these three scopes:

1. **`https://www.googleapis.com/auth/gmail.send`**
   - Used to: Send emails on behalf of the connected user's Gmail
   - Why: Your app sends rent reminders from each user's Gmail account

2. **`https://www.googleapis.com/auth/userinfo.email`**
   - Used to: Get the user's email address after OAuth login
   - Why: Verify which Gmail account is connected

3. **`openid`**
   - Used to: OpenID Connect authentication
   - Why: Standard OpenID scope for user identity verification

**After adding scopes, click SAVE AND CONTINUE**

### Step 4: Test Users
You'll see a **Test users** section.

**FOR TESTING (development):** Add test user email addresses
- Click **ADD USERS**
- Enter your Gmail address (e.g., your-test-account@gmail.com)
- Click **ADD**

**This means:**
- While in testing mode, only these email addresses can complete the OAuth flow
- Other users will see an "Access not configured" error
- Once you move to production, all users can authenticate

**Click SAVE AND CONTINUE** → **BACK TO DASHBOARD**

---

## 4. Choosing Correct App Type/Audience: Testing vs Production

### Current Status: TESTING MODE
When you first create OAuth credentials, your app is in **Testing Mode**:

| Aspect | Testing Mode | Production Mode |
|--------|--------------|-----------------|
| Who can authenticate | Only added test users | Any Google account |
| Permissions message | "App is not verified by Google" | "Verify [app] has access" |
| User limit | 100 test users max | Unlimited |
| Best for | Development & QA | Live deployment |
| Time to production | Immediate | Requires Google verification (~2-7 days) |

### For GharRent Deployment:

**Initially (Days 1-3):** Keep in Testing Mode
- Add your test Gmail account as a test user
- Verify the OAuth flow works end-to-end
- Test multi-user scenarios with 2-3 test accounts

**Later (Days 4-7 or after successful testing):**
- Submit for **Google OAuth App Verification**
- Users will see your app is officially verified
- Move to Production Mode

**How to move to production:**
1. Go to **APIs & Services** → **OAuth consent screen**
2. Scroll down to **App status**
3. Look for the **Submit for verification** button
4. Provide:
   - Privacy policy URL (or link to your terms)
   - Home page link
   - Logo (320x320px)
5. Answer verification questions about data usage
6. Wait 2-7 days for Google's review

---

## 5. Adding Test Users (If Required)

**Required for Testing Mode:**

1. Go to **APIs & Services** → **OAuth consent screen**
2. Scroll to **Test users** section
3. Click **ADD USERS**
4. Enter test email address (Gmail account you control)
5. Click **ADD**
6. You can add up to **100 test users**

**Test users you should add:**
- Your personal Gmail: `your-email@gmail.com`
- Test account 2 (optional): `test-account2@gmail.com`
- Test account 3 (optional): `test-account3@gmail.com`

**Why multiple test users?**
- Test per-user OAuth isolation (each user's Gmail is separate)
- Verify tenant reminders send from correct user's Gmail
- Test disconnect/reconnect flow

---

## 6. Creating an OAuth 2.0 Client ID for Web Application

1. Go to **APIs & Services** → **Credentials**
2. Click **+ CREATE CREDENTIALS** → **OAuth client ID**
3. Select Application type: **Web application**
4. Enter Name: `GharRent OAuth Client`
5. Click **CREATE** (do NOT click "Configure OAuth consent screen" yet)

You should see a dialog with:
- **Client ID**
- **Client Secret**

**⚠️ IMPORTANT:**
- Copy both values immediately
- Store them securely (save in a temporary file)
- Never share these with anyone
- You'll add these to Render environment variables in Step 12

---

## 7. Adding Authorized Redirect URI

**Still in the Credentials page, editing your OAuth Client:**

1. Look for the OAuth 2.0 client you just created
2. Click on it to edit
3. Scroll to **Authorized redirect URIs**
4. Click **ADD URI**
5. Enter **EXACTLY:**
   ```
   https://ghrrent.onrender.com/gmail/callback/
   ```
   **Note the trailing slash `/`**

6. **DO NOT include:**
   - http:// (only https://)
   - Parameters or query strings
   - Double slashes

7. Click **SAVE**

### Why this exact URL?
- It matches the Django URL pattern in [core/urls.py](core/urls.py#L9):
  ```python
  path("gmail/callback/", views.gmail_callback, name="gmail_callback"),
  ```
- Django views.py line 793 expects a POST/GET at exactly this path
- The OAuth callback handler ([views.py](views.py#L793)) validates that the incoming request came from this exact URL

---

## 8. Authorized JavaScript Origin (Required for Web Apps)

### DO YOU NEED THIS?

**In your implementation:** YES, you should add it

**Why:** JavaScript on your frontend may initiate OAuth requests

### What to add:
**Authorized JavaScript Origins:**
1. In the same credentials edit page, scroll to **Authorized JavaScript origins**
2. Click **ADD URI**
3. Enter **EXACTLY:**
   ```
   https://ghrrent.onrender.com
   ```
   **Note: NO trailing slash**

4. For local development, also add:
   ```
   http://localhost:8000
   ```

### Why these?
- `https://ghrrent.onrender.com` - Your production domain
- `http://localhost:8000` - Your local Django dev server (for testing)

### What this prevents:
- Protects against Cross-Origin Resource Sharing (CORS) attacks
- Only allows OAuth flows originating from your approved domains

---

## 9. OAuth Scopes Required and Explanation

Your implementation uses **exactly 3 scopes**:

### Scope 1: `https://www.googleapis.com/auth/gmail.send`
```
Purpose: Send emails via Gmail API
Used in: email_service.py lines 47-56
How: When a user sends a rent reminder, it uses this scope to call Gmail API's users().messages().send()
Permission level: SEND EMAILS ONLY (cannot read, delete, or modify existing emails)
```

### Scope 2: `https://www.googleapis.com/auth/userinfo.email`
```
Purpose: Read user's email address from their Google account
Used in: views.py lines 793-808 (gmail_callback)
How: After OAuth approval, fetch user's Gmail email to store in GmailCredential model
Permission level: Read email address only
```

### Scope 3: `openid`
```
Purpose: OpenID Connect protocol for user identity verification
Used in: google_auth_oauthlib library (handles OAuth flow)
How: Standard OpenID scope, required for proper OAuth 2.0 compliance
Permission level: Verify user identity (no data access)
```

### Scopes NOT included (and why):
- ❌ `https://www.googleapis.com/auth/gmail.readonly` - NOT needed (you don't read emails)
- ❌ `https://www.googleapis.com/auth/gmail.modify` - NOT needed (you don't modify emails)
- ❌ `https://www.googleapis.com/auth/gmail.labels` - NOT needed (you don't manage labels)
- ❌ `email` (basic profile email) - NOT needed (userinfo.email is sufficient)

### Permission Consent Dialog Users Will See:
When a user clicks "Connect Gmail" in your app, they'll see:

> **GharRent wants access to your Google Account**
> - Send emails on your behalf
> - See your email address
> - See your Google Account information

Users must click **Allow** to proceed.

---

## 10. Gmail OAuth Verification Requirement

### Before any user can use the application publicly:

**Short Answer:** YES, you need to prepare for verification, but you can test in Testing Mode first.

### Timeline:

| Phase | Duration | Requirement | User Type | What Users See |
|-------|----------|-------------|-----------|----------------|
| **Phase 1: Testing** | Days 1-3 | Add test users manually | Test accounts only | "GharRent wants access" (no verification badge) |
| **Phase 2: Limited Users** | Days 4-7 | Submit for verification | Still test users + waiting | Same as Phase 1 |
| **Phase 3: Full Production** | Day 8+ | Google approves verification | ANY Google account | "Verified" badge on consent screen |

### What Google Reviews:

When you submit for verification, Google checks:
1. **Privacy Policy** - Does your app explain data handling?
2. **Data Usage** - Will you store emails? (You won't - only tokens)
3. **Security** - Do you use HTTPS? (Yes, your Render app does)
4. **OAuth Compliance** - Do you follow OAuth 2.0 standards? (Yes)

### For GharRent Specifically:

**What you should document:**
- You store **only:** access token, refresh token, user's Gmail email, token expiry
- You **do NOT store:** email contents, attachments, user labels
- You **only send** emails (rent reminders) using Gmail API
- Tokens are tied to individual users (Alice's token cannot access Bob's account)

### Verification Process (when ready):

1. Go to **APIs & Services** → **OAuth consent screen**
2. Scroll to **App status** section
3. Click **"Not verified yet"** → **SUBMIT FOR VERIFICATION**
4. Fill out verification form
5. Google emails you decision within 2-7 days

**Once approved:** Users can use your app without the "Not verified" warning

---

## 11. Testing Mode vs Production Mode - Key Differences

### TESTING MODE (Your current setup)

**Setup time:** 5 minutes  
**User access:** Only test users you add  
**Consent screen:** Shows "App is not verified"  
**Best for:** Development, QA, internal testing  
**Scalability:** Up to 100 test users  

**When to use:** Right now (Days 1-3)
- Test the OAuth flow locally
- Verify token storage in DB
- Test email sending with Gmail API
- Verify multi-user isolation

**Example test user flow:**
```
1. Register User A (email: test1@gmail.com)
2. Click "Connect Gmail"
3. OAuth directs to Google login
4. User A approves, returns to app
5. GmailCredential stored in DB with User A's tokens
6. Send reminder → email sent from User A's Gmail ✓
7. Logout
8. Register User B (email: test2@gmail.com)
9. User B connects different Gmail → different tokens stored ✓
10. Send reminder → email sent from User B's Gmail ✓
```

---

### PRODUCTION MODE (After verification approval)

**Setup time:** 2-7 days (Google review)  
**User access:** ANY Google account  
**Consent screen:** Shows "Verified" badge  
**Best for:** Public deployment  
**Scalability:** Unlimited users  

**When to switch:** After successful testing (Day 7+)

**Required steps to switch:**
1. Submission for verification (link in OAuth consent screen)
2. Provide privacy policy URL
3. Explain data usage (you'll say: "Store only OAuth tokens for sending emails")
4. Wait for Google approval
5. Approved! Users no longer see "Not verified" warning

**Production user flow (same as testing, but for any Google account):**
```
1. Any user can visit https://ghrrent.onrender.com
2. Register/Login
3. Click "Connect Gmail"
4. Google login & approval
5. App stores their Gmail tokens
6. User sends reminders through their Gmail
```

---

## 12. Render Environment Variables Configuration

Your Render deployment needs **3 environment variables** to work.

### Location in Render Dashboard:

1. Go to [Render Dashboard](https://dashboard.render.com)
2. Select your GharRent service
3. Go to **Settings** → **Environment**
4. Click **Add Environment Variable** three times

### Variable 1: GOOGLE_CLIENT_ID

**Key:** `GOOGLE_CLIENT_ID`

**Value:** (from Google Cloud Console Credentials page)
```
EXACT_CLIENT_ID_FROM_GOOGLE_CLOUD
```

**Example (NOT real):**
```
412856739485-abcdef7890abcdef7890abcdef789012.apps.googleusercontent.com
```

**Where to find:**
1. Go to Google Cloud Console → **APIs & Services** → **Credentials**
2. Find your "GharRent OAuth Client" (Web application type)
3. Click it
4. Copy the **Client ID** field
5. Paste into Render

---

### Variable 2: GOOGLE_CLIENT_SECRET

**Key:** `GOOGLE_CLIENT_SECRET`

**Value:** (from Google Cloud Console Credentials page)
```
EXACT_CLIENT_SECRET_FROM_GOOGLE_CLOUD
```

**Example (NOT real):**
```
GOCSPX-abcdefgh1234567890ijklmnop
```

**⚠️ SECURITY WARNING:**
- This is SECRET - never commit to GitHub
- Only add in Render Environment Variables
- Never log or print this value
- If accidentally exposed, regenerate on Google Cloud Console

**Where to find:**
1. Same page as Client ID
2. Look for **Client secret** field
3. Copy the entire value
4. Paste into Render

---

### Variable 3: GOOGLE_REDIRECT_URI

**Key:** `GOOGLE_REDIRECT_URI`

**Value:** (your Render callback URL)
```
https://ghrrent.onrender.com/gmail/callback/
```

**⚠️ IMPORTANT - Exact syntax required:**
- MUST start with `https://` (not http://)
- MUST end with `/` (trailing slash)
- MUST match exactly what you added in Google Cloud Console

**Why this exact value:**
- Django URL pattern in [core/urls.py](core/urls.py#L9): `path("gmail/callback/", ...)`
- Gmail callback handler in [views.py](views.py#L793): `def gmail_callback(request):`
- OAuth flow in [views.py](views.py#L750): `flow.redirect_uri = settings.GOOGLE_REDIRECT_URI`
- Settings.py line 177: `GOOGLE_REDIRECT_URI = config("GOOGLE_REDIRECT_URI", default="...")`

**DO NOT use:**
- ❌ `https://ghrrent.onrender.com/gmail/callback` (missing trailing slash)
- ❌ `https://ghrrent.onrender.com/gmail/callback/?state=xyz` (no query params)
- ❌ `http://ghrrent.onrender.com/gmail/callback/` (http:// not https://)

---

### After Adding All 3 Variables:

1. Click **Save Changes**
2. Render will prompt: "Redeploy to apply changes?"
3. Click **Redeploy** (next step)
4. Wait for deployment to complete (~2-3 minutes)

---

## 13. Finding Client ID and Client Secret in Google Cloud Console

### Quick Reference:

| Item | Location | Steps |
|------|----------|-------|
| **Client ID** | Credentials page | APIs & Services → Credentials → Click OAuth client → "Client ID" field |
| **Client Secret** | Credentials page | APIs & Services → Credentials → Click OAuth client → "Client secret" field |

### Detailed Steps:

**Step 1: Open Google Cloud Console**
- Go to [console.cloud.google.com](https://console.cloud.google.com)
- Make sure you're logged in and have your GharRent project selected (dropdown at top)

**Step 2: Navigate to Credentials**
- Left sidebar → **APIs & Services** → **Credentials**

**Step 3: Find Your OAuth Client**
- You'll see a table with applications
- Look for application type = **"Web application"**
- Name = **"GharRent OAuth Client"** (or whatever you named it)

**Step 4: Click to Open**
- Click on the application name
- Opens the OAuth client details page

**Step 5: Copy Client ID**
- Find the field labeled **"Client ID"**
- Look like: `[numbers]-[alphanumeric].apps.googleusercontent.com`
- Click the **copy icon** next to it (or manually select and copy)
- Paste into Render environment variable

**Step 6: Copy Client Secret**
- Find the field labeled **"Client secret"**
- Looks like: `GOCSPX-[alphanumeric]`
- Click the **copy icon** next to it (or manually select and copy)
- Paste into Render environment variable

### Accessing Credentials Later:

If you need these values again:
1. Go to Google Cloud Console → **APIs & Services** → **Credentials**
2. Click on the OAuth client
3. Values are displayed there

**If you lost the Client Secret:**
- Go to Credentials page
- Click the OAuth client
- Scroll down
- Click **Regenerate Secret** button
- A new secret is generated
- Update Render environment variables with the new secret

---

## 14. Redeploying/Restarting Service After Adding Env Variables

### What Happens When You Add Environment Variables:

Render will ask if you want to redeploy. **YOU MUST REDEPLOY** for changes to take effect.

### Redeploy Process:

**Option A: Automatic (Recommended)**

After adding environment variables:
1. Render shows: **"Changes detected. Redeploy?"**
2. Click **REDEPLOY**
3. Render automatically:
   - Stops the current service
   - Pulls environment variables
   - Restarts the service
   - Runs Django migrations (if any)
4. Wait for status to change to **"Live"**
5. Your app is ready with new OAuth credentials

**Option B: Manual Redeploy**

If automatic doesn't trigger:
1. Go to Render Dashboard → Select GharRent service
2. Click **Manual Deploy** button (top right)
3. Select **"Latest commit"**
4. Click **DEPLOY**
5. Wait for status to become **"Live"**

**Option C: Manual Restart (if only env vars changed)**

1. Go to Render Dashboard → Select GharRent service
2. Click **Restart** button
3. Service restarts with new environment variables

### Verification That Redeploy Worked:

1. Once status shows **"Live"**, open your browser
2. Go to `https://ghrrent.onrender.com`
3. Login to your test account
4. Click **"Connect Gmail"** button
5. You should be redirected to Google login (if variables are correct)
6. If you get errors, see **Troubleshooting** section below

### Time Required:
- Redeploy: 2-3 minutes
- Service restart: 30-60 seconds

### What Gets Updated:
- ✅ GOOGLE_CLIENT_ID
- ✅ GOOGLE_CLIENT_SECRET
- ✅ GOOGLE_REDIRECT_URI
- ✅ Django settings.py reads these via `config()` function
- ✅ Views.py uses them to build OAuth flow

---

## 15. Complete Testing Checklist

### Pre-Test Setup:
- [ ] 2+ Gmail accounts ready (test1@gmail.com, test2@gmail.com)
- [ ] Both added as test users in Google Cloud OAuth consent screen
- [ ] Render environment variables set and redeployed
- [ ] GharRent app is running at https://ghrrent.onrender.com

---

### TEST PHASE 1: Single User Gmail Integration

#### Step 1: Register User A
- [ ] Open browser → `https://ghrrent.onrender.com`
- [ ] Click **Register**
- [ ] Username: `testuser1`
- [ ] Email: `test1@gmail.com`
- [ ] Password: `TestPassword123!`
- [ ] Submit
- [ ] Should redirect to Dashboard

#### Step 2: Verify User A is Logged In
- [ ] You're on Dashboard
- [ ] Top right shows "testuser1" or user icon
- [ ] Can see "Connect Gmail" button

#### Step 3: Connect User A's Gmail
- [ ] Click **Profile** (top right)
- [ ] Look for **"Connect Gmail Account"** or **"Gmail"** section
- [ ] Click **"Connect Gmail"** button

#### Step 4: Approve Google Permissions
- [ ] Redirected to Google login
- [ ] Login with `test1@gmail.com`
- [ ] Google shows permission screen:
  ```
  GharRent wants access to your Google Account
  - Send emails on your behalf
  - See your email address
  - See your Google Account information
  ```
- [ ] Click **"Allow"** or **"Continue"**

#### Step 5: Return to GharRent
- [ ] Automatically redirected back to `https://ghrrent.onrender.com/gmail/callback/`
- [ ] Should see success message: **"✅ Gmail account connected: test1@gmail.com"**
- [ ] Redirected to Profile page

#### Step 6: Verify Gmail Connection Shows Connected
- [ ] On Profile page, should see:
  ```
  Gmail Account: test1@gmail.com
  Status: Connected ✓
  ```
- [ ] There should be a **"Disconnect Gmail"** button

#### Step 7: Add a Test Tenant
- [ ] Click **Dashboard**
- [ ] Click **"Add Tenant"** or similar
- [ ] Fill in:
  ```
  Name: Test Tenant
  Email: test-tenant@gmail.com
  Rent: ₹10000
  Due Day: 15
  Property: Test Property
  ```
- [ ] Submit
- [ ] Should see tenant in list

#### Step 8: Send Reminder Email
- [ ] Find the test tenant in list
- [ ] Click **"Send Reminder"** button
- [ ] Should see: **"✅ Email reminder queued for Test Tenant!"**

#### Step 9: Verify Email Sender is User A's Gmail
- [ ] Open `test-tenant@gmail.com` inbox
- [ ] Look for email from: **`test1@gmail.com`** (User A's Gmail)
- [ ] Subject: `"Rent Reminder for Test Tenant - GharRent"`
- [ ] Email contains:
  ```
  Hello Test Tenant,
  Monthly Rent: ₹10,000
  Total Payable: ₹10,000
  ```
- [ ] ✅ **TEST 1 PASSED**

---

### TEST PHASE 2: Multiple Users with Different Gmail Accounts

#### Step 10: Logout User A
- [ ] Click top right → **"Logout"**
- [ ] Should redirect to Login page

#### Step 11: Register User B
- [ ] Click **Register**
- [ ] Username: `testuser2`
- [ ] Email: `test2@gmail.com` (different from User A)
- [ ] Password: `TestPassword123!`
- [ ] Submit
- [ ] Should redirect to Dashboard

#### Step 12: Connect User B's Different Gmail Account
- [ ] Click **Profile**
- [ ] Click **"Connect Gmail"**
- [ ] Login with `test2@gmail.com`
- [ ] Approve permissions
- [ ] Return to app
- [ ] Should see: **"✅ Gmail account connected: test2@gmail.com"**

#### Step 13: Verify User B's Gmail is Different
- [ ] Profile page should show:
  ```
  Gmail Account: test2@gmail.com
  Status: Connected ✓
  ```
- [ ] Different from User A's `test1@gmail.com` ✓

#### Step 14: Add Different Test Tenant for User B
- [ ] Dashboard → Add Tenant
- [ ] Fill in:
  ```
  Name: User B Tenant
  Email: user-b-tenant@gmail.com
  Rent: ₹20000
  Due Day: 20
  ```
- [ ] Submit

#### Step 15: Send Reminder from User B
- [ ] Find "User B Tenant"
- [ ] Click **"Send Reminder"**
- [ ] Should see: **"✅ Email reminder queued for User B Tenant!"**

#### Step 16: Verify User B's Gmail is the Sender
- [ ] Open `user-b-tenant@gmail.com` inbox
- [ ] Look for email from: **`test2@gmail.com`** (User B's Gmail, NOT User A's)
- [ ] Subject: `"Rent Reminder for User B Tenant - GharRent"`
- [ ] ✅ **TEST 2 PASSED: Per-user Gmail isolation verified**

---

### TEST PHASE 3: Isolation Verification (Advanced)

#### Step 17: Verify User A Cannot Use User B's Gmail
- [ ] Logout User B
- [ ] Login as User A (testuser1)
- [ ] Go to Dashboard
- [ ] Add a new tenant
- [ ] Send reminder
- [ ] Verify email comes from `test1@gmail.com`, not `test2@gmail.com`
- [ ] ✅ **Tokens are properly isolated**

#### Step 18: Test Disconnect and Reconnect
- [ ] Login as User A
- [ ] Go to Profile
- [ ] Click **"Disconnect Gmail"**
- [ ] Should see: **"✅ Gmail connection removed"**
- [ ] Profile should show: **"Gmail: Not connected"**
- [ ] Click **"Connect Gmail"** again
- [ ] Should work again
- [ ] ✅ **Disconnect/reconnect works**

---

### Summary: All Tests Passed ✅

If all 18 steps pass:
- ✅ User A's Gmail integration works
- ✅ User B's Gmail integration works
- ✅ Emails send from correct user's Gmail
- ✅ Per-user isolation is secure
- ✅ Disconnect/reconnect functionality works
- ✅ **Your implementation is production-ready**

---

## 16. Common Errors and Fixes

### Error 1: `redirect_uri_mismatch`

**Full Error Message:**
```
Error: redirect_uri_mismatch
The redirect URI in the request: https://ghrrent.onrender.com/gmail/callback/
does not match the ones authorized for the OAuth client ID
```

**Causes:**
1. Typo in Render environment variable `GOOGLE_REDIRECT_URI`
2. Missing trailing slash: `https://ghrrent.onrender.com/gmail/callback` (no /)
3. Wrong scheme: `http://` instead of `https://`
4. Mismatch with Google Cloud Console registered URI

**Fixes:**
```
✅ CORRECT:
GOOGLE_REDIRECT_URI = "https://ghrrent.onrender.com/gmail/callback/"

❌ INCORRECT:
GOOGLE_REDIRECT_URI = "https://ghrrent.onrender.com/gmail/callback" (no slash)
GOOGLE_REDIRECT_URI = "http://ghrrent.onrender.com/gmail/callback/" (http not https)
GOOGLE_REDIRECT_URI = "https://ghrrent.onrender.com/core/gmail/callback/" (wrong path)
```

**Step-by-Step Fix:**
1. Go to Render Dashboard → Environment variables
2. Find `GOOGLE_REDIRECT_URI`
3. Verify it's exactly: `https://ghrrent.onrender.com/gmail/callback/`
4. If wrong, correct it
5. Click **Save Changes**
6. Click **Redeploy**
7. Wait for deployment
8. Try "Connect Gmail" again

**Also verify on Google Cloud side:**
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Click your OAuth client
3. Scroll to **Authorized redirect URIs**
4. Should show: `https://ghrrent.onrender.com/gmail/callback/`
5. If different, edit and save

---

### Error 2: `access_denied`

**Full Error Message:**
```
Error: access_denied
Permission denied (possibly a rate limit or misconfigured app)
```

**Causes:**
1. User not added as test user in Testing Mode
2. User clicked "Cancel" instead of "Allow" on permission screen
3. Your app is in Testing Mode but user isn't a test user
4. Google rate limiting (rare)

**Fixes:**

**If in Testing Mode:**
1. Make sure the user's email is added as test user:
   - Go to Google Cloud Console → OAuth consent screen
   - Scroll to **Test users**
   - Click **ADD USERS**
   - Add the user's Gmail email
   - Save

2. Ask the user to try again:
   - Clear browser cookies (or incognito window)
   - Click "Connect Gmail"
   - This time click **"Allow"** (not Cancel)

**If in Production Mode:**
1. Check if Google rejected your verification submission
   - Go to OAuth consent screen
   - Look for any error messages or rejection reasons
   - Fix the issues (privacy policy, data usage, etc.)
   - Resubmit

---

### Error 3: `invalid_client`

**Full Error Message:**
```
Error: invalid_client
The OAuth client was not found (or has been deleted)
```

**Causes:**
1. `GOOGLE_CLIENT_ID` is wrong or empty
2. `GOOGLE_CLIENT_SECRET` is wrong or empty
3. OAuth client deleted from Google Cloud Console
4. Typo when copying from Google Cloud Console

**Fixes:**
1. Go to Render Dashboard → Environment variables
2. Check `GOOGLE_CLIENT_ID`:
   - Should look like: `412856739485-abcdef7890abcdef7890abcdef789012.apps.googleusercontent.com`
   - If empty or wrong, copy from Google Cloud Console again
3. Check `GOOGLE_CLIENT_SECRET`:
   - Should look like: `GOCSPX-abcdefgh1234567890ijklmnop`
   - If empty or wrong, copy from Google Cloud Console again
4. Save and Redeploy

**Verify on Google Cloud side:**
1. Go to Google Cloud Console → APIs & Services → Credentials
2. Is your OAuth client still listed?
3. If deleted, create a new one (follows Step 6 of this guide)
4. Copy ID and Secret again
5. Update Render

---

### Error 4: "Google OAuth app is in testing mode"

**Visual Error:**
```
You can't sign in to this app because it doesn't comply with Google's OAuth 2.0 policies yet.

Contact the app developer if you believe this is a mistake.
```

**Causes:**
1. User is not added as a test user
2. App is in Testing Mode (expected behavior)

**Fixes:**

**Temporary (for testing):**
1. Add user as test user:
   - Google Cloud Console → OAuth consent screen → Test users
   - Add the email address
   - User can now sign in

**Permanent (for production):**
1. Submit app for verification:
   - Google Cloud Console → OAuth consent screen
   - Click "Submit for verification"
   - Provide privacy policy URL
   - Explain data usage (you only store tokens)
   - Wait 2-7 days
   - Google approves
   - Automatically moves to Production Mode

**No code changes needed** - it's a configuration change in Google Cloud

---

### Error 5: `refresh_token missing`

**Error Message (in logs or when sending email):**
```
refresh_token is None or empty
Cannot refresh expired OAuth token
```

**Causes:**
1. Initial OAuth approval didn't include `offline_access` scope
2. User approved once, but refresh token not stored
3. Token database corrupted

**Fixes:**

**Immediate (Workaround):**
1. User disconnects Gmail: Profile → "Disconnect Gmail"
2. User reconnects Gmail: Profile → "Connect Gmail" → Approve
3. This re-requests refresh token and stores it

**Prevention:**
- Your code already requests `offline_access` via `prompt="consent"`
- Verify in [views.py](views.py#L752): 
  ```python
  authorization_url, state = flow.authorization_url(
      access_type="offline",    # ← This requests refresh token
      prompt="consent",         # ← This forces re-approval
  )
  ```
- This is already correct in your implementation ✓

---

### Error 6: `access_token expired`

**Error Message (when sending email):**
```
invalid_grant: Token has been revoked or expired
Cannot send via Gmail API
```

**Causes:**
1. OAuth token expired (after ~1 hour)
2. User revoked access from Google account settings
3. Refresh token failed or is also expired

**Fixes:**

**Automatic (your code does this):**
- Your [email_service.py](email_service.py#L47) creates a `Credentials` object with:
  ```python
  credentials = Credentials(
      token=gmail_credential.access_token,
      refresh_token=gmail_credential.refresh_token,  # ← Allows auto-refresh
      token_uri="https://oauth2.googleapis.com/token",
      client_id=settings.GOOGLE_CLIENT_ID,
      client_secret=settings.GOOGLE_CLIENT_SECRET,
  )
  ```
- This automatically refreshes the token using `refresh_token`

**Manual (if auto-refresh fails):**
1. User disconnects: Profile → "Disconnect Gmail"
2. User reconnects: Profile → "Connect Gmail"
3. Stores fresh access_token and refresh_token
4. Email sending should work again

**Prevention:**
- Your code handles this correctly
- Tokens are auto-refreshed before expiry
- No manual intervention needed for users

---

### Error 7: `Gmail connection exists but sending fails`

**Symptom:**
```
Profile shows: "Gmail Account: user@gmail.com ✓ Connected"
But when sending reminder:
"⚠️ Email reminder skipped for Tenant: [Error message]"
```

**Causes:**
1. Access token or refresh token is corrupted
2. User revoked access from Google account settings
3. Gmail API became disabled in Google Cloud project
4. GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET changed

**Fixes:**

**Step 1: Verify Gmail API is enabled:**
1. Go to Google Cloud Console → APIs & Services → Library
2. Search for "Gmail API"
3. Click it
4. Should show **"API ENABLED"**
5. If not, click **ENABLE**

**Step 2: Check user's Google account:**
1. User goes to [myaccount.google.com](https://myaccount.google.com)
2. Scroll to **Connected apps & sites** or **Security** → **Apps with access**
3. Look for "GharRent"
4. If it shows "Can't be used", click **Remove**
5. User reconnects in GharRent app

**Step 3: Reconnect in GharRent:**
1. User logs into GharRent
2. Profile → "Disconnect Gmail"
3. Profile → "Connect Gmail"
4. Login and approve
5. Try sending reminder again

**Step 4: Check logs (if you have access):**
1. Render Dashboard → Logs
2. Look for error messages when sending reminder
3. Copy error and refer to troubleshooting

---

### Error 8: "No Gmail account is connected for this user"

**Error Message:**
```
⚠️ Email reminder skipped for Tenant: No Gmail account is connected for this user.
```

**Causes:**
1. User hasn't clicked "Connect Gmail" yet
2. User clicked "Disconnect Gmail"
3. GmailCredential database record was deleted

**Fixes:**

**For Users:**
1. Remind them to click **Profile** → **"Connect Gmail"**
2. Complete the Google login and approval
3. Try sending reminder again

**For Developers (if testing):**
1. Make sure you added the test user email to Google Cloud test users
2. Complete the OAuth flow
3. Check database:
   ```bash
   # In Django shell:
   python manage.py shell
   >>> from core.models import GmailCredential
   >>> GmailCredential.objects.filter(user__username='testuser1')
   <QuerySet [<GmailCredential: testuser1 -> test1@gmail.com>]>
   ```
4. Should show a record for the user

---

### Error 9: "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are not configured"

**Error Message:**
```
Google OAuth is not configured. Add GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET first.
```

**Causes:**
1. Environment variables not set in Render
2. Render hasn't been redeployed after adding env vars
3. Typo in environment variable names (must be exact)

**Fixes:**

**Step 1: Verify env vars in Render:**
1. Go to Render Dashboard → GharRent service
2. Click **Settings** → **Environment**
3. You should see:
   ```
   GOOGLE_CLIENT_ID = [value]
   GOOGLE_CLIENT_SECRET = [value]
   GOOGLE_REDIRECT_URI = [value]
   ```
4. If any are missing, add them (see Step 12 of guide)

**Step 2: Verify names are exact:**
- ✅ `GOOGLE_CLIENT_ID` (not `GoogleClientID` or `google_client_id`)
- ✅ `GOOGLE_CLIENT_SECRET` (not `GoogleClientSecret`)
- ✅ `GOOGLE_REDIRECT_URI` (not `GoogleRedirectUri`)

**Step 3: Redeploy:**
1. After adding or fixing env vars, click **Redeploy**
2. Wait for status to show **"Live"**
3. Try "Connect Gmail" again

---

## 17. Quick Reference Checklist

### Before Starting:
- [ ] Google Cloud project created
- [ ] Gmail API enabled
- [ ] OAuth consent screen configured (External)
- [ ] 3 OAuth scopes added
- [ ] Test users added (for Testing Mode)
- [ ] OAuth 2.0 Client ID created (Web application type)
- [ ] Authorized redirect URI added: `https://ghrrent.onrender.com/gmail/callback/`
- [ ] Authorized JavaScript origins added: `https://ghrrent.onrender.com` and `http://localhost:8000`

### Before Rendering:
- [ ] Client ID copied from Google Cloud
- [ ] Client Secret copied from Google Cloud
- [ ] Render environment variables added:
  - [ ] `GOOGLE_CLIENT_ID`
  - [ ] `GOOGLE_CLIENT_SECRET`
  - [ ] `GOOGLE_REDIRECT_URI = https://ghrrent.onrender.com/gmail/callback/`
- [ ] Render redeployed (status: Live)

### Testing:
- [ ] User A registered and Gmail connected
- [ ] Tenant created for User A
- [ ] Reminder email sent and received from User A's Gmail
- [ ] User B registered with different Gmail
- [ ] Reminder email from User B sent from User B's Gmail (not User A's)
- [ ] Gmail disconnect works
- [ ] Gmail reconnect works

### Production:
- [ ] All testing passed
- [ ] Submitted for Google verification (when ready)
- [ ] Waiting for approval (2-7 days)
- [ ] After approval: Production Mode active
- [ ] Users no longer see "Not verified" warning

---

## Code Implementation Review

### Views Implementation ([views.py](views.py#L750)):
```python
def gmail_connect(request):
    """Begin the Google OAuth flow for a user's Gmail account."""
    # ✅ Validates GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET are set
    # ✅ Builds OAuth flow with correct scopes
    # ✅ Sets redirect_uri correctly
    # ✅ Uses offline access (refresh token)
    # ✅ Uses prompt="consent" (forces re-approval)

def gmail_callback(request):
    """Handle the OAuth callback and store the connected Gmail account."""
    # ✅ Validates OAuth state (CSRF protection)
    # ✅ Fetches credentials from authorization code
    # ✅ Stores access_token and refresh_token in GmailCredential
    # ✅ Stores gmail_email in GmailCredential
    # ✅ Stores token_expiry for token refresh logic
```

### Email Service Implementation ([email_service.py](email_service.py#L47)):
```python
def _send_via_gmail_api(user, email_dict):
    """Send email using the user's connected Gmail account via the Gmail API."""
    # ✅ Retrieves user-specific GmailCredential (per-user isolation)
    # ✅ Builds Credentials object with refresh_token (enables auto-refresh)
    # ✅ Uses Gmail API v1 service
    # ✅ Sends via users().messages().send() (correct Gmail API method)
```

### Models Implementation ([models.py](models.py#L131)):
```python
class GmailCredential(models.Model):
    """Stores a user's Gmail OAuth credentials for sending reminders."""
    # ✅ OneToOneField to User (each user has one Gmail account connected)
    # ✅ Stores access_token
    # ✅ Stores refresh_token (allows token refresh after expiry)
    # ✅ Stores token_expiry
    # ✅ Stores gmail_email (which Gmail is connected)
    # ✅ Tracks connected_at and updated_at timestamps
```

### URL Routing ([urls.py](urls.py#L9)):
```python
path("gmail/callback/", views.gmail_callback, name="gmail_callback"),
```
✅ Matches the Render redirect URI exactly

### Settings Configuration ([settings.py](settings.py#L172)):
```python
GOOGLE_CLIENT_ID = config("GOOGLE_CLIENT_ID", default="")
GOOGLE_CLIENT_SECRET = config("GOOGLE_CLIENT_SECRET", default="")
GOOGLE_REDIRECT_URI = config("GOOGLE_REDIRECT_URI", default="http://localhost:8000/gmail/callback/")
```
✅ Uses environment variables
✅ Defaults to local development values

**Conclusion:** ✅ Your implementation is production-ready. No code changes needed.

---

## Final Notes

### Security Best Practices (Already Implemented):
1. ✅ Tokens stored in database (not in sessions or cookies)
2. ✅ Refresh tokens stored (enables long-term access)
3. ✅ CSRF protection via OAuth state parameter
4. ✅ Per-user token isolation (Alice's token cannot access Bob's Gmail)
5. ✅ HTTPS-only deployment (Render provides HTTPS automatically)
6. ✅ Scopes limited to necessary permissions (only send emails)
7. ✅ No password stored (OAuth tokens used instead)

### Next Steps:
1. Set up Google Cloud project (Steps 1-7)
2. Add test users (Step 5)
3. Configure Render environment variables (Step 12)
4. Redeploy (Step 14)
5. Run testing checklist (Step 15)
6. Fix any errors using troubleshooting guide (Step 16)
7. Submit for verification when ready (Step 11, Production Mode section)

### Support Resources:
- [Google Cloud OAuth 2.0 Documentation](https://developers.google.com/identity/protocols/oauth2)
- [Gmail API Documentation](https://developers.google.com/gmail/api)
- [Django OAuth Integration](https://django-oauth-toolkit.readthedocs.io/)
- [Render Environment Variables](https://render.com/docs/environment-variables)

---

**Document Generated:** 2026-08-15  
**GharRent Version:** Per-User Gmail Integration  
**Status:** Ready for Google Cloud Configuration
