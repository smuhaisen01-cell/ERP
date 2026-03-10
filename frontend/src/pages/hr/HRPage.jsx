import { useState } from 'react'
import { Plus, Search, Users, TrendingUp, DollarSign, BarChart2, Eye, ChevronRight } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts'

const EMPLOYEES = [
  { id: 1, nameAr: 'محمد أحمد العتيبي',   nameEn: 'Mohammed Al-Otaibi',  id_no: '1098765432', dept: 'الإدارة',    deptEn: 'Management',  nat: 'saudi', title: 'مدير عام',         titleEn: 'General Manager',  salary: 18000, status: 'active', hire: '2019-03-01' },
  { id: 2, nameAr: 'سارة محمد القحطاني',  nameEn: 'Sara Al-Qahtani',     id_no: '1123456789', dept: 'المالية',    deptEn: 'Finance',     nat: 'saudi', title: 'محاسبة رئيسية',   titleEn: 'Chief Accountant', salary: 12000, status: 'active', hire: '2020-06-15' },
  { id: 3, nameAr: 'رامي خالد المصري',    nameEn: 'Rami Al-Masri',       id_no: 'A5432109',   dept: 'تقنية المعلومات', deptEn: 'IT',     nat: 'expat', title: 'مطور برمجيات',    titleEn: 'Software Dev',     salary: 9500,  status: 'active', hire: '2021-01-20' },
  { id: 4, nameAr: 'نورة عبدالله السعدي', nameEn: 'Noura Al-Saadi',      id_no: '1087654321', dept: 'المبيعات',   deptEn: 'Sales',       nat: 'saudi', title: 'مديرة مبيعات',    titleEn: 'Sales Manager',    salary: 11000, status: 'active', hire: '2020-09-01' },
  { id: 5, nameAr: 'أحمد خير الدين',      nameEn: 'Ahmed Khairuddin',    id_no: 'B9876543',   dept: 'العمليات',   deptEn: 'Operations',  nat: 'expat', title: 'مشرف عمليات',     titleEn: 'Ops Supervisor',   salary: 7200,  status: 'active', hire: '2021-11-10' },
  { id: 6, nameAr: 'فاطمة علي الشمري',   nameEn: 'Fatima Al-Shammari',  id_no: '1076543210', dept: 'الموارد البشرية', deptEn: 'HR',     nat: 'saudi', title: 'أخصائية HR',       titleEn: 'HR Specialist',    salary: 9000,  status: 'active', hire: '2022-02-14' },
  { id: 7, nameAr: 'كريم يوسف إبراهيم',  nameEn: 'Karim Ibrahim',       id_no: 'C1234567',   dept: 'المبيعات',   deptEn: 'Sales',       nat: 'expat', title: 'مندوب مبيعات',    titleEn: 'Sales Rep',        salary: 6500,  status: 'active', hire: '2022-05-01' },
  { id: 8, nameAr: 'عبدالرحمن الحربي',   nameEn: 'Abdulrahman Al-Harbi',id_no: '1054321098', dept: 'الإدارة',    deptEn: 'Management',  nat: 'saudi', title: 'مساعد إداري',     titleEn: 'Admin Assistant',  salary: 7500,  status: 'on_leave', hire: '2021-08-20' },
]

const saudizationData = [
  { dept: 'الإدارة / Mgmt',  saudi: 2, expat: 0 },
  { dept: 'المالية / Finance', saudi: 1, expat: 1 },
  { dept: 'IT',              saudi: 0, expat: 2 },
  { dept: 'المبيعات / Sales', saudi: 1, expat: 1 },
  { dept: 'العمليات / Ops',  saudi: 1, expat: 1 },
  { dept: 'الموارد / HR',    saudi: 1, expat: 0 },
]

const TAB = ['employees', 'payroll', 'saudization']

export default function HRPage() {
  const { t, lang } = useLang()
  const [tab, setTab] = useState('employees')
  const [search, setSearch] = useState('')
  const [natFilter, setNatFilter] = useState('all')

  const filtered = EMPLOYEES.filter(e => {
    const name = lang === 'ar' ? e.nameAr : e.nameEn
    const matchSearch = name.toLowerCase().includes(search.toLowerCase()) || e.id_no.includes(search)
    const matchNat = natFilter === 'all' || e.nat === natFilter
    return matchSearch && matchNat
  })

  const saudiCount = EMPLOYEES.filter(e => e.nat === 'saudi').length
  const saudizationPct = Math.round((saudiCount / EMPLOYEES.length) * 100)
  const fmt = n => new Intl.NumberFormat('en-SA').format(n)

  return (
    <div className="space-y-5">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('hr')}</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {lang === 'ar' ? 'إدارة الموارد البشرية والرواتب والسعودة' : 'HR, Payroll & Saudization Management'}
          </p>
        </div>
        <button className="btn btn-primary">
          <Plus size={16} /> {t('newEmployee')}
        </button>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        {[
          { label: lang === 'ar' ? 'إجمالي الموظفين' : 'Total Employees', value: EMPLOYEES.length, icon: Users, color: 'text-brand-600 bg-brand-50' },
          { label: lang === 'ar' ? 'نسبة السعودة' : 'Saudization %', value: `${saudizationPct}%`, icon: TrendingUp, color: saudizationPct >= 75 ? 'text-green-600 bg-green-50' : 'text-amber-600 bg-amber-50' },
          { label: lang === 'ar' ? 'إجمالي الرواتب' : 'Total Payroll', value: `${fmt(EMPLOYEES.reduce((s,e)=>s+e.salary,0))} ${t('sar')}`, icon: DollarSign, color: 'text-purple-600 bg-purple-50' },
          { label: lang === 'ar' ? 'في إجازة' : 'On Leave', value: EMPLOYEES.filter(e=>e.status==='on_leave').length, icon: BarChart2, color: 'text-orange-600 bg-orange-50' },
        ].map(({ label, value, icon: Icon, color }) => (
          <div key={label} className="card p-4 flex items-center gap-3">
            <div className={`w-11 h-11 rounded-xl ${color} flex items-center justify-center flex-shrink-0`}>
              <Icon size={20} />
            </div>
            <div>
              <div className="text-xl font-bold text-slate-900 num">{value}</div>
              <div className="text-xs text-slate-500">{label}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Tabs */}
      <div className="flex gap-1 bg-slate-100 p-1 rounded-xl w-fit">
        {TAB.map(tb => (
          <button key={tb} onClick={() => setTab(tb)}
            className={`px-5 py-2 rounded-lg text-sm font-medium transition-all ${
              tab === tb ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'
            }`}>
            {lang === 'ar'
              ? { employees: 'الموظفون', payroll: 'الرواتب', saudization: 'السعودة' }[tb]
              : { employees: 'Employees', payroll: 'Payroll', saudization: 'Saudization' }[tb]
            }
          </button>
        ))}
      </div>

      {/* ── Employees tab ─────────────────────────────── */}
      {tab === 'employees' && (
        <div className="space-y-4">
          <div className="flex gap-3">
            <div className="relative flex-1">
              <Search size={15} className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input className="input ps-9 py-2 text-sm"
                placeholder={lang === 'ar' ? 'بحث بالاسم أو رقم الهوية...' : 'Search by name or ID...'}
                value={search} onChange={e => setSearch(e.target.value)} />
            </div>
            <select className="input w-auto py-2 text-sm"
              value={natFilter} onChange={e => setNatFilter(e.target.value)}>
              <option value="all">{t('all')}</option>
              <option value="saudi">{t('saudi')}</option>
              <option value="expat">{t('expat')}</option>
            </select>
          </div>

          <div className="card">
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{lang === 'ar' ? 'الموظف' : 'Employee'}</th>
                    <th>{t('department')}</th>
                    <th>{lang === 'ar' ? 'المسمى الوظيفي' : 'Job Title'}</th>
                    <th>{t('nationality')}</th>
                    <th>{t('salary')}</th>
                    <th>{t('status')}</th>
                    <th>{t('hireDate')}</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {filtered.map(emp => (
                    <tr key={emp.id}>
                      <td>
                        <div className="flex items-center gap-2.5">
                          <div className="w-8 h-8 rounded-full bg-brand-100 text-brand-700 flex items-center justify-center font-semibold text-sm flex-shrink-0">
                            {(lang === 'ar' ? emp.nameAr : emp.nameEn)[0]}
                          </div>
                          <div>
                            <div className="font-medium text-sm">{lang === 'ar' ? emp.nameAr : emp.nameEn}</div>
                            <div className="text-xs text-slate-400 num">{emp.id_no}</div>
                          </div>
                        </div>
                      </td>
                      <td className="text-sm">{lang === 'ar' ? emp.dept : emp.deptEn}</td>
                      <td className="text-sm text-slate-600">{lang === 'ar' ? emp.title : emp.titleEn}</td>
                      <td>
                        <span className={`badge ${emp.nat === 'saudi' ? 'badge-green' : 'badge-blue'}`}>
                          {lang === 'ar'
                            ? (emp.nat === 'saudi' ? '🇸🇦 سعودي' : '👤 وافد')
                            : (emp.nat === 'saudi' ? '🇸🇦 Saudi' : '👤 Expat')}
                        </span>
                      </td>
                      <td className="font-semibold num">{fmt(emp.salary)}</td>
                      <td>
                        <span className={`badge ${emp.status === 'active' ? 'badge-green' : 'badge-yellow'}`}>
                          {emp.status === 'active'
                            ? (lang === 'ar' ? 'نشط' : 'Active')
                            : (lang === 'ar' ? 'إجازة' : 'On Leave')}
                        </span>
                      </td>
                      <td className="text-xs text-slate-400 num">{emp.hire}</td>
                      <td>
                        <button className="text-slate-400 hover:text-brand-600 p-1">
                          <Eye size={15} />
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── Payroll tab ───────────────────────────────── */}
      {tab === 'payroll' && (
        <div className="space-y-4">
          <div className="card p-5">
            <div className="flex items-center justify-between mb-5">
              <div>
                <h3 className="font-semibold text-slate-900">
                  {lang === 'ar' ? 'مسير رواتب مارس 2024' : 'March 2024 Payroll Run'}
                </h3>
                <p className="text-xs text-slate-400 mt-0.5">
                  {lang === 'ar' ? 'الحالة: مسودة' : 'Status: Draft'}
                </p>
              </div>
              <button className="btn btn-primary">
                {lang === 'ar' ? 'معالجة الرواتب' : 'Process Payroll'}
              </button>
            </div>
            <div className="grid grid-cols-3 gap-4 mb-5">
              {[
                { label: lang === 'ar' ? 'إجمالي الرواتب' : 'Gross Payroll', value: fmt(EMPLOYEES.reduce((s,e)=>s+e.salary,0)) },
                { label: lang === 'ar' ? 'اشتراكات GOSI' : 'GOSI Contributions', value: fmt(Math.round(EMPLOYEES.reduce((s,e)=>s+e.salary,0) * 0.1175)) },
                { label: lang === 'ar' ? 'صافي الرواتب' : 'Net Payroll', value: fmt(Math.round(EMPLOYEES.reduce((s,e)=>s+e.salary,0) * 0.9)) },
              ].map(({ label, value }) => (
                <div key={label} className="p-4 bg-slate-50 rounded-xl">
                  <div className="text-xs text-slate-500 mb-1">{label}</div>
                  <div className="font-bold text-slate-900 text-lg num">{value} <span className="text-sm font-normal text-slate-400">{t('sar')}</span></div>
                </div>
              ))}
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>{lang === 'ar' ? 'الموظف' : 'Employee'}</th>
                    <th>{lang === 'ar' ? 'الراتب الأساسي' : 'Basic'}</th>
                    <th>{lang === 'ar' ? 'بدل السكن' : 'Housing'}</th>
                    <th>{lang === 'ar' ? 'بدل النقل' : 'Transport'}</th>
                    <th>{lang === 'ar' ? 'اشتراك GOSI' : 'GOSI'}</th>
                    <th>{lang === 'ar' ? 'الصافي' : 'Net'}</th>
                  </tr>
                </thead>
                <tbody>
                  {EMPLOYEES.slice(0,5).map(emp => {
                    const housing = Math.round(emp.salary * 0.25)
                    const transport = 800
                    const gosi = Math.round(emp.salary * 0.1)
                    const net = emp.salary + housing + transport - gosi
                    return (
                      <tr key={emp.id}>
                        <td className="font-medium">{lang === 'ar' ? emp.nameAr : emp.nameEn}</td>
                        <td className="num">{fmt(emp.salary)}</td>
                        <td className="num">{fmt(housing)}</td>
                        <td className="num">{fmt(transport)}</td>
                        <td className="num text-red-500">({fmt(gosi)})</td>
                        <td className="font-bold num text-green-700">{fmt(net)}</td>
                      </tr>
                    )
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* ── Saudization tab ───────────────────────────── */}
      {tab === 'saudization' && (
        <div className="grid lg:grid-cols-2 gap-4">
          <div className="card p-5">
            <h3 className="font-semibold text-slate-900 mb-1">
              {lang === 'ar' ? 'نسبة السعودة الإجمالية' : 'Overall Saudization'}
            </h3>
            <p className="text-xs text-slate-400 mb-4">
              {lang === 'ar' ? 'المتطلب الأدنى: 75% (نطاق أخضر متوسط)' : 'Minimum required: 75% (Medium Green)'}
            </p>
            <div className="flex items-end gap-3 mb-3">
              <span className={`text-5xl font-black ${saudizationPct >= 75 ? 'text-green-600' : 'text-amber-600'}`}>
                {saudizationPct}%
              </span>
              <span className={`badge mb-2 ${saudizationPct >= 75 ? 'badge-green' : 'badge-yellow'}`}>
                {saudizationPct >= 75
                  ? (lang === 'ar' ? 'نطاق أخضر ✓' : 'Green Band ✓')
                  : (lang === 'ar' ? 'نطاق أصفر ⚠' : 'Yellow Band ⚠')}
              </span>
            </div>
            <div className="h-4 bg-slate-100 rounded-full overflow-hidden">
              <div
                className={`h-full rounded-full transition-all ${saudizationPct >= 75 ? 'bg-green-500' : 'bg-amber-400'}`}
                style={{ width: `${saudizationPct}%` }}
              />
            </div>
            <div className="flex justify-between text-xs text-slate-400 mt-1.5">
              <span>0%</span><span>75% {lang === 'ar' ? 'المطلوب' : 'required'}</span><span>100%</span>
            </div>
          </div>

          <div className="card p-5">
            <h3 className="font-semibold text-slate-900 mb-4">
              {lang === 'ar' ? 'السعودة حسب القسم' : 'Saudization by Department'}
            </h3>
            <ResponsiveContainer width="100%" height={200}>
              <BarChart data={saudizationData} barSize={16}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                <XAxis dataKey="dept" tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <YAxis tick={{ fontSize: 10, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 12 }} />
                <Bar dataKey="saudi" name={lang === 'ar' ? 'سعودي' : 'Saudi'} fill="#16a34a" radius={[4,4,0,0]} />
                <Bar dataKey="expat" name={lang === 'ar' ? 'وافد' : 'Expat'} fill="#94a3b8" radius={[4,4,0,0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>
      )}
    </div>
  )
}
