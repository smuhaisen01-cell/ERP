import { useState, useEffect } from 'react'
import { Plus, Search, Send, FileText, CheckCircle2, Clock, XCircle, Loader2, RefreshCw, Eye, QrCode } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import { zatcaAPI } from '../../services/api'
import toast from 'react-hot-toast'

const STATUS_CONFIG = {
  cleared:  { bg: 'bg-green-100', text: 'text-green-700', labelAr: 'مُصفّاة', labelEn: 'Cleared', icon: CheckCircle2 },
  reported: { bg: 'bg-blue-100',  text: 'text-blue-700',  labelAr: 'مُبلَّغة', labelEn: 'Reported', icon: Send },
  pending:  { bg: 'bg-yellow-100',text: 'text-yellow-700',labelAr: 'معلقة',    labelEn: 'Pending',  icon: Clock },
  error:    { bg: 'bg-red-100',   text: 'text-red-700',   labelAr: 'خطأ',      labelEn: 'Error',    icon: XCircle },
  draft:    { bg: 'bg-slate-100', text: 'text-slate-600',  labelAr: 'مسودة',    labelEn: 'Draft',    icon: FileText },
}

function NewInvoiceModal({ onClose, onSave, lang }) {
  const [type, setType] = useState('388')
  const [lines, setLines] = useState([{ description_ar: '', quantity: 1, unit_price: 0 }])
  const [buyer, setBuyer] = useState({ buyer_name_ar: '', buyer_vat_number: '' })

  const addLine = () => setLines(l => [...l, { description_ar: '', quantity: 1, unit_price: 0 }])
  const updateLine = (i, k, v) => setLines(l => l.map((line, idx) => idx === i ? { ...line, [k]: v } : line))

  const subtotal = lines.reduce((s, l) => s + (l.quantity * l.unit_price), 0)
  const vat = subtotal * 0.15
  const total = subtotal + vat

  const handleSave = () => {
    const data = {
      invoice_type: type,
      issue_date: new Date().toISOString().split('T')[0],
      issue_time: new Date().toTimeString().split(' ')[0],
      ...buyer,
      subtotal: subtotal.toFixed(2),
      taxable_amount: subtotal.toFixed(2),
      vat_amount: vat.toFixed(2),
      total_amount: total.toFixed(2),
      lines: lines.map(l => ({
        description_ar: l.description_ar,
        quantity: l.quantity,
        unit_price: l.unit_price,
        line_total: (l.quantity * l.unit_price).toFixed(2),
        vat_rate: '15.00',
        vat_amount: (l.quantity * l.unit_price * 0.15).toFixed(2),
      })),
    }
    onSave(data)
  }

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold">{lang === 'ar' ? 'فاتورة جديدة' : 'New Invoice'}</h2>

        <div className="flex gap-3">
          <button onClick={() => setType('388')} className={`flex-1 py-2 rounded-lg text-sm font-medium ${type === '388' ? 'bg-brand-500 text-white' : 'bg-slate-100'}`}>
            B2B {lang === 'ar' ? '(ضريبية)' : '(Standard)'}
          </button>
          <button onClick={() => setType('386')} className={`flex-1 py-2 rounded-lg text-sm font-medium ${type === '386' ? 'bg-brand-500 text-white' : 'bg-slate-100'}`}>
            B2C {lang === 'ar' ? '(مبسطة)' : '(Simplified)'}
          </button>
        </div>

        {type === '388' && (
          <div className="grid grid-cols-2 gap-3">
            <input className="input" placeholder={lang === 'ar' ? 'اسم المشتري' : 'Buyer name'} value={buyer.buyer_name_ar} onChange={e => setBuyer(b => ({ ...b, buyer_name_ar: e.target.value }))} />
            <input className="input" placeholder={lang === 'ar' ? 'رقم VAT المشتري' : 'Buyer VAT number'} value={buyer.buyer_vat_number} onChange={e => setBuyer(b => ({ ...b, buyer_vat_number: e.target.value }))} dir="ltr" />
          </div>
        )}

        <div className="space-y-2">
          <div className="text-sm font-medium text-slate-700">{lang === 'ar' ? 'بنود الفاتورة' : 'Invoice Lines'}</div>
          {lines.map((l, i) => (
            <div key={i} className="grid grid-cols-4 gap-2">
              <input className="input col-span-2" placeholder={lang === 'ar' ? 'الوصف' : 'Description'} value={l.description_ar} onChange={e => updateLine(i, 'description_ar', e.target.value)} />
              <input className="input" type="number" placeholder={lang === 'ar' ? 'الكمية' : 'Qty'} value={l.quantity} onChange={e => updateLine(i, 'quantity', parseFloat(e.target.value) || 0)} dir="ltr" />
              <input className="input" type="number" placeholder={lang === 'ar' ? 'السعر' : 'Price'} value={l.unit_price} onChange={e => updateLine(i, 'unit_price', parseFloat(e.target.value) || 0)} dir="ltr" />
            </div>
          ))}
          <button onClick={addLine} className="text-sm text-brand-600 hover:text-brand-700">+ {lang === 'ar' ? 'بند جديد' : 'Add line'}</button>
        </div>

        <div className="bg-slate-50 rounded-xl p-4 space-y-1 text-sm">
          <div className="flex justify-between"><span>{lang === 'ar' ? 'المجموع' : 'Subtotal'}</span><span className="num font-semibold">{subtotal.toFixed(2)} SAR</span></div>
          <div className="flex justify-between"><span>{lang === 'ar' ? 'ضريبة 15%' : 'VAT 15%'}</span><span className="num font-semibold">{vat.toFixed(2)} SAR</span></div>
          <div className="flex justify-between text-lg font-bold border-t pt-2"><span>{lang === 'ar' ? 'الإجمالي' : 'Total'}</span><span className="num">{total.toFixed(2)} SAR</span></div>
        </div>

        <div className="flex gap-3 justify-end">
          <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
          <button className="btn btn-primary" onClick={handleSave}>{lang === 'ar' ? 'إنشاء الفاتورة' : 'Create Invoice'}</button>
        </div>
      </div>
    </div>
  )
}

function InvoiceDetailModal({ invoice, onClose, lang, api }) {
  const [detail, setDetail] = useState(null)
  const [loading, setLoading] = useState(true)
  const fmt = (n) => parseFloat(n || 0).toFixed(2)

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await zatcaAPI.getInvoice(api, invoice.id)
        setDetail(res.data)
      } catch { setDetail(invoice) }
      finally { setLoading(false) }
    }
    fetch()
  }, [invoice.id])

  const inv = detail || invoice

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-2xl p-6 space-y-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        {loading ? (
          <div className="flex justify-center py-8"><Loader2 size={32} className="animate-spin text-brand-500" /></div>
        ) : (
          <>
            <div className="flex items-start justify-between">
              <div>
                <h2 className="text-xl font-bold">{inv.invoice_number}</h2>
                <div className="text-sm text-slate-500">{inv.issue_date} · {inv.hijri_date || ''}</div>
              </div>
              <span className={`text-xs px-3 py-1 rounded-full ${inv.invoice_type === '388' ? 'bg-purple-100 text-purple-700' : 'bg-teal-100 text-teal-700'}`}>
                {inv.invoice_type === '388' ? 'B2B' : 'B2C'}
              </span>
            </div>

            {inv.buyer_name_ar && (
              <div className="bg-slate-50 rounded-xl p-3">
                <div className="text-xs text-slate-500 mb-1">{lang === 'ar' ? 'المشتري' : 'Buyer'}</div>
                <div className="font-medium">{inv.buyer_name_ar}</div>
                {inv.buyer_vat_number && <div className="text-sm text-slate-500 num">{lang === 'ar' ? 'رقم VAT:' : 'VAT:'} {inv.buyer_vat_number}</div>}
              </div>
            )}

            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div className="bg-slate-50 rounded-xl p-3">
                <div className="text-xs text-slate-500">{lang === 'ar' ? 'المجموع' : 'Subtotal'}</div>
                <div className="font-bold num">{fmt(inv.subtotal)} SAR</div>
              </div>
              <div className="bg-slate-50 rounded-xl p-3">
                <div className="text-xs text-slate-500">{lang === 'ar' ? 'الضريبة' : 'VAT'}</div>
                <div className="font-bold num">{fmt(inv.vat_amount)} SAR</div>
              </div>
              <div className="bg-brand-50 rounded-xl p-3">
                <div className="text-xs text-brand-600">{lang === 'ar' ? 'الإجمالي' : 'Total'}</div>
                <div className="font-bold text-brand-700 num">{fmt(inv.total_amount)} SAR</div>
              </div>
              <div className="bg-slate-50 rounded-xl p-3">
                <div className="text-xs text-slate-500">ZATCA</div>
                <div className="font-bold">{inv.zatca_status}</div>
              </div>
            </div>

            {/* Invoice Lines */}
            {inv.lines && inv.lines.length > 0 && (
              <div>
                <h4 className="font-semibold mb-2">{lang === 'ar' ? 'بنود الفاتورة' : 'Invoice Lines'}</h4>
                <table className="w-full text-sm">
                  <thead><tr className="border-b">
                    <th className="text-start py-2">{lang === 'ar' ? 'الوصف' : 'Description'}</th>
                    <th className="text-start py-2">{lang === 'ar' ? 'الكمية' : 'Qty'}</th>
                    <th className="text-start py-2">{lang === 'ar' ? 'السعر' : 'Price'}</th>
                    <th className="text-start py-2">{lang === 'ar' ? 'الضريبة' : 'VAT'}</th>
                    <th className="text-start py-2">{lang === 'ar' ? 'المجموع' : 'Total'}</th>
                  </tr></thead>
                  <tbody>
                    {inv.lines.map((line, i) => (
                      <tr key={i} className="border-b border-slate-100">
                        <td className="py-2">{line.description_ar}</td>
                        <td className="py-2 num">{line.quantity}</td>
                        <td className="py-2 num">{fmt(line.unit_price)}</td>
                        <td className="py-2 num">{fmt(line.vat_amount)}</td>
                        <td className="py-2 num font-semibold">{fmt(line.line_total)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}

            {/* QR Code */}
            {inv.qr_code_tlv && (
              <div className="border rounded-xl p-4 text-center">
                <div className="flex items-center justify-center gap-2 mb-2">
                  <QrCode size={18} className="text-slate-500" />
                  <span className="text-sm font-medium text-slate-600">{lang === 'ar' ? 'رمز QR — ZATCA' : 'ZATCA QR Code'}</span>
                </div>
                <div className="bg-white p-4 rounded-lg inline-block border">
                  <img
                    src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(inv.qr_code_tlv)}`}
                    alt="ZATCA QR Code"
                    className="w-48 h-48 mx-auto"
                  />
                </div>
                <div className="text-xs text-slate-400 mt-2 break-all max-w-sm mx-auto" dir="ltr">{inv.qr_code_tlv.substring(0, 60)}...</div>
              </div>
            )}

            <div className="flex justify-end">
              <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إغلاق' : 'Close'}</button>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default function InvoicingPage() {
  const { lang } = useLang()
  const { api } = useAuth()
  const [loading, setLoading] = useState(true)
  const [invoices, setInvoices] = useState([])
  const [showNew, setShowNew] = useState(false)
  const [selectedInvoice, setSelectedInvoice] = useState(null)
  const [search, setSearch] = useState('')

  const fetchInvoices = async () => {
    setLoading(true)
    try {
      const res = await zatcaAPI.getInvoices(api)
      setInvoices(res.data.results || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchInvoices() }, [])

  const handleCreateInvoice = async (data) => {
    try {
      await zatcaAPI.createInvoice(api, data)
      toast.success(lang === 'ar' ? 'تم إنشاء الفاتورة' : 'Invoice created')
      setShowNew(false)
      fetchInvoices()
    } catch (err) {
      toast.error(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Error')
    }
  }

  const fmt = (n) => new Intl.NumberFormat(lang === 'ar' ? 'ar-SA' : 'en-SA').format(parseFloat(n))

  const filtered = invoices.filter(i =>
    i.invoice_number?.toLowerCase().includes(search.toLowerCase()) ||
    i.buyer_name_ar?.includes(search)
  )

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'الفوترة الإلكترونية' : 'E-Invoicing'}</h1>
          <p className="text-sm text-slate-500">{lang === 'ar' ? 'ZATCA المرحلة الثانية — فاتورة' : 'ZATCA Phase 2 — Fatoora'}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchInvoices} className="btn btn-secondary"><RefreshCw size={16} /></button>
          <button onClick={() => setShowNew(true)} className="btn btn-primary flex items-center gap-2">
            <Plus size={16} />{lang === 'ar' ? 'فاتورة جديدة' : 'New Invoice'}
          </button>
        </div>
      </div>

      <div className="relative">
        <Search size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400" />
        <input className="input ps-10" placeholder={lang === 'ar' ? 'بحث عن فاتورة...' : 'Search invoices...'} value={search} onChange={e => setSearch(e.target.value)} />
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={32} className="animate-spin text-brand-500" /></div>
      ) : (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-200">
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'رقم الفاتورة' : 'Invoice #'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'النوع' : 'Type'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'التاريخ' : 'Date'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'المشتري' : 'Buyer'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'المبلغ' : 'Amount'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">ZATCA</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">QR</th>
              </tr></thead>
              <tbody>
                {filtered.map(inv => {
                  const sc = STATUS_CONFIG[inv.zatca_status] || STATUS_CONFIG.pending
                  return (
                    <tr key={inv.id} className="border-b border-slate-100 hover:bg-slate-50 cursor-pointer" onClick={() => setSelectedInvoice(inv)}>
                      <td className="py-3 px-2 font-medium num">{inv.invoice_number}</td>
                      <td className="py-3 px-2"><span className={`text-xs px-2 py-0.5 rounded-full ${inv.invoice_type === '388' ? 'bg-purple-100 text-purple-700' : 'bg-teal-100 text-teal-700'}`}>{inv.invoice_type === '388' ? 'B2B' : 'B2C'}</span></td>
                      <td className="py-3 px-2 text-slate-600 num">{inv.issue_date}</td>
                      <td className="py-3 px-2">{inv.buyer_name_ar || '-'}</td>
                      <td className="py-3 px-2 font-semibold num">{fmt(inv.total_amount)} SAR</td>
                      <td className="py-3 px-2"><span className={`text-xs px-2 py-0.5 rounded-full ${sc.bg} ${sc.text}`}>{lang === 'ar' ? sc.labelAr : sc.labelEn}</span></td>
                      <td className="py-3 px-2">
                        <button onClick={(e) => { e.stopPropagation(); setSelectedInvoice(inv) }} className="text-slate-400 hover:text-brand-600">
                          <Eye size={16} />
                        </button>
                      </td>
                    </tr>
                  )
                })}
              </tbody>
            </table>
            {filtered.length === 0 && <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا توجد فواتير' : 'No invoices yet'}</p>}
          </div>
        </div>
      )}

      {showNew && <NewInvoiceModal onClose={() => setShowNew(false)} onSave={handleCreateInvoice} lang={lang} />}
      {selectedInvoice && <InvoiceDetailModal invoice={selectedInvoice} onClose={() => setSelectedInvoice(null)} lang={lang} api={api} />}
    </div>
  )
}
