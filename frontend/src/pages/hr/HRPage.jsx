import { useState, useEffect } from 'react'
import { Plus, Search, Users, DollarSign, Loader2, RefreshCw } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import { hrAPI } from '../../services/api'
import toast from 'react-hot-toast'

const TAB = ['employees', 'payroll', 'saudization']

function AddEmployeeModal({ onClose, onSave, departments, lang }) {
  const [form, setForm] = useState({
    name_ar: '', name_en: '', nationality: 'saudi', job_title_ar: '',
    department: departments[0]?.id || '', hire_date: new Date().toISOString().split('T')[0],
    basic_salary: '', housing_allowance: '0', transport_allowance: '0',
  })
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 space-y-4" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold">{lang === 'ar' ? 'إضافة موظف' : 'Add Employee'}</h2>
        <div className="grid grid-cols-2 gap-3">
          <input className="input" placeholder={lang === 'ar' ? 'الاسم بالعربي' : 'Name (Arabic)'} value={form.name_ar} onChange={e => set('name_ar', e.target.value)} />
          <input className="input" placeholder="Name (English)" value={form.name_en} onChange={e => set('name_en', e.target.value)} dir="ltr" />
          <select className="input" value={form.nationality} onChange={e => set('nationality', e.target.value)}>
            <option value="saudi">{lang === 'ar' ? 'سعودي' : 'Saudi'}</option>
            <option value="expat">{lang === 'ar' ? 'وافد' : 'Expat'}</option>
          </select>
          <select className="input" value={form.department} onChange={e => set('department', e.target.value)}>
            {departments.map(d => <option key={d.id} value={d.id}>{lang === 'ar' ? d.name_ar : d.name_en}</option>)}
          </select>
          <input className="input" placeholder={lang === 'ar' ? 'المسمى الوظيفي' : 'Job Title'} value={form.job_title_ar} onChange={e => set('job_title_ar', e.target.value)} />
          <input className="input" type="date" value={form.hire_date} onChange={e => set('hire_date', e.target.value)} dir="ltr" />
          <input className="input" type="number" placeholder={lang === 'ar' ? 'الراتب الأساسي' : 'Basic Salary'} value={form.basic_salary} onChange={e => set('basic_salary', e.target.value)} dir="ltr" />
          <input className="input" type="number" placeholder={lang === 'ar' ? 'بدل السكن' : 'Housing'} value={form.housing_allowance} onChange={e => set('housing_allowance', e.target.value)} dir="ltr" />
        </div>
        <div className="flex gap-3 justify-end">
          <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
          <button className="btn btn-primary" onClick={() => onSave(form)}>{lang === 'ar' ? 'حفظ' : 'Save'}</button>
        </div>
      </div>
    </div>
  )
}

export default function HRPage() {
  const { t, lang } = useLang()
  const { api } = useAuth()
  const [tab, setTab] = useState('employees')
  const [loading, setLoading] = useState(true)
  const [employees, setEmployees] = useState([])
  const [departments, setDepartments] = useState([])
  const [payrolls, setPayrolls] = useState([])
  const [saudization, setSaudization] = useState([])
  const [showAdd, setShowAdd] = useState(false)
  const [search, setSearch] = useState('')

  const fetchData = async () => {
    setLoading(true)
    try {
      const [empRes, deptRes, payRes, saudRes] = await Promise.allSettled([
        hrAPI.getEmployees(api), hrAPI.getDepartments(api),
        hrAPI.getPayrollRuns(api), hrAPI.getSaudization(api),
      ])
      if (empRes.status === 'fulfilled') setEmployees(empRes.value.data.results || [])
      if (deptRes.status === 'fulfilled') setDepartments(deptRes.value.data.results || [])
      if (payRes.status === 'fulfilled') setPayrolls(payRes.value.data.results || [])
      if (saudRes.status === 'fulfilled') setSaudization(saudRes.value.data.results || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const handleAddEmployee = async (form) => {
    try {
      await hrAPI.createEmployee(api, form)
      toast.success(lang === 'ar' ? 'تم إضافة الموظف' : 'Employee added')
      setShowAdd(false)
      fetchData()
    } catch (err) {
      toast.error(err.response?.data?.detail || 'Error adding employee')
    }
  }

  const handleGenerateSaudization = async () => {
    try {
      await hrAPI.generateSaudization(api)
      toast.success(lang === 'ar' ? 'تم إنشاء التقرير' : 'Report generated')
      fetchData()
    } catch (err) { toast.error('Error generating report') }
  }

  const fmt = (n) => new Intl.NumberFormat(lang === 'ar' ? 'ar-SA' : 'en-SA').format(n)
  const filtered = employees.filter(e =>
    e.name_ar?.includes(search) || e.name_en?.toLowerCase().includes(search.toLowerCase()) || e.employee_number?.includes(search)
  )

  const tabLabels = {
    employees: lang === 'ar' ? 'الموظفون' : 'Employees',
    payroll: lang === 'ar' ? 'الرواتب' : 'Payroll',
    saudization: lang === 'ar' ? 'السعودة' : 'Saudization',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'الموارد البشرية' : 'Human Resources'}</h1>
        <div className="flex gap-2">
          <button onClick={fetchData} className="btn btn-secondary"><RefreshCw size={16} /></button>
          {tab === 'employees' && <button onClick={() => setShowAdd(true)} className="btn btn-primary flex items-center gap-2"><Plus size={16} />{lang === 'ar' ? 'موظف جديد' : 'New Employee'}</button>}
          {tab === 'saudization' && <button onClick={handleGenerateSaudization} className="btn btn-primary flex items-center gap-2"><Plus size={16} />{lang === 'ar' ? 'تقرير جديد' : 'Generate Report'}</button>}
        </div>
      </div>

      <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
        {TAB.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${tab === t ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
            {tabLabels[t]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={32} className="animate-spin text-brand-500" /></div>
      ) : tab === 'employees' ? (
        <div className="card">
          <div className="mb-4">
            <div className="relative">
              <Search size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400" />
              <input className="input ps-10" placeholder={lang === 'ar' ? 'بحث عن موظف...' : 'Search employees...'} value={search} onChange={e => setSearch(e.target.value)} />
            </div>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-200">
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الرقم' : 'ID'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الاسم' : 'Name'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الجنسية' : 'Nationality'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'المسمى' : 'Title'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الراتب' : 'Salary'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الحالة' : 'Status'}</th>
              </tr></thead>
              <tbody>
                {filtered.map(emp => (
                  <tr key={emp.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-2 num text-xs text-slate-500">{emp.employee_number}</td>
                    <td className="py-3 px-2 font-medium">{lang === 'ar' ? emp.name_ar : emp.name_en}</td>
                    <td className="py-3 px-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${emp.nationality === 'saudi' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>
                        {emp.nationality === 'saudi' ? (lang === 'ar' ? 'سعودي' : 'Saudi') : (lang === 'ar' ? 'وافد' : 'Expat')}
                      </span>
                    </td>
                    <td className="py-3 px-2 text-slate-600">{emp.job_title_ar}</td>
                    <td className="py-3 px-2 num font-semibold">{fmt(parseFloat(emp.basic_salary))} SAR</td>
                    <td className="py-3 px-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${emp.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-slate-100 text-slate-600'}`}>
                        {emp.status}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {filtered.length === 0 && <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا يوجد موظفون' : 'No employees found'}</p>}
          </div>
        </div>
      ) : tab === 'saudization' ? (
        <div className="card">
          {saudization.length === 0 ? (
            <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا توجد تقارير' : 'No reports yet. Click Generate Report.'}</p>
          ) : (
            <div className="space-y-4">
              {saudization.map(r => (
                <div key={r.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                  <div>
                    <div className="font-medium">{r.report_date}</div>
                    <div className="text-sm text-slate-500">{r.total_employees} {lang === 'ar' ? 'موظف' : 'employees'} · {r.saudi_employees} {lang === 'ar' ? 'سعودي' : 'Saudi'}</div>
                  </div>
                  <div className="flex items-center gap-3">
                    <span className="text-lg font-bold num">{r.saudization_percentage}%</span>
                    <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                      r.nitaqat_band === 'platinum' ? 'bg-emerald-100 text-emerald-800' :
                      r.nitaqat_band?.includes('green') ? 'bg-green-100 text-green-800' :
                      'bg-yellow-100 text-yellow-800'
                    }`}>{r.nitaqat_band}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'قريباً — إدارة الرواتب' : 'Coming soon — Payroll management'}</p>
        </div>
      )}

      {showAdd && <AddEmployeeModal onClose={() => setShowAdd(false)} onSave={handleAddEmployee} departments={departments} lang={lang} />}
    </div>
  )
}
