# Quick Start: Deploy to Render & Vercel

## 1. Push latest code to GitHub
```bash
git add .
git commit -m "Setup Render deployment config"
git push origin main
```

## 2. Generate JWT Secret
Run this command to generate a secure 32-character string:
```bash
# Windows PowerShell
[Convert]::ToBase64String([byte[]]((1..32 | ForEach-Object { Get-Random -Maximum 256 }))) | % { $_ -replace "[^A-Za-z0-9]", "" } | % { $_.Substring(0, 32) }

# macOS/Linux
openssl rand -hex 16
```
Copy the output — you'll need it in Step 4.

## 3. Deploy Backend to Render (5 mins)

### 3a. Go to render.com
1. Sign up/Login at https://render.com
2. Click **"New"** → **"Blueprint"**
3. Select your GitHub repo
4. Click **"Deploy"**

### 3b. Wait for services to start
- Web Service (FastAPI)
- PostgreSQL database
- Redis cache

Takes ~2-3 minutes. Check logs for any errors.

### 3c. Copy your backend URL
In Render Dashboard:
- Click **"quantedge-backend"** service
- Copy the URL from the top (e.g., `https://quantedge-backend.onrender.com`)

## 4. Set Environment Variables in Render
In Render Dashboard → **quantedge-backend** → **Environment**:

Add these variables:
```
JWT_SECRET = [paste the 32-char string from Step 2]
ALLOWED_ORIGINS = https://quantedge.vercel.app,https://quantedge-theta.vercel.app,https://quantedge.in
ENVIRONMENT = production
DEBUG = false
```

**Render auto-provides:**
- `REDIS_URL`
- `DATABASE_URL`

Click **"Save"** and wait for auto-redeploy.

## 5. Update Vercel Frontend
1. Go to **your Vercel project** → **Settings** → **Environment Variables**
2. Add/Update:
   ```
   VITE_API_BASE_URL = https://quantedge-backend.onrender.com/api/v1
   ```
   (Replace `quantedge-backend` with your actual service name)

3. Go to **Deployments** → Click latest → **Redeploy**

## 6. Test the Connection
```bash
# Test backend health
curl https://quantedge-backend.onrender.com/api/v1/health

# Test from front-end in browser console
fetch('https://quantedge-backend.onrender.com/api/v1/health').then(r => r.json()).then(console.log)
```

## 7. Monitor
- **Render Logs**: https://render.com → Web Service → Logs
- **Vercel Logs**: https://vercel.com → Project → Deployments
- **Health Check**: https://your-backend.onrender.com/api/v1/health

## Common Issues

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Backend still starting (1-2 min). Check Render logs. |
| CORS error in console | Update `ALLOWED_ORIGINS` and redeploy. |
| DB connection error | PostgreSQL takes time to initialize. Redeploy in 2 min. |
| API returns 404 | `VITE_API_BASE_URL` in Vercel doesn't match backend URL. |

## How to Stop Free Tier Auto-Sleep

By default, Render free services sleep after 15 min of inactivity. To keep it running:
- **Option A**: Upgrade to paid ($7/month)
- **Option B**: Add a monitoring service that pings the health endpoint every 14 minutes

## Next Steps
- ✅ Backend deployed
- ✅ Frontend connected
- ⏭️ Add database migrations (if needed)
- ⏭️ Set up error tracking
- ⏭️ Monitor performance

See [DEPLOYMENT.md](DEPLOYMENT.md) for more details.
