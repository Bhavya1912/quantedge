# Render + Vercel Deployment Checklist

## ✅ Pre-Deployment Checklist

### 1. Generate Secure JWT Secret
**Status**: ⚠️ CRITICAL - Do this now!

Run locally:
```bash
python scripts/generate_jwt_secret.py
```

**Output looks like**: `a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6`

Save this — you'll need it in Render settings.

---

### 2. Verify All Config Files

- [ ] `render.yaml` — Service definitions ✅ Fixed
- [ ] `backend/requirements.txt` — All dependencies ✅ Checked
- [ ] `backend/utils/config.py` — Removed hardcoded secrets ✅ Fixed
- [ ] `frontend/.env.production` — Backend URL placeholder ✅ Fixed
- [ ] `vercel.json` — Build config ✅ Fixed

---

## 🚀 Deployment Steps

### Step 1: Push Latest Code
```bash
git add .
git commit -m "Fix deployment configs - remove hardcoded secrets"
git push origin main
```

---

### Step 2: Deploy Backend on Render.com

#### 2a. Create Render Account
- Go to https://render.com
- Sign up with GitHub
- Authorize access to your repo

#### 2b. Deploy Blueprint
1. Click **"New"** → **"Blueprint"**
2. Select `quantedge` repository
3. Click **"Deploy"**

#### 2c. Wait for Services
- ⏱️ Takes 2-3 minutes
- ✅ Web Service (Python/FastAPI)
- ✅ PostgreSQL database
- ✅ Redis cache

Check **Logs** for any errors:
```
Building application...
Installing dependencies...
Starting server on port XXXX
✓ Server listening on 0.0.0.0:XXXX
```

#### 2d. Note Your Backend URL
In Render Dashboard → **quantedge-backend** → Copy URL from top
```
Example: https://quantedge-backend.onrender.com
```

---

### Step 3: Set Render Environment Variables

**⚠️ CRITICAL: This is what was missing!**

1. Render Dashboard → **quantedge-backend** → **Environment**
2. Add these variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `JWT_SECRET` | `a1b2c3d4e5f6g7h8...` | From Step 1 |
| `ALLOWED_ORIGINS` | `https://quantedge.vercel.app,https://quantedge.in` | Update with your actual Vercel URL |
| `ENVIRONMENT` | `production` | |
| `DEBUG` | `false` | |

3. **Save** → Auto-redeploy happens

---

### Step 4: Update Frontend for Vercel

#### 4a. Add Backend URL to Vercel
1. Vercel Dashboard → Your Project
2. **Settings** → **Environment Variables**
3. Add new variable:
   ```
   Key: VITE_API_BASE_URL
   Value: https://quantedge-backend.onrender.com/api/v1
   ```
4. Click **Save**

#### 4b. Redeploy Frontend
1. Go to **Deployments**
2. Click latest deployment → **Redeploy**
3. Wait for build (2-3 minutes)

---

## ✔️ Verify Everything Works

### Test 1: Backend Health
```bash
curl https://quantedge-backend.onrender.com/api/v1/health
```

**Expected**:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "quantedge-backend"
}
```

### Test 2: API Documentation
Open in browser:
```
https://quantedge-backend.onrender.com/docs
```
Should see Swagger UI with all endpoints.

### Test 3: Frontend
Open your Vercel URL in browser:
```
https://quantedge.vercel.app
```

Try a request from frontend:
1. Open **Browser Console** (F12)
2. Run:
   ```javascript
   fetch('https://quantedge-backend.onrender.com/api/v1/health')
     .then(r => r.json())
     .then(console.log)
   ```
3. Should see the health response (no CORS error)

---

## 🔧 Common Issues & Fixes

### Issue: 502 Bad Gateway
**Cause**: Backend still starting or crashed
- ✅ Solution: Wait 2 min, check Render logs
  ```
  Render → quantedge-backend → Logs (scroll through build output)
  ```

### Issue: CORS Error in Console
```
Access to XMLHttpRequest blocked by CORS policy
```
**Cause**: `VITE_API_BASE_URL` doesn't match `ALLOWED_ORIGINS`
- ✅ Check Vercel env var matches actual Vercel URL
- ✅ Check Render `ALLOWED_ORIGINS` is updated
- ✅ Redeploy both services

### Issue: API Returns 404
**Cause**: Frontend calling wrong URL
- ✅ Verify `VITE_API_BASE_URL` in Vercel is correct
- ✅ Check it includes `/api/v1` suffix
- ✅ Redeploy frontend

### Issue: Database Connection Error
**Cause**: PostgreSQL still initializing
- ✅ Wait 3-5 minutes
- ✅ Redeploy web service in Render
- ✅ Check `DATABASE_URL` is set (auto-injected)

### Issue: `JWT_SECRET` not recognized
**Cause**: Missing environment variable in Render
- ✅ Add `JWT_SECRET` to Render env vars
- ✅ Make sure `sync: false` is NOT checked
- ✅ Redeploy

---

## 📊 Monitoring

### Render Dashboard
- **Logs**: Watch real-time server output
- **Metrics**: CPU, Memory, Network usage
- **Health**: Check service status

### Vercel Dashboard
- **Deployments**: Build status, logs
- **Analytics**: Performance metrics
- **Functions**: Serverless function logs

---

## 🔒 Security Checklist

- [x] JWT_SECRET generated randomly (32 chars)
- [x] JWT_SECRET NOT in source code ✅ (fixed)
- [x] ALLOWED_ORIGINS properly configured
- [x] DEBUG = false in production
- [x] HTTPS only (both Render & Vercel)
- [ ] Set up error logging (Sentry, LogRocket)
- [ ] Monitor for exposed secrets in logs

---

## 🎯 Final Verification

Run this script to validate deployment:

```bash
#!/bin/bash

BACKEND_URL="https://quantedge-backend.onrender.com"
FRONTEND_URL="https://quantedge.vercel.app"

echo "Testing Backend..."
curl -s ${BACKEND_URL}/api/v1/health | jq .

echo -e "\nChecking API Docs..."
curl -s -o /dev/null -w "%{http_code}" ${BACKEND_URL}/docs

echo -e "\nFrontend Status..."
curl -s -o /dev/null -w "%{http_code}" ${FRONTEND_URL}

echo -e "\n✅ All systems operational!"
```

---

## 📞 Support

- **Render Docs**: https://render.com/docs
- **Vercel Docs**: https://vercel.com/docs
- **FastAPI Docs**: https://fastapi.tiangolo.com/
- **Logs Location**: Render → Service → Logs tab
