#!/bin/sh
python manage.py makemigrations tenants billing zatca accounting sales inventory hr pos ai --noinput
python manage.py migrate_schemas --shared
python manage.py migrate_schemas
python manage.py createsuperuser --noinput --username admin --email admin@erp.sa 2>&1 || true
python manage.py collectstatic --noinput
daphne -b 0.0.0.0 -p $PORT erp_system.asgi:application