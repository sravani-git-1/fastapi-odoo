# FastAPI Odoo Integration - Setup Guide

## Overview
This application provides CRUD (Create, Read, Update, Delete) operations for Odoo partners (customers/vendors) via REST API.

---

## LOCAL DEVELOPMENT SETUP

### Step 1: Configure Odoo Credentials Locally

Create a `config.json` file in the project root:

```json
{
  "ODOO_URL": "https://odoo.avowaldatasystems.in/",
  "ODOO_DB": "odooKmmDb",
  "ODOO_USERNAME": "rajugenai@gmail.com",
  "ODOO_PASSWORD": "P@$$W0rd&$@"
}
```

**Important:** Do NOT commit `config.json` to Git (it's already in `.gitignore`)

### Step 2: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 3: Run Locally

```bash
uvicorn main:app --reload
```

Access the API at: `http://localhost:8000`

---

## RENDER DEPLOYMENT SETUP

### Step 1: Set Environment Variables

1. Go to your Render service dashboard
2. Click **Settings** → **Environment** 
3. Add these 4 environment variables:

| Key | Value |
|-----|-------|
| `ODOO_URL` | `https://odoo.avowaldatasystems.in/` |
| `ODOO_DB` | `odooKmmDb` |
| `ODOO_USERNAME` | `rajugenai@gmail.com` |
| `ODOO_PASSWORD` | `P@$$W0rd&$@` |

**Important Notes:**
- Use exact values from your `config.json`
- Special characters (like `@`, `$`, `&`) are fine - Render handles them automatically
- Do NOT include `config.json` in your Render deployment

### Step 2: Redeploy Service

After setting environment variables:
1. Click **Manual Deploy**
2. Wait for deployment to complete
3. Test the API

---

## API ENDPOINTS

### Authentication Test
```
GET /odoo/auth-verify
```
Response: `{"authenticated": true, "uid": 2, "db": "odooKmmDb", "user": "rajugenai@gmail.com"}`

### Get All Customers
```
GET /odoo/customers
```

### Get All Vendors
```
GET /odoo/vendors
```

### Get Partners (Flexible)
```
GET /odoo/partners?role=customer&limit=100
```
Parameters:
- `role`: `customer`, `vendor`, or `all`
- `limit`: max records to return

### Create Partner
```
POST /odoo/partners
Content-Type: application/json

{
  "name": "Partner Name",
  "email": "email@example.com",
  "phone": "+1234567890",
  "mobile": "+1234567890",
  "company_type": "person",
  "vat": "123456789",
  "role": "customer"
}
```

Response includes: `created`, `id`, `roles`, `is_customer`, `is_vendor`

### Update Partner
```
PUT /odoo/partners/{partner_id}
Content-Type: application/json

{
  "name": "New Name",
  "email": "newemail@example.com",
  "role": "vendor"
}
```

Response includes: `updated`, `roles`, `verified_data`

### Delete Partner
```
DELETE /odoo/partners/{partner_id}
```

Response includes: `deleted` flag (true/false)

---

## RESPONSE FORMAT

### Partner Object
```json
{
  "id": 123,
  "name": "Partner Name",
  "email": "email@example.com",
  "phone": "+1234567890",
  "mobile": "+1234567890",
  "company_type": "person",
  "vat": "123456789",
  "customer_rank": 1,
  "supplier_rank": 0,
  "roles": ["customer"],
  "is_customer": true,
  "is_vendor": false
}
```

### Success Response
```json
{
  "message": "Operation successful",
  "created": true,
  "id": 123,
  "data": {...}
}
```

### Error Response
```json
{
  "detail": "Error message describing what went wrong"
}
```

---

## TROUBLESHOOTING

### "Missing required configuration"
**Solution:** 
- Local: Create `config.json` with all 4 keys
- Render: Add all 4 environment variables in Settings

### "Odoo authentication failed"
**Solution:** 
- Check credentials in `config.json` (local) or environment variables (Render)
- Verify email and password are correct
- Test password doesn't have trailing spaces

### "Odoo database error: Check ODOO_DB"
**Solution:**
- Verify database name matches Odoo instance
- Check special characters are not being escaped

### "Odoo connection error: Check ODOO_URL"
**Solution:**
- Verify URL is correct and ends with `/`
- Check Odoo instance is accessible
- Test connection from your location

---

## ROLE MANAGEMENT

### Creating Partners with Roles

**Customer Only:**
```json
{
  "name": "Customer Name",
  "role": "customer"
}
```

**Vendor Only:**
```json
{
  "name": "Vendor Name",
  "role": "vendor"
}
```

**Both Customer & Vendor:**
```json
{
  "name": "Partner Name",
  "role": "all"
}
```

The response will always include:
- `roles`: Array of roles `["customer"]`, `["vendor"]`, `["customer", "vendor"]`, or `["other"]`
- `is_customer`: Boolean true/false
- `is_vendor`: Boolean true/false

---

## N8N INTEGRATION

When using with N8N:

1. **Create Partner:**
   - Check response has `"created": true` before proceeding
   - Use `id` field for future updates

2. **Update Partner:**
   - Check response has `"updated": true`
   - Use `verified_data` to confirm changes

3. **Delete Partner:**
   - Check response has `"deleted": true`
   - Confirm deletion succeeded before logging

---

## PRODUCTION CHECKLIST

- [x] All environment variables set on Render
- [x] Odoo credentials verified and working
- [x] API endpoints tested
- [x] Error handling in place
- [x] Role management working (customer/vendor/all)
- [x] Verification in place (created/updated/deleted flags)
- [x] N8N workflow integration tested

---

## SUPPORT

If issues persist after following this guide:
1. Check Render logs: Service → Logs
2. Verify environment variables are exactly as specified
3. Test local version first with `config.json`
4. Compare working local config with Render env vars

