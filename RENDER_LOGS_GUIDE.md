# Reading Render Logs - Debugging Guide

## Log Locations

In Render Dashboard:
1. Click **"quantedge-backend"** service
2. Go to **"Logs"** tab
3. Scroll through the output

---

## Understanding Build Output

### ✅ Successful Build

```
Building application...
Installing Python 3.11...
Caching pip packages...
Collecting fastapi==0.111.0
Collecting uvicorn[standard]==0.29.0
...
Successfully installed fastapi uvicorn python-dotenv ...
Build completed.
Starting server...
Server is running on 0.0.0.0:XXXXX
INFO:     Uvicorn running on http://0.0.0.0:XXXXX
INFO:     QuantEdge backend starting up...
INFO:     Redis cache connected.
✓ Server listening on 0.0.0.0:XXXXX
```

**Status**: ✅ All good! Backend is ready.

---

### ❌ Build Failed - Missing Dependency

```
Collecting fastapi==0.111.0
ERROR: pip's dependency resolver does not currently support all the features
used by the following packages: ...

ERROR: Could not find a version that satisfies the requirement ...
```

**Fix**: 
1. Check `backend/requirements.txt`
2. Verify valid package names and versions
3. Run locally: `pip install -r backend/requirements.txt`
4. If fixed, commit and redeploy

---

### ❌ Build Failed - Python Version

```
python: No such file or directory
The runtime you selected doesn't support this environment
```

**Fix**:
1. In Render Dashboard → **Settings** → **Build Command**
2. Check value: Should be `pip install -r backend/requirements.txt`
3. Check Runtime: Should be **Python 3.11**
4. Redeploy

---

### ❌ Runtime Error - ImportError

```
Traceback (most recent call last):
  File "backend/main.py", line 10, in <module>
    from api.optimizer import router as optimizer_router
ModuleNotFoundError: No module named 'api'
```

**Fix**:
1. Verify working directory is `backend/` (check `startCommand`)
2. Verify `backend/api/` folder exists
3. Verify `backend/__init__.py` exists
4. Test locally: `cd backend && python -c "from api.optimizer import router"`

---

### ❌ Runtime Error - Redis Connection

```
redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379
```

**Fix**:
1. ⚠️ Can't use `localhost` in Render!
2. Check: Environment variable `REDIS_URL` is set
3. In Render, should be auto-injected from Redis service
4. Verify in **Environment** tab shows `REDIS_URL` value
5. Redeploy

---

### ❌ Runtime Error - Database Connection

```
sqlalchemy.exc.ArgumentError: Could not parse SQLAlchemy URL
postgresql+asyncpg://postgres:postgres@localhost/quantedge
```

**Fix**:
1. `localhost` doesn't work in Render
2. Check: Environment variable `DATABASE_URL` is set
3. Should be auto-injected by Render from PostgreSQL service
4. Verify in **Environment** tab
5. Redeploy

---

### ⚠️ Warning - Missing Environment Variable

```
WARNING: Could not load environment variable JWT_SECRET
Using default: 'change-me-in-production-...'
```

**Fix** (**CRITICAL**):
1. In Render Dashboard → **quantedge-backend** → **Environment**
2. Add `JWT_SECRET` variable
3. Paste your generated secret (32 chars from `generate_jwt_secret.py`)
4. **Save** and redeploy

---

## Troubleshooting Steps

### Step 1: Check if Service is Running
```bash
curl https://your-backend.onrender.com/api/v1/health
```

If **502 Bad Gateway**: Backend is down or still starting.

### Step 2: View Live Logs
In Render Dashboard:
1. Click service
2. Go to **Logs** tab
3. Look for recent errors (red text)

### Step 3: Check Environment Variables
1. Click service
2. Go to **Environment** tab
3. Verify these are set:
   - `JWT_SECRET` ✓
   - `DATABASE_URL` ✓
   - `REDIS_URL` ✓
   - `ALLOWED_ORIGINS` ✓

### Step 4: Redeploy
1. Click **"Redeploy"** button
2. Choose **"Clear build cache"** (if stuck)
3. Wait 3-5 minutes

---

## Common Patterns to Look For

### ✅ Good Signs
```
uvicorn running on http://0.0.0.0:PORT
QuantEdge backend starting up...
Redis cache connected.
Database connected.
✓ Health check: OK
```

### ❌ Bad Signs
```
ERROR
Exception
ModuleNotFoundError
ConnectionError
Traceback
Port already in use
```

---

## Log Severity Levels

| Level | Color | Meaning |
|-------|-------|---------|
| DEBUG | Blue | Detailed info (can ignore) |
| INFO | Gray | Normal operation |
| WARNING | Yellow | Something unusual (check it) |
| ERROR | Red |🚨 Something failed |
| CRITICAL | Red/Bold | 🚨 System down |

---

## Performance Logs

### Slow Startup (takes >30 sec)
```
Collecting numpy==1.26.4...
Collecting scipy==1.13.0...
[takes a long time with lots of packages]
```

⏱️ This is **normal** on first deploy. Subsequent deploys are faster.

### High Memory Usage
```
Memory: 450MB / 512MB
```

If consistently > 90%, might need to upgrade instance type (paid plan).

---

## Export Logs for Debugging

```bash
# Copy all logs (in browser, right-click and Save As)
# Or use Render API:
curl -H "Authorization: Bearer RENDER_API_KEY" \
  https://api.render.com/v1/services/SERVICE_ID/events
```

---

## Still Stuck?

1. **Check Render Status**: https://render.com/status
2. **Read Full Error**: Scroll all the way to the error line
3. **Search Error Code**: Copy error message → Google it
4. **Check Dependencies**: Verify package versions in requirements.txt match local
5. **Restart Service**: Click "Redeploy" with "Clear build cache"

---

## Example: Real Deployment Log

```
Building application...
Language: python
Python version: 3.11.0

Installing dependencies
Collecting fastapi==0.111.0
  Using cached fastapi-0.111.0-py3-none-any.whl
Collecting uvicorn[standard]==0.29.0
  Using cached uvicorn_standard-0.29.0-py3-none-any.whl
...collecting packages...
Successfully installed fastapi-0.111.0 uvicorn-0.29.0 ... (36 packages)

Starting service
INFO:     Uvicorn running on http://0.0.0.0:10000 (Press CTRL+C to quit)
INFO:     QuantEdge backend starting up...
INFO:     Waiting for Redis...
INFO:     Redis cache connected.
INFO:     Waiting for PostgreSQL...
INFO:     Database connected.
=== BUILD SUCCESSFUL ===
Service is live at https://quantedge-backend.onrender.com
```

✅ **All green! Ready to accept requests.**
