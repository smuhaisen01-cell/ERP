import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Eye, EyeOff, Building2, Globe, Loader2 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'
import { useLang } from '../../contexts/LangContext'
import toast from 'react-hot-toast'

export default function LoginPage() {
  const { login } = useAuth()
  const { t, toggle, lang, isRTL } = useLang()
  const navigate = useNavigate()
  const [showPass, setShowPass] = useState(false)
  const [loading, setLoading] = useState(false)
  const [form, setForm] = useState({ username: '', password: '' })

  const handleSubmit = async (e) => {
    e.preventDefault()
    setLoading(true)
    try {
      await login(form.username, form.password)
      navigate('/dashboard')
    } catch (err) {
      toast.error(lang === 'ar' ? 'بيانات الدخول غير صحيحة' : 'Invalid credentials')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex" dir={isRTL ? 'rtl' : 'ltr'}>
      {/* Left panel */}
      <div className="hidden lg:flex flex-col w-[52%] bg-surface-900 relative overflow-hidden p-12">
        <div className="absolute inset-0">
          <div className="absolute top-0 start-0 w-[600px] h-[600px] rounded-full bg-brand-600/20 -translate-x-1/2 -translate-y-1/2 blur-3xl" />
          <div className="absolute bottom-0 end-0 w-[400px] h-[400px] rounded-full bg-sand-500/10 translate-x-1/3 translate-y-1/3 blur-3xl" />
        </div>
        <div className="relative flex items-center gap-3 mb-auto">
          <div className="w-10 h-10 rounded-xl bg-brand-500 flex items-center justify-center">
            <Building2 size={22} className="text-white" />
          </div>
          <div>
            <div className="text-white font-bold text-lg leading-tight">
              {lang === 'ar' ? 'نظام ERP' : 'ERP System'}
            </div>
            <div className="text-white/40 text-xs">Saudi Arabia</div>
          </div>
        </div>
        <div className="relative mt-auto space-y-6">
          <h2 className="text-white text-3xl font-bold leading-snug">
            {lang === 'ar'
              ? 'إدارة أعمالك بذكاء\nوامتثال كامل لمتطلبات\nهيئة الزكاة والضريبة'
              : 'Manage your business\nwith full ZATCA\ncompliance'}
          </h2>
          {[
            lang === 'ar' ? '✦ فوترة إلكترونية متوافقة مع ZATCA المرحلة الثانية' : '✦ ZATCA Phase 2 e-Invoicing compliant',
            lang === 'ar' ? '✦ إدارة الموارد البشرية والرواتب وGOSI' : '✦ HR, Payroll & GOSI management',
            lang === 'ar' ? '✦ نقطة بيع متكاملة مع الفوترة الضريبية' : '✦ Integrated POS with tax invoicing',
            lang === 'ar' ? '✦ تقارير وتحليلات ذكاء اصطناعي فورية' : '✦ Real-time AI analytics & insights',
          ].map((f, i) => (
            <div key={i} className="text-white/60 text-sm">{f}</div>
          ))}
        </div>
      </div>

      {/* Right panel: login form */}
      <div className="flex-1 flex flex-col items-center justify-center p-8 bg-white relative">
        <button onClick={toggle}
          className="absolute top-6 end-6 flex items-center gap-2 text-sm text-slate-500 hover:text-slate-800 transition-colors">
          <Globe size={16} />
          {lang === 'ar' ? 'English' : 'العربية'}
        </button>

        <div className="w-full max-w-[380px]">
          <div className="lg:hidden flex items-center gap-2 mb-8">
            <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
              <Building2 size={16} className="text-white" />
            </div>
            <span className="font-bold text-slate-900">
              {lang === 'ar' ? 'نظام ERP' : 'ERP System'}
            </span>
          </div>

          <div className="mb-8">
            <h1 className="text-2xl font-bold text-slate-900 mb-1">{t('welcomeBack')}</h1>
            <p className="text-slate-500 text-sm">{t('signInSubtitle')}</p>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                {lang === 'ar' ? 'اسم المستخدم' : 'Username'}
              </label>
              <input
                type="text"
                required
                className="input"
                placeholder={lang === 'ar' ? 'أدخل اسم المستخدم' : 'Enter your username'}
                value={form.username}
                onChange={e => setForm(f => ({ ...f, username: e.target.value }))}
                dir="ltr"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                {t('password')}
              </label>
              <div className="relative">
                <input
                  type={showPass ? 'text' : 'password'}
                  required
                  className="input pe-11"
                  placeholder={lang === 'ar' ? 'أدخل كلمة المرور' : 'Enter your password'}
                  value={form.password}
                  onChange={e => setForm(f => ({ ...f, password: e.target.value }))}
                  dir="ltr"
                />
                <button type="button" onClick={() => setShowPass(s => !s)}
                  className="absolute inset-y-0 end-3 flex items-center text-slate-400 hover:text-slate-600">
                  {showPass ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <div className="flex items-center justify-between">
              <label className="flex items-center gap-2 text-sm text-slate-600 cursor-pointer">
                <input type="checkbox" className="rounded" />
                {t('rememberMe')}
              </label>
            </div>

            <button type="submit" disabled={loading}
              className="btn btn-primary w-full justify-center py-3 text-base mt-2">
              {loading
                ? <><Loader2 size={18} className="animate-spin" /> {t('loading')}</>
                : t('signIn')
              }
            </button>
          </form>

          <p className="text-center text-sm text-slate-500 mt-6">
            {lang === 'ar' ? 'ليس لديك حساب؟' : "Don't have an account?"}{' '}
            <a href="/app/signup" className="text-brand-600 font-semibold hover:underline">
              {lang === 'ar' ? 'سجّل شركتك' : 'Register your company'}
            </a>
          </p>
        </div>
      </div>
    </div>
  )
}
