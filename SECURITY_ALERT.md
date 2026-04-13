# 🚨 SECURITY ALERT - CREDENTIALS EXPOSED ON GITHUB

## What Happened
You pushed `config.json` with REAL Odoo credentials to your GitHub repository. Anyone with access to your repo can now see:
- Odoo URL
- Database name
- Email/username
- Password

**This is a security breach!**

---

## ⚡ IMMEDIATE ACTIONS (Do These NOW)

### 1. Change Your Odoo Password
1. Go to https://odoo.avowaldatasystems.in/
2. Log in with your account
3. Go to **Settings** → **Change Password**
4. Set a NEW, STRONG password
5. Update `config.json` with new password (locally only)

### 2. Remove config.json from Git History
Your GitHub repo has the old credentials in the history. They need to be removed:

```bash
# Option A: Use BFG Repo-Cleaner (RECOMMENDED)
# This removes the file from all commits
bfg --delete-files config.json

# Option B: Use git filter-branch (more complex)
git filter-branch --tree-filter 'rm -f config.json' HEAD

# After either option, force push:
git push origin --force
```

### 3. Verify config.json is in .gitignore
The file `.gitignore` now has:
```
config.json
```

To verify git ignores it:
```bash
git status
# config.json should NOT appear in the output
```

---

## 📋 Moving Forward

### Local Development
- ✅ Keep `config.json` with real credentials
- ✅ `.gitignore` prevents it from being committed
- ✅ Only you see it on your machine

### Render Deployment
- ✅ Set environment variables (NOT in code)
- ✅ Use single quotes for special characters
- ✅ Credentials never committed to git

---

## Files To Update/Check

### config.json (Local Only)
```json
{
  "ODOO_URL": "https://odoo.avowaldatasystems.in/",
  "ODOO_DB": "odooKmmDb",
  "ODOO_USERNAME": "rajugenai@gmail.com",
  "ODOO_PASSWORD": "NEW_PASSWORD_HERE"
}
```

### .gitignore (In Git)
```
config.json
.env
.env.local
.env.*.local
```

### config.example.json (In Git - TEMPLATE ONLY)
```json
{
  "ODOO_URL": "https://your-instance.odoo.com/",
  "ODOO_DB": "your_database_name",
  "ODOO_USERNAME": "your_email@example.com",
  "ODOO_PASSWORD": "your_password_here"
}
```

---

## Checklist

- [ ] Changed Odoo password (NEW password, not the old one)
- [ ] Removed config.json from git history (BFG or git filter-branch)
- [ ] Force pushed changes to GitHub
- [ ] Verified `.gitignore` has `config.json`
- [ ] Verified `config.example.json` is the template (no real credentials)
- [ ] Updated local `config.json` with new password
- [ ] Tested locally with new password
- [ ] Updated Render environment variables with new password

---

## How To Prevent This in Future

**NEVER do this:**
```bash
git add config.json  # ❌ WRONG
git commit -m "add config"
git push
```

**Always do this:**
```bash
# 1. Create config.example.json (for documentation)
# 2. Add config.json to .gitignore  
# 3. Create local config.json
# 4. Git will automatically ignore it
```

---

## If You Need Help Cleaning Git History

The easiest way to remove config.json from git history:

```bash
# Install BFG Repo-Cleaner if you don't have it
brew install bfg  # macOS
# or download from: https://rtyley.github.io/bfg-repo-cleaner/

# Go to your project directory
cd ~/Downloads/FastAPI_project

# Remove config.json from ALL commits
bfg --delete-files config.json

# Review changes
git log --follow config.json  # Should show nothing

# Force push to GitHub (CAUTION: this rewrites history)
git push origin --force --all
```

---

## Questions?

- **Is my data safe now?** No. Change your Odoo password IMMEDIATELY.
- **When will GitHub delete it?** When you remove it from history with BFG or git filter-branch.
- **What about Render?** Use environment variables - much safer than committing config files.
- **Did anyone see it?** Unknown. Assume any repo on GitHub can be downloaded by anyone. Better to be safe.

---

**SECURITY REMINDER: NEVER commit credentials. ALWAYS use environment variables or local config files added to .gitignore.**

