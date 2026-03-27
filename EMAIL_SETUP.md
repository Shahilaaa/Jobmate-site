# 📧 JobMate Email Setup Guide

Enquiry form submissions are saved to the database automatically.
To **also send an email** to `jobmate393@gmail.com`, follow these steps:

---

## Step 1 — Enable 2-Step Verification on Gmail

1. Go to: https://myaccount.google.com/security
2. Under "How you sign in to Google", click **2-Step Verification**
3. Follow the prompts to turn it **ON**

> ⚠️ This is required — Gmail blocks SMTP without 2-Step Verification

---

## Step 2 — Create a Gmail App Password

1. Go to: https://myaccount.google.com/apppasswords
2. Click **"Create"** (or the **+** button)
3. Give it any name (e.g. `JobMate`)
4. Google will show you a **16-character password**, like:
   ```
   abcd efgh ijkl mnop
   ```
5. **Copy it without spaces**: `abcdefghijklmnop`

---

## Step 3 — Add it to `.env`

Open the `.env` file in the project root and update this line:

```
EMAIL_HOST_PASSWORD=abcdefghijklmnop
```

Replace `abcdefghijklmnop` with your actual 16-character App Password.

---

## Step 4 — Restart the Django server

Stop the server (`Ctrl+C`) and start it again:

```bash
python manage.py runserver
```

---

## Step 5 — Test it

Run this command to verify everything works:

```bash
python manage.py test_email
```

You should see: `✅ SUCCESS! Test email sent to jobmate393@gmail.com`

Check your Gmail inbox (and Spam folder).

---

## Troubleshooting

| Error | Fix |
|-------|-----|
| `SMTPAuthenticationError` | App Password is wrong or has spaces |
| `Connection refused` | Firewall blocking port 587 — try a different network |
| `Console backend active` | Password not set or less than 16 chars in `.env` |
| Email in Spam | Add `jobmate393@gmail.com` to your contacts |

---

## How it works

When someone submits the Enquiry form on the About page:

1. ✅ Enquiry is **always** saved to the database (even if email fails)
2. 📧 A formatted HTML email is sent to `jobmate393@gmail.com`
3. ↩️ The **Reply-To** is set to the enquirer's email — just hit Reply to respond
4. ✅ User sees a success message on the page

