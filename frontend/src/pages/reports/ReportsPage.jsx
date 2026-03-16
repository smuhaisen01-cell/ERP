import { useState, useEffect } from 'react'
import { FileBarChart, DollarSign, Receipt, Users, ShoppingBag, Shield, Loader2, RefreshCw, Download } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import { reportsAPI } from '../../services/api'

const TABS = [
  { id: 'trial_balance',     icon: FileBarChart, labelAr: 'ميزان المراجعة',     labelEn: 'Trial Balance' },
  { id: 'income_statement',  icon: DollarSign,   labelAr: 'قائمة الدخل',         labelEn: 'Income Statement' },
  { id: 'balance_sheet',     icon: FileBarChart, labelAr: 'الميزانية العمومية',  labelEn: 'Balance Sheet' },
  { id: 'vat_103',           icon: Receipt,      labelAr: 'إقرار VAT-103',       labelEn: 'VAT-103 Return' },
  { id: 'hr_summary',        icon: Users,        labelAr: 'ملخص الموارد البشرية', labelEn: 'HR Summary' },
  { id: 'zatca_status',      icon: Shield,       labelAr: 'حالة ZATCA',           labelEn: 'ZATCA Status' },
  { id: 'pos_daily',         icon: ShoppingBag,  labelAr: 'مبيعات يومية',         labelEn: 'POS Daily Sales' },
]

function ReportCard({ label, value, sub, color = 'blue' }) {
  const bg = { blue: 'bg-blue-50', green: 'bg-green-50', red: 'bg-red-50', purple: 'bg-purple-50', orange: 'bg-orange-50' }
  return (
    <div className={`${bg[color] || bg.blue} rounded-xl p-4`}>
      <div className="text-xs text-slate-500 mb-1">{label}</div>
      <div className="text-xl font-bold text-slate-900 num">{value}</div>
      {sub && <div className="text-xs text-slate-400 mt-1">{sub}</div>}
    </div>
  )
}

function DataTable({ headers, rows, lang }) {
  return (
    <div className="overflow-x-auto">
      <table className="w-full text-sm">
        <thead><tr className="border-b border-slate-200">
          {headers.map((h, i) => <th key={i} className="text-start py-3 px-2 font-medium text-slate-500">{h}</th>)}
        </tr></thead>
        <tbody>
          {rows.map((row, i) => (
            <tr key={i} className="border-b border-slate-100 hover:bg-slate-50">
              {row.map((cell, j) => <td key={j} className="py-2.5 px-2">{cell}</td>)}
            </tr>
          ))}
          {rows.length === 0 && (
            <tr><td colSpan={headers.length} className="text-center py-8 text-slate-400">
              {lang === 'ar' ? 'لا توجد بيانات' : 'No data available'}
            </td></tr>
          )}
        </tbody>
      </table>
    </div>
  )
}

export default function ReportsPage() {
  const { lang } = useLang()
  const { api } = useAuth()
  const [tab, setTab] = useState('trial_balance')
  const [loading, setLoading] = useState(false)
  const [data, setData] = useState(null)

  const fmt = (n) => {
    const num = parseFloat(n || 0)
    return new Intl.NumberFormat(lang === 'ar' ? 'ar-SA' : 'en-SA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(num)
  }

  const fetchReport = async (reportId) => {
    setLoading(true)
    setData(null)
    try {
      const fetchers = {
        trial_balance: () => reportsAPI.getTrialBalance(api),
        income_statement: () => reportsAPI.getIncomeStatement(api),
        balance_sheet: () => reportsAPI.getBalanceSheet(api),
        vat_103: () => reportsAPI.getVAT103(api),
        hr_summary: () => reportsAPI.getHRSummary(api),
        zatca_status: () => reportsAPI.getZATCAStatus(api),
        pos_daily: () => reportsAPI.getPOSDaily(api),
      }
      const res = await fetchers[reportId]()
      setData(res.data)
    } catch (err) {
      console.error('Report error:', err)
      setData({ error: true })
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchReport(tab) }, [tab])

  const renderReport = () => {
    if (loading) return <div className="flex justify-center py-16"><Loader2 size={32} className="animate-spin text-brand-500" /></div>
    if (!data) return null
    if (data.error) return <p className="text-center py-8 text-red-400">{lang === 'ar' ? 'خطأ في تحميل التقرير' : 'Error loading report'}</p>

    switch (tab) {
      case 'trial_balance':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <ReportCard label={lang === 'ar' ? 'إجمالي المدين' : 'Total Debit'} value={`${fmt(data.total_debit)} SAR`} color="blue" />
              <ReportCard label={lang === 'ar' ? 'إجمالي الدائن' : 'Total Credit'} value={`${fmt(data.total_credit)} SAR`} color="green" />
              <ReportCard label={lang === 'ar' ? 'متوازن؟' : 'Balanced?'} value={data.is_balanced ? '✓' : '✗'} color={data.is_balanced ? 'green' : 'red'} />
            </div>
            <DataTable
              lang={lang}
              headers={[lang === 'ar' ? 'الرمز' : 'Code', lang === 'ar' ? 'الحساب' : 'Account', lang === 'ar' ? 'مدين' : 'Debit', lang === 'ar' ? 'دائن' : 'Credit', lang === 'ar' ? 'الرصيد' : 'Balance']}
              rows={(data.rows || []).map(r => [
                <span className="font-mono font-semibold">{r.code}</span>,
                lang === 'ar' ? r.name_ar : r.name_en,
                <span className="num">{fmt(r.debit)}</span>,
                <span className="num">{fmt(r.credit)}</span>,
                <span className={`num font-semibold ${parseFloat(r.balance) < 0 ? 'text-red-600' : ''}`}>{fmt(r.balance)}</span>,
              ])}
            />
          </div>
        )

      case 'income_statement':
        return (
          <div className="space-y-4">
            <div className="text-sm text-slate-500 mb-2">{data.period_start} — {data.period_end}</div>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <ReportCard label={lang === 'ar' ? 'الإيرادات' : 'Revenue'} value={`${fmt(data.revenue)} SAR`} color="green" />
              <ReportCard label={lang === 'ar' ? 'تكلفة المبيعات' : 'COGS'} value={`${fmt(data.cost_of_sales)} SAR`} color="orange" />
              <ReportCard label={lang === 'ar' ? 'مصروفات تشغيلية' : 'Operating Exp.'} value={`${fmt(data.operating_expenses)} SAR`} color="red" />
              <ReportCard label={lang === 'ar' ? 'صافي الدخل' : 'Net Income'} value={`${fmt(data.net_income)} SAR`} color={parseFloat(data.net_income) >= 0 ? 'green' : 'red'} />
            </div>
            <div className="card bg-slate-50 space-y-3">
              <div className="flex justify-between py-2 border-b"><span>{lang === 'ar' ? 'الإيرادات' : 'Revenue'}</span><span className="num font-semibold">{fmt(data.revenue)}</span></div>
              <div className="flex justify-between py-2 border-b"><span>{lang === 'ar' ? '(-) تكلفة المبيعات' : '(-) Cost of Sales'}</span><span className="num">{fmt(data.cost_of_sales)}</span></div>
              <div className="flex justify-between py-2 border-b font-semibold"><span>{lang === 'ar' ? 'إجمالي الربح' : 'Gross Profit'}</span><span className="num">{fmt(data.gross_profit)}</span></div>
              <div className="flex justify-between py-2 border-b"><span>{lang === 'ar' ? '(-) مصروفات تشغيلية' : '(-) Operating Expenses'}</span><span className="num">{fmt(data.operating_expenses)}</span></div>
              <div className="flex justify-between py-2 text-lg font-bold"><span>{lang === 'ar' ? 'صافي الدخل' : 'Net Income'}</span><span className={`num ${parseFloat(data.net_income) >= 0 ? 'text-green-600' : 'text-red-600'}`}>{fmt(data.net_income)} SAR</span></div>
            </div>
          </div>
        )

      case 'balance_sheet':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <ReportCard label={lang === 'ar' ? 'الأصول' : 'Assets'} value={`${fmt(data.total_assets)} SAR`} color="blue" />
              <ReportCard label={lang === 'ar' ? 'الخصوم' : 'Liabilities'} value={`${fmt(data.total_liabilities)} SAR`} color="red" />
              <ReportCard label={lang === 'ar' ? 'حقوق الملكية' : 'Equity'} value={`${fmt(data.total_equity)} SAR`} color="purple" />
              <ReportCard label={lang === 'ar' ? 'متوازن؟' : 'Balanced?'} value={data.is_balanced ? '✓' : '✗'} color={data.is_balanced ? 'green' : 'red'} />
            </div>
          </div>
        )

      case 'vat_103':
        return (
          <div className="space-y-4">
            <div className="text-sm text-slate-500">{data.period_start} — {data.period_end}</div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <ReportCard label={lang === 'ar' ? 'مبيعات خاضعة' : 'Taxable Sales'} value={`${fmt(data.box_1_taxable_sales)} SAR`} color="blue" />
              <ReportCard label={lang === 'ar' ? 'ضريبة المبيعات' : 'VAT on Sales'} value={`${fmt(data.box_2_vat_on_sales)} SAR`} color="orange" />
              <ReportCard label={lang === 'ar' ? 'صافي الضريبة المستحقة' : 'Net VAT Due'} value={`${fmt(data.box_7_net_vat_due)} SAR`} color="red" />
            </div>
            <div className="card bg-slate-50 space-y-2">
              <h4 className="font-semibold mb-2">{lang === 'ar' ? 'تفاصيل VAT-103' : 'VAT-103 Details'}</h4>
              {[
                ['Box 1', lang === 'ar' ? 'مبيعات خاضعة للضريبة' : 'Standard Rated Sales', data.box_1_taxable_sales],
                ['Box 2', lang === 'ar' ? 'ضريبة على المبيعات' : 'VAT on Sales', data.box_2_vat_on_sales],
                ['Box 3', lang === 'ar' ? 'مبيعات بنسبة صفر' : 'Zero-Rated Sales', data.box_3_zero_rated],
                ['Box 4', lang === 'ar' ? 'مبيعات معفاة' : 'Exempt Sales', data.box_4_exempt_sales],
                ['Box 5', lang === 'ar' ? 'مشتريات خاضعة' : 'Taxable Purchases', data.box_5_taxable_purchases],
                ['Box 6', lang === 'ar' ? 'ضريبة على المشتريات' : 'VAT on Purchases', data.box_6_vat_on_purchases],
                ['Box 7', lang === 'ar' ? 'صافي الضريبة المستحقة' : 'Net VAT Due', data.box_7_net_vat_due],
              ].map(([box, label, val]) => (
                <div key={box} className="flex justify-between py-1.5 border-b border-slate-200 last:border-0">
                  <span><span className="text-xs text-slate-400 me-2">{box}</span>{label}</span>
                  <span className="num font-semibold">{fmt(val)} SAR</span>
                </div>
              ))}
            </div>
            <div className="grid grid-cols-2 gap-4">
              <ReportCard label="B2B" value={`${data.b2b_count} ${lang === 'ar' ? 'فاتورة' : 'invoices'}`} sub={`${fmt(data.b2b_total)} SAR`} color="purple" />
              <ReportCard label="B2C" value={`${data.b2c_count} ${lang === 'ar' ? 'فاتورة' : 'invoices'}`} sub={`${fmt(data.b2c_total)} SAR`} color="green" />
            </div>
          </div>
        )

      case 'hr_summary':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <ReportCard label={lang === 'ar' ? 'إجمالي الموظفين' : 'Total Employees'} value={data.total_employees} color="blue" />
              <ReportCard label={lang === 'ar' ? 'سعوديون' : 'Saudi'} value={data.saudi_employees} sub={`${data.saudization_percentage}%`} color="green" />
              <ReportCard label={lang === 'ar' ? 'وافدون' : 'Expat'} value={data.expat_employees} color="orange" />
              <ReportCard label={lang === 'ar' ? 'نطاقات' : 'Nitaqat'} value={data.nitaqat_band?.replace('_', ' ')} color={data.nitaqat_band?.includes('green') || data.nitaqat_band === 'platinum' ? 'green' : 'red'} />
            </div>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <ReportCard label={lang === 'ar' ? 'إجمالي الرواتب' : 'Total Gross Salary'} value={`${fmt(data.total_gross_salary)} SAR`} color="blue" />
              <ReportCard label={lang === 'ar' ? 'GOSI صاحب العمل' : 'GOSI Employer'} value={`${fmt(data.gosi_employer_total)} SAR`} color="orange" />
              <ReportCard label={lang === 'ar' ? 'GOSI الموظف' : 'GOSI Employee'} value={`${fmt(data.gosi_employee_total)} SAR`} color="purple" />
            </div>
            {data.department_breakdown?.length > 0 && (
              <DataTable
                lang={lang}
                headers={[lang === 'ar' ? 'القسم' : 'Department', lang === 'ar' ? 'الموظفون' : 'Employees', lang === 'ar' ? 'سعوديون' : 'Saudi', lang === 'ar' ? 'وافدون' : 'Expat', lang === 'ar' ? 'إجمالي الرواتب' : 'Total Salary']}
                rows={data.department_breakdown.map(d => [
                  lang === 'ar' ? d.department_ar : d.department_en,
                  d.employees,
                  <span className="text-green-600 font-semibold">{d.saudi}</span>,
                  <span className="text-blue-600">{d.expat}</span>,
                  <span className="num font-semibold">{fmt(d.total_salary)} SAR</span>,
                ])}
              />
            )}
          </div>
        )

      case 'zatca_status':
        return (
          <div className="space-y-4">
            <div className="text-sm text-slate-500">{data.period_start} — {data.period_end}</div>
            <div className="grid grid-cols-3 gap-4">
              <ReportCard label={lang === 'ar' ? 'إجمالي الفواتير' : 'Total Invoices'} value={data.total_invoices} color="blue" />
              <ReportCard label={lang === 'ar' ? 'إجمالي المبلغ' : 'Total Amount'} value={`${fmt(data.total_amount)} SAR`} color="green" />
              <ReportCard label={lang === 'ar' ? 'إجمالي الضريبة' : 'Total VAT'} value={`${fmt(data.total_vat)} SAR`} color="orange" />
            </div>
            {data.by_status?.length > 0 && (
              <DataTable
                lang={lang}
                headers={[lang === 'ar' ? 'الحالة' : 'Status', lang === 'ar' ? 'العدد' : 'Count', lang === 'ar' ? 'المبلغ' : 'Amount', lang === 'ar' ? 'الضريبة' : 'VAT']}
                rows={data.by_status.map(s => [
                  <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'cleared' ? 'bg-green-100 text-green-700' : s.status === 'reported' ? 'bg-blue-100 text-blue-700' : s.status === 'pending' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>{s.status}</span>,
                  s.count,
                  <span className="num">{fmt(s.total)} SAR</span>,
                  <span className="num">{fmt(s.vat)} SAR</span>,
                ])}
              />
            )}
            {data.by_type?.length > 0 && (
              <div className="grid grid-cols-2 gap-4">
                {data.by_type.map(t => (
                  <ReportCard key={t.type} label={t.type_label} value={`${t.count} ${lang === 'ar' ? 'فاتورة' : 'invoices'}`} sub={`${fmt(t.total)} SAR`} color={t.type === '388' ? 'purple' : 'green'} />
                ))}
              </div>
            )}
          </div>
        )

      case 'pos_daily':
        return (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <ReportCard label={lang === 'ar' ? 'إجمالي المبيعات' : 'Total Sales'} value={`${fmt(data.grand_total_sales)} SAR`} color="green" />
              <ReportCard label={lang === 'ar' ? 'إجمالي الضريبة' : 'Total VAT'} value={`${fmt(data.grand_total_vat)} SAR`} color="orange" />
              <ReportCard label={lang === 'ar' ? 'عدد المعاملات' : 'Transactions'} value={data.grand_transaction_count} color="blue" />
            </div>
            {data.sessions?.length > 0 ? (
              <DataTable
                lang={lang}
                headers={[lang === 'ar' ? 'الطرفية' : 'Terminal', lang === 'ar' ? 'الكاشير' : 'Cashier', lang === 'ar' ? 'الحالة' : 'Status', lang === 'ar' ? 'المبيعات' : 'Sales', lang === 'ar' ? 'المعاملات' : 'Txns']}
                rows={data.sessions.map(s => [
                  s.terminal || '-',
                  s.cashier,
                  <span className={`text-xs px-2 py-0.5 rounded-full ${s.status === 'closed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{s.status}</span>,
                  <span className="num font-semibold">{fmt(s.total_sales)} SAR</span>,
                  s.transaction_count,
                ])}
              />
            ) : (
              <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا توجد جلسات لهذا اليوم' : 'No POS sessions for today'}</p>
            )}
          </div>
        )

      default: return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'التقارير' : 'Reports'}</h1>
          <p className="text-sm text-slate-500">{lang === 'ar' ? 'التقارير المالية والتشغيلية والضريبية' : 'Financial, operational & tax reports'}</p>
        </div>
        <button onClick={() => fetchReport(tab)} className="btn btn-secondary flex items-center gap-2">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          {lang === 'ar' ? 'تحديث' : 'Refresh'}
        </button>
      </div>

      {/* Tab selector */}
      <div className="flex gap-2 overflow-x-auto pb-2">
        {TABS.map(t => {
          const Icon = t.icon
          return (
            <button key={t.id} onClick={() => setTab(t.id)}
              className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
                tab === t.id ? 'bg-brand-500 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
              }`}>
              <Icon size={16} />
              {lang === 'ar' ? t.labelAr : t.labelEn}
            </button>
          )
        })}
      </div>

      {/* Report content */}
      <div className="card">
        {renderReport()}
      </div>
    </div>
  )
}
