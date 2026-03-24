import { useState, useEffect } from 'react'
import { Building2, Shield, Key, Globe, Users, Plus, Loader2, Trash2, Server, Bot } from 'lucide-react'
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

      {/* AI Backend Configuration */}
      <AIConfigPanel lang={lang} api={api} />

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

      {/* Super-Admin: Tenant Management */}
      {user?.is_superuser && <TenantPanel lang={lang} api={api} />}
    </div>
  )
}

function TenantPanel({ lang, api }) {
  const [tenants, setTenants] = useState([])
  const [stats, setStats] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchTenants = async () => {
    setLoading(true)
    try {
      const [tRes, sRes] = await Promise.allSettled([
        api.get('/public/tenants/'),
        api.get('/public/tenants/stats/'),
      ])
      if (tRes.status === 'fulfilled') setTenants(tRes.value.data.results || [])
      if (sRes.status === 'fulfilled') setStats(sRes.value.data)
    } catch {}
    finally { setLoading(false) }
  }

  useEffect(() => { fetchTenants() }, [])

  const toggleActive = async (id, isActive) => {
    try {
      await api.post(`/public/tenants/${id}/${isActive ? 'deactivate' : 'activate'}/`)
      toast.success(isActive ? 'Deactivated' : 'Activated')
      fetchTenants()
    } catch { toast.error('Error') }
  }

  const changePlan = async (id, plan) => {
    try {
      await api.post(`/public/tenants/${id}/change_plan/`, { plan })
      toast.success('Plan changed')
      fetchTenants()
    } catch { toast.error('Error') }
  }

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center"><Server size={20} /></div>
          <h2 className="text-lg font-semibold">{lang === 'ar' ? 'إدارة الشركات (المستأجرين)' : 'Tenant Management'}</h2>
        </div>
      </div>

      {stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-4">
          <div className="bg-blue-50 rounded-xl p-3"><div className="text-xs text-blue-600">{lang === 'ar' ? 'إجمالي' : 'Total'}</div><div className="text-xl font-bold">{stats.total_tenants}</div></div>
          <div className="bg-green-50 rounded-xl p-3"><div className="text-xs text-green-600">{lang === 'ar' ? 'نشط' : 'Active'}</div><div className="text-xl font-bold">{stats.active_tenants}</div></div>
          <div className="bg-yellow-50 rounded-xl p-3"><div className="text-xs text-yellow-600">Starter</div><div className="text-xl font-bold">{stats.by_plan?.starter || 0}</div></div>
          <div className="bg-purple-50 rounded-xl p-3"><div className="text-xs text-purple-600">Growth</div><div className="text-xl font-bold">{stats.by_plan?.growth || 0}</div></div>
        </div>
      )}

      {loading ? <div className="flex justify-center py-6"><Loader2 size={24} className="animate-spin text-brand-500" /></div> : (
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead><tr className="border-b">
              <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الشركة' : 'Company'}</th>
              <th className="text-start py-2 px-2 font-medium text-slate-500">VAT</th>
              <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'النطاق' : 'Domain'}</th>
              <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الخطة' : 'Plan'}</th>
              <th className="text-start py-2 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الحالة' : 'Status'}</th>
              <th className="py-2 px-2"></th>
            </tr></thead>
            <tbody>{tenants.map(t => (
              <tr key={t.id} className="border-b border-slate-100 hover:bg-slate-50">
                <td className="py-2.5 px-2">
                  <div className="font-medium">{t.name_en}</div>
                  <div className="text-xs text-slate-400">{t.schema_name}</div>
                </td>
                <td className="py-2.5 px-2 font-mono text-xs">{t.vat_number}</td>
                <td className="py-2.5 px-2 font-mono text-xs text-brand-600">{t.domain}</td>
                <td className="py-2.5 px-2">
                  <select className="text-xs border rounded px-1 py-0.5" value={t.plan}
                    onChange={e => changePlan(t.id, e.target.value)}>
                    <option value="starter">Starter</option>
                    <option value="growth">Growth</option>
                    <option value="enterprise">Enterprise</option>
                  </select>
                </td>
                <td className="py-2.5 px-2">
                  <span className={`text-xs px-2 py-0.5 rounded-full ${t.is_active ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'}`}>
                    {t.is_active ? (lang === 'ar' ? 'نشط' : 'Active') : (lang === 'ar' ? 'معطل' : 'Inactive')}
                  </span>
                </td>
                <td className="py-2.5 px-2">
                  <button onClick={() => toggleActive(t.id, t.is_active)}
                    className={`text-xs px-2 py-1 rounded ${t.is_active ? 'text-red-600 hover:bg-red-50' : 'text-green-600 hover:bg-green-50'}`}>
                    {t.is_active ? (lang === 'ar' ? 'تعطيل' : 'Deactivate') : (lang === 'ar' ? 'تفعيل' : 'Activate')}
                  </button>
                </td>
              </tr>
            ))}</tbody>
          </table>
          {tenants.length === 0 && <p className="text-center py-6 text-slate-400">{lang === 'ar' ? 'لا توجد شركات' : 'No tenants'}</p>}
        </div>
      )}
    </div>
  )
}

function AIConfigPanel({ lang, api }) {
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ backend: 'anthropic', ollama_url: 'http://localhost:11434', ollama_model: 'command-r:35b', anthropic_api_key: '' })

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await api.get('/ai/status/')
        setConfig(res.data)
        setForm(f => ({
          ...f,
          backend: res.data.backend || 'anthropic',
          ollama_url: res.data.ollama_url || 'http://localhost:11434',
          ollama_model: res.data.ollama_model || 'command-r:35b',
        }))
      } catch {}
      finally { setLoading(false) }
    }
    fetch()
  }, [])

  const switchBackend = async () => {
    setSaving(true)
    try {
      const res = await api.post('/ai/status/', form)
      toast.success(res.data.message || 'AI backend switched')
      const statusRes = await api.get('/ai/status/')
      setConfig(statusRes.data)
    } catch (err) {
      toast.error(err.response?.data?.error || 'Error switching backend')
    } finally { setSaving(false) }
  }

  const s = (k, v) => setForm(f => ({ ...f, [k]: v }))

  if (loading) return null

  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center"><Bot size={20} /></div>
          <div>
            <h2 className="text-lg font-semibold">{lang === 'ar' ? 'إعدادات الذكاء الاصطناعي' : 'AI Configuration'}</h2>
            <p className="text-xs text-slate-400">{lang === 'ar' ? 'التبديل بين Claude السحابي و Ollama المحلي' : 'Switch between Cloud (Claude) and Local (Ollama)'}</p>
          </div>
        </div>
        <span className={`text-xs px-3 py-1 rounded-full ${config?.status === 'connected' ? 'bg-green-100 text-green-700' : config?.status === 'no_api_key' ? 'bg-yellow-100 text-yellow-700' : 'bg-red-100 text-red-700'}`}>
          {config?.backend} — {config?.status}
        </span>
      </div>

      <div className="flex gap-3 mb-4">
        <button onClick={() => s('backend', 'anthropic')}
          className={`flex-1 p-4 rounded-xl border-2 transition-all ${form.backend === 'anthropic' ? 'border-purple-500 bg-purple-50' : 'border-slate-200 hover:border-slate-300'}`}>
          <div className="font-semibold text-sm">{lang === 'ar' ? '☁️ سحابي — Claude' : '☁️ Cloud — Claude'}</div>
          <div className="text-xs text-slate-500 mt-1">{lang === 'ar' ? 'يتطلب مفتاح API' : 'Requires API key'}</div>
          <div className="text-xs text-slate-400 mt-1">claude-sonnet-4-20250514</div>
        </button>
        <button onClick={() => s('backend', 'ollama')}
          className={`flex-1 p-4 rounded-xl border-2 transition-all ${form.backend === 'ollama' ? 'border-purple-500 bg-purple-50' : 'border-slate-200 hover:border-slate-300'}`}>
          <div className="font-semibold text-sm">{lang === 'ar' ? '🖥️ محلي — Ollama' : '🖥️ Local — Ollama'}</div>
          <div className="text-xs text-slate-500 mt-1">{lang === 'ar' ? 'بدون إنترنت' : 'No internet needed'}</div>
          <div className="text-xs text-slate-400 mt-1">{form.ollama_model}</div>
        </button>
      </div>

      {form.backend === 'anthropic' ? (
        <div className="space-y-3 mb-4">
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Anthropic API Key</label>
            <input className="input" type="password" placeholder="sk-ant-..." dir="ltr"
              value={form.anthropic_api_key} onChange={e => s('anthropic_api_key', e.target.value)} />
            <p className="text-xs text-slate-400 mt-1">{lang === 'ar' ? 'اتركه فارغاً لاستخدام متغير البيئة' : 'Leave empty to use env var'}</p>
          </div>
        </div>
      ) : (
        <div className="space-y-3 mb-4">
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Ollama URL</label>
            <input className="input" placeholder="http://localhost:11434" dir="ltr"
              value={form.ollama_url} onChange={e => s('ollama_url', e.target.value)} />
          </div>
          <div>
            <label className="text-sm font-medium text-slate-600 mb-1 block">Model</label>
            <select className="input" value={form.ollama_model} onChange={e => s('ollama_model', e.target.value)}>
              <option value="command-r:35b">Command-R 35B</option>
              <option value="llama3:8b">Llama 3 8B</option>
              <option value="llama3:70b">Llama 3 70B</option>
              <option value="mistral:7b">Mistral 7B</option>
              <option value="qwen2:7b">Qwen2 7B</option>
              <option value="gemma2:9b">Gemma2 9B</option>
            </select>
          </div>
          <div className="bg-blue-50 rounded-lg p-3 text-xs text-blue-700">
            <span className="font-semibold">{lang === 'ar' ? 'ملاحظة:' : 'Setup:'}</span>{' '}
            ollama serve && ollama pull {form.ollama_model}
          </div>
        </div>
      )}

      <button onClick={switchBackend} disabled={saving}
        className="btn btn-primary flex items-center gap-2">
        {saving ? <Loader2 size={16} className="animate-spin" /> : null}
        {lang === 'ar' ? 'حفظ وتطبيق' : 'Save & Apply'}
      </button>

      <p className="text-xs text-slate-400 mt-3">
        {lang === 'ar'
          ? 'التغيير مؤقت — لتغيير دائم عدّل AI_BACKEND في Railway'
          : 'Temporary until redeploy — set AI_BACKEND env var for permanent'}
      </p>
    </div>
  )
}