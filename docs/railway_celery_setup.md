# ═══════════════════════════════════════════════════════════════
# Railway Setup Guide — Celery Worker + Beat
# ═══════════════════════════════════════════════════════════════

## Step 1: Create Worker Service

1. Go to Railway dashboard → your project
2. Click "New Service" → "Empty Service"
3. Name it: "erp-worker"
4. Go to Settings:
   - Source: Connect to the SAME GitHub repo (smuhaisen01-cell/ERP)
   - Build: Dockerfile
5. Go to Variables → Add these (reference from main service):
   - DATABASE_URL = (copy from main service, or use Railway's shared variables)
   - REDIS_URL = (copy from main service)
   - SECRET_KEY = (copy from main service)
   - DJANGO_SETTINGS_MODULE = erp_system.settings_production
   - ENVIRONMENT = production
6. Go to Settings → Deploy:
   - Start Command: celery -A erp_system worker -l info --concurrency=2 -Q default,zatca_clearance,zatca_reporting
   - Remove the health check path (workers don't serve HTTP)

## Step 2: Create Beat Service

1. Click "New Service" → "Empty Service"
2. Name it: "erp-beat"
3. Same setup as worker for source + variables
4. Start Command: celery -A erp_system beat -l info --schedule=/tmp/celerybeat-schedule
5. Remove health check path

## Step 3: Verify

After deployment, check worker logs:
- Should show: "celery@... ready"
- Should show: "Received task" when tasks run

Check beat logs:
- Should show: "beat: Starting..."
- Should show scheduled task entries at their cron times

## Alternative: Use Procfile

Railway can auto-detect Procfile. Each line becomes a service option:
- web → main ERP (Daphne)
- worker → Celery worker
- beat → Celery beat

## Task Schedule (Asia/Riyadh timezone)

| Task                          | Schedule              | Queue              |
|-------------------------------|-----------------------|--------------------|
| Flush B2C invoices to ZATCA   | Every hour at :00     | zatca_reporting    |
| Check CSID expiry             | Daily 6:00 AM         | default            |
| Payroll reminder              | Monthly 25th, 9:00 AM | default            |
| Check expiring documents      | Daily 8:00 AM         | default            |
| Attendance summary            | Daily 6:00 PM         | default            |
| Trial balance snapshot        | Daily midnight         | default            |
| Check trial expirations       | Daily 7:00 AM         | default            |

## Monitoring

Check task execution in Railway logs:
- Worker: shows "Task apps.zatca.tasks.flush_pending_b2c_invoices[...] succeeded"
- Beat: shows "Scheduler: Sending due task..."

For production, add Flower (Celery monitoring):
- New service, start command: celery -A erp_system flower --port=$PORT
- Provides web UI for task monitoring
