# Quick Start - Render Deployment

## The Issue You're Facing
Your password with special chars (`@$&`) is being corrupted on Render, appearing as the database name in the error.

## The Fix (3 Steps)

### Step 1: Make sure `config.json` exists
```json
{
  "ODOO_URL": "https://odoo.avowaldatasystems.in/",
  "ODOO_DB": "odooKmmDb",
  "ODOO_USERNAME": "rajugenai@gmail.com",
  "ODOO_PASSWORD": "P@$$W0rd&$@"
}
```

### Step 2: Push to git
```bash
git add config.json
git commit -m "Add Odoo config"
git push
```

### Step 3: Redeploy on Render
- Go to your Render dashboard
- Click "Manual Deploy" / "Redeploy latest commit"

That's it! ✅

## Verify It Works
When the app starts, logs should show:
```
✅ Loaded from config.json
   - ODOO_DB: odooKmmDb
```

If it shows `ODOO_DB: P@$W0rd&$@`, then `config.json` wasn't found.

## For Local Development
Create `.env` instead:
```
ODOO_URL=https://odoo.avowaldatasystems.in/
ODOO_DB=odooKmmDb
ODOO_USERNAME=rajugenai@gmail.com
ODOO_PASSWORD=P@$$W0rd&$@
```

Then: `uvicorn main:app --reload`

---

For detailed info, see `RENDER_DEPLOYMENT.md`
