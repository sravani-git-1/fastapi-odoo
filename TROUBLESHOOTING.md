# Troubleshooting Guide - Odoo FastAPI Integration

## Error Analysis & Solutions

### Overview of Changes
All errors now include **full details** (no truncation), plus comprehensive logging to stderr for debugging.

Each operation (GET, CREATE, UPDATE, DELETE) now logs:
- **DEBUG messages** showing what data is being sent
- **Full error messages** from Odoo 
- **Verification steps** to confirm operations succeeded

---

## Common Errors & Solutions

### ❌ "502: Odoo database error: Check ODOO_DB configuration"

**Causes:**
1. Database name (`ODOO_DB`) doesn't exist in Odoo
2. Typo in database name
3. Odoo database is offline or unreachable
4. Wrong Odoo instance URL

**How to Fix:**
1. Verify database name exists in your Odoo instance
2. Check Render environment variable: `ODOO_DB=odooKmmDb` (exactly)
3. Verify database is running: `https://odoo.avowaldatasystems.in/` can be accessed
4. **DEBUG:** Check stderr logs for the full error message from Odoo

---

### ❌ "502: Odoo connection error: Check ODOO_URL"

**Causes:**
1. Wrong Odoo URL
2. Odoo instance is down
3. Network connectivity issue
4. URL doesn't end with `/`

**How to Fix:**
1. Verify URL is correct: `https://odoo.avowaldatasystems.in/`
2. Test URL in browser - should show Odoo login
3. Ensure URL ends with `/`
4. Check network connectivity from Render server

---

### ❌ "401: Invalid Odoo credentials"

**Causes:**
1. Wrong email/username
2. Wrong password
3. Special characters in password not escaped
4. User doesn't have API access

**How to Fix:**
1. Verify email: `rajugenai@gmail.com` (exactly)
2. Verify password: `P@$$W0rd&$@` (exactly, with special characters)
3. Test credentials locally with config.json first
4. Check if user has proper permissions in Odoo

---

### ❌ "502: Odoo data retrieval error"

**Causes:**
1. Invalid field names in search query
2. Corrupted data in Odoo database
3. Missing Odoo modules
4. Field validation errors

**How to Fix:**
1. Check stderr logs - will show exact field that's invalid
2. Verify `customer_rank` and `supplier_rank` fields exist in your Odoo instance
3. Try basic query first: `GET /odoo/customers`
4. If specific roles fail, check Odoo configuration

---

### ❌ "Invalid field '...' on model 'res.partner'"

**Causes:**
1. Using field that doesn't exist in Odoo
2. Odoo doesn't have required modules installed
3. Field name typo

**Solution:**
- Our code uses only these fields (verified to exist):
  - `customer_rank` (integer)
  - `supplier_rank` (integer)
  - `name`, `email`, `phone`, `mobile`, `company_type`, `vat`
  
- If you get "Invalid field" errors, your Odoo instance may not have standard modules

---

## How to Debug Issues

### Step 1: Check Local Logs
Run locally and check stdout/stderr:
```bash
uvicorn main:app --reload
```
Error messages will appear in the console with DEBUG info.

### Step 2: Check Render Logs
1. Go to Render dashboard
2. Select your service
3. Click **Logs** tab
4. Look for messages between `====================` lines

### Step 3: Test Each Operation

**1. Test Authentication:**
```bash
curl https://your-render-url.onrender.com/odoo/auth-verify
```
Response should be:
```json
{"authenticated": true, "uid": 2, "db": "odooKmmDb", "user": "rajugenai@gmail.com"}
```

**2. Test Get Customers:**
```bash
curl https://your-render-url.onrender.com/odoo/customers
```

**3. Test Get Vendors:**
```bash
curl https://your-render-url.onrender.com/odoo/vendors
```

**4. Test Get All:**
```bash
curl https://your-render-url.onrender.com/odoo/partners?role=all
```

**5. Test Create:**
```bash
curl -X POST https://your-render-url.onrender.com/odoo/partners \
  -H "Content-Type: application/json" \
  -d '{"name": "Test Partner", "role": "customer"}'
```

---

## Log Message Locations

### Authentication Errors
```
============================================================
AUTH ERROR:
[Full traceback and error message here]
============================================================
```

### Search/Read Errors
```
============================================================
GET PARTNERS ERROR:
[Full error message here]
============================================================
```

### Create Errors
```
============================================================
CREATE ERROR:
[Full error message here]
============================================================
```
Or
```
============================================================
CREATE PARTNER ERROR:
[Full error message here]
============================================================
```

### Update Errors
```
============================================================
UPDATE ERROR:
[Full error message here]
============================================================
```

### Delete Errors
```
============================================================
DELETE ERROR:
[Full error message here]
============================================================
```

---

## Configuration Verification

### Local Development
1. Create `config.json` with:
```json
{
  "ODOO_URL": "https://odoo.avowaldatasystems.in/",
  "ODOO_DB": "odooKmmDb",
  "ODOO_USERNAME": "rajugenai@gmail.com",
  "ODOO_PASSWORD": "P@$$W0rd&$@"
}
```

2. Run and check logs:
```bash
uvicorn main:app --reload
```

### Render Deployment
1. Go to Settings → Environment
2. Verify these 4 variables are set:
   - `ODOO_URL`: `https://odoo.avowaldatasystems.in/`
   - `ODOO_DB`: `odooKmmDb`
   - `ODOO_USERNAME`: `rajugenai@gmail.com`
   - `ODOO_PASSWORD`: `P@$$W0rd&$@`

3. Click Manual Deploy
4. Check logs after ~1 minute

---

## Testing Checklist

- [ ] Can access Odoo instance in browser: https://odoo.avowaldatasystems.in/
- [ ] Odoo database `odooKmmDb` exists
- [ ] User `rajugenai@gmail.com` can login to Odoo
- [ ] User has API access enabled
- [ ] `customer_rank` and `supplier_rank` fields exist
- [ ] Local `config.json` works
- [ ] Environment variables set on Render
- [ ] `/odoo/auth-verify` returns success
- [ ] `/odoo/customers` returns partners
- [ ] `/odoo/vendors` returns partners
- [ ] `/odoo/partners?role=all` returns all partners

---

## Still Having Issues?

1. **Share the exact error message** from the API response
2. **Share the logs** from between the `====` lines
3. **Verify configuration** locally first before testing on Render
4. **Check Odoo instance** directly - is it accessible and working?
5. **Verify user permissions** - does the user have API access in Odoo?

---

## Field Reference

These are the **only fields** used by this API:

### Search/Filter Fields (must exist):
- `customer_rank` - Integer, > 0 means customer
- `supplier_rank` - Integer, > 0 means vendor

### Information Fields (read-only):
- `id` - Partner ID
- `name` - Partner name
- `email` - Email address
- `phone` - Phone number
- `mobile` - Mobile number
- `company_type` - "person" or "company"
- `vat` - Tax ID

### Computed Fields (calculated by API):
- `roles` - Array of "customer", "vendor", or ["other"]
- `is_customer` - Boolean
- `is_vendor` - Boolean

---

## Version Info

- **API Framework:** FastAPI
- **Odoo Integration:** XML-RPC
- **Python Version:** 3.8+
- **Last Updated:** 2026-04-13

