# Deployment Guide - Render

## Problem
Environment variables with special characters (`@`, `$`, `&`) don't work reliably on Render because the shell interprets these characters.

## Solution
Use a `config.json` file instead of environment variables on Render.

### Steps

1. **Create `config.json` in your repository root** (it's in `.gitignore` so real credentials won't be committed):

```json
{
  "ODOO_URL": "https://your-instance.odoo.com/",
  "ODOO_DB": "your_database_name",
  "ODOO_USERNAME": "your_email@example.com",
  "ODOO_PASSWORD": "your_password_with_special_chars"
}
```

2. **Push to Git** (don't worry - `config.json` is in `.gitignore`)

3. **On Render:**
   - Go to your service settings → Code & Builds → Build Command
   - Make sure you have a `build.sh` or similar that deploys `config.json`
   - Or manually create it in Render's File Storage

4. **Redeploy** your service

### Local Development

For local development, use `.env` file:
```
ODOO_URL=https://your-instance.odoo.com/
ODOO_DB=your_database_name
ODOO_USERNAME=your_email@example.com
ODOO_PASSWORD=your_password
```

Then run:
```bash
python -m uvicorn main:app --reload
```

## Troubleshooting

When the app starts, you'll see:
```
[INFO] Configuration Loading:
Running on Render: true/false
Env vars corrupted: true/false
```

- If `Env vars corrupted: true`, it means the app fell back to `config.json`
- Check `config.json` exists in your app directory on Render
