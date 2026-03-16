from django.urls import path
from apps.accounting.reports import (
    TrialBalanceReport,
    IncomeStatementReport,
    BalanceSheetReport,
    VAT103Report,
    HRPayrollReport,
    ZATCAStatusReport,
    POSDailySalesReport,
)

urlpatterns = [
    path('trial-balance/', TrialBalanceReport.as_view(), name='report-trial-balance'),
    path('income-statement/', IncomeStatementReport.as_view(), name='report-income-statement'),
    path('balance-sheet/', BalanceSheetReport.as_view(), name='report-balance-sheet'),
    path('vat-103/', VAT103Report.as_view(), name='report-vat-103'),
    path('hr-summary/', HRPayrollReport.as_view(), name='report-hr-summary'),
    path('zatca-status/', ZATCAStatusReport.as_view(), name='report-zatca-status'),
    path('pos-daily/', POSDailySalesReport.as_view(), name='report-pos-daily'),
]
