# Deploying QuantEdge to Render.com

## Prerequisites
- GitHub account with your repo pushed
- Render.com account (https://render.com)
- Frontend deployed on Vercel (get the URL)

## Step 1: Push to GitHub
```bash
git add .
git commit -m "Add Render deployment config"
git push origin main
```

## Step 2: Create Render Account
1. Go to https://render.com
2. Sign up with GitHub
3. Connect your GitHub account

## Step 3: Deploy with render.yaml
1. In Render dashboard, click **"New"** → **"Blueprint"**
2. Select your GitHub repository
3. Render will auto-detect `render.yaml`
4. Click **"Deploy"**

## Step 4: Set Environment Variables
After deployment starts, go to the **Web Service** settings:

1. Navigate to **Environment**
2. Add these required variables:

| Variable | Value | Notes |
|----------|-------|-------|
| `JWT_SECRET` | Generate random 32-char string | Use: `openssl rand -hex 16` |
| `ALLOWED_ORIGINS` | `https://your-frontend.vercel.app,https://quantedge.in` | Add your actual Vercel URL |
| `ENVIRONMENT` | `production` | |
| `DEBUG` | `false` | |

**Render will automatically inject:**
- `REDIS_URL` (from Redis service)
- `DATABASE_URL` (from PostgreSQL service)

## Step 5: Update Frontend
Update your Vercel frontend environment variable:

1. In Vercel Dashboard → Your Project → Settings → Environment Variables
2. Set: `VITE_API_BASE_URL=https://your-backend.onrender.com/api/v1`
3. Redeploy frontend

You can find your backend URL in Render dashboard → Web Service → URL

## Step 6: Verify Deployment
```bash
curl https://your-backend.onrender.com/api/v1/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "quantedge-backend"
}
```

## Troubleshooting

### Build fails
- Check [Render Logs](https://render.com) → Web Service → Logs
- Ensure `requirements.txt` has all dependencies

### 502 Bad Gateway
- Backend is still starting (can take 1-2 minutes on free tier)
- Check Render logs for errors

### CORS errors in frontend
- Update `ALLOWED_ORIGINS` in Render environment variables
- Frontend URL should match exactly

### Database connection errors
- PostgreSQL service may still be initializing
- Wait 2-3 minutes and redeploy

## Pricing
- **Web Service**: Free tier (slow, auto-sleeps after 15 min inactivity)
- **PostgreSQL**: Free tier (removed after 90 days of inactivity)
- **Redis**: Free tier (same auto-sleep behavior)

To prevent sleep, upgrade to paid tier ($7/month+) or add a simple uptime monitor.

## Next Steps
- Monitor logs in Render dashboard
- Set up error tracking (Sentry, LogRocket)
- Configure backup strategy for PostgreSQL
