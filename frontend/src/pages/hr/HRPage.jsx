import { useState, useEffect } from 'react'
import { Plus, Search, Users, Loader2, RefreshCw, Check, X, Download, Calendar, Clock, FileText, UserMinus } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import { hrAPI } from '../../services/api'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'employees', labelAr: 'الموظفون', labelEn: 'Employees' },
  { id: 'leave', labelAr: 'الإجازات', labelEn: 'Leave' },
  { id: 'attendance', labelAr: 'الحضور', labelEn: 'Attendance' },
  { id: 'payroll', labelAr: 'الرواتب', labelEn: 'Payroll' },
  { id: 'termination', labelAr: 'إنهاء الخدمة', labelEn: 'Termination' },
  { id: 'documents', labelAr: 'المستندات', labelEn: 'Documents' },
  { id: 'saudization', labelAr: 'السعودة', labelEn: 'Saudization' },
]

function Modal({ onClose, title, children }) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold">{title}</h2>
        {children}
      </div>
    </div>
  )
}

export default function HRPage() {
  const { lang } = useLang()
  const { api, user } = useAuth()
  const [tab, setTab] = useState('employees')
  const [loading, setLoading] = useState(true)
  const [data, setData] = useState({
    employees: [], departments: [], leaveTypes: [], leaveRequests: [],
    attendance: [], payrolls: [], saudization: [], terminations: [], documents: [],
  })
  const [modal, setModal] = useState(null)
  const [search, setSearch] = useState('')

  const fmt = (n) => new Intl.NumberFormat(lang === 'ar' ? 'ar-SA' : 'en-SA', { minimumFractionDigits: 2 }).format(parseFloat(n || 0))

  const fetchAll = async () => {
    setLoading(true)
    try {
      const [emp, dept, lt, lr, att, pay, saud, term, docs] = await Promise.allSettled([
        hrAPI.getEmployees(api), hrAPI.getDepartments(api),
        hrAPI.getLeaveTypes(api), hrAPI.getLeaveRequests(api),
        hrAPI.getAttendance(api), hrAPI.getPayrollRuns(api),
        hrAPI.getSaudization(api), hrAPI.getTerminations(api),
        hrAPI.getDocuments(api),
      ])
      setData({
        employees: emp.status === 'fulfilled' ? emp.value.data.results || [] : [],
        departments: dept.status === 'fulfilled' ? dept.value.data.results || [] : [],
        leaveTypes: lt.status === 'fulfilled' ? lt.value.data.results || [] : [],
        leaveRequests: lr.status === 'fulfilled' ? lr.value.data.results || [] : [],
        attendance: att.status === 'fulfilled' ? att.value.data.results || [] : [],
        payrolls: pay.status === 'fulfilled' ? pay.value.data.results || [] : [],
        saudization: saud.status === 'fulfilled' ? saud.value.data.results || [] : [],
        terminations: term.status === 'fulfilled' ? term.value.data.results || [] : [],
        documents: docs.status === 'fulfilled' ? docs.value.data.results || [] : [],
      })
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchAll() }, [])

  // ─── Action Handlers ──────────────────────────────────
  const addEmployee = async (form) => {
    try {
      await hrAPI.createEmployee(api, form)
      toast.success(lang === 'ar' ? 'تم إضافة الموظف' : 'Employee added')
      setModal(null); fetchAll()
    } catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const createPayroll = async () => {
    const now = new Date()
    try {
      const res = await hrAPI.createPayrollRun(api, { period_month: now.getMonth() + 1, period_year: now.getFullYear() })
      toast.success(lang === 'ar' ? 'تم إنشاء مسير الرواتب' : 'Payroll created')
      fetchAll()
    } catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const calcPayroll = async (id) => {
    try { await hrAPI.calculatePayroll(api, id); toast.success('Calculated'); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }
  const approvePayroll = async (id) => {
    try { await hrAPI.approvePayroll(api, id); toast.success('Approved'); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }
  const payPayroll = async (id) => {
    try { await hrAPI.payPayroll(api, id); toast.success('Paid + GL posted'); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const approveLeave = async (id) => {
    try { await hrAPI.approveLeave(api, id); toast.success('Approved'); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }
  const rejectLeave = async (id) => {
    try { await hrAPI.rejectLeave(api, id, {}); toast.success('Rejected'); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const bulkCheckin = async () => {
    try { const res = await hrAPI.bulkAttendance(api); toast.success(`Checked in ${res.data.checked_in} employees`); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const seedLeaveTypes = async () => {
    try { await hrAPI.seedLeaveTypes(api); toast.success('Leave types seeded'); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const calcTermination = async (form) => {
    try {
      const res = await hrAPI.calculateTermination(api, form)
      setModal({ type: 'term_result', data: res.data, form })
    } catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const processTermination = async (form) => {
    try {
      await hrAPI.processTermination(api, form)
      toast.success(lang === 'ar' ? 'تم إنهاء الخدمة' : 'Termination processed')
      setModal(null); fetchAll()
    } catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const genSaudization = async () => {
    try { await hrAPI.generateSaudization(api); toast.success('Report generated'); fetchAll() }
    catch (err) { toast.error('Error') }
  }

  const submitLeave = async (form) => {
    try { await hrAPI.createLeaveRequest(api, form); toast.success('Leave request submitted'); setModal(null); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const filtered = data.employees.filter(e =>
    e.name_ar?.includes(search) || e.name_en?.toLowerCase().includes(search.toLowerCase()) || e.employee_number?.includes(search)
  )

  // ─── Render Tabs ──────────────────────────────────────
  const renderTab = () => {
    if (loading) return <div className="flex justify-center py-12"><Loader2 size={32} className="animate-spin text-brand-500" /></div>

    switch (tab) {
      case 'employees': return (
        <div className="card">
          <div className="mb-4 relative">
            <Search size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input className="input ps-10" placeholder={lang === 'ar' ? 'بحث...' : 'Search...'} value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-200">
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الرقم' : 'ID'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الاسم' : 'Name'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الجنسية' : 'Nat.'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'القسم' : 'Dept'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الراتب' : 'Salary'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الإجازات' : 'Leave'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الحالة' : 'Status'}</th>
              </tr></thead>
              <tbody>{filtered.map(e => (
                <tr key={e.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-2 num text-xs">{e.employee_number}</td>
                  <td className="py-3 px-2 font-medium">{lang === 'ar' ? e.name_ar : e.name_en}</td>
                  <td className="py-3 px-2"><span className={`text-xs px-2 py-0.5 rounded-full ${e.nationality === 'saudi' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'}`}>{e.nationality === 'saudi' ? 'SA' : 'EX'}</span></td>
                  <td className="py-3 px-2 text-xs text-slate-500">{e.department_name}</td>
                  <td className="py-3 px-2 num font-semibold">{fmt(e.basic_salary)}</td>
                  <td className="py-3 px-2 num text-xs">{e.annual_leave_balance || '21'} d</td>
                  <td className="py-3 px-2"><span className={`text-xs px-2 py-0.5 rounded-full ${e.status === 'active' ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-600'}`}>{e.status}</span></td>
                </tr>
              ))}</tbody>
            </table>
            {filtered.length === 0 && <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا يوجد موظفون' : 'No employees'}</p>}
          </div>
        </div>
      )

      case 'leave': return (
        <div className="space-y-4">
          {data.leaveTypes.length === 0 && (
            <div className="card text-center py-6">
              <p className="text-slate-400 mb-3">{lang === 'ar' ? 'لم يتم إعداد أنواع الإجازات بعد' : 'Leave types not set up yet'}</p>
              <button onClick={seedLeaveTypes} className="btn btn-primary">{lang === 'ar' ? 'إعداد أنواع الإجازات' : 'Seed Leave Types'}</button>
            </div>
          )}
          <div className="card">
            <h3 className="font-semibold mb-3">{lang === 'ar' ? 'طلبات الإجازة' : 'Leave Requests'}</h3>
            {data.leaveRequests.length === 0 ? <p className="text-slate-400 text-sm py-4">{lang === 'ar' ? 'لا توجد طلبات' : 'No requests'}</p> : (
              <div className="space-y-2">{data.leaveRequests.map(lr => (
                <div key={lr.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
                  <div>
                    <div className="font-medium">{lr.employee_name}</div>
                    <div className="text-xs text-slate-500">{lr.leave_type_name} · {lr.start_date} → {lr.end_date} · {lr.days} {lang === 'ar' ? 'يوم' : 'days'}</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-0.5 rounded-full ${lr.status === 'approved' ? 'bg-green-100 text-green-700' : lr.status === 'rejected' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'}`}>{lr.status}</span>
                    {lr.status === 'pending' && <>
                      <button onClick={() => approveLeave(lr.id)} className="w-7 h-7 rounded-lg bg-green-100 text-green-600 flex items-center justify-center hover:bg-green-200"><Check size={14} /></button>
                      <button onClick={() => rejectLeave(lr.id)} className="w-7 h-7 rounded-lg bg-red-100 text-red-600 flex items-center justify-center hover:bg-red-200"><X size={14} /></button>
                    </>}
                  </div>
                </div>
              ))}</div>
            )}
          </div>
        </div>
      )

      case 'attendance': return (
        <div className="card">
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold">{lang === 'ar' ? 'سجل الحضور' : 'Attendance Log'}</h3>
            <button onClick={bulkCheckin} className="btn btn-primary text-sm flex items-center gap-2"><Clock size={14} />{lang === 'ar' ? 'تسجيل حضور اليوم' : 'Bulk Check-in Today'}</button>
          </div>
          {data.attendance.length === 0 ? <p className="text-slate-400 text-sm py-4">{lang === 'ar' ? 'لا يوجد سجلات' : 'No records'}</p> : (
            <table className="w-full text-sm">
              <thead><tr className="border-b"><th className="text-start py-2 px-2">{lang === 'ar' ? 'الموظف' : 'Employee'}</th><th className="text-start py-2 px-2">{lang === 'ar' ? 'التاريخ' : 'Date'}</th><th className="text-start py-2 px-2">{lang === 'ar' ? 'الدخول' : 'In'}</th><th className="text-start py-2 px-2">{lang === 'ar' ? 'الخروج' : 'Out'}</th><th className="text-start py-2 px-2">{lang === 'ar' ? 'الحالة' : 'Status'}</th></tr></thead>
              <tbody>{data.attendance.map(a => (
                <tr key={a.id} className="border-b border-slate-100"><td className="py-2 px-2">{a.employee_name}</td><td className="py-2 px-2 num">{a.date}</td><td className="py-2 px-2 num">{a.check_in || '-'}</td><td className="py-2 px-2 num">{a.check_out || '-'}</td><td className="py-2 px-2"><span className={`text-xs px-2 py-0.5 rounded-full ${a.status === 'present' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'}`}>{a.status}</span></td></tr>
              ))}</tbody>
            </table>
          )}
        </div>
      )

      case 'payroll': return (
        <div className="space-y-4">
          <div className="card">
            <div className="flex items-center justify-between mb-4">
              <h3 className="font-semibold">{lang === 'ar' ? 'مسيرات الرواتب' : 'Payroll Runs'}</h3>
              <button onClick={createPayroll} className="btn btn-primary text-sm flex items-center gap-2"><Plus size={14} />{lang === 'ar' ? 'مسير جديد' : 'New Payroll'}</button>
            </div>
            {data.payrolls.length === 0 ? <p className="text-slate-400 text-sm py-4">{lang === 'ar' ? 'لا يوجد مسيرات' : 'No payroll runs'}</p> : (
              <div className="space-y-3">{data.payrolls.map(p => (
                <div key={p.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                  <div>
                    <div className="font-semibold">{p.period_year}/{String(p.period_month).padStart(2, '0')}</div>
                    <div className="text-xs text-slate-500">{p.employee_count} {lang === 'ar' ? 'موظف' : 'employees'} · {lang === 'ar' ? 'إجمالي:' : 'Total:'} {fmt(p.total_gross)} SAR · {lang === 'ar' ? 'صافي:' : 'Net:'} {fmt(p.total_net)} SAR</div>
                  </div>
                  <div className="flex items-center gap-2">
                    <span className={`text-xs px-2 py-1 rounded-full ${p.status === 'paid' ? 'bg-green-100 text-green-700' : p.status === 'approved' ? 'bg-blue-100 text-blue-700' : p.status === 'calculated' ? 'bg-yellow-100 text-yellow-700' : 'bg-slate-100 text-slate-600'}`}>{p.status}</span>
                    {p.status === 'draft' && <button onClick={() => calcPayroll(p.id)} className="btn btn-secondary text-xs py-1">{lang === 'ar' ? 'حساب' : 'Calculate'}</button>}
                    {p.status === 'calculated' && <button onClick={() => approvePayroll(p.id)} className="btn btn-secondary text-xs py-1">{lang === 'ar' ? 'اعتماد' : 'Approve'}</button>}
                    {p.status === 'approved' && <>
                      <button onClick={() => payPayroll(p.id)} className="btn btn-primary text-xs py-1">{lang === 'ar' ? 'صرف' : 'Pay'}</button>
                      <a href={`/api/hr/payroll-runs/${p.id}/wps_export/`} target="_blank" className="btn btn-secondary text-xs py-1 flex items-center gap-1"><Download size={12} />WPS</a>
                    </>}
                    {p.status === 'paid' && <button onClick={async () => {
                      try { const res = await hrAPI.getPayslipData(api, p.id); setModal({ type: 'payslips', data: res.data }) }
                      catch { toast.error('Error') }
                    }} className="btn btn-secondary text-xs py-1 flex items-center gap-1"><FileText size={12} />{lang === 'ar' ? 'كشوف' : 'Payslips'}</button>}
                  </div>
                </div>
              ))}</div>
            )}
          </div>
        </div>
      )

      case 'termination': return (
        <div className="space-y-4">
          <div className="card">
            <h3 className="font-semibold mb-3">{lang === 'ar' ? 'تسويات نهاية الخدمة' : 'Termination Settlements'}</h3>
            {data.terminations.length > 0 && data.terminations.map(t => (
              <div key={t.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl mb-2">
                <div>
                  <div className="font-medium">{t.employee_name}</div>
                  <div className="text-xs text-slate-500">{t.reason} · {t.years_of_service} {lang === 'ar' ? 'سنة' : 'yrs'} · EOSB: {fmt(t.eosb_amount)} SAR</div>
                </div>
                <div className="text-end">
                  <div className="font-bold num">{fmt(t.total_settlement)} SAR</div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${t.is_paid ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>{t.is_paid ? (lang === 'ar' ? 'مدفوع' : 'Paid') : (lang === 'ar' ? 'معلق' : 'Pending')}</span>
                </div>
              </div>
            ))}
            {data.terminations.length === 0 && <p className="text-slate-400 text-sm py-4">{lang === 'ar' ? 'لا توجد تسويات' : 'No settlements'}</p>}
          </div>
        </div>
      )

      case 'documents': return (
        <div className="card">
          <h3 className="font-semibold mb-3">{lang === 'ar' ? 'مستندات الموظفين' : 'Employee Documents'}</h3>
          {data.documents.length === 0 ? <p className="text-slate-400 text-sm py-4">{lang === 'ar' ? 'لا توجد مستندات' : 'No documents'}</p> : (
            <table className="w-full text-sm">
              <thead><tr className="border-b"><th className="text-start py-2 px-2">{lang === 'ar' ? 'الموظف' : 'Employee'}</th><th className="text-start py-2 px-2">{lang === 'ar' ? 'النوع' : 'Type'}</th><th className="text-start py-2 px-2">{lang === 'ar' ? 'العنوان' : 'Title'}</th><th className="text-start py-2 px-2">{lang === 'ar' ? 'انتهاء' : 'Expiry'}</th></tr></thead>
              <tbody>{data.documents.map(d => (
                <tr key={d.id} className="border-b border-slate-100"><td className="py-2 px-2">{d.employee_name}</td><td className="py-2 px-2 text-xs">{d.doc_type}</td><td className="py-2 px-2">{d.title}</td><td className="py-2 px-2 num">{d.expiry_date || '-'}</td></tr>
              ))}</tbody>
            </table>
          )}
        </div>
      )

      case 'saudization': return (
        <div className="card">
          {data.saudization.length === 0 ? <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا توجد تقارير' : 'No reports'}</p> : (
            <div className="space-y-3">{data.saudization.map(r => (
              <div key={r.id} className="flex items-center justify-between p-4 bg-slate-50 rounded-xl">
                <div>
                  <div className="font-medium">{r.report_date}</div>
                  <div className="text-sm text-slate-500">{r.total_employees} {lang === 'ar' ? 'موظف' : 'employees'} · {r.saudi_employees} {lang === 'ar' ? 'سعودي' : 'Saudi'}</div>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-lg font-bold num">{r.saudization_percentage}%</span>
                  <span className={`px-3 py-1 rounded-full text-sm font-medium ${r.nitaqat_band === 'platinum' ? 'bg-emerald-100 text-emerald-800' : r.nitaqat_band?.includes('green') ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'}`}>{r.nitaqat_band?.replace('_', ' ')}</span>
                </div>
              </div>
            ))}</div>
          )}
        </div>
      )
    }
  }

  // ─── Tab Actions ──────────────────────────────────────
  const tabActions = () => {
    switch (tab) {
      case 'employees': return <button onClick={() => setModal({ type: 'add_employee' })} className="btn btn-primary flex items-center gap-2 text-sm"><Plus size={14} />{lang === 'ar' ? 'موظف' : 'Employee'}</button>
      case 'leave': return <button onClick={() => setModal({ type: 'add_leave' })} className="btn btn-primary flex items-center gap-2 text-sm"><Plus size={14} />{lang === 'ar' ? 'طلب إجازة' : 'Leave Request'}</button>
      case 'termination': return <button onClick={() => setModal({ type: 'add_term' })} className="btn btn-primary flex items-center gap-2 text-sm"><UserMinus size={14} />{lang === 'ar' ? 'إنهاء خدمة' : 'Terminate'}</button>
      case 'documents': return <button onClick={() => setModal({ type: 'add_doc' })} className="btn btn-primary flex items-center gap-2 text-sm"><Plus size={14} />{lang === 'ar' ? 'مستند' : 'Document'}</button>
      case 'saudization': return <button onClick={genSaudization} className="btn btn-primary flex items-center gap-2 text-sm"><Plus size={14} />{lang === 'ar' ? 'تقرير' : 'Generate'}</button>
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'الموارد البشرية' : 'Human Resources'}</h1>
        <div className="flex gap-2">
          <button onClick={fetchAll} className="btn btn-secondary"><RefreshCw size={16} /></button>
          {tabActions()}
        </div>
      </div>

      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-3 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${tab === t.id ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
            {lang === 'ar' ? t.labelAr : t.labelEn}
          </button>
        ))}
      </div>

      {renderTab()}

      {/* ─── Modals ──────────────────────────────────────── */}
      {modal?.type === 'add_employee' && (
        <Modal onClose={() => setModal(null)} title={lang === 'ar' ? 'إضافة موظف' : 'Add Employee'}>
          <AddEmployeeForm departments={data.departments} lang={lang} onSave={addEmployee} onClose={() => setModal(null)} />
        </Modal>
      )}
      {modal?.type === 'add_leave' && (
        <Modal onClose={() => setModal(null)} title={lang === 'ar' ? 'طلب إجازة' : 'Leave Request'}>
          <AddLeaveForm employees={data.employees} leaveTypes={data.leaveTypes} lang={lang} onSave={submitLeave} onClose={() => setModal(null)} />
        </Modal>
      )}
      {modal?.type === 'add_term' && (
        <Modal onClose={() => setModal(null)} title={lang === 'ar' ? 'إنهاء خدمة' : 'Terminate Employee'}>
          <TerminationForm employees={data.employees.filter(e => e.status === 'active')} lang={lang} onCalculate={calcTermination} onClose={() => setModal(null)} />
        </Modal>
      )}
      {modal?.type === 'term_result' && (
        <Modal onClose={() => setModal(null)} title={lang === 'ar' ? 'تسوية نهاية الخدمة' : 'EOSB Settlement'}>
          <div className="space-y-3">
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div className="bg-slate-50 rounded-lg p-3"><span className="text-slate-500">{lang === 'ar' ? 'الموظف' : 'Employee'}</span><div className="font-semibold">{modal.data.name}</div></div>
              <div className="bg-slate-50 rounded-lg p-3"><span className="text-slate-500">{lang === 'ar' ? 'سنوات الخدمة' : 'Years'}</span><div className="font-semibold num">{modal.data.years_of_service}</div></div>
              <div className="bg-blue-50 rounded-lg p-3"><span className="text-blue-600">EOSB</span><div className="font-bold num">{fmt(modal.data.eosb_amount)} SAR</div></div>
              <div className="bg-green-50 rounded-lg p-3"><span className="text-green-600">{lang === 'ar' ? 'رصيد الإجازات' : 'Leave Payout'}</span><div className="font-bold num">{fmt(modal.data.leave_balance_payout)} SAR</div></div>
            </div>
            <div className="bg-brand-50 rounded-lg p-4 text-center">
              <span className="text-brand-600 text-sm">{lang === 'ar' ? 'إجمالي التسوية' : 'Total Settlement'}</span>
              <div className="text-2xl font-bold text-brand-700 num">{fmt(modal.data.total_settlement)} SAR</div>
            </div>
            <div className="flex gap-3 justify-end">
              <button className="btn btn-secondary" onClick={() => setModal(null)}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
              <button className="btn btn-primary" onClick={() => processTermination(modal.form)}>{lang === 'ar' ? 'تأكيد الإنهاء' : 'Confirm Termination'}</button>
            </div>
          </div>
        </Modal>
      )}
      {modal?.type === 'add_doc' && (
        <Modal onClose={() => setModal(null)} title={lang === 'ar' ? 'إضافة مستند' : 'Add Document'}>
          <AddDocForm employees={data.employees} lang={lang} onSave={async (form) => {
            try { await hrAPI.uploadDocument(api, form); toast.success('Document added'); setModal(null); fetchAll() }
            catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
          }} onClose={() => setModal(null)} />
        </Modal>
      )}
      {modal?.type === 'payslips' && (
        <Modal onClose={() => setModal(null)} title={`${lang === 'ar' ? 'كشوف الرواتب' : 'Payslips'} — ${modal.data.period}`}>
          <div className="space-y-3 max-h-96 overflow-y-auto">
            {modal.data.payslips?.map((ps, i) => (
              <div key={i} className="bg-slate-50 rounded-xl p-4 text-sm space-y-2">
                <div className="flex justify-between font-semibold"><span>{ps.name_ar}</span><span className="num">{ps.employee_number}</span></div>
                <div className="grid grid-cols-3 gap-2 text-xs">
                  <div><span className="text-slate-500">{lang === 'ar' ? 'أساسي' : 'Basic'}</span><div className="num">{fmt(ps.basic_salary)}</div></div>
                  <div><span className="text-slate-500">{lang === 'ar' ? 'سكن' : 'Housing'}</span><div className="num">{fmt(ps.housing_allowance)}</div></div>
                  <div><span className="text-slate-500">{lang === 'ar' ? 'نقل' : 'Transport'}</span><div className="num">{fmt(ps.transport_allowance)}</div></div>
                  <div><span className="text-slate-500">{lang === 'ar' ? 'إجمالي' : 'Gross'}</span><div className="num font-semibold">{fmt(ps.gross_salary)}</div></div>
                  <div><span className="text-slate-500">GOSI</span><div className="num text-red-600">-{fmt(ps.gosi_employee)}</div></div>
                  <div><span className="text-green-600 font-semibold">{lang === 'ar' ? 'صافي' : 'Net'}</span><div className="num font-bold text-green-700">{fmt(ps.net_salary)}</div></div>
                </div>
              </div>
            ))}
          </div>
        </Modal>
      )}
    </div>
  )
}

// ─── Form Components ────────────────────────────────────

function AddEmployeeForm({ departments, lang, onSave, onClose }) {
  const [f, setF] = useState({ name_ar: '', name_en: '', nationality: 'saudi', job_title_ar: '', department: departments[0]?.id || '', hire_date: new Date().toISOString().split('T')[0], basic_salary: '', housing_allowance: '0', transport_allowance: '0', contract_type: 'permanent', bank_name: '', iban: '' })
  const s = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <input className="input" placeholder={lang === 'ar' ? 'الاسم (عربي)' : 'Name (Arabic)'} value={f.name_ar} onChange={e => s('name_ar', e.target.value)} />
        <input className="input" placeholder="Name (English)" value={f.name_en} onChange={e => s('name_en', e.target.value)} dir="ltr" />
        <select className="input" value={f.nationality} onChange={e => s('nationality', e.target.value)}>
          <option value="saudi">{lang === 'ar' ? 'سعودي' : 'Saudi'}</option><option value="expat">{lang === 'ar' ? 'وافد' : 'Expat'}</option>
        </select>
        <select className="input" value={f.department} onChange={e => s('department', e.target.value)}>
          {departments.map(d => <option key={d.id} value={d.id}>{lang === 'ar' ? d.name_ar : d.name_en}</option>)}
        </select>
        <input className="input" placeholder={lang === 'ar' ? 'المسمى' : 'Job Title'} value={f.job_title_ar} onChange={e => s('job_title_ar', e.target.value)} />
        <input className="input" type="date" value={f.hire_date} onChange={e => s('hire_date', e.target.value)} dir="ltr" />
        <input className="input" type="number" placeholder={lang === 'ar' ? 'الراتب' : 'Basic Salary'} value={f.basic_salary} onChange={e => s('basic_salary', e.target.value)} dir="ltr" />
        <input className="input" type="number" placeholder={lang === 'ar' ? 'بدل سكن' : 'Housing'} value={f.housing_allowance} onChange={e => s('housing_allowance', e.target.value)} dir="ltr" />
        <input className="input" placeholder={lang === 'ar' ? 'البنك' : 'Bank'} value={f.bank_name} onChange={e => s('bank_name', e.target.value)} />
        <input className="input" placeholder="IBAN" value={f.iban} onChange={e => s('iban', e.target.value)} dir="ltr" />
      </div>
      <div className="flex gap-3 justify-end">
        <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
        <button className="btn btn-primary" onClick={() => onSave(f)}>{lang === 'ar' ? 'حفظ' : 'Save'}</button>
      </div>
    </div>
  )
}

function AddLeaveForm({ employees, leaveTypes, lang, onSave, onClose, currentUser }) {
  const myEmployee = employees.find(e => e.name_en?.toLowerCase().includes(currentUser?.username?.toLowerCase()) || e.id === currentUser?.employee_id)
  const isAdmin = currentUser?.is_staff
  const [f, setF] = useState({ employee: myEmployee?.id || employees[0]?.id || '', leave_type: leaveTypes[0]?.id || '', start_date: '', end_date: '', days: '', reason: '' })
  const s = (k, v) => {
    const updated = { ...f, [k]: v }
    if ((k === 'start_date' || k === 'end_date') && updated.start_date && updated.end_date) {
      const start = new Date(updated.start_date)
      const end = new Date(updated.end_date)
      const diff = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1
      if (diff > 0) updated.days = diff.toString()
    }
    setF(updated)
  }
  return (
    <div className="space-y-3">
      {isAdmin ? (
        <select className="input" value={f.employee} onChange={e => s('employee', e.target.value)}>
          {employees.map(e => <option key={e.id} value={e.id}>{e.name_ar} ({e.employee_number})</option>)}
        </select>
      ) : (
        <div className="input bg-slate-50">{myEmployee ? `${myEmployee.name_ar} (${myEmployee.employee_number})` : (lang === 'ar' ? 'لم يتم ربط حسابك بموظف' : 'Your account is not linked to an employee')}</div>
      )}
      <select className="input" value={f.leave_type} onChange={e => s('leave_type', e.target.value)}>
        {leaveTypes.map(t => <option key={t.id} value={t.id}>{lang === 'ar' ? t.name_ar : t.name_en}</option>)}
      </select>
      <div className="grid grid-cols-3 gap-3">
        <div>
          <label className="text-xs text-slate-500 mb-1 block">{lang === 'ar' ? 'من' : 'From'}</label>
          <input className="input" type="date" value={f.start_date} onChange={e => s('start_date', e.target.value)} dir="ltr" />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">{lang === 'ar' ? 'إلى' : 'To'}</label>
          <input className="input" type="date" value={f.end_date} onChange={e => s('end_date', e.target.value)} dir="ltr" />
        </div>
        <div>
          <label className="text-xs text-slate-500 mb-1 block">{lang === 'ar' ? 'الأيام' : 'Days'}</label>
          <input className="input bg-slate-50 font-semibold" type="number" value={f.days} readOnly dir="ltr" />
        </div>
      </div>
      <textarea className="input" rows={2} placeholder={lang === 'ar' ? 'السبب' : 'Reason'} value={f.reason} onChange={e => s('reason', e.target.value)} />
      <div className="flex gap-3 justify-end">
        <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
        <button className="btn btn-primary" onClick={() => onSave(f)}>{lang === 'ar' ? 'إرسال' : 'Submit'}</button>
      </div>
    </div>
  )
}
function TerminationForm({ employees, lang, onCalculate, onClose }) {
  const [f, setF] = useState({ employee: employees[0]?.id || '', reason: 'resignation', termination_date: new Date().toISOString().split('T')[0] })
  const s = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <div className="space-y-3">
      <select className="input" value={f.employee} onChange={e => s('employee', e.target.value)}>
        {employees.map(e => <option key={e.id} value={e.id}>{e.name_ar} ({e.employee_number})</option>)}
      </select>
      <select className="input" value={f.reason} onChange={e => s('reason', e.target.value)}>
        <option value="resignation">{lang === 'ar' ? 'استقالة' : 'Resignation'}</option>
        <option value="termination">{lang === 'ar' ? 'إنهاء خدمات' : 'Termination'}</option>
        <option value="contract_end">{lang === 'ar' ? 'انتهاء العقد' : 'Contract End'}</option>
        <option value="retirement">{lang === 'ar' ? 'تقاعد' : 'Retirement'}</option>
      </select>
      <input className="input" type="date" value={f.termination_date} onChange={e => s('termination_date', e.target.value)} dir="ltr" />
      <div className="flex gap-3 justify-end">
        <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
        <button className="btn btn-primary" onClick={() => onCalculate(f)}>{lang === 'ar' ? 'حساب التسوية' : 'Calculate EOSB'}</button>
      </div>
    </div>
  )
}

function AddDocForm({ employees, lang, onSave, onClose }) {
  const [f, setF] = useState({ employee: employees[0]?.id || '', doc_type: 'contract', title: '', issue_date: '', expiry_date: '', notes: '' })
  const s = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <div className="space-y-3">
      <select className="input" value={f.employee} onChange={e => s('employee', e.target.value)}>
        {employees.map(e => <option key={e.id} value={e.id}>{e.name_ar} ({e.employee_number})</option>)}
      </select>
      <select className="input" value={f.doc_type} onChange={e => s('doc_type', e.target.value)}>
        <option value="contract">{lang === 'ar' ? 'عقد عمل' : 'Contract'}</option>
        <option value="national_id">{lang === 'ar' ? 'هوية/إقامة' : 'National ID / Iqama'}</option>
        <option value="passport">{lang === 'ar' ? 'جواز سفر' : 'Passport'}</option>
        <option value="certificate">{lang === 'ar' ? 'شهادة' : 'Certificate'}</option>
        <option value="gosi_cert">GOSI</option>
        <option value="medical">{lang === 'ar' ? 'تقرير طبي' : 'Medical'}</option>
        <option value="other">{lang === 'ar' ? 'أخرى' : 'Other'}</option>
      </select>
      <input className="input" placeholder={lang === 'ar' ? 'عنوان المستند' : 'Document Title'} value={f.title} onChange={e => s('title', e.target.value)} />
      <div className="grid grid-cols-2 gap-3">
        <input className="input" type="date" placeholder={lang === 'ar' ? 'تاريخ الإصدار' : 'Issue Date'} value={f.issue_date} onChange={e => s('issue_date', e.target.value)} dir="ltr" />
        <input className="input" type="date" placeholder={lang === 'ar' ? 'تاريخ الانتهاء' : 'Expiry Date'} value={f.expiry_date} onChange={e => s('expiry_date', e.target.value)} dir="ltr" />
      </div>
      <textarea className="input" rows={2} placeholder={lang === 'ar' ? 'ملاحظات' : 'Notes'} value={f.notes} onChange={e => s('notes', e.target.value)} />
      <div className="flex gap-3 justify-end">
        <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
        <button className="btn btn-primary" onClick={() => onSave(f)}>{lang === 'ar' ? 'حفظ' : 'Save'}</button>
      </div>
    </div>
  )
}
