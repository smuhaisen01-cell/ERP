"""
Management command: seed_socpa_coa
Seeds the SOCPA (Saudi Organization for Certified Public Accountants)
Chart of Accounts for a given tenant schema.
Called automatically when a new tenant is created.

Usage:
    python manage.py seed_socpa_coa --schema t_300000000000003
    python manage.py seed_socpa_coa --all  # seed all tenants missing CoA
"""
from django.core.management.base import BaseCommand
from django_tenants.utils import schema_context


# SOCPA Chart of Accounts — bilingual Arabic/English
# Structured: (code, name_ar, name_en, type, socpa_category, normal_balance, is_vat, is_zakat)
SOCPA_ACCOUNTS = [
    # ── ASSETS ────────────────────────────────────────────────
    ("1000", "الأصول",                     "Assets",                     "asset",     "current_assets",        "debit",  False, False),
    ("1100", "الأصول المتداولة",           "Current Assets",             "asset",     "current_assets",        "debit",  False, False),
    ("1110", "النقدية وما يعادلها",        "Cash and Cash Equivalents",  "asset",     "current_assets",        "debit",  False, False),
    ("1111", "الصندوق",                    "Petty Cash",                 "asset",     "current_assets",        "debit",  False, False),
    ("1112", "البنك الرئيسي",             "Main Bank Account",          "asset",     "current_assets",        "debit",  False, False),
    ("1113", "حساب مدى",                  "Mada Payment Account",       "asset",     "current_assets",        "debit",  False, False),
    ("1114", "حساب STC Pay",              "STC Pay Account",            "asset",     "current_assets",        "debit",  False, False),
    ("1120", "الذمم المدينة",             "Accounts Receivable",        "asset",     "current_assets",        "debit",  False, False),
    ("1121", "ذمم مدينة — عملاء",         "Trade Receivables",          "asset",     "current_assets",        "debit",  False, False),
    ("1122", "مخصص الديون المشكوك فيها", "Allowance for Doubtful Debts","asset",    "current_assets",        "credit", False, False),
    ("1130", "المخزون",                   "Inventory",                  "asset",     "current_assets",        "debit",  False, True),
    ("1131", "بضاعة تامة الصنع",          "Finished Goods",             "asset",     "current_assets",        "debit",  False, True),
    ("1132", "مواد خام",                  "Raw Materials",              "asset",     "current_assets",        "debit",  False, True),
    ("1140", "ضريبة القيمة المضافة — مدخلات", "VAT Input Tax",         "asset",     "current_assets",        "debit",  True,  False),
    ("1150", "مصروفات مدفوعة مقدماً",     "Prepaid Expenses",           "asset",     "current_assets",        "debit",  False, False),
    ("1200", "الأصول غير المتداولة",       "Non-Current Assets",        "asset",     "non_current_assets",    "debit",  False, False),
    ("1210", "الممتلكات والمعدات",         "Property, Plant & Equipment","asset",    "non_current_assets",    "debit",  False, False),
    ("1211", "أجهزة الحاسب الآلي",        "Computer Equipment",         "asset",     "non_current_assets",    "debit",  False, False),
    ("1212", "الأثاث والمعدات",           "Furniture and Equipment",    "asset",     "non_current_assets",    "debit",  False, False),
    ("1220", "مجمع الاستهلاك",            "Accumulated Depreciation",   "asset",     "non_current_assets",    "credit", False, False),

    # ── LIABILITIES ───────────────────────────────────────────
    ("2000", "الخصوم",                     "Liabilities",               "liability", "current_liabilities",   "credit", False, False),
    ("2100", "الخصوم المتداولة",           "Current Liabilities",       "liability", "current_liabilities",   "credit", False, False),
    ("2110", "الذمم الدائنة",             "Accounts Payable",          "liability", "current_liabilities",   "credit", False, False),
    ("2111", "ذمم دائنة — موردون",         "Trade Payables",            "liability", "current_liabilities",   "credit", False, False),
    ("2120", "ضريبة القيمة المضافة — مخرجات","VAT Output Tax",         "liability", "current_liabilities",   "credit", True,  False),
    ("2121", "ضريبة القيمة المضافة — صافي","VAT Payable (Net)",        "liability", "current_liabilities",   "credit", True,  False),
    ("2130", "الزكاة المستحقة",           "Zakat Payable",             "liability", "current_liabilities",   "credit", False, True),
    ("2140", "التأمينات الاجتماعية (GOSI)","GOSI Payable",            "liability", "current_liabilities",   "credit", False, False),
    ("2141", "GOSI — حصة صاحب العمل",    "GOSI — Employer Share",     "liability", "current_liabilities",   "credit", False, False),
    ("2142", "GOSI — حصة الموظف",        "GOSI — Employee Share",     "liability", "current_liabilities",   "credit", False, False),
    ("2150", "رواتب مستحقة",              "Accrued Salaries",          "liability", "current_liabilities",   "credit", False, False),
    ("2160", "دفعات مقدمة من العملاء",    "Customer Advances",         "liability", "current_liabilities",   "credit", False, False),
    ("2200", "الخصوم طويلة الأجل",        "Long-Term Liabilities",     "liability", "long_term_liabilities", "credit", False, False),
    ("2210", "قروض بنكية طويلة الأجل",   "Long-Term Bank Loans",      "liability", "long_term_liabilities", "credit", False, False),
    ("2220", "مكافأة نهاية الخدمة",       "End of Service Benefits (EOSB)","liability","long_term_liabilities","credit",False,False),

    # ── EQUITY ────────────────────────────────────────────────
    ("3000", "حقوق الملكية",              "Equity",                    "equity",    "equity",                "credit", False, True),
    ("3100", "رأس المال",                 "Share Capital",             "equity",    "equity",                "credit", False, True),
    ("3200", "الأرباح المحتجزة",          "Retained Earnings",         "equity",    "equity",                "credit", False, False),
    ("3300", "الأرباح / (الخسائر) للفترة","Net Income / (Loss)",      "equity",    "equity",                "credit", False, False),

    # ── REVENUE ───────────────────────────────────────────────
    ("4000", "الإيرادات",                 "Revenue",                   "revenue",   "revenue",               "credit", False, False),
    ("4100", "إيرادات المبيعات",          "Sales Revenue",             "revenue",   "revenue",               "credit", False, False),
    ("4110", "مبيعات البضاعة",            "Product Sales",             "revenue",   "revenue",               "credit", False, False),
    ("4120", "إيرادات الخدمات",           "Service Revenue",           "revenue",   "revenue",               "credit", False, False),
    ("4130", "مبيعات نقطة البيع (POS)",   "POS Sales",                 "revenue",   "revenue",               "credit", False, False),
    ("4200", "إيرادات أخرى",              "Other Revenue",             "revenue",   "revenue",               "credit", False, False),
    ("4210", "خصم نقدي مكتسب",           "Purchase Discounts Earned", "revenue",   "revenue",               "credit", False, False),

    # ── COST OF GOODS SOLD ────────────────────────────────────
    ("5000", "تكلفة المبيعات",            "Cost of Goods Sold",        "expense",   "cogs",                  "debit",  False, False),
    ("5100", "تكلفة البضاعة المباعة",     "Cost of Products Sold",     "expense",   "cogs",                  "debit",  False, False),

    # ── OPERATING EXPENSES ────────────────────────────────────
    ("6000", "المصروفات التشغيلية",       "Operating Expenses",        "expense",   "operating_expenses",    "debit",  False, False),
    ("6100", "الرواتب والأجور",           "Salaries and Wages",        "expense",   "operating_expenses",    "debit",  False, False),
    ("6101", "رواتب موظفين سعوديين",      "Saudi National Salaries",   "expense",   "operating_expenses",    "debit",  False, False),
    ("6102", "رواتب موظفين وافدين",       "Expat Salaries",            "expense",   "operating_expenses",    "debit",  False, False),
    ("6110", "GOSI — مصروف صاحب العمل",  "GOSI — Employer Expense",  "expense",   "operating_expenses",    "debit",  False, False),
    ("6120", "الإيجارات",                 "Rent Expense",              "expense",   "operating_expenses",    "debit",  False, False),
    ("6130", "الكهرباء والماء",           "Utilities",                 "expense",   "operating_expenses",    "debit",  False, False),
    ("6140", "الاتصالات والإنترنت",       "Communications",            "expense",   "operating_expenses",    "debit",  False, False),
    ("6150", "مصروفات التسويق",           "Marketing Expenses",        "expense",   "operating_expenses",    "debit",  False, False),
    ("6160", "الاستهلاك",                 "Depreciation Expense",      "expense",   "operating_expenses",    "debit",  False, False),
    ("6170", "مصروفات الصيانة",           "Maintenance Expenses",      "expense",   "operating_expenses",    "debit",  False, False),
    ("6200", "المصروفات الإدارية",         "Administrative Expenses",   "expense",   "operating_expenses",    "debit",  False, False),
    ("6210", "القرطاسية ومستلزمات المكتب","Stationery and Office Supplies","expense","operating_expenses",   "debit",  False, False),
    ("6900", "مصروفات أخرى",              "Other Expenses",            "expense",   "other_expenses",        "debit",  False, False),
    ("6910", "غرامات وعقوبات",            "Fines and Penalties",       "expense",   "other_expenses",        "debit",  False, False),
]


class Command(BaseCommand):
    help = "Seed SOCPA Chart of Accounts for a tenant schema"

    def add_arguments(self, parser):
        parser.add_argument("--schema", type=str, help="Tenant schema name (e.g. t_300000000000003)")
        parser.add_argument("--all", action="store_true", help="Seed all active tenants")

    def handle(self, *args, **options):
        from apps.tenants.models import Tenant

        if options["all"]:
            tenants = Tenant.objects.filter(is_active=True)
            for tenant in tenants:
                self._seed_for_schema(tenant.schema_name)
        elif options["schema"]:
            self._seed_for_schema(options["schema"])
        else:
            self.stderr.write("Provide --schema or --all")

    def _seed_for_schema(self, schema: str):
        from apps.accounting.models import ChartOfAccount

        with schema_context(schema):
            created = 0
            for code, name_ar, name_en, acct_type, socpa_cat, normal_bal, is_vat, is_zakat in SOCPA_ACCOUNTS:
                obj, was_created = ChartOfAccount.objects.get_or_create(
                    code=code,
                    defaults={
                        "name_ar": name_ar,
                        "name_en": name_en,
                        "account_type": acct_type,
                        "socpa_category": socpa_cat,
                        "normal_balance": normal_bal,
                        "is_vat_account": is_vat,
                        "is_zakat_account": is_zakat,
                        "is_leaf": not any(
                            other_code != code and other_code.startswith(code)
                            for other_code, *_ in SOCPA_ACCOUNTS
                        ),
                    }
                )
                if was_created:
                    created += 1

            self.stdout.write(
                self.style.SUCCESS(f"✓ {schema}: {created} accounts seeded ({len(SOCPA_ACCOUNTS)} total)")
            )
