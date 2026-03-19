# Railway Procfile — each line becomes a separate service
# Deploy: Railway auto-detects. Or create services manually with these commands.

web: sh -c "python manage.py migrate_schemas --shared; python manage.py migrate_schemas --tenant; python manage.py seed_socpa_coa --all; python manage.py collectstatic --noinput; daphne -b 0.0.0.0 -p $PORT erp_system.asgi:application"

worker: celery -A erp_system worker -l info --concurrency=2 -Q default,zatca_clearance,zatca_reporting

beat: celery -A erp_system beat -l info --schedule=/tmp/celerybeat-schedule
