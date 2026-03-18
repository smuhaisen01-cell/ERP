import { useState, useEffect } from 'react'
import { Building2, Shield, Key, Globe, Users, Plus, Loader2, Trash2 } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

const ROLES = [
  { id: 'super_admin', labelAr: 'مدير النظام', labelEn: 'Super Admin', color: 'bg-red-100 text-red-700' },
  { id: 'hr_manager', labelAr: 'مدير HR', labelEn: 'HR Manager', color: 'bg-blue-100 text-blue-700' },
  { id: 'accountant', labelAr: 'محاسب', labelEn: 'Accountant', color: 'bg-green-100 text-green-700' },
  { id: 'pos_cashier', labelAr: 'كاشير', labelEn: 'POS Cashier', color: 'bg-yellow-100 text-yellow-700' },
  { id: 'employee', labelAr: 'موظف', labelEn: 'Employee', color: 'bg-slate-100 text-slate-600' },
]

function AddUserModal({ onClose, onSave, lang, loading }) {
  const [form, setForm] = useState({
    username: '', email: '', password: '', first_name: '', last_name: '', role: 'employee',
  })
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 space-y-4" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold">{lang === 'ar' ? 'إضافة مستخدم' : 'Add User'}</h2>
        <div className="grid grid-cols-2 gap-3">
          <input className="input" placeholder={lang === 'ar' ? 'اسم المستخدم' : 'Username'} value={form.username} onChange={e => set('username', e.target.value)} dir="ltr" />
          <input className="input" type="email" placeholder={lang === 'ar' ? 'البريد' : 'Email'} value={form.email} onChange={e => set('email', e.target.value)} dir="ltr" />
          <input className="input" placeholder={lang === 'ar' ? 'الاسم الأول' : 'First Name'} value={form.first_name} onChange={e => set('first_name', e.target.value)} />
          <input className="input" placeholder={lang === 'ar' ? 'اسم العائلة' : 'Last Name'} value={form.last_name} onChange={e => set('last_name', e.target.value)} />
          <input className="input col-span-2" type="password" placeholder={lang === 'ar' ? 'كلمة المرور (8+)' : 'Password (8+ chars)'} value={form.password} onChange={e => set('password', e.target.value)} dir="ltr" />
          <select className="input col-span-2" value={form.role} onChange={e => set('role', e.target.value)}>
            {ROLES.map(r => <option key={r.id} value={r.id}>{lang === 'ar' ? r.labelAr : r.labelEn}</option>)}
          </select>
        </div>
        <div className="flex gap-3 justify-end">
          <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
          <button className="btn btn-primary flex items-center gap-2" onClick={() => onSave(form)} disabled={loading}>
            {loading && <Loader2 size={16} className="animate-spin" />}
            {lang === 'ar' ? 'إنشاء' : 'Create'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function SettingsPage() {
  const { lang } = useLang()
  const { user, api } = useAuth()
  const [users, setUsers] = useState([])
  const [loadingUsers, setLoadingUsers] = useState(true)
  const [showAddUser, setShowAddUser] = useState(false)
  const [saving, setSaving] = useState(false)

  const fetchUsers = async () => {
    setLoadingUsers(true)
    try {
      const res = await api.get('/users/')
      setUsers(res.data.results || [])
    } catch (err) { console.error(err) }
    finally { setLoadingUsers(false) }
  }

  useEffect(() => { fetchUsers() }, [])

  const handleAddUser = async (form) => {
    setSaving(true)
    try {
      await api.post('/users/', form)
      toast.success(lang === 'ar' ? 'تم إنشاء المستخدم' : 'User created')
      setShowAddUser(false)
      fetchUsers()
    } catch (err) {
      toast.error(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Error')
    } finally { setSaving(false) }
  }

  const handleChangeRole = async (userId, newRole) => {
    try {
      await api.post(`/users/${userId}/change_role/`, { role: newRole })
      toast.success(lang === 'ar' ? 'تم تغيير الصلاحية' : 'Role changed')
      fetchUsers()
    } catch (err) { toast.error('Error changing role') }
  }

  const handleDeleteUser = async (id, username) => {
    if (!confirm(lang === 'ar' ? `حذف ${username}?` : `Delete ${username}?`)) return
    try {
      await api.delete(`/users/${id}/`)
      toast.success('User deleted')
      fetchUsers()
    } catch (err) { toast.error('Error') }
  }

  const getRoleBadge = (role) => {
    const r = ROLES.find(x => x.id === role) || ROLES[4]
    return <span className={`text-xs px-2 py-0.5 rounded-full ${r.color}`}>{lang === 'ar' ? r.labelAr : r.labelEn}</span>
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'الإعدادات' : 'Settings'}</h1>
        <p className="text-sm text-slate-500">{lang === 'ar' ? 'إدارة المستخدمين والصلاحيات' : 'User management & roles'}</p>
      </div>

      {/* User Management */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center"><Users size={20} /></div>
            <h2 className="text-lg font-semibold">{lang === 'ar' ? 'إدارة المستخدمين' : 'User Management'}</h2>
          </div>
          <button onClick={() => setShowAddUser(true)} className="btn btn-primary flex items-center gap-2 text-sm">
            <Plus size={16} /> {lang === 'ar' ? 'مستخدم جديد' : 'Add User'}
          </button>
        </div>

        {loadingUsers ? (
          <div className="flex justify-center py-8"><Loader2 size={24} className="animate-spin text-brand-500" /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-200">
                <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'المستخدم' : 'Username'}</th>
                <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'البريد' : 'Email'}</th>
                <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الاسم' : 'Name'}</th>
                <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الصلاحية' : 'Role'}</th>
                <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الحالة' : 'Status'}</th>
                <th className="py-2 px-2"></th>
              </tr></thead>
              <tbody>
                {users.map(u => (
                  <tr key={u.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-2.5 px-2 font-medium" dir="ltr">{u.username}</td>
                    <td className="py-2.5 px-2 text-slate-500" dir="ltr">{u.email}</td>
                    <td className="py-2.5 px-2">{u.first_name} {u.last_name}</td>
                    <td className="py-2.5 px-2">
                      <select className="text-xs border rounded-lg px-2 py-1 bg-transparent"
                        value={u.role || 'employee'}
                        onChange={e => handleChangeRole(u.id, e.target.value)}>
                        {ROLES.map(r => <option key={r.id} value={r.id}>{lang === 'ar' ? r.labelAr : r.labelEn}</option>)}
                      </select>
                    </td>
                    <td className="py-2.5 px-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {u.is_active ? (lang === 'ar' ? 'نشط' : 'Active') : (lang === 'ar' ? 'معطل' : 'Inactive')}
                      </span>
                    </td>
                    <td className="py-2.5 px-2">
                      {u.username !== 'admin' && (
                        <button onClick={() => handleDeleteUser(u.id, u.username)} className="text-red-400 hover:text-red-600"><Trash2 size={16} /></button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Role Reference */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center"><Key size={20} /></div>
          <h2 className="text-lg font-semibold">{lang === 'ar' ? 'دليل الصلاحيات' : 'Role Reference'}</h2>
        </div>
        <div className="space-y-2">
          {ROLES.map(r => (
            <div key={r.id} className="flex items-center justify-between p-3 bg-slate-50 rounded-xl">
              <div className="flex items-center gap-3">
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${r.color}`}>{lang === 'ar' ? r.labelAr : r.labelEn}</span>
              </div>
              <div className="text-xs text-slate-500">
                {r.id === 'super_admin' && (lang === 'ar' ? 'كل الصلاحيات' : 'Full access to all modules')}
                {r.id === 'hr_manager' && (lang === 'ar' ? 'الموارد البشرية + التقارير' : 'HR, Dashboard, Reports')}
                {r.id === 'accountant' && (lang === 'ar' ? 'المحاسبة + الفواتير + التقارير' : 'Invoicing, Accounting, Reports')}
                {r.id === 'pos_cashier' && (lang === 'ar' ? 'نقطة البيع فقط' : 'Dashboard, POS only')}
                {r.id === 'employee' && (lang === 'ar' ? 'خدمة ذاتية: إجازات، كشوف' : 'Self-service: own leave, payslips')}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Company + ZATCA */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center"><Building2 size={20} /></div>
          <h2 className="text-lg font-semibold">{lang === 'ar' ? 'معلومات الشركة' : 'Company Info'}</h2>
        </div>
        <div className="grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-slate-500">{lang === 'ar' ? 'الرقم الضريبي' : 'VAT'}</span><div className="font-semibold mt-1" dir="ltr">300000000000003</div></div>
          <div><span className="text-slate-500">ZATCA</span><div className="font-semibold mt-1">Phase 2 — Sandbox</div></div>
          <div><span className="text-slate-500">{lang === 'ar' ? 'الإصدار' : 'Version'}</span><div className="font-semibold mt-1">1.0.0</div></div>
          <div><span className="text-slate-500">API</span><div className="font-semibold mt-1">/api/</div></div>
        </div>
      </div>

      {showAddUser && <AddUserModal onClose={() => setShowAddUser(false)} onSave={handleAddUser} lang={lang} loading={saving} />}
    </div>
  )
}
