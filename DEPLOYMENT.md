# Backend Deployment Guide

## Quick Deploy to Railway (Recommended)

Railway offers free tier with 500 hours/month - perfect for this project.

### 1. Create Railway Account

Visit https://railway.app and sign up with GitHub.

### 2. Create New Project

1. Click "New Project"
2. Select "Deploy from GitHub repo"
3. Connect your GitHub account
4. Select "fpl-optimizer-backend" repository

### 3. Configure Environment Variables

In Railway dashboard, add these environment variables:

```
DATABASE_URL=postgresql://... (Railway will auto-generate this)
FPL_API_BASE_URL=https://fantasy.premierleague.com/api
CORS_ORIGINS=https://fpl-optimizer-frontend.vercel.app
API_RATE_LIMIT=10/minute
```

**Important:** Railway will automatically provision a PostgreSQL database. Use that instead of SQLite for production.

### 4. Update database.py for PostgreSQL

Railway uses PostgreSQL, so update `database.py`:

```python
# Remove SQLite-specific connect_args
engine = create_engine(
    DATABASE_URL,
    echo=False
)
```

### 5. Add Procfile

Create `Procfile` in root:

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

### 6. Update requirements.txt

Add PostgreSQL driver:

```bash
pip install psycopg2-binary
pip freeze > requirements.txt
```

### 7. Deploy

Railway will automatically:
- Detect Python project
- Install dependencies from requirements.txt
- Run migrations (if using Alembic)
- Start the server with Procfile command

### 8. Get Backend URL

Railway will provide a URL like: `https://fpl-optimizer-backend-production.up.railway.app`

Copy this URL - you'll need it for frontend integration.

---

## Alternative: Deploy to Render

Render also offers free tier with similar features.

### 1. Create Render Account

Visit https://render.com and sign up with GitHub.

### 2. Create New Web Service

1. Click "New +" → "Web Service"
2. Connect GitHub repository
3. Configure:
   - Name: fpl-optimizer-backend
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn main:app --host 0.0.0.0 --port $PORT`

### 3. Add Environment Variables

Same as Railway (see above).

### 4. Deploy

Render will build and deploy automatically.

---

## Database Initialization

After first deployment, initialize the database:

```bash
# SSH into your server (Railway/Render dashboard)
python -c "from database import engine; from models import Base; Base.metadata.create_all(bind=engine)"
```

Or use Alembic for migrations:

```bash
pip install alembic
alembic init migrations
alembic revision --autogenerate -m "Initial migration"
alembic upgrade head
```

---

## Testing the Deployment

Once deployed, test these endpoints:

### Health Check
```bash
curl https://your-backend-url.railway.app/health
```

Expected response:
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "FPL Optimizer API"
}
```

### API Documentation
Visit: `https://your-backend-url.railway.app/docs`

### Test Team Fetch
```bash
curl https://your-backend-url.railway.app/api/team/123456
```

### Test Optimization
```bash
curl -X POST https://your-backend-url.railway.app/api/optimize \
  -H "Content-Type: application/json" \
  -d '{"team_id": 123456}'
```

---

## Monitoring

### Logs

**Railway:** Dashboard → Deployments → Logs
**Render:** Dashboard → Logs tab

### Database

**Railway:** Dashboard → Database tab (connection string, metrics)
**Render:** Dashboard → PostgreSQL (separate service)

### Health Checks

Both platforms support automatic health checks at `/health` endpoint.

---

## Troubleshooting

### Build Fails

- Check `requirements.txt` is up to date
- Ensure Python 3.9+ is specified
- Verify all imports are correct

### Database Connection Errors

- Verify `DATABASE_URL` environment variable
- Check PostgreSQL service is running
- Run initial migration

### CORS Errors

- Verify `CORS_ORIGINS` includes frontend URL
- Check no trailing slashes in URLs

### Rate Limit Issues

- Adjust `API_RATE_LIMIT` if needed
- Check SlowAPI configuration in `main.py`

---

## Updating After Deployment

1. Push changes to GitHub:
   ```bash
   git push origin master
   ```

2. Railway/Render will automatically:
   - Detect the push
   - Rebuild the application
   - Deploy the new version
   - Zero-downtime deployment

---

## Cost Estimates

### Railway Free Tier
- 500 hours/month (enough for 24/7 operation for ~20 days)
- 100GB outbound bandwidth
- PostgreSQL included

### Render Free Tier
- Spins down after 15 min inactivity
- 750 hours/month
- PostgreSQL separate service (also free tier)

Both are sufficient for this project's initial deployment and testing phase.
