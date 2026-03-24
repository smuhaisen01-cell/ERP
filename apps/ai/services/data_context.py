"""
AI Data Context Builder — provides read-only tenant data to LLM.
Gathers financial summaries, KPIs, and recent activity for AI analysis.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone


def get_financial_context(tenant_schema=None):
    """Build comprehensive financial context string for LLM."""
    try:
        data = {}

        # Revenue & Invoicing
        from apps.zatca.models import TaxInvoice
        today = date.today()
        month_start = today.replace(day=1)
        year_start = today.replace(month=1, day=1)

        invoices_month = TaxInvoice.objects.filter(
            issue_date__gte=month_start, is_cancelled=False
        ).aggregate(
            count=Count('id'), total=Sum('total_amount'), vat=Sum('vat_amount'),
            b2b=Count('id', filter=Q(invoice_type='388')),
            b2c=Count('id', filter=Q(invoice_type='386')),
        )

        invoices_year = TaxInvoice.objects.filter(
            issue_date__gte=year_start, is_cancelled=False
        ).aggregate(count=Count('id'), total=Sum('total_amount'), vat=Sum('vat_amount'))

        data['invoices_this_month'] = {
            'count': invoices_month['count'] or 0,
            'total': str(invoices_month['total'] or 0),
            'vat': str(invoices_month['vat'] or 0),
            'b2b_count': invoices_month['b2b'] or 0,
            'b2c_count': invoices_month['b2c'] or 0,
        }
        data['invoices_ytd'] = {
            'count': invoices_year['count'] or 0,
            'total': str(invoices_year['total'] or 0),
            'vat': str(invoices_year['vat'] or 0),
        }

        # GL Balances
        from apps.accounting.models import JournalEntryLine
        gl_agg = JournalEntryLine.objects.filter(
            entry__status='posted'
        ).values('account__code', 'account__name_en', 'account__account_type').annotate(
            debit=Sum('debit_amount'), credit=Sum('credit_amount')
        ).order_by('account__code')

        accounts = []
        for a in gl_agg:
            balance = (a['debit'] or 0) - (a['credit'] or 0)
            if a['account__account_type'] in ('liability', 'equity', 'revenue'):
                balance = (a['credit'] or 0) - (a['debit'] or 0)
            if balance != 0:
                accounts.append(f"  {a['account__code']} {a['account__name_en']}: {balance} SAR")
        data['gl_balances'] = '\n'.join(accounts) if accounts else 'No posted entries'

        # HR
        from apps.hr.models import Employee
        employees = Employee.objects.filter(status='active')
        hr_data = employees.aggregate(
            total=Count('id'),
            saudi=Count('id', filter=Q(nationality='saudi')),
            total_salary=Sum('basic_salary'),
        )
        data['hr'] = {
            'total_employees': hr_data['total'] or 0,
            'saudi': hr_data['saudi'] or 0,
            'expat': (hr_data['total'] or 0) - (hr_data['saudi'] or 0),
            'saudization_pct': round((hr_data['saudi'] or 0) / max(hr_data['total'] or 1, 1) * 100, 1),
            'total_monthly_salary': str(hr_data['total_salary'] or 0),
        }

        # POS
        from apps.pos.models import POSTransaction
        pos_today = POSTransaction.objects.filter(
            transacted_at__date=today
        ).aggregate(count=Count('id'), total=Sum('total_amount'))
        pos_month = POSTransaction.objects.filter(
            transacted_at__date__gte=month_start
        ).aggregate(count=Count('id'), total=Sum('total_amount'))

        data['pos'] = {
            'today_sales': str(pos_today['total'] or 0),
            'today_count': pos_today['count'] or 0,
            'month_sales': str(pos_month['total'] or 0),
            'month_count': pos_month['count'] or 0,
        }

        # Build context string
        ctx = f"""=== COMPANY FINANCIAL DATA (READ-ONLY) ===
Date: {today.isoformat()}

--- INVOICING (This Month) ---
Total invoices: {data['invoices_this_month']['count']}
Total amount: {data['invoices_this_month']['total']} SAR
VAT collected: {data['invoices_this_month']['vat']} SAR
B2B invoices: {data['invoices_this_month']['b2b_count']}
B2C invoices: {data['invoices_this_month']['b2c_count']}

--- INVOICING (Year to Date) ---
Total invoices: {data['invoices_ytd']['count']}
Total amount: {data['invoices_ytd']['total']} SAR
VAT collected: {data['invoices_ytd']['vat']} SAR

--- GL ACCOUNT BALANCES ---
{data['gl_balances']}

--- HR ---
Total employees: {data['hr']['total_employees']}
Saudi: {data['hr']['saudi']} | Expat: {data['hr']['expat']}
Saudization: {data['hr']['saudization_pct']}%
Monthly salary cost: {data['hr']['total_monthly_salary']} SAR

--- POS SALES ---
Today: {data['pos']['today_count']} transactions, {data['pos']['today_sales']} SAR
This month: {data['pos']['month_count']} transactions, {data['pos']['month_sales']} SAR
"""
        return ctx, data

    except Exception as e:
        return f"Error loading data: {e}", {}


def get_alert_context():
    """Check for anomalies and generate alert data."""
    alerts = []
    try:
        from apps.zatca.models import TaxInvoice
        from apps.hr.models import Employee, EmployeeDocument
        from apps.pos.models import POSTransaction
        today = date.today()

        # 1. Pending ZATCA invoices older than 12 hours
        cutoff = timezone.now() - timedelta(hours=12)
        stale = TaxInvoice.objects.filter(zatca_status='pending', created_at__lt=cutoff).count()
        if stale > 0:
            alerts.append({
                'type': 'zatca_stale',
                'severity': 'high',
                'message_en': f'{stale} invoices pending ZATCA submission for over 12 hours',
                'message_ar': f'{stale} فواتير معلقة لأكثر من 12 ساعة',
            })

        # 2. Expiring documents (within 30 days)
        threshold = today + timedelta(days=30)
        expiring = EmployeeDocument.objects.filter(
            expiry_date__isnull=False, expiry_date__lte=threshold, expiry_date__gte=today
        ).count()
        if expiring > 0:
            alerts.append({
                'type': 'doc_expiry',
                'severity': 'medium',
                'message_en': f'{expiring} employee documents expiring within 30 days',
                'message_ar': f'{expiring} مستندات موظفين تنتهي خلال 30 يوم',
            })

        # 3. Low saudization warning
        total = Employee.objects.filter(status='active').count()
        saudi = Employee.objects.filter(status='active', nationality='saudi').count()
        if total > 0:
            pct = saudi / total * 100
            if pct < 30:
                alerts.append({
                    'type': 'saudization_low',
                    'severity': 'high',
                    'message_en': f'Saudization at {pct:.1f}% — below minimum Nitaqat threshold',
                    'message_ar': f'نسبة السعودة {pct:.1f}% — أقل من الحد الأدنى لنطاقات',
                })

        # 4. No POS sales today (if it's after noon)
        if today.isoformat() and timezone.now().hour >= 12:
            today_sales = POSTransaction.objects.filter(transacted_at__date=today).count()
            if today_sales == 0:
                alerts.append({
                    'type': 'no_sales',
                    'severity': 'low',
                    'message_en': 'No POS sales recorded today',
                    'message_ar': 'لا توجد مبيعات نقطة بيع اليوم',
                })

    except Exception as e:
        alerts.append({'type': 'error', 'severity': 'low', 'message_en': f'Alert check error: {e}', 'message_ar': 'خطأ'})

    return alerts


def get_forecast_data():
    """Get monthly revenue data for forecasting."""
    try:
        from apps.zatca.models import TaxInvoice
        from django.db.models.functions import TruncMonth

        monthly = TaxInvoice.objects.filter(
            is_cancelled=False
        ).annotate(
            month=TruncMonth('issue_date')
        ).values('month').annotate(
            revenue=Sum('taxable_amount'),
            vat=Sum('vat_amount'),
            count=Count('id'),
        ).order_by('month')

        return [
            {
                'month': m['month'].isoformat() if m['month'] else '',
                'revenue': str(m['revenue'] or 0),
                'vat': str(m['vat'] or 0),
                'invoice_count': m['count'] or 0,
            }
            for m in monthly
        ]
    except Exception:
        return []
