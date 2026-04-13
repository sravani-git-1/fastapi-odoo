# Authentication (401) Error Debugging Guide

## Error: "401: Odoo authentication failed: Invalid credentials"

This means your credentials are not being accepted by Odoo. Here's how to debug it:

---

## Step 1: Test Configuration Locally

Run the diagnostic script first:

```bash
python test_odoo_connection.py
```

This will test:
- ✅ Is Odoo URL reachable?
- ✅ Can we connect to XML-RPC?
- ✅ Are the credentials valid?
- ✅ Can we read partners?

If this passes locally, your config is correct.

---

## Step 2: Check Credentials Exactly Match

Your credentials **MUST** match exactly (case-sensitive, no extra spaces):

```json
{
  "ODOO_URL": "https://odoo.avowaldatasystems.in/",
  "ODOO_DB": "odooKmmDb",
  "ODOO_USERNAME": "rajugenai@gmail.com",
  "ODOO_PASSWORD": "P@$$W0rd&$@"
}
```

### Common Issues:
- ❌ Extra space at end: `"rajugenai@gmail.com "` (notice the space)
- ❌ Wrong casing: `"rajugenai@GMAIL.com"` (emails are case-insensitive but be consistent)
- ❌ Wrong password: Even one character off will fail
- ❌ Special characters: `P@$$W0rd&$@` must be exact

---

## Step 3: For Render Deployment

1. Go to Render Dashboard
2. Select your service
3. Click **Settings** → **Environment**
4. Make sure ALL 4 variables are set:

```
ODOO_URL=https://odoo.avowaldatasystems.in/
ODOO_DB=odooKmmDb
ODOO_USERNAME=rajugenai@gmail.com
ODOO_PASSWORD=P@$$W0rd&$@
```

5. Click **Manual Deploy**
6. Wait for deployment (1-2 minutes)

---

## Step 4: Check Logs

### Local Logs:
Run your local server:
```bash
uvicorn main:app --reload
```

Look for:
```
============================================================
CONFIGURATION LOADED SUCCESSFULLY
Source: config.json
URL: https://odoo.avowaldatasystems.in/
Database: odooKmmDb
Username: rajugenai@gmail.com
Password length: 15 characters
============================================================
```

Then when you test authentication, look for:
```
============================================================
ODOO AUTHENTICATION DEBUG
URL: https://odoo.avowaldatasystems.in/
Database: odooKmmDb
Username: rajugenai@gmail.com
Password length: 15 chars
Attempting authenticate call...
Authentication returned: 2
============================================================
```

If `Authentication returned: 0`, the user doesn't exist.
If it's empty or an exception, check the AUTH ERROR section.

### Render Logs:
1. Go to Render Dashboard
2. Select your service
3. Click **Logs** tab
4. Look for the same `============` sections

---

## Step 5: Verify Odoo User

The user `rajugenai@gmail.com` must:

1. ✅ Exist in Odoo
2. ✅ Have correct password
3. ✅ NOT be deactivated
4. ✅ Have API access enabled (usually default for Internal Users)

How to check in Odoo:
1. Log in to Odoo as an admin
2. Go to **Settings** → **Users & Companies** → **Users**
3. Find `rajugenai@gmail.com`
4. Check if user is **Active** (not greyed out)
5. Check if user has **Access Rights**

---

## Step 6: Database Verification

The database `odooKmmDb` must:

1. ✅ Exist in your Odoo instance
2. ✅ Be running and not in maintenance
3. ✅ Have the `res.partner` model (standard in all Odoo installations)

How to check:
1. Visit https://odoo.avowaldatasystems.in/
2. You should see database options to log into
3. `odooKmmDb` should be available
4. You should be able to log in with the credentials

---

## Step 7: Password Special Characters

Your password has special characters: `P@$$W0rd&$@`

Make sure it doesn't have any leading/trailing spaces:

```
GOOD:  P@$$W0rd&$@
BAD:   P@$$W0rd&$@ (space at end)
BAD:    P@$$W0rd&$@ (space at start)
```

On Render, paste the exact password without quotes in the value field.

---

## Full Debugging Checklist

- [ ] Ran `python test_odoo_connection.py` - all tests passed
- [ ] Verified config.json has exact credentials
- [ ] Verified no extra spaces in credentials
- [ ] User `rajugenai@gmail.com` exists in Odoo
- [ ] User is Active (not deactivated)
- [ ] Database `odooKmmDb` exists and is running
- [ ] URL `https://odoo.avowaldatasystems.in/` is accessible
- [ ] Environment variables set on Render (if deploying there)
- [ ] Clicked Manual Deploy on Render
- [ ] Waited 1-2 minutes for deployment to complete
- [ ] Checked Render logs for `CONFIGURATION LOADED SUCCESSFULLY`

---

## If Still Failing - Collect This Info

Run locally with:
```bash
python test_odoo_connection.py 2>&1 | tee diagnostic.log
```

This creates a `diagnostic.log` file showing:
- Exact configuration values being used
- All connection test results
- Any error messages

Share this log if you're still having issues.

---

## Common Resolution Steps

**Most Common Fix:**
```bash
# Local - test with this exact command:
python test_odoo_connection.py

# If it passes locally, issue is on Render:
# 1. Go to Render Settings → Environment
# 2. Delete ALL 4 Odoo variables
# 3. Add them again - copy-paste from config.json
# 4. Click Manual Deploy
# 5. Wait 2 minutes and test again
```

---

## Need More Help?

Provide us with:
1. Output of `python test_odoo_connection.py`
2. Your Render logs (copy the error section)
3. Confirm your credentials are correct (without sharing the actual password)
4. Confirm the Odoo user exists and is active

