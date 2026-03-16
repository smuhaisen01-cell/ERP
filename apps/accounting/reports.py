"""
Reports API — generates structured report data from live database.
All reports are read-only and tenant-scoped.
"""
from decimal import Decimal
from datetime import date, timedelta
from django.db.models import Sum, Count, Q, F
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class TrialBalanceReport(APIView):
    """Trial Balance — totals per account from journal entries."""

    def get(self, request):
        from apps.accounting.models import ChartOfAccount, JournalEntryLine

        as_of = request.query_params.get('as_of', date.today().isoformat())
        accounts = ChartOfAccount.objects.filter(is_leaf=True, is_active=True).order_by('code')

        rows = []
        total_debit = Decimal('0')
        total_credit = Decimal('0')

        for acc in accounts:
            agg = JournalEntryLine.objects.filter(
                account=acc,
                entry__status='posted',
                entry__entry_date__lte=as_of,
            ).aggregate(
                debit=Sum('debit_amount'),
                credit=Sum('credit_amount'),
            )
            debit = agg['debit'] or Decimal('0')
            credit = agg['credit'] or Decimal('0')
            balance = debit - credit

            if debit > 0 or credit > 0:
                rows.append({
                    'code': acc.code,
                    'name_ar': acc.name_ar,
                    'name_en': acc.name_en,
                    'account_type': acc.account_type,
                    'debit': str(debit),
                    'credit': str(credit),
                    'balance': str(balance),
                })
                total_debit += debit
                total_credit += credit

        return Response({
            'report': 'trial_balance',
            'as_of': as_of,
            'rows': rows,
            'total_debit': str(total_debit),
            'total_credit': str(total_credit),
            'is_balanced': total_debit == total_credit,
        })


class IncomeStatementReport(APIView):
    """Income Statement (Profit & Loss) for a period."""

    def get(self, request):
        from apps.accounting.models import JournalEntryLine

        start = request.query_params.get('start', date.today().replace(month=1, day=1).isoformat())
        end = request.query_params.get('end', date.today().isoformat())

        def sum_by_type(acct_type):
            agg = JournalEntryLine.objects.filter(
                entry__status='posted',
                entry__entry_date__gte=start,
                entry__entry_date__lte=end,
                account__account_type=acct_type,
            ).aggregate(debit=Sum('debit_amount'), credit=Sum('credit_amount'))
            return (agg['credit'] or Decimal('0')) - (agg['debit'] or Decimal('0'))

        revenue = sum_by_type('revenue')
        cogs = -sum_by_type('expense')  # expenses are debit-normal
        # Separate operating from other
        gross_profit = revenue - cogs
        operating_exp = JournalEntryLine.objects.filter(
            entry__status='posted',
            entry__entry_date__gte=start,
            entry__entry_date__lte=end,
            account__socpa_category='operating_expenses',
        ).aggregate(debit=Sum('debit_amount'))['debit'] or Decimal('0')

        net_income = revenue - cogs - operating_exp

        return Response({
            'report': 'income_statement',
            'period_start': start,
            'period_end': end,
            'revenue': str(revenue),
            'cost_of_sales': str(cogs),
            'gross_profit': str(gross_profit),
            'operating_expenses': str(operating_exp),
            'net_income': str(net_income),
        })


class BalanceSheetReport(APIView):
    """Balance Sheet — Assets, Liabilities, Equity snapshot."""

    def get(self, request):
        from apps.accounting.models import JournalEntryLine

        as_of = request.query_params.get('as_of', date.today().isoformat())

        def sum_type(acct_type):
            agg = JournalEntryLine.objects.filter(
                entry__status='posted',
                entry__entry_date__lte=as_of,
                account__account_type=acct_type,
            ).aggregate(debit=Sum('debit_amount'), credit=Sum('credit_amount'))
            debit = agg['debit'] or Decimal('0')
            credit = agg['credit'] or Decimal('0')
            if acct_type in ('asset',):
                return debit - credit
            return credit - debit

        assets = sum_type('asset')
        liabilities = sum_type('liability')
        equity = sum_type('equity')

        return Response({
            'report': 'balance_sheet',
            'as_of': as_of,
            'total_assets': str(assets),
            'total_liabilities': str(liabilities),
            'total_equity': str(equity),
            'liabilities_plus_equity': str(liabilities + equity),
            'is_balanced': assets == liabilities + equity,
        })


class VAT103Report(APIView):
    """VAT-103 Return Report — Saudi quarterly VAT filing data."""

    def get(self, request):
        from apps.zatca.models import TaxInvoice

        # Default to current quarter
        today = date.today()
        q_start = date(today.year, ((today.month - 1) // 3) * 3 + 1, 1)
        q_end_month = q_start.month + 2
        q_end = date(today.year, q_end_month, 28)

        start = request.query_params.get('start', q_start.isoformat())
        end = request.query_params.get('end', q_end.isoformat())

        invoices = TaxInvoice.objects.filter(
            issue_date__gte=start,
            issue_date__lte=end,
            is_cancelled=False,
        )

        # Box 1: Standard rated sales (B2B + B2C)
        sales_agg = invoices.filter(
            invoice_type__in=['388', '386'],
        ).aggregate(
            taxable=Sum('taxable_amount'),
            vat=Sum('vat_amount'),
            total=Sum('total_amount'),
            count=Count('id'),
        )

        box_1 = sales_agg['taxable'] or Decimal('0')
        box_2 = sales_agg['vat'] or Decimal('0')

        # B2B vs B2C breakdown
        b2b = invoices.filter(invoice_type='388').aggregate(
            amount=Sum('total_amount'), count=Count('id'))
        b2c = invoices.filter(invoice_type='386').aggregate(
            amount=Sum('total_amount'), count=Count('id'))

        return Response({
            'report': 'vat_103',
            'period_start': start,
            'period_end': end,
            'box_1_taxable_sales': str(box_1),
            'box_2_vat_on_sales': str(box_2),
            'box_3_zero_rated': '0.00',
            'box_4_exempt_sales': '0.00',
            'box_5_taxable_purchases': '0.00',
            'box_6_vat_on_purchases': '0.00',
            'box_7_net_vat_due': str(box_2),
            'total_invoices': sales_agg['count'] or 0,
            'b2b_total': str(b2b['amount'] or Decimal('0')),
            'b2b_count': b2b['count'] or 0,
            'b2c_total': str(b2c['amount'] or Decimal('0')),
            'b2c_count': b2c['count'] or 0,
        })


class HRPayrollReport(APIView):
    """HR Summary — employees, GOSI, saudization, payroll cost."""

    def get(self, request):
        from apps.hr.models import Employee, SaudizationReport

        employees = Employee.objects.filter(status='active')
        total = employees.count()
        saudi = employees.filter(nationality='saudi').count()
        expat = employees.filter(nationality='expat').count()

        salary_agg = employees.aggregate(
            total_basic=Sum('basic_salary'),
            total_housing=Sum('housing_allowance'),
            total_transport=Sum('transport_allowance'),
        )

        total_basic = salary_agg['total_basic'] or Decimal('0')
        total_housing = salary_agg['total_housing'] or Decimal('0')
        total_transport = salary_agg['total_transport'] or Decimal('0')
        total_gross = total_basic + total_housing + total_transport

        # GOSI totals
        gosi_employer = Decimal('0')
        gosi_employee = Decimal('0')
        for emp in employees:
            gosi = emp.calculate_gosi()
            gosi_employer += gosi['employer_contribution']
            gosi_employee += gosi['employee_deduction']

        # Saudization
        saud_pct = round(saudi / total * 100, 2) if total > 0 else 0
        if saud_pct >= 80: band = 'platinum'
        elif saud_pct >= 60: band = 'high_green'
        elif saud_pct >= 40: band = 'medium_green'
        elif saud_pct >= 25: band = 'low_green'
        elif saud_pct >= 10: band = 'yellow'
        else: band = 'red'

        # By department
        dept_breakdown = []
        for emp in employees.values('department__name_ar', 'department__name_en').annotate(
            count=Count('id'),
            saudi_count=Count('id', filter=Q(nationality='saudi')),
            total_salary=Sum('basic_salary'),
        ):
            dept_breakdown.append({
                'department_ar': emp['department__name_ar'],
                'department_en': emp['department__name_en'],
                'employees': emp['count'],
                'saudi': emp['saudi_count'],
                'expat': emp['count'] - emp['saudi_count'],
                'total_salary': str(emp['total_salary'] or 0),
            })

        return Response({
            'report': 'hr_summary',
            'total_employees': total,
            'saudi_employees': saudi,
            'expat_employees': expat,
            'saudization_percentage': saud_pct,
            'nitaqat_band': band,
            'total_basic_salary': str(total_basic),
            'total_housing': str(total_housing),
            'total_transport': str(total_transport),
            'total_gross_salary': str(total_gross),
            'gosi_employer_total': str(gosi_employer),
            'gosi_employee_total': str(gosi_employee),
            'gosi_total': str(gosi_employer + gosi_employee),
            'department_breakdown': dept_breakdown,
        })


class ZATCAStatusReport(APIView):
    """ZATCA Invoice Status Report — submission status breakdown."""

    def get(self, request):
        from apps.zatca.models import TaxInvoice

        start = request.query_params.get('start', (date.today() - timedelta(days=30)).isoformat())
        end = request.query_params.get('end', date.today().isoformat())

        invoices = TaxInvoice.objects.filter(
            issue_date__gte=start,
            issue_date__lte=end,
        )

        status_breakdown = invoices.values('zatca_status').annotate(
            count=Count('id'),
            total=Sum('total_amount'),
            vat=Sum('vat_amount'),
        )

        type_breakdown = invoices.values('invoice_type').annotate(
            count=Count('id'),
            total=Sum('total_amount'),
        )

        totals = invoices.aggregate(
            count=Count('id'),
            total=Sum('total_amount'),
            vat=Sum('vat_amount'),
        )

        return Response({
            'report': 'zatca_status',
            'period_start': start,
            'period_end': end,
            'total_invoices': totals['count'] or 0,
            'total_amount': str(totals['total'] or Decimal('0')),
            'total_vat': str(totals['vat'] or Decimal('0')),
            'by_status': [
                {
                    'status': s['zatca_status'],
                    'count': s['count'],
                    'total': str(s['total'] or Decimal('0')),
                    'vat': str(s['vat'] or Decimal('0')),
                }
                for s in status_breakdown
            ],
            'by_type': [
                {
                    'type': t['invoice_type'],
                    'type_label': 'B2B' if t['invoice_type'] == '388' else 'B2C',
                    'count': t['count'],
                    'total': str(t['total'] or Decimal('0')),
                }
                for t in type_breakdown
            ],
        })


class POSDailySalesReport(APIView):
    """POS Daily Sales (Z-Report) — per terminal/session breakdown."""

    def get(self, request):
        from apps.pos.models import POSSession, POSTransaction

        report_date = request.query_params.get('date', date.today().isoformat())

        sessions = POSSession.objects.filter(
            opened_at__date=report_date,
        ).select_related('terminal', 'terminal__branch', 'cashier')

        session_data = []
        grand_total = Decimal('0')
        grand_vat = Decimal('0')
        grand_txn_count = 0

        for s in sessions:
            txns = s.transactions.all()
            txn_agg = txns.aggregate(
                total=Sum('total_amount'),
                vat=Sum('vat_amount'),
                count=Count('id'),
            )
            total = txn_agg['total'] or Decimal('0')
            vat = txn_agg['vat'] or Decimal('0')
            count = txn_agg['count'] or 0

            payment_breakdown = {}
            for method in ['cash', 'mada', 'stc_pay', 'credit_card', 'apple_pay']:
                method_total = txns.filter(payment_method=method).aggregate(t=Sum('total_amount'))['t']
                if method_total:
                    payment_breakdown[method] = str(method_total)

            session_data.append({
                'session_id': s.id,
                'terminal': s.terminal.terminal_id if s.terminal else '',
                'branch': s.terminal.branch.name_ar if s.terminal and s.terminal.branch else '',
                'cashier': s.cashier.get_full_name() or s.cashier.username,
                'opened_at': s.opened_at.isoformat() if s.opened_at else '',
                'closed_at': s.closed_at.isoformat() if s.closed_at else '',
                'status': s.status,
                'total_sales': str(total),
                'total_vat': str(vat),
                'transaction_count': count,
                'payment_breakdown': payment_breakdown,
            })

            grand_total += total
            grand_vat += vat
            grand_txn_count += count

        return Response({
            'report': 'pos_daily_sales',
            'date': report_date,
            'sessions': session_data,
            'grand_total_sales': str(grand_total),
            'grand_total_vat': str(grand_vat),
            'grand_transaction_count': grand_txn_count,
        })
