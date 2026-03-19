"""
HR async tasks.
- send_payroll_reminder: Monthly reminder on 25th
- check_expiring_documents: Daily check for expiring IDs/contracts
- daily_attendance_summary: End-of-day attendance report
"""
import logging
from datetime import date, timedelta
from celery import shared_task
from django_tenants.utils import get_tenant_model, tenant_context

logger = logging.getLogger("apps.hr")


@shared_task(name="apps.hr.tasks.send_payroll_reminder")
def send_payroll_reminder():
    """Monthly: Remind HR managers to run payroll (25th of month)."""
    Tenant = get_tenant_model()
    tenants = Tenant.objects.filter(is_active=True).exclude(schema_name="public")
    for tenant in tenants:
        try:
            with tenant_context(tenant):
                from apps.hr.models import PayrollRun, Employee
                today = date.today()
                existing = PayrollRun.objects.filter(
                    period_month=today.month, period_year=today.year
                ).first()
                emp_count = Employee.objects.filter(status="active").count()
                if not existing and emp_count > 0:
                    logger.info(
                        f"[{tenant.schema_name}] PAYROLL REMINDER: "
                        f"{emp_count} employees, no payroll run for {today.year}/{today.month:02d}"
                    )
                    # TODO: Send email/notification to HR managers
        except Exception as e:
            logger.error(f"[{tenant.schema_name}] Payroll reminder error: {e}")
    return "Payroll reminders sent"


@shared_task(name="apps.hr.tasks.check_expiring_documents")
def check_expiring_documents():
    """Daily: Find documents expiring within 30 days."""
    Tenant = get_tenant_model()
    tenants = Tenant.objects.filter(is_active=True).exclude(schema_name="public")
    total_expiring = 0
    for tenant in tenants:
        try:
            with tenant_context(tenant):
                from apps.hr.models import EmployeeDocument
                threshold = date.today() + timedelta(days=30)
                expiring = EmployeeDocument.objects.filter(
                    expiry_date__isnull=False,
                    expiry_date__lte=threshold,
                    expiry_date__gte=date.today(),
                ).select_related("employee")
                for doc in expiring:
                    days_left = (doc.expiry_date - date.today()).days
                    logger.warning(
                        f"[{tenant.schema_name}] EXPIRING DOC: "
                        f"{doc.employee.name_en} — {doc.title} expires in {days_left} days"
                    )
                    total_expiring += 1
                    # TODO: Send notification
        except Exception as e:
            logger.error(f"[{tenant.schema_name}] Doc expiry check error: {e}")
    return f"{total_expiring} expiring documents found"


@shared_task(name="apps.hr.tasks.daily_attendance_summary")
def daily_attendance_summary():
    """Daily at 6 PM: Summarize attendance for all tenants."""
    Tenant = get_tenant_model()
    tenants = Tenant.objects.filter(is_active=True).exclude(schema_name="public")
    for tenant in tenants:
        try:
            with tenant_context(tenant):
                from apps.hr.models import Attendance, Employee
                today = date.today()
                total_emp = Employee.objects.filter(status="active").count()
                present = Attendance.objects.filter(date=today, status="present").count()
                absent = total_emp - present
                logger.info(
                    f"[{tenant.schema_name}] ATTENDANCE: "
                    f"{present}/{total_emp} present, {absent} absent"
                )
        except Exception as e:
            logger.error(f"[{tenant.schema_name}] Attendance summary error: {e}")
    return "Attendance summaries generated"
