# 🚀 Render Deployment Guide

## The Problem

When you add environment variables with special characters (`@`, `$`, `&`) on Render, they get corrupted because the shell interprets these characters. This causes your **password to leak into the database name field**, resulting in:

```
psycopg2.OperationalError: connection to server at "db" (172.21.0.2), port 5432 
failed: FATAL:  database "P@$W0rd&$@" does not exist
```

## The Solution ✅

Use a **`config.json`** file instead of environment variables. This file is NOT gitignored and will be deployed to Render.

---

## Step-by-Step Deployment to Render

### 1. Create `config.json` with Your Credentials

In your project root, create `config.json`:

```json
{
  "ODOO_URL": "https://odoo.avowaldatasystems.in/",
  "ODOO_DB": "odooKmmDb",
  "ODOO_USERNAME": "rajugenai@gmail.com",
  "ODOO_PASSWORD": "P@$$W0rd&$@"
}
```

**⚠️ WARNING:** This file contains real credentials. Be careful not to accidentally commit it to a public repository!

### 2. Commit and Push to Git

```bash
git add config.json
git commit -m "Add Odoo configuration"
git push
```

### 3. On Render Dashboard

1. Go to your FastAPI service
2. Click **"Manual Deploy"** or **"Redeploy"**
3. Wait for deployment to complete

### 4. Verify Deployment

Check the **Logs** tab. You should see:

```
════════════════════════════════════════════════════════════════
[INFO] CONFIGURATION LOADING
════════════════════════════════════════════════════════════════
Script location: /opt/render/project/src
Config file path: /opt/render/project/src/config.json
Config file exists: True
Running on Render: true

✅ Loaded from config.json
   - ODOO_URL: https://odoo.avowaldatasystems.in/...
   - ODOO_DB: odooKmmDb
   - ODOO_USERNAME: rajugenai@gmail.com
   - ODOO_PASSWORD: ******** (length: 15)
════════════════════════════════════════════════════════════════
```

---

## Local Development

### Option 1: Using `.env` file

Create `.env` in your project root:

```
ODOO_URL=https://odoo.avowaldatasystems.in/
ODOO_DB=odooKmmDb
ODOO_USERNAME=rajugenai@gmail.com
ODOO_PASSWORD=P@$$W0rd&$@
```

Then run:

```bash
python -m uvicorn main:app --reload
```

### Option 2: Using `config.json`

The app will automatically load `config.json` if it exists, so you can use the same file for local dev and Render.

---

## Troubleshooting

### ❌ Error: "config.json NOT found"

**Solution:** Make sure `config.json` is committed and pushed to git:

```bash
git add config.json
git commit -m "Add config"
git push
```

Then redeploy on Render.

### ❌ Error: "ODOO_DB contains special chars"

**Solution:** The environment variables on Render are still corrupted. Delete any Render environment variables you set and make sure `config.json` exists.

### ✅ To Verify Everything Works

Try calling your API:

```bash
curl https://fastapi-odoo.onrender.com/odoo/partners?role=all&limit=100
```

Should return partner data, not a 502 error.

---

## Security Notes

- `config.json` is NOT in `.gitignore` and **will be committed to git**
- Only use this with a **private repository**
- If your repository is public, store credentials in **Render's Secret Files** instead

### Using Render Secret Files (Advanced)

1. Go to your service → **Settings** → **Environment**
2. Click **"Add Secret File"**
3. Set the file path to `config.json` and paste the content
4. Render will store it securely and mount it as a file

---

## What the App Does on Startup

1. **Looks for `config.json`** → Uses it if found ✅
2. **Falls back to env variables** → Only if `config.json` missing
3. **Falls back to `.env` file** → For local development
4. **Validates all values** → Exits with clear error if missing

This ensures maximum compatibility across Render, local dev, and different environments.

