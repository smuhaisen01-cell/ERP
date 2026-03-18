import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Building2, Loader2, ArrowRight } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import axios from 'axios'

export default function SignupPage() {
  const { lang, toggle } = useLang()
  const navigate = useNavigate()
  const [step, setStep] = useState(1)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [result, setResult] = useState(null)

  const [form, setForm] = useState({
    company_name_ar: '', company_name_en: '', vat_number: '', cr_number: '', city: 'Riyadh',
    admin_username: '', admin_email: '', admin_password: '', subdomain: '',
  })
  const s = (k, v) => setForm(f => ({ ...f, [k]: v }))

  const handleSignup = async () => {
    setLoading(true)
    setError('')
    try {
      const res = await axios.post('/api/public/signup/', form)
      setResult(res.data)
      setStep(3)
    } catch (err) {
      setError(err.response?.data?.error || JSON.stringify(err.response?.data) || 'Signup failed')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50 flex items-center justify-center p-4">
      <div className="w-full max-w-lg">
        {/* Header */}
        <div className="text-center mb-8">
          <div className="w-16 h-16 bg-brand-500 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <Building2 size={32} className="text-white" />
          </div>
          <h1 className="text-3xl font-bold text-slate-900">{lang === 'ar' ? 'تسجيل شركة جديدة' : 'Register Your Company'}</h1>
          <p className="text-slate-500 mt-2">{lang === 'ar' ? 'ابدأ تجربة مجانية لمدة 30 يوم' : 'Start your 30-day free trial'}</p>
          <button onClick={toggle} className="text-sm text-brand-600 mt-2">{lang === 'ar' ? 'English' : 'العربية'}</button>
        </div>

        <div className="bg-white rounded-2xl shadow-xl p-8">
          {/* Step indicator */}
          <div className="flex items-center justify-center gap-2 mb-6">
            {[1, 2, 3].map(i => (
              <div key={i} className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-semibold transition-all ${step >= i ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-400'}`}>{i}</div>
            ))}
          </div>

          {/* Step 1: Company Info */}
          {step === 1 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold mb-2">{lang === 'ar' ? 'بيانات الشركة' : 'Company Information'}</h2>
              <div className="grid grid-cols-2 gap-3">
                <input className="input" placeholder={lang === 'ar' ? 'اسم الشركة (عربي)' : 'Company Name (Arabic)'} value={form.company_name_ar} onChange={e => s('company_name_ar', e.target.value)} />
                <input className="input" placeholder="Company Name (English)" value={form.company_name_en} onChange={e => s('company_name_en', e.target.value)} dir="ltr" />
              </div>
              <input className="input" placeholder={lang === 'ar' ? 'الرقم الضريبي (15 رقم)' : 'VAT Number (15 digits)'} value={form.vat_number} onChange={e => s('vat_number', e.target.value)} dir="ltr" maxLength={15} />
              <input className="input" placeholder={lang === 'ar' ? 'رقم السجل التجاري (اختياري)' : 'CR Number (optional)'} value={form.cr_number} onChange={e => s('cr_number', e.target.value)} dir="ltr" />
              <input className="input" placeholder={lang === 'ar' ? 'المدينة' : 'City'} value={form.city} onChange={e => s('city', e.target.value)} />

              <div>
                <label className="text-xs text-slate-500 mb-1 block">{lang === 'ar' ? 'النطاق الفرعي' : 'Subdomain'}</label>
                <div className="flex items-center gap-2">
                  <input className="input flex-1" placeholder="mycompany" value={form.subdomain} onChange={e => s('subdomain', e.target.value.toLowerCase().replace(/[^a-z0-9-]/g, ''))} dir="ltr" />
                  <span className="text-sm text-slate-400">.erp.sa</span>
                </div>
              </div>

              <button onClick={() => setStep(2)} disabled={!form.company_name_en || !form.vat_number || !form.subdomain}
                className="btn btn-primary w-full py-3 flex items-center justify-center gap-2 disabled:opacity-50">
                {lang === 'ar' ? 'التالي' : 'Next'} <ArrowRight size={16} />
              </button>
            </div>
          )}

          {/* Step 2: Admin Account */}
          {step === 2 && (
            <div className="space-y-4">
              <h2 className="text-lg font-semibold mb-2">{lang === 'ar' ? 'حساب المدير' : 'Admin Account'}</h2>
              <input className="input" placeholder={lang === 'ar' ? 'اسم المستخدم' : 'Username'} value={form.admin_username} onChange={e => s('admin_username', e.target.value)} dir="ltr" />
              <input className="input" type="email" placeholder={lang === 'ar' ? 'البريد الإلكتروني' : 'Email'} value={form.admin_email} onChange={e => s('admin_email', e.target.value)} dir="ltr" />
              <input className="input" type="password" placeholder={lang === 'ar' ? 'كلمة المرور (8+ أحرف)' : 'Password (8+ chars)'} value={form.admin_password} onChange={e => s('admin_password', e.target.value)} dir="ltr" />

              {error && <div className="bg-red-50 text-red-700 text-sm p-3 rounded-lg">{error}</div>}

              <div className="flex gap-3">
                <button onClick={() => setStep(1)} className="btn btn-secondary flex-1">{lang === 'ar' ? 'رجوع' : 'Back'}</button>
                <button onClick={handleSignup} disabled={loading || !form.admin_username || !form.admin_email || !form.admin_password}
                  className="btn btn-primary flex-1 flex items-center justify-center gap-2 disabled:opacity-50">
                  {loading ? <Loader2 size={16} className="animate-spin" /> : null}
                  {lang === 'ar' ? 'إنشاء الحساب' : 'Create Account'}
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Success */}
          {step === 3 && result && (
            <div className="text-center space-y-4">
              <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto">
                <span className="text-3xl">🎉</span>
              </div>
              <h2 className="text-xl font-bold text-green-700">{lang === 'ar' ? 'تم إنشاء شركتك بنجاح!' : 'Your company is ready!'}</h2>

              <div className="bg-slate-50 rounded-xl p-4 text-sm text-start space-y-2">
                <div className="flex justify-between"><span className="text-slate-500">{lang === 'ar' ? 'الشركة' : 'Company'}</span><span className="font-semibold">{result.tenant?.name}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">VAT</span><span className="font-mono">{result.tenant?.vat_number}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">{lang === 'ar' ? 'النطاق' : 'Domain'}</span><span className="font-mono text-brand-600">{result.tenant?.domain}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">{lang === 'ar' ? 'الخطة' : 'Plan'}</span><span>{result.tenant?.plan} — 30 {lang === 'ar' ? 'يوم تجربة' : 'day trial'}</span></div>
                <div className="flex justify-between"><span className="text-slate-500">{lang === 'ar' ? 'المستخدم' : 'Username'}</span><span className="font-mono">{result.admin?.username}</span></div>
              </div>

              <a href={`/app/login`}
                className="btn btn-primary w-full py-3 inline-flex items-center justify-center gap-2">
                {lang === 'ar' ? 'تسجيل الدخول' : 'Go to Login'} <ArrowRight size={16} />
              </a>

              <p className="text-xs text-slate-400">
                {lang === 'ar'
                  ? 'عند إعداد النطاق المخصص، ستتمكن من الوصول عبر: '
                  : 'Once custom domain is configured, access via: '}
                <span className="font-mono">{result.login_url}</span>
              </p>
            </div>
          )}
        </div>

        {/* Login link */}
        {step < 3 && (
          <p className="text-center text-sm text-slate-500 mt-4">
            {lang === 'ar' ? 'لديك حساب بالفعل؟' : 'Already have an account?'}{' '}
            <a href="/app/login" className="text-brand-600 font-semibold hover:underline">
              {lang === 'ar' ? 'تسجيل الدخول' : 'Sign in'}
            </a>
          </p>
        )}
      </div>
    </div>
  )
}
