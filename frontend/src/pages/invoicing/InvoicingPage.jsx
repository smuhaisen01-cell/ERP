import { useState } from 'react'
import { Plus, Search, Filter, Download, Eye, Send, FileText, CheckCircle2, Clock, XCircle, ChevronDown } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'

const INVOICES = [
  { id: 'INV-2024-0892', customer: 'شركة الأفق للتجارة', customerEn: 'Al-Ufuq Trading Co.', vat: '300012345678903', amount: 18500, vatAmt: 2775, total: 21275, type: 'B2B', status: 'cleared', date: '2024-01-15', due: '2024-02-14' },
  { id: 'INV-2024-0891', customer: 'رياض للتجزئة', customerEn: 'Riyadh Retail', vat: '', amount: 340, vatAmt: 51, total: 391, type: 'B2C', status: 'reported', date: '2024-01-15', due: '2024-01-15' },
  { id: 'INV-2024-0890', customer: 'مجموعة النخيل', customerEn: 'Al-Nakheel Group', vat: '300098765432109', amount: 42000, vatAmt: 6300, total: 48300, type: 'B2B', status: 'cleared', date: '2024-01-14', due: '2024-02-13' },
  { id: 'INV-2024-0889', customer: 'Saudi Retail Solutions', customerEn: 'Saudi Retail Solutions', vat: '', amount: 3500, vatAmt: 525, total: 4025, type: 'B2C', status: 'draft', date: '2024-01-14', due: '2024-01-14' },
  { id: 'INV-2024-0888', customer: 'شركة الرياض للخدمات', customerEn: 'Riyadh Services Co.', vat: '300055544433301', amount: 12750, vatAmt: 1912, total: 14662, type: 'B2B', status: 'pending_clearance', date: '2024-01-13', due: '2024-02-12' },
  { id: 'INV-2024-0887', customer: 'النور للاستشارات', customerEn: 'Al-Noor Consulting', vat: '300011122233301', amount: 8900, vatAmt: 1335, total: 10235, type: 'B2B', status: 'rejected', date: '2024-01-12', due: '2024-02-11' },
]

const STATUS_CONFIG = {
  cleared:            { badge: 'badge-green',  labelAr: 'مُصفّاة',          labelEn: 'Cleared',           icon: CheckCircle2 },
  reported:           { badge: 'badge-blue',   labelAr: 'مُبلَّغة',          labelEn: 'Reported',          icon: Send },
  pending_clearance:  { badge: 'badge-yellow', labelAr: 'في انتظار التصفية', labelEn: 'Pending Clearance', icon: Clock },
  draft:              { badge: 'badge-gray',   labelAr: 'مسودة',             labelEn: 'Draft',             icon: FileText },
  rejected:           { badge: 'badge-red',    labelAr: 'مرفوضة',            labelEn: 'Rejected',          icon: XCircle },
}

function NewInvoiceModal({ onClose, lang, t }) {
  const [lines, setLines] = useState([{ desc: '', qty: 1, price: 0 }])
  const [type, setType] = useState('B2B')

  const addLine = () => setLines(l => [...l, { desc: '', qty: 1, price: 0 }])
  const subtotal = lines.reduce((s, l) => s + (l.qty * l.price), 0)
  const vat = subtotal * 0.15
  const total = subtotal + vat

  const fmt = n => new Intl.NumberFormat('en-SA', { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n)

  return (
    <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto shadow-2xl">
        <div className="p-6 border-b border-slate-100 flex items-center justify-between sticky top-0 bg-white z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {lang === 'ar' ? 'فاتورة ضريبية جديدة' : 'New Tax Invoice'}
            </h2>
            <p className="text-xs text-slate-400 mt-0.5">ZATCA Phase 2 — UBL 2.1</p>
          </div>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl font-light">✕</button>
        </div>

        <div className="p-6 space-y-5">
          {/* Invoice type */}
          <div className="flex gap-2">
            {['B2B', 'B2C'].map(t => (
              <button key={t} onClick={() => setType(t)}
                className={`flex-1 py-2.5 rounded-xl border-2 text-sm font-semibold transition-all ${
                  type === t
                    ? 'border-brand-600 bg-brand-50 text-brand-700'
                    : 'border-slate-200 text-slate-500 hover:border-slate-300'
                }`}>
                {t} — {t === 'B2B'
                  ? (lang === 'ar' ? 'فاتورة ضريبية (يتطلب تصفية)' : 'Tax Invoice (requires clearance)')
                  : (lang === 'ar' ? 'فاتورة مبسّطة (إبلاغ خلال 24 ساعة)' : 'Simplified (report within 24h)')}
              </button>
            ))}
          </div>

          {/* Customer */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                {t('customer')} *
              </label>
              <input className="input" placeholder={lang === 'ar' ? 'اسم العميل' : 'Customer name'} />
            </div>
            {type === 'B2B' && (
              <div>
                <label className="block text-sm font-medium text-slate-700 mb-1.5">
                  {lang === 'ar' ? 'الرقم الضريبي للعميل *' : 'Customer VAT Number *'}
                </label>
                <input className="input" dir="ltr" placeholder="300XXXXXXXXXXX3" maxLength={15} />
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">{t('issueDate')}</label>
              <input type="date" className="input" defaultValue={new Date().toISOString().split('T')[0]} />
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">{t('dueDate')}</label>
              <input type="date" className="input" />
            </div>
          </div>

          {/* Line items */}
          <div>
            <div className="flex items-center justify-between mb-2">
              <label className="text-sm font-medium text-slate-700">
                {lang === 'ar' ? 'بنود الفاتورة' : 'Invoice Lines'}
              </label>
              <button onClick={addLine} className="text-xs text-brand-600 hover:text-brand-700 font-medium flex items-center gap-1">
                <Plus size={12} /> {lang === 'ar' ? 'إضافة بند' : 'Add line'}
              </button>
            </div>

            <div className="border border-slate-200 rounded-xl overflow-hidden">
              <table className="w-full text-sm">
                <thead>
                  <tr className="bg-slate-50">
                    <th className="text-start p-3 font-medium text-slate-500 text-xs">{lang === 'ar' ? 'الوصف' : 'Description'}</th>
                    <th className="text-center p-3 font-medium text-slate-500 text-xs w-16">{lang === 'ar' ? 'الكمية' : 'Qty'}</th>
                    <th className="text-end p-3 font-medium text-slate-500 text-xs w-28">{lang === 'ar' ? 'السعر' : 'Unit Price'}</th>
                    <th className="text-end p-3 font-medium text-slate-500 text-xs w-28">{lang === 'ar' ? 'الإجمالي' : 'Total'}</th>
                  </tr>
                </thead>
                <tbody>
                  {lines.map((line, i) => (
                    <tr key={i} className="border-t border-slate-100">
                      <td className="p-2">
                        <input className="w-full text-sm border-0 outline-none bg-transparent"
                          placeholder={lang === 'ar' ? 'وصف المنتج أو الخدمة' : 'Product/service description'}
                          value={line.desc}
                          onChange={e => setLines(ls => ls.map((l,j) => j===i ? {...l, desc: e.target.value} : l))} />
                      </td>
                      <td className="p-2">
                        <input type="number" min="1" className="w-full text-center text-sm border-0 outline-none bg-transparent num"
                          value={line.qty}
                          onChange={e => setLines(ls => ls.map((l,j) => j===i ? {...l, qty: +e.target.value} : l))} />
                      </td>
                      <td className="p-2">
                        <input type="number" min="0" step="0.01" className="w-full text-end text-sm border-0 outline-none bg-transparent num"
                          value={line.price}
                          onChange={e => setLines(ls => ls.map((l,j) => j===i ? {...l, price: +e.target.value} : l))} />
                      </td>
                      <td className="p-2 text-end text-sm font-medium num">{fmt(line.qty * line.price)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Totals */}
          <div className="bg-slate-50 rounded-xl p-4 space-y-2">
            {[
              [t('subtotal'), fmt(subtotal)],
              [`${lang === 'ar' ? 'ضريبة القيمة المضافة' : 'VAT'} (15%)`, fmt(vat)],
            ].map(([l, v]) => (
              <div key={l} className="flex justify-between text-sm">
                <span className="text-slate-500">{l}</span>
                <span className="font-medium num">{v} {t('sar')}</span>
              </div>
            ))}
            <div className="flex justify-between font-bold text-slate-900 pt-2 border-t border-slate-200">
              <span>{t('total')}</span>
              <span className="num">{fmt(total)} {t('sar')}</span>
            </div>
          </div>
        </div>

        <div className="px-6 pb-6 flex gap-3 justify-end">
          <button onClick={onClose} className="btn btn-ghost">{t('cancel')}</button>
          <button className="btn btn-ghost border border-slate-200">
            {lang === 'ar' ? 'حفظ كمسودة' : 'Save Draft'}
          </button>
          <button className="btn btn-primary">
            <Send size={15} />
            {type === 'B2B'
              ? (lang === 'ar' ? 'إرسال للتصفية' : 'Send for Clearance')
              : (lang === 'ar' ? 'إصدار وإبلاغ' : 'Issue & Report')}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function InvoicingPage() {
  const { t, lang } = useLang()
  const [showNew, setShowNew] = useState(false)
  const [search, setSearch] = useState('')
  const [filterStatus, setFilterStatus] = useState('all')

  const fmt = n => new Intl.NumberFormat('en-SA', { minimumFractionDigits: 2 }).format(n)

  const filtered = INVOICES.filter(inv => {
    const matchSearch = inv.id.includes(search) || inv.customer.toLowerCase().includes(search.toLowerCase()) || inv.customerEn.toLowerCase().includes(search.toLowerCase())
    const matchStatus = filterStatus === 'all' || inv.status === filterStatus
    return matchSearch && matchStatus
  })

  return (
    <div className="space-y-5">
      {showNew && <NewInvoiceModal onClose={() => setShowNew(false)} lang={lang} t={t} />}

      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{t('invoicing')}</h1>
          <p className="text-sm text-slate-500 mt-0.5">
            {lang === 'ar' ? 'الفوترة الإلكترونية — ZATCA المرحلة الثانية' : 'E-Invoicing — ZATCA Phase 2'}
          </p>
        </div>
        <button onClick={() => setShowNew(true)} className="btn btn-primary">
          <Plus size={16} /> {t('newInvoice')}
        </button>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {[
          { label: lang === 'ar' ? 'مُصفّاة' : 'Cleared',           value: '847', badge: 'badge-green' },
          { label: lang === 'ar' ? 'مُبلَّغة' : 'Reported',          value: '312', badge: 'badge-blue' },
          { label: lang === 'ar' ? 'في الانتظار' : 'Pending',        value: '23',  badge: 'badge-yellow' },
          { label: lang === 'ar' ? 'مرفوضة' : 'Rejected',           value: '4',   badge: 'badge-red' },
        ].map(s => (
          <div key={s.label} className="card p-4 flex items-center gap-3">
            <span className={`badge ${s.badge} text-base font-bold px-3 py-1`}>{s.value}</span>
            <span className="text-sm text-slate-600">{s.label}</span>
          </div>
        ))}
      </div>

      {/* Filters */}
      <div className="card p-4 flex flex-wrap gap-3 items-center">
        <div className="relative flex-1 min-w-[200px]">
          <Search size={15} className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400" />
          <input
            className="input ps-9 py-2 text-sm"
            placeholder={lang === 'ar' ? 'بحث في الفواتير...' : 'Search invoices...'}
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>
        <select className="input w-auto py-2 text-sm"
          value={filterStatus} onChange={e => setFilterStatus(e.target.value)}>
          <option value="all">{t('all')}</option>
          {Object.entries(STATUS_CONFIG).map(([k, v]) => (
            <option key={k} value={k}>{lang === 'ar' ? v.labelAr : v.labelEn}</option>
          ))}
        </select>
        <button className="btn btn-ghost border border-slate-200 text-sm py-2">
          <Download size={15} /> {t('export')}
        </button>
      </div>

      {/* Table */}
      <div className="card">
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>{t('invoiceNumber')}</th>
                <th>{t('customer')}</th>
                <th>
                  {lang === 'ar' ? 'النوع' : 'Type'}
                </th>
                <th>{t('amount')}</th>
                <th>{t('vat')}</th>
                <th>{t('total')}</th>
                <th>{t('status')}</th>
                <th>{t('issueDate')}</th>
                <th></th>
              </tr>
            </thead>
            <tbody>
              {filtered.map(inv => {
                const cfg = STATUS_CONFIG[inv.status]
                const StatusIcon = cfg.icon
                return (
                  <tr key={inv.id}>
                    <td>
                      <span className="font-mono text-xs text-brand-600 num">{inv.id}</span>
                    </td>
                    <td>
                      <div className="font-medium text-sm">{lang === 'ar' ? inv.customer : inv.customerEn}</div>
                      {inv.vat && <div className="text-xs text-slate-400 num">{inv.vat}</div>}
                    </td>
                    <td>
                      <span className={`badge ${inv.type === 'B2B' ? 'badge-blue' : 'badge-gray'}`}>
                        {inv.type}
                      </span>
                    </td>
                    <td className="num">{fmt(inv.amount)}</td>
                    <td className="num text-slate-500">{fmt(inv.vatAmt)}</td>
                    <td className="font-semibold num">{fmt(inv.total)}</td>
                    <td>
                      <span className={`badge ${cfg.badge} gap-1`}>
                        <StatusIcon size={11} />
                        {lang === 'ar' ? cfg.labelAr : cfg.labelEn}
                      </span>
                    </td>
                    <td className="text-slate-400 text-xs num">{inv.date}</td>
                    <td>
                      <button className="text-slate-400 hover:text-brand-600 p-1">
                        <Eye size={15} />
                      </button>
                    </td>
                  </tr>
                )
              })}
            </tbody>
          </table>
        </div>

        {filtered.length === 0 && (
          <div className="text-center py-12 text-slate-400">
            <FileText size={32} className="mx-auto mb-2 opacity-30" />
            <p>{t('noData')}</p>
          </div>
        )}
      </div>
    </div>
  )
}
