import { useState, useEffect } from 'react'
import { Building2, Shield, Key, Globe, Users, Plus, Loader2, Trash2 } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import { usersAPI } from '../../services/api'
import toast from 'react-hot-toast'

function AddUserModal({ onClose, onSave, lang, loading }) {
  const [form, setForm] = useState({
    username: '', email: '', password: '', first_name: '', last_name: '', is_staff: false,
  })
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 space-y-4" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold">{lang === 'ar' ? 'إضافة مستخدم' : 'Add User'}</h2>
        <div className="grid grid-cols-2 gap-3">
          <input className="input" placeholder={lang === 'ar' ? 'اسم المستخدم' : 'Username'} value={form.username} onChange={e => set('username', e.target.value)} dir="ltr" />
          <input className="input" type="email" placeholder={lang === 'ar' ? 'البريد الإلكتروني' : 'Email'} value={form.email} onChange={e => set('email', e.target.value)} dir="ltr" />
          <input className="input" placeholder={lang === 'ar' ? 'الاسم الأول' : 'First Name'} value={form.first_name} onChange={e => set('first_name', e.target.value)} />
          <input className="input" placeholder={lang === 'ar' ? 'اسم العائلة' : 'Last Name'} value={form.last_name} onChange={e => set('last_name', e.target.value)} />
          <input className="input col-span-2" type="password" placeholder={lang === 'ar' ? 'كلمة المرور (8 أحرف على الأقل)' : 'Password (min 8 chars)'} value={form.password} onChange={e => set('password', e.target.value)} dir="ltr" />
          <label className="col-span-2 flex items-center gap-2 text-sm">
            <input type="checkbox" checked={form.is_staff} onChange={e => set('is_staff', e.target.checked)} />
            {lang === 'ar' ? 'صلاحيات مدير (staff)' : 'Staff / Admin access'}
          </label>
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
      const res = await usersAPI.getUsers(api)
      setUsers(res.data.results || [])
    } catch (err) { console.error(err) }
    finally { setLoadingUsers(false) }
  }

  useEffect(() => { fetchUsers() }, [])

  const handleAddUser = async (form) => {
    setSaving(true)
    try {
      await usersAPI.createUser(api, form)
      toast.success(lang === 'ar' ? 'تم إنشاء المستخدم' : 'User created')
      setShowAddUser(false)
      fetchUsers()
    } catch (err) {
      toast.error(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Error')
    } finally { setSaving(false) }
  }

  const handleDeleteUser = async (id, username) => {
    if (!confirm(lang === 'ar' ? `حذف المستخدم ${username}?` : `Delete user ${username}?`)) return
    try {
      await usersAPI.deleteUser(api, id)
      toast.success(lang === 'ar' ? 'تم حذف المستخدم' : 'User deleted')
      fetchUsers()
    } catch (err) { toast.error('Error deleting user') }
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'الإعدادات' : 'Settings'}</h1>
        <p className="text-sm text-slate-500">{lang === 'ar' ? 'إعدادات النظام والشركة والمستخدمين' : 'System, company & user settings'}</p>
      </div>

      {/* User Management */}
      <div className="card">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
              <Users size={20} />
            </div>
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
                      <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_staff ? 'bg-purple-100 text-purple-700' : 'bg-slate-100 text-slate-600'}`}>
                        {u.is_staff ? (lang === 'ar' ? 'مدير' : 'Admin') : (lang === 'ar' ? 'مستخدم' : 'User')}
                      </span>
                    </td>
                    <td className="py-2.5 px-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${u.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                        {u.is_active ? (lang === 'ar' ? 'نشط' : 'Active') : (lang === 'ar' ? 'معطل' : 'Inactive')}
                      </span>
                    </td>
                    <td className="py-2.5 px-2">
                      {u.username !== 'admin' && (
                        <button onClick={() => handleDeleteUser(u.id, u.username)} className="text-red-400 hover:text-red-600">
                          <Trash2 size={16} />
                        </button>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
            {users.length === 0 && <p className="text-center py-6 text-slate-400">{lang === 'ar' ? 'لا يوجد مستخدمون' : 'No users'}</p>}
          </div>
        )}
      </div>

      {/* Company Info */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-600 flex items-center justify-center">
            <Building2 size={20} />
          </div>
          <h2 className="text-lg font-semibold">{lang === 'ar' ? 'معلومات الشركة' : 'Company Information'}</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'اسم الشركة' : 'Company Name'}</label>
            <input className="input" disabled placeholder={lang === 'ar' ? 'متاح من لوحة الإدارة' : 'Available from admin panel'} />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'الرقم الضريبي' : 'VAT Number'}</label>
            <input className="input" disabled placeholder="300000000000003" dir="ltr" />
          </div>
        </div>
      </div>

      {/* ZATCA Settings */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-green-50 text-green-600 flex items-center justify-center">
            <Shield size={20} />
          </div>
          <h2 className="text-lg font-semibold">{lang === 'ar' ? 'إعدادات ZATCA' : 'ZATCA Settings'}</h2>
        </div>
        <div className="flex gap-2">
          {['sandbox', 'simulation', 'production'].map(env => (
            <span key={env} className={`px-3 py-1.5 rounded-lg text-sm ${env === 'sandbox' ? 'bg-yellow-100 text-yellow-800 font-medium' : 'bg-slate-100 text-slate-500'}`}>
              {env}
            </span>
          ))}
        </div>
      </div>

      {/* System Info */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-slate-100 text-slate-600 flex items-center justify-center">
            <Globe size={20} />
          </div>
          <h2 className="text-lg font-semibold">{lang === 'ar' ? 'معلومات النظام' : 'System Info'}</h2>
        </div>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div><span className="text-slate-500">{lang === 'ar' ? 'الإصدار' : 'Version'}</span><div className="font-semibold mt-1">1.0.0</div></div>
          <div><span className="text-slate-500">API</span><div className="font-semibold mt-1">/api/</div></div>
          <div><span className="text-slate-500">ZATCA</span><div className="font-semibold mt-1">Phase 2</div></div>
          <div><span className="text-slate-500">{lang === 'ar' ? 'المنطقة الزمنية' : 'Timezone'}</span><div className="font-semibold mt-1">Asia/Riyadh</div></div>
        </div>
      </div>

      {showAddUser && <AddUserModal onClose={() => setShowAddUser(false)} onSave={handleAddUser} lang={lang} loading={saving} />}
    </div>
  )
}
