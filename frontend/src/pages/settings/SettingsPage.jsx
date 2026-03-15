import { useState } from 'react'
import { Building2, Shield, Bell, Globe, Key, Users } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'

export default function SettingsPage() {
  const { lang } = useLang()
  const { user } = useAuth()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'الإعدادات' : 'Settings'}</h1>
        <p className="text-sm text-slate-500">{lang === 'ar' ? 'إعدادات النظام والشركة' : 'System and company settings'}</p>
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
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'اسم الشركة (عربي)' : 'Company Name (Arabic)'}</label>
            <input className="input" disabled placeholder={lang === 'ar' ? 'اسم الشركة' : 'Company name'} />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">Company Name (English)</label>
            <input className="input" disabled placeholder="Company name" dir="ltr" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'الرقم الضريبي (VAT)' : 'VAT Number'}</label>
            <input className="input" disabled placeholder="300000000000003" dir="ltr" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'السجل التجاري' : 'Commercial Registration'}</label>
            <input className="input" disabled placeholder="CR Number" dir="ltr" />
          </div>
        </div>
        <p className="text-xs text-slate-400 mt-3">{lang === 'ar' ? 'تعديل بيانات الشركة متاح من لوحة الإدارة' : 'Company details can be edited from the admin panel'}</p>
      </div>

      {/* ZATCA Settings */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-green-50 text-green-600 flex items-center justify-center">
            <Shield size={20} />
          </div>
          <h2 className="text-lg font-semibold">{lang === 'ar' ? 'إعدادات ZATCA' : 'ZATCA Settings'}</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'البيئة' : 'Environment'}</label>
            <div className="flex gap-2">
              {['sandbox', 'simulation', 'production'].map(env => (
                <span key={env} className={`px-3 py-1.5 rounded-lg text-sm ${env === 'sandbox' ? 'bg-yellow-100 text-yellow-800 font-medium' : 'bg-slate-100 text-slate-500'}`}>
                  {env}
                </span>
              ))}
            </div>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'حالة CSID' : 'CSID Status'}</label>
            <span className="px-3 py-1.5 rounded-lg text-sm bg-green-100 text-green-700 font-medium">
              {lang === 'ar' ? 'نشط' : 'Active'}
            </span>
          </div>
        </div>
      </div>

      {/* User Account */}
      <div className="card">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center">
            <Key size={20} />
          </div>
          <h2 className="text-lg font-semibold">{lang === 'ar' ? 'حساب المستخدم' : 'User Account'}</h2>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'اسم المستخدم' : 'Username'}</label>
            <input className="input" disabled value={user?.username || user?.name || 'admin'} dir="ltr" />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-600 mb-1">{lang === 'ar' ? 'البريد الإلكتروني' : 'Email'}</label>
            <input className="input" disabled value={user?.email || 'admin@erp.sa'} dir="ltr" />
          </div>
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
          <div><span className="text-slate-500">{lang === 'ar' ? 'البيئة' : 'Environment'}</span><div className="font-semibold mt-1">Production</div></div>
          <div><span className="text-slate-500">API</span><div className="font-semibold mt-1">/api/</div></div>
          <div><span className="text-slate-500">ZATCA</span><div className="font-semibold mt-1">Phase 2</div></div>
        </div>
      </div>
    </div>
  )
}
