import { useState, useEffect } from 'react'
import {
  DollarSign, Users, ShoppingBag, FileCheck,
  Receipt, Calculator, AlertCircle, Loader2, RefreshCw
} from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import { hrAPI, accountingAPI, zatcaAPI, posAPI } from '../../services/api'

function KPICard({ icon: Icon, label, value, sub, color = 'blue', loading }) {
  const colors = {
    blue:   { light: 'bg-brand-50',  text: 'text-brand-600' },
    green:  { light: 'bg-green-50',  text: 'text-green-600' },
    orange: { light: 'bg-orange-50', text: 'text-orange-600' },
    purple: { light: 'bg-purple-50', text: 'text-purple-600' },
  }
  const c = colors[color]
  return (
    <div className="kpi-card card-hover">
      <div className="flex items-start justify-between mb-4">
        <div className={`w-11 h-11 rounded-xl ${c.light} ${c.text} flex items-center justify-center`}>
          <Icon size={22} />
        </div>
      </div>
      {loading ? (
        <Loader2 size={20} className="animate-spin text-slate-400" />
      ) : (
        <>
          <div className="text-2xl font-bold text-slate-900 mb-0.5 num">{value}</div>
          <div className="text-sm font-medium text-slate-700 mb-1">{label}</div>
          <div className="text-xs text-slate-400">{sub}</div>
        </>
      )}
    </div>
  )
}

export default function DashboardPage() {
  const { t, lang } = useLang()
  const { api } = useAuth()
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    employees: 0, saudiPct: 0, nitaqat: '',
    accounts: 0, invoices: 0, pendingInvoices: 0,
    sessions: 0, departments: 0,
  })
  const [recentEmployees, setRecentEmployees] = useState([])
  const [recentInvoices, setRecentInvoices] = useState([])

  const fetchDashboard = async () => {
    setLoading(true)
    try {
      const [empRes, deptRes, coaRes, invRes, sessRes] = await Promise.allSettled([
        hrAPI.getEmployees(api),
        hrAPI.getDepartments(api),
        accountingAPI.getChartOfAccounts(api),
        zatcaAPI.getInvoices(api),
        posAPI.getSessions(api),
      ])

      const employees = empRes.status === 'fulfilled' ? empRes.value.data.results || [] : []
      const departments = deptRes.status === 'fulfilled' ? deptRes.value.data.results || [] : []
      const accounts = coaRes.status === 'fulfilled' ? coaRes.value.data.results || [] : []
      const invoices = invRes.status === 'fulfilled' ? invRes.value.data.results || [] : []
      const sessions = sessRes.status === 'fulfilled' ? sessRes.value.data.results || [] : []

      const saudiCount = employees.filter(e => e.nationality === 'saudi').length
      const saudiPct = employees.length > 0 ? Math.round(saudiCount / employees.length * 100) : 0

      setStats({
        employees: employees.length,
        saudiPct,
        nitaqat: saudiPct >= 80 ? 'Platinum' : saudiPct >= 60 ? 'High Green' : saudiPct >= 40 ? 'Medium Green' : 'Yellow',
        accounts: accounts.length,
        invoices: invoices.length,
        pendingInvoices: invoices.filter(i => i.zatca_status === 'pending').length,
        sessions: sessions.length,
        departments: departments.length,
      })

      setRecentEmployees(employees.slice(0, 5))
      setRecentInvoices(invoices.slice(0, 5))
    } catch (err) {
      console.error('Dashboard fetch error:', err)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchDashboard() }, [])

  const fmt = (n) => new Intl.NumberFormat(lang === 'ar' ? 'ar-SA' : 'en-SA').format(n)

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">
            {lang === 'ar' ? 'لوحة المعلومات' : 'Dashboard'}
          </h1>
          <p className="text-sm text-slate-500">
            {lang === 'ar' ? 'نظرة عامة على أعمالك' : 'Overview of your business'}
          </p>
        </div>
        <button onClick={fetchDashboard} className="btn btn-secondary flex items-center gap-2">
          <RefreshCw size={16} className={loading ? 'animate-spin' : ''} />
          {lang === 'ar' ? 'تحديث' : 'Refresh'}
        </button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard icon={Users} label={lang === 'ar' ? 'الموظفون' : 'Employees'}
          value={fmt(stats.employees)} sub={`${stats.saudiPct}% ${lang === 'ar' ? 'سعودة' : 'Saudization'}`}
          color="blue" loading={loading} />
        <KPICard icon={FileCheck} label={lang === 'ar' ? 'الفواتير' : 'Invoices'}
          value={fmt(stats.invoices)} sub={`${stats.pendingInvoices} ${lang === 'ar' ? 'بانتظار ZATCA' : 'pending ZATCA'}`}
          color="green" loading={loading} />
        <KPICard icon={Calculator} label={lang === 'ar' ? 'الحسابات' : 'Chart of Accounts'}
          value={fmt(stats.accounts)} sub={lang === 'ar' ? 'حساب SOCPA' : 'SOCPA accounts'}
          color="orange" loading={loading} />
        <KPICard icon={ShoppingBag} label={lang === 'ar' ? 'نقاط البيع' : 'POS Sessions'}
          value={fmt(stats.sessions)} sub={`${stats.departments} ${lang === 'ar' ? 'أقسام' : 'departments'}`}
          color="purple" loading={loading} />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="card">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            {lang === 'ar' ? 'آخر الموظفين' : 'Recent Employees'}
          </h3>
          {recentEmployees.length === 0 ? (
            <p className="text-sm text-slate-400">{lang === 'ar' ? 'لا يوجد موظفون بعد' : 'No employees yet'}</p>
          ) : (
            <div className="space-y-3">
              {recentEmployees.map(emp => (
                <div key={emp.id} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                  <div>
                    <div className="font-medium text-slate-900">{lang === 'ar' ? emp.name_ar : emp.name_en}</div>
                    <div className="text-xs text-slate-500">{emp.employee_number}</div>
                  </div>
                  <div className="text-end">
                    <div className="text-sm font-semibold num">{fmt(parseFloat(emp.basic_salary))} SAR</div>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${emp.nationality === 'saudi' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                      {emp.nationality === 'saudi' ? (lang === 'ar' ? 'سعودي' : 'Saudi') : (lang === 'ar' ? 'وافد' : 'Expat')}
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        <div className="card">
          <h3 className="text-lg font-semibold text-slate-900 mb-4">
            {lang === 'ar' ? 'آخر الفواتير' : 'Recent Invoices'}
          </h3>
          {recentInvoices.length === 0 ? (
            <p className="text-sm text-slate-400">{lang === 'ar' ? 'لا توجد فواتير بعد' : 'No invoices yet'}</p>
          ) : (
            <div className="space-y-3">
              {recentInvoices.map(inv => (
                <div key={inv.id} className="flex items-center justify-between py-2 border-b border-slate-100 last:border-0">
                  <div>
                    <div className="font-medium text-slate-900">{inv.invoice_number}</div>
                    <div className="text-xs text-slate-500">{inv.issue_date}</div>
                  </div>
                  <div className="text-end">
                    <div className="text-sm font-semibold num">{fmt(parseFloat(inv.total_amount))} SAR</div>
                    <span className={`text-xs px-2 py-0.5 rounded-full ${
                      inv.zatca_status === 'cleared' ? 'bg-green-100 text-green-700' :
                      inv.zatca_status === 'reported' ? 'bg-blue-100 text-blue-700' :
                      'bg-yellow-100 text-yellow-700'
                    }`}>{inv.zatca_status}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {!loading && stats.employees > 0 && (
        <div className="card">
          <h3 className="text-lg font-semibold text-slate-900 mb-3">
            {lang === 'ar' ? 'مؤشر السعودة (نطاقات)' : 'Saudization (Nitaqat)'}
          </h3>
          <div className="flex items-center gap-4">
            <div className="flex-1 bg-slate-100 rounded-full h-4 overflow-hidden">
              <div className={`h-full rounded-full transition-all ${
                stats.saudiPct >= 80 ? 'bg-emerald-500' :
                stats.saudiPct >= 60 ? 'bg-green-500' :
                stats.saudiPct >= 40 ? 'bg-yellow-500' : 'bg-red-500'
              }`} style={{ width: `${stats.saudiPct}%` }} />
            </div>
            <span className="text-lg font-bold num">{stats.saudiPct}%</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
              stats.saudiPct >= 80 ? 'bg-emerald-100 text-emerald-800' :
              stats.saudiPct >= 60 ? 'bg-green-100 text-green-800' :
              stats.saudiPct >= 40 ? 'bg-yellow-100 text-yellow-800' : 'bg-red-100 text-red-800'
            }`}>{stats.nitaqat}</span>
          </div>
        </div>
      )}
    </div>
  )
}
