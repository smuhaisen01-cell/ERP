import { useState } from 'react'
import {
  AreaChart, Area, BarChart, Bar, XAxis, YAxis,
  CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell
} from 'recharts'
import {
  TrendingUp, TrendingDown, DollarSign, Users,
  ShoppingBag, FileCheck, ArrowUpRight, Plus,
  Receipt, Calculator, BarChart2, AlertCircle
} from 'lucide-react'
import { useLang } from '../../contexts/LangContext'

// ── Mock data ──────────────────────────────────────────────────────
const revenueData = [
  { month: 'يناير/Jan', revenue: 142000, vat: 21300 },
  { month: 'فبراير/Feb', revenue: 168000, vat: 25200 },
  { month: 'مارس/Mar', revenue: 155000, vat: 23250 },
  { month: 'أبريل/Apr', revenue: 201000, vat: 30150 },
  { month: 'مايو/May', revenue: 189000, vat: 28350 },
  { month: 'يونيو/Jun', revenue: 234000, vat: 35100 },
  { month: 'يوليو/Jul', revenue: 218000, vat: 32700 },
]

const zatcaStatus = [
  { name: 'مصفّاة / Cleared', value: 847, color: '#16a34a' },
  { name: 'معلّقة / Pending', value: 23,  color: '#ca8a04' },
  { name: 'مرفوضة / Rejected', value: 4,  color: '#dc2626' },
]

const recentInvoices = [
  { id: 'INV-2024-0892', customer: 'شركة الأفق للتجارة', amount: 18500, vat: 2775, status: 'cleared', date: '2024-01-15' },
  { id: 'INV-2024-0891', customer: 'Al-Madar Trading Co.', amount: 7200, vat: 1080, status: 'pending', date: '2024-01-15' },
  { id: 'INV-2024-0890', customer: 'مجموعة النخيل', amount: 42000, vat: 6300, status: 'cleared', date: '2024-01-14' },
  { id: 'INV-2024-0889', customer: 'Saudi Retail Solutions', amount: 3500, vat: 525, status: 'draft', date: '2024-01-14' },
  { id: 'INV-2024-0888', customer: 'شركة الرياض للخدمات', amount: 12750, vat: 1912.5, status: 'cleared', date: '2024-01-13' },
]

const statusBadge = {
  cleared: 'badge badge-green',
  pending: 'badge badge-yellow',
  draft:   'badge badge-gray',
  rejected:'badge badge-red',
}

const statusLabel = {
  ar: { cleared: 'مُصفّاة', pending: 'معلّقة', draft: 'مسودة', rejected: 'مرفوضة' },
  en: { cleared: 'Cleared', pending: 'Pending', draft: 'Draft', rejected: 'Rejected' },
}

function KPICard({ icon: Icon, label, value, sub, trend, color = 'blue' }) {
  const colors = {
    blue:   { bg: 'bg-brand-500',  light: 'bg-brand-50',  text: 'text-brand-600' },
    green:  { bg: 'bg-green-500',  light: 'bg-green-50',  text: 'text-green-600' },
    orange: { bg: 'bg-orange-500', light: 'bg-orange-50', text: 'text-orange-600' },
    purple: { bg: 'bg-purple-500', light: 'bg-purple-50', text: 'text-purple-600' },
  }
  const c = colors[color]
  const isUp = trend > 0

  return (
    <div className="kpi-card card-hover">
      <div className={`absolute inset-0 ${c.light} opacity-0 hover:opacity-30 transition-opacity rounded-2xl`} />
      <div className="flex items-start justify-between mb-4">
        <div className={`w-11 h-11 rounded-xl ${c.light} ${c.text} flex items-center justify-center`}>
          <Icon size={22} />
        </div>
        <div className={`flex items-center gap-1 text-sm font-medium ${isUp ? 'text-green-600' : 'text-red-500'}`}>
          {isUp ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
          <span className="num">{Math.abs(trend)}%</span>
        </div>
      </div>
      <div className="text-2xl font-bold text-slate-900 mb-0.5 num">{value}</div>
      <div className="text-sm font-medium text-slate-700 mb-1">{label}</div>
      <div className="text-xs text-slate-400">{sub}</div>
    </div>
  )
}

export default function DashboardPage() {
  const { t, lang } = useLang()
  const [period, setPeriod] = useState('month')

  const fmt = (n) => new Intl.NumberFormat(lang === 'ar' ? 'ar-SA' : 'en-SA', {
    style: 'currency', currency: 'SAR', maximumFractionDigits: 0
  }).format(n)

  return (
    <div className="space-y-6">
      {/* Page header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('dashboard')}</h1>
          <p className="text-slate-500 text-sm mt-0.5">
            {lang === 'ar'
              ? 'آخر تحديث: اليوم، 10:42 ص'
              : 'Last updated: Today, 10:42 AM'}
          </p>
        </div>
        <div className="flex gap-2">
          {['week','month','quarter'].map(p => (
            <button
              key={p}
              onClick={() => setPeriod(p)}
              className={`px-3 py-1.5 rounded-lg text-sm font-medium transition-colors ${
                period === p
                  ? 'bg-brand-600 text-white'
                  : 'bg-white text-slate-600 border border-slate-200 hover:bg-slate-50'
              }`}
            >
              {lang === 'ar'
                ? { week: 'أسبوع', month: 'شهر', quarter: 'ربع سنة' }[p]
                : { week: 'Week', month: 'Month', quarter: 'Quarter' }[p]
              }
            </button>
          ))}
        </div>
      </div>

      {/* KPI row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <KPICard icon={DollarSign} color="blue"
          label={t('totalRevenue')} value={fmt(234000)} trend={12.4}
          sub={t('thisMonth')} />
        <KPICard icon={Receipt} color="orange"
          label={t('vatDue')} value={fmt(35100)} trend={12.4}
          sub={lang === 'ar' ? 'مستحق يونيو' : 'Due Jun 30'} />
        <KPICard icon={Users} color="green"
          label={t('activeEmployees')} value="142" trend={3.1}
          sub={lang === 'ar' ? '68% سعودة' : '68% Saudization'} />
        <KPICard icon={ShoppingBag} color="purple"
          label={t('todaySales')} value={fmt(18450)} trend={-2.3}
          sub={lang === 'ar' ? '47 معاملة' : '47 transactions'} />
      </div>

      {/* Charts row */}
      <div className="grid lg:grid-cols-3 gap-4">

        {/* Revenue chart */}
        <div className="card p-5 lg:col-span-2">
          <div className="flex items-center justify-between mb-5">
            <div>
              <h3 className="font-semibold text-slate-900">
                {lang === 'ar' ? 'الإيرادات وضريبة القيمة المضافة' : 'Revenue & VAT'}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {lang === 'ar' ? 'آخر 7 أشهر' : 'Last 7 months'}
              </p>
            </div>
            <BarChart2 size={18} className="text-slate-300" />
          </div>
          <ResponsiveContainer width="100%" height={220}>
            <AreaChart data={revenueData} margin={{ top: 0, right: 0, left: -20, bottom: 0 }}>
              <defs>
                <linearGradient id="revGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#026fc2" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#026fc2" stopOpacity={0} />
                </linearGradient>
                <linearGradient id="vatGrad" x1="0" y1="0" x2="0" y2="1">
                  <stop offset="0%" stopColor="#d98c2c" stopOpacity={0.15} />
                  <stop offset="100%" stopColor="#d98c2c" stopOpacity={0} />
                </linearGradient>
              </defs>
              <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
              <XAxis dataKey="month" tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
              <YAxis tick={{ fontSize: 11, fill: '#94a3b8' }} axisLine={false} tickLine={false}
                tickFormatter={v => `${(v/1000).toFixed(0)}k`} />
              <Tooltip
                contentStyle={{ borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 12 }}
                formatter={(v, name) => [fmt(v), name === 'revenue'
                  ? (lang === 'ar' ? 'الإيرادات' : 'Revenue')
                  : (lang === 'ar' ? 'ضريبة القيمة المضافة' : 'VAT')]}
              />
              <Area type="monotone" dataKey="revenue" stroke="#026fc2" strokeWidth={2} fill="url(#revGrad)" />
              <Area type="monotone" dataKey="vat" stroke="#d98c2c" strokeWidth={2} fill="url(#vatGrad)" />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* ZATCA status donut */}
        <div className="card p-5">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h3 className="font-semibold text-slate-900">
                {lang === 'ar' ? 'حالة فواتير ZATCA' : 'ZATCA Invoice Status'}
              </h3>
              <p className="text-xs text-slate-400 mt-0.5">
                {lang === 'ar' ? '874 فاتورة هذا الشهر' : '874 invoices this month'}
              </p>
            </div>
            <FileCheck size={18} className="text-slate-300" />
          </div>
          <ResponsiveContainer width="100%" height={160}>
            <PieChart>
              <Pie data={zatcaStatus} cx="50%" cy="50%" innerRadius={50} outerRadius={72}
                dataKey="value" paddingAngle={3} strokeWidth={0}>
                {zatcaStatus.map((entry, i) => (
                  <Cell key={i} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip contentStyle={{ borderRadius: 10, border: '1px solid #e2e8f0', fontSize: 12 }} />
            </PieChart>
          </ResponsiveContainer>
          <div className="space-y-2 mt-2">
            {zatcaStatus.map((s, i) => (
              <div key={i} className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full" style={{ background: s.color }} />
                  <span className="text-slate-600 text-xs">{s.name}</span>
                </div>
                <span className="font-semibold text-slate-800 num">{s.value}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Quick actions */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: t('newInvoice'),  icon: Plus,       color: 'text-brand-600 bg-brand-50', path: '/app/invoicing/new' },
          { label: t('runPayroll'),  icon: Users,      color: 'text-green-600 bg-green-50', path: '/app/hr/payroll' },
          { label: t('vatReturn'),   icon: Calculator, color: 'text-orange-600 bg-orange-50', path: '/app/accounting/vat' },
          { label: t('inventory'),   icon: ShoppingBag, color: 'text-purple-600 bg-purple-50', path: '/app/inventory' },
        ].map(({ label, icon: Icon, color }) => (
          <button key={label}
            className="card card-hover p-4 flex items-center gap-3 text-start hover:cursor-pointer">
            <div className={`w-10 h-10 rounded-xl ${color} flex items-center justify-center flex-shrink-0`}>
              <Icon size={18} />
            </div>
            <span className="font-medium text-slate-700 text-sm">{label}</span>
            <ArrowUpRight size={14} className="ms-auto text-slate-300" />
          </button>
        ))}
      </div>

      {/* Recent invoices */}
      <div className="card">
        <div className="flex items-center justify-between p-5 border-b border-slate-100">
          <h3 className="font-semibold text-slate-900">{t('recentInvoices')}</h3>
          <button className="text-sm text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1">
            {lang === 'ar' ? 'عرض الكل' : 'View all'}
            <ArrowUpRight size={14} />
          </button>
        </div>
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t('invoiceNumber')}</th>
                <th>{t('customer')}</th>
                <th>{t('amount')}</th>
                <th>{t('vat')}</th>
                <th>{t('status')}</th>
                <th>{t('issueDate')}</th>
              </tr>
            </thead>
            <tbody>
              {recentInvoices.map(inv => (
                <tr key={inv.id}>
                  <td className="font-mono text-brand-600 text-xs num">{inv.id}</td>
                  <td className="font-medium">{inv.customer}</td>
                  <td className="num">{fmt(inv.amount)}</td>
                  <td className="num text-slate-500">{fmt(inv.vat)}</td>
                  <td>
                    <span className={statusBadge[inv.status]}>
                      {statusLabel[lang][inv.status]}
                    </span>
                  </td>
                  <td className="text-slate-500 num">{inv.date}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* ZATCA compliance alert */}
      <div className="rounded-xl border border-amber-200 bg-amber-50 p-4 flex items-start gap-3">
        <AlertCircle size={18} className="text-amber-600 mt-0.5 flex-shrink-0" />
        <div>
          <p className="text-sm font-medium text-amber-800">
            {lang === 'ar'
              ? 'تذكير: الموعد النهائي لتسجيل ZATCA المرحلة الثانية — 30 يونيو 2026'
              : 'Reminder: ZATCA Phase 2 registration deadline — June 30, 2026'}
          </p>
          <p className="text-xs text-amber-600 mt-0.5">
            {lang === 'ar'
              ? 'تأكد من استكمال شهادة CSID لجميع نقاط البيع والأجهزة الطرفية'
              : 'Ensure CSID certification is complete for all POS terminals and devices'}
          </p>
        </div>
      </div>
    </div>
  )
}
