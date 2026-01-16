# 🚀 Deploy Backend NOW - Step by Step Guide

The backend is **100% ready for deployment**. Follow these steps:

---

## Step 1: Create GitHub Repository (2 minutes)

### Option A: Using GitHub Web Interface

1. Go to https://github.com/new
2. Repository name: **fpl-optimizer-backend**
3. Description: **FastAPI backend for FPL team optimization and transfer recommendations**
4. Visibility: **Public** (recommended) or Private
5. **DO NOT** initialize with README, .gitignore, or license (we have these)
6. Click **Create repository**

### Option B: Using Git Commands

```bash
cd /Users/danbass/Projects/fpl-optimizer-backend

# Add GitHub remote (replace YOUR_USERNAME)
git remote add origin https://github.com/YOUR_USERNAME/fpl-optimizer-backend.git

# Push code
git push -u origin master
```

---

## Step 2: Deploy to Railway (3 minutes)

### 2.1 Create Railway Account

1. Go to https://railway.app
2. Click **Login with GitHub**
3. Authorize Railway to access your GitHub account

### 2.2 Create New Project

1. Click **New Project**
2. Select **Deploy from GitHub repo**
3. Choose **fpl-optimizer-backend** from the list
4. Railway will automatically:
   - Detect Python project
   - Install dependencies from requirements.txt
   - Provision PostgreSQL database
   - Start deployment

### 2.3 Add PostgreSQL Database

1. In your Railway project, click **+ New**
2. Select **Database** → **PostgreSQL**
3. Railway will automatically:
   - Create PostgreSQL instance
   - Set DATABASE_URL environment variable
   - Link to your backend service

### 2.4 Set Environment Variables

1. Click on your backend service
2. Go to **Variables** tab
3. Add these variables:

```
FPL_API_BASE_URL=https://fantasy.premierleague.com/api
CORS_ORIGINS=https://fpl-optimizer-frontend.vercel.app
API_RATE_LIMIT=10/minute
```

**Note:** DATABASE_URL is automatically set by Railway when you add PostgreSQL.

### 2.5 Initialize Database

1. Go to **Deployments** tab
2. Wait for deployment to complete (green checkmark)
3. Click **View Logs**
4. In the top right, click **Shell** (terminal icon)
5. Run:

```bash
python init_db.py
```

You should see: "Database tables created successfully!"

---

## Step 3: Get Your Backend URL

1. In Railway dashboard, click on your backend service
2. Go to **Settings** tab
3. Scroll to **Domains**
4. Copy the Railway-provided domain (e.g., `fpl-optimizer-backend-production.up.railway.app`)

**Your backend URL:**
```
https://YOUR-PROJECT-NAME.up.railway.app
```

---

## Step 4: Test Your Deployment

### Test Health Check

```bash
curl https://YOUR-BACKEND-URL.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "FPL Optimizer API"
}
```

### Test API Documentation

Visit in browser:
```
https://YOUR-BACKEND-URL.railway.app/docs
```

You should see interactive API docs (Swagger UI).

### Test Team Endpoint (use a real FPL team ID)

```bash
curl https://YOUR-BACKEND-URL.railway.app/api/team/123456
```

**Note:** First request will sync data from FPL API (~10 seconds).

### Test Optimization Endpoint

```bash
curl -X POST https://YOUR-BACKEND-URL.railway.app/api/optimize \
  -H "Content-Type: application/json" \
  -d '{"team_id": 123456}'
```

---

## Step 5: Update Frontend (Next Step)

After backend is deployed, you'll need to:

1. Update frontend `.env.production` with backend URL
2. Replace mock data with real API calls
3. Redeploy frontend to Vercel

**This will be Story 3.7 - I'll handle it automatically once you provide the backend URL.**

---

## Troubleshooting

### Deployment Failed

**Check logs:**
1. Railway dashboard → Deployments → Click failed deployment → View Logs
2. Common issues:
   - Missing dependencies: Check requirements.txt
   - Python version: Railway uses Python 3.9+ by default
   - Port binding: Make sure using `$PORT` env variable

**Solution:**
```bash
# Fix locally, then:
git add .
git commit -m "fix: deployment issue"
git push origin master
# Railway auto-redeploys
```

### Database Connection Error

**Verify DATABASE_URL:**
1. Railway dashboard → Variables tab
2. Check DATABASE_URL exists and starts with `postgresql://`

**Re-initialize database:**
```bash
# In Railway shell
python init_db.py
```

### CORS Errors in Frontend

**Update CORS_ORIGINS:**
1. Railway dashboard → Variables tab
2. Edit CORS_ORIGINS to include your frontend domain:
```
https://fpl-optimizer-frontend.vercel.app,http://localhost:5173
```
3. Railway will auto-redeploy

### FPL API Rate Limiting

If you see "Too many requests" errors:

**First request to `/api/team/{id}` syncs ~600 players** - this is normal and takes ~10 seconds.

Data is cached for 6 hours, so subsequent requests are instant.

---

## Monitoring

### Logs

Railway dashboard → Deployments → Logs (real-time)

### Metrics

Railway dashboard → Metrics tab shows:
- CPU usage
- Memory usage
- Request volume

### Database

Railway dashboard → PostgreSQL service shows:
- Connection string
- Database size
- Active connections

---

## Cost

**Railway Free Tier:**
- $5 free credit per month
- ~500 hours of server time
- PostgreSQL included
- More than enough for testing and early users

**When you need to upgrade:**
- Free tier runs out (rare for this project)
- Need custom domain
- Need more database storage

---

## Ready to Deploy?

**Current Status:**
✅ Backend code complete (Stories 3.1-3.6)
✅ Deployment files ready (Procfile, railway.json, init_db.py)
✅ PostgreSQL support added
✅ Git repository initialized

**What you need to do:**
1. ☐ Create GitHub repository (2 min)
2. ☐ Push code to GitHub (1 min)
3. ☐ Create Railway project (2 min)
4. ☐ Add PostgreSQL database (1 min)
5. ☐ Set environment variables (1 min)
6. ☐ Initialize database (1 min)
7. ☐ Test endpoints (2 min)

**Total time: ~10 minutes**

---

## After Deployment

**Reply with your backend URL and I'll automatically:**
1. Update frontend to use real backend API
2. Remove all mock data
3. Add error handling for API calls
4. Update environment variables
5. Redeploy frontend to Vercel
6. Test end-to-end flow

**Example reply:**
```
Backend deployed at: https://fpl-optimizer-backend-production-xyz.up.railway.app
```

Then I'll complete Story 3.7 (Frontend Integration) autonomously! 🚀
