# Fixed Deployment Guide - Render + Vercel

## ⚠️ Issue Resolved

Render's blueprint format doesn't support creating managed database services (PostgreSQL/Redis) via YAML. You must:
1. Deploy the **web service** via blueprint ✅
2. **Manually create** database services in Render UI OR use cloud services

---

## 📋 New Deployment Flow

### Phase 1: Deploy Web Service (Blueprint) - 2 mins

#### 1a. Generate JWT Secret First
```bash
python scripts/generate_jwt_secret.py
```
Save the 32-character output.

#### 1b. Deploy on Render
1. Go to https://render.com → **"New"** → **"Blueprint"**
2. Select `quantedge` repository
3. Click **"Deploy"**
4. ✅ Should succeed now (only web service)

#### 1c. Note Your Backend URL
- Render Dashboard → **quantedge-backend**
- Copy URL: `https://quantedge-backend.onrender.com`

---

### Phase 2: Set Up Database & Redis - Choose ONE Option

#### **OPTION A: Render Managed Services** (Easiest)

**Create PostgreSQL:**
1. Render Dashboard → **"New"** → **"PostgreSQL"**
2. Name: `quantedge-postgres`
3. Region: Same as web service
4. PostgreSQL Version: 15
5. Click **"Create Database"**
6. Copy the **Connection String** from the dashboard

**Create Redis:**
1. Render Dashboard → **"New"** → **"Redis"**
2. Name: `quantedge-redis`
3. Region: Same as web service
4. Plan: Free
5. Click **"Create"**
6. Copy the **Redis URL** from the dashboard

---

#### **OPTION B: Upstash (Cheaper/Faster)** ⭐ Recommended

**For Redis (Free tier available):**
1. Go to https://upstash.com
2. Sign up with GitHub
3. Click **"Create Database"** → Redis
4. Name: `quantedge-redis`
5. Region: Closest to Render
6. Copy the **Redis connection URL** from "Connect" tab
   ```
   redis://default:PASSWORD@HOST:PORT
   ```

**For PostgreSQL:**
- Use Render's managed PostgreSQL (Option A above)
- Or use external service like Railway, Supabase, etc.

---

### Phase 3: Configure Environment Variables - 5 mins

#### In Render Dashboard for `quantedge-backend`:

1. Click **"quantedge-backend"** service
2. Go to **"Environment"** tab
3. Add/Update these variables:

| Variable | Value |
|----------|-------|
| `JWT_SECRET` | `[your 32-char secret from Phase 1]` |
| `ALLOWED_ORIGINS` | `http://localhost:5173,http://localhost:3000,https://quantedge.vercel.app,https://quantedge.in` |
| `REDIS_URL` | `redis://default:PASSWORD@HOST:PORT` (from Phase 2) |
| `DATABASE_URL` | `postgresql+asyncpg://user:password@host:5432/quantedge` (from Phase 2) |
| `ENVIRONMENT` | `production` |
| `DEBUG` | `false` |

4. Click **"Save"** → Auto-redeploy

---

### Phase 4: Update Vercel Frontend - 3 mins

1. Vercel Dashboard → Your Project
2. **Settings** → **Environment Variables**
3. Add/Update:
   ```
   VITE_API_BASE_URL = https://quantedge-backend.onrender.com/api/v1
   ```
4. Click **"Save"**
5. Go to **Deployments** → Click latest → **Redeploy**

---

## ✅ Verify Deployment

### Test 1: Backend Health
```bash
curl https://quantedge-backend.onrender.com/api/v1/health
```

Expected:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "quantedge-backend"
}
```

### Test 2: Database Connection
In Render logs, should see:
```
INFO:     Database connected.
INFO:     Redis cache connected.
```

### Test 3: Frontend
Open https://your-vercel-url.vercel.app in browser → Should work without errors

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 Bad Gateway | Check if DATABASE_URL/REDIS_URL are set correctly |
| `ModuleNotFoundError` | Check requirements.txt has all dependencies |
| Database connection error | Verify DATABASE_URL connection string is correct |
| Redis connection error | Verify REDIS_URL connection string is correct |
| CORS error | Update ALLOWED_ORIGINS to match your Vercel URL |

---

## 📊 Service Architecture

```
┌─────────────────────────────────────┐
│  Frontend (Vercel)                  │
│  https://quantedge.vercel.app       │
└────────────────────┬────────────────┘
                     │
                     ↓ VITE_API_BASE_URL
┌─────────────────────────────────────┐
│  Backend (Render Web)               │
│  https://quantedge-backend....      │
└────────┬────────────────────┬───────┘
         │                    │
         ↓ DATABASE_URL       ↓ REDIS_URL
    ┌─────────────┐      ┌──────────────┐
    │ PostgreSQL  │      │   Redis      │
    │ (Render)    │      │ (Upstash)    │
    └─────────────┘      └──────────────┘
```

---

## 📞 Finding Connection Strings

### Render PostgreSQL
Render Dashboard → Click PostgreSQL service → Copy "External Database URL"

### Render Redis
Render Dashboard → Click Redis service → Copy "Redis URL"

### Upstash Redis
Upstash Console → Click database → "Connect" tab → Copy Redis URL

---

## 🔄 Deploy Checklist

- [ ] Generate JWT Secret
- [ ] Deploy web service via blueprint
- [ ] Create PostgreSQL service (Render)
- [ ] Create Redis service (Render or Upstash)
- [ ] Set 6 environment variables in Render
- [ ] Update VITE_API_BASE_URL in Vercel
- [ ] Redeploy frontend
- [ ] Test health endpoint
- [ ] Test frontend in browser
- [ ] Check Render logs for errors

---

## 💡 Pro Tips

1. **Keep Redis simple**: Use Upstash free tier (easier to manage)
2. **Monitor costs**: Render free tier auto-sleeps after 15 min
3. **Backup database**: Enable automated backups in Render PostgreSQL settings
4. **Set up logging**: Use Render's logs tab to debug issues
5. **Test locally first**: Run `uvicorn main:app` locally with real DB URLs

---

## 📚 Useful Links

- [Render Docs](https://render.com/docs)
- [Upstash Docs](https://upstash.com/docs)
- [FastAPI Guide](https://fastapi.tiangolo.com/)
- [Vercel Docs](https://vercel.com/docs)
