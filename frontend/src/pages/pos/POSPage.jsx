import { useState, useEffect } from 'react'
import { Plus, Minus, Trash2, Search, CreditCard, Banknote, Smartphone, Check, ShoppingBag, Loader2, Printer } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import { posAPI, zatcaAPI } from '../../services/api'
import toast from 'react-hot-toast'

const PRODUCTS = [
  { id: 1, code: 'P001', nameAr: 'قهوة عربية', nameEn: 'Arabic Coffee', price: 15, category: 'beverages' },
  { id: 2, code: 'P002', nameAr: 'شاي أخضر', nameEn: 'Green Tea', price: 12, category: 'beverages' },
  { id: 3, code: 'P003', nameAr: 'كابتشينو', nameEn: 'Cappuccino', price: 20, category: 'beverages' },
  { id: 4, code: 'P004', nameAr: 'تمر ممتاز', nameEn: 'Premium Dates', price: 45, category: 'food' },
  { id: 5, code: 'P005', nameAr: 'معمول', nameEn: "Ma'amoul", price: 35, category: 'food' },
  { id: 6, code: 'P006', nameAr: 'زعفران أصلي', nameEn: 'Saffron', price: 120, category: 'spices' },
  { id: 7, code: 'P007', nameAr: 'هيل مطحون', nameEn: 'Ground Cardamom', price: 25, category: 'spices' },
  { id: 8, code: 'P008', nameAr: 'عطر عود', nameEn: 'Oud Perfume', price: 350, category: 'fragrance' },
  { id: 9, code: 'P009', nameAr: 'بخور فاخر', nameEn: 'Luxury Incense', price: 85, category: 'fragrance' },
  { id: 10, code: 'P010', nameAr: 'ماء زمزم', nameEn: 'Zamzam Water', price: 18, category: 'beverages' },
  { id: 11, code: 'P011', nameAr: 'حلويات شرقية', nameEn: 'Oriental Sweets', price: 60, category: 'food' },
  { id: 12, code: 'P012', nameAr: 'خبز تنور', nameEn: 'Tandoor Bread', price: 8, category: 'food' },
]

const CATEGORIES = [
  { id: 'all', labelAr: 'الكل', labelEn: 'All' },
  { id: 'beverages', labelAr: 'مشروبات', labelEn: 'Beverages' },
  { id: 'food', labelAr: 'طعام', labelEn: 'Food' },
  { id: 'spices', labelAr: 'توابل', labelEn: 'Spices' },
  { id: 'fragrance', labelAr: 'عطور', labelEn: 'Fragrance' },
]

function PaymentModal({ total, onClose, onComplete, lang, loading }) {
  const [method, setMethod] = useState('mada')
  const [cash, setCash] = useState('')
  const change = method === 'cash' ? Math.max(0, (parseFloat(cash) || 0) - total) : 0
  const canPay = method !== 'cash' || (parseFloat(cash) || 0) >= total
  const fmt = (n) => n.toFixed(2)

  const methods = [
    { id: 'mada', icon: CreditCard, labelAr: 'مدى', labelEn: 'Mada' },
    { id: 'cash', icon: Banknote, labelAr: 'نقدي', labelEn: 'Cash' },
    { id: 'stc_pay', icon: Smartphone, labelAr: 'STC Pay', labelEn: 'STC Pay' },
    { id: 'credit_card', icon: CreditCard, labelAr: 'بطاقة ائتمان', labelEn: 'Credit Card' },
    { id: 'apple_pay', icon: Smartphone, labelAr: 'Apple Pay', labelEn: 'Apple Pay' },
  ]

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-md p-6 space-y-4" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold text-center">{lang === 'ar' ? 'الدفع' : 'Payment'}</h2>
        <div className="text-center text-3xl font-bold text-brand-600 num">{fmt(total)} SAR</div>

        <div className="grid grid-cols-2 gap-2">
          {methods.map(m => (
            <button key={m.id} onClick={() => setMethod(m.id)}
              className={`flex items-center gap-2 p-3 rounded-xl text-sm font-medium transition-all ${method === m.id ? 'bg-brand-500 text-white' : 'bg-slate-100 hover:bg-slate-200'}`}>
              <m.icon size={18} /> {lang === 'ar' ? m.labelAr : m.labelEn}
            </button>
          ))}
        </div>

        {method === 'cash' && (
          <div>
            <label className="text-sm text-slate-600 mb-1 block">{lang === 'ar' ? 'المبلغ المدفوع' : 'Amount Paid'}</label>
            <input className="input text-center text-xl num" type="number" value={cash} onChange={e => setCash(e.target.value)} dir="ltr" autoFocus />
            {change > 0 && <div className="text-center mt-2 text-green-600 font-semibold">{lang === 'ar' ? 'الباقي:' : 'Change:'} {fmt(change)} SAR</div>}
          </div>
        )}

        <div className="flex gap-3">
          <button className="btn btn-secondary flex-1" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
          <button disabled={!canPay || loading} onClick={() => onComplete(method, parseFloat(cash) || total)}
            className="btn btn-primary flex-1 flex items-center justify-center gap-2">
            {loading ? <Loader2 size={18} className="animate-spin" /> : <Check size={18} />}
            {lang === 'ar' ? 'تأكيد الدفع' : 'Confirm Payment'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function POSPage() {
  const { lang } = useLang()
  const { api } = useAuth()
  const [cart, setCart] = useState([])
  const [category, setCategory] = useState('all')
  const [search, setSearch] = useState('')
  const [showPayment, setShowPayment] = useState(false)
  const [loading, setLoading] = useState(false)
  const [session, setSession] = useState(null)
  const [recentSales, setRecentSales] = useState([])
  const [receipt, setReceipt] = useState(null)

  const fmt = (n) => n.toFixed(2)

  // Filter products
  const filtered = PRODUCTS.filter(p => {
    if (category !== 'all' && p.category !== category) return false
    if (search && !p.nameAr.includes(search) && !p.nameEn.toLowerCase().includes(search.toLowerCase())) return false
    return true
  })

  // Cart operations
  const addToCart = (product) => {
    setCart(c => {
      const idx = c.findIndex(i => i.product.id === product.id)
      if (idx >= 0) {
        const updated = [...c]
        updated[idx] = { ...updated[idx], qty: updated[idx].qty + 1 }
        return updated
      }
      return [...c, { product, qty: 1 }]
    })
  }

  const updateQty = (productId, delta) => {
    setCart(c => c.map(i =>
      i.product.id === productId ? { ...i, qty: Math.max(0, i.qty + delta) } : i
    ).filter(i => i.qty > 0))
  }

  const clearCart = () => setCart([])

  // Totals
  const subtotal = cart.reduce((s, i) => s + i.product.price * i.qty, 0)
  const vat = subtotal * 0.15
  const total = subtotal + vat

  // Complete sale — sends to API
  const completeSale = async (paymentMethod, amountPaid) => {
    setLoading(true)
    try {
      // 1. Ensure branch + terminal exist (auto-setup)
      let terminalId = session?.terminal
      if (!terminalId) {
        try {
          const setupRes = await posAPI.setupDefault(api)
          terminalId = setupRes.data.terminal_id
        } catch (err) {
          console.log('Terminal setup skipped:', err)
        }
      }

      // 2. Ensure we have a session
      let sessionId = session?.id
      if (!sessionId && terminalId) {
        try {
          const sessRes = await posAPI.createSession(api, {
            terminal: terminalId,
            opening_cash: '0.00',
          })
          setSession(sessRes.data)
          sessionId = sessRes.data.id
        } catch (err) {
          console.log('Session creation skipped:', err)
        }
      }

      // 3. Create ZATCA simplified invoice (B2C) — this also auto-creates GL entries
      const invoiceData = {
        invoice_type: '386',
        issue_date: new Date().toISOString().split('T')[0],
        issue_time: new Date().toTimeString().split(' ')[0],
        subtotal: subtotal.toFixed(2),
        taxable_amount: subtotal.toFixed(2),
        vat_amount: vat.toFixed(2),
        total_amount: total.toFixed(2),
        lines: cart.map(item => ({
          description_ar: item.product.nameAr,
          description_en: item.product.nameEn,
          quantity: item.qty.toString(),
          unit_price: item.product.price.toFixed(4),
          line_total: (item.product.price * item.qty).toFixed(2),
          vat_rate: '15.00',
          vat_amount: (item.product.price * item.qty * 0.15).toFixed(2),
        })),
      }

      const invRes = await zatcaAPI.createInvoice(api, invoiceData)

      // 4. Create POS transaction linked to session
      if (sessionId) {
        try {
          await posAPI.createTransaction(api, {
            session: sessionId,
            payment_method: paymentMethod,
            subtotal: subtotal.toFixed(2),
            vat_amount: vat.toFixed(2),
            total_amount: total.toFixed(2),
            amount_paid: amountPaid.toFixed(2),
            change_due: Math.max(0, amountPaid - total).toFixed(2),
            transacted_at: new Date().toISOString(),
            lines: cart.map(item => ({
              product_code: item.product.code,
              product_name_ar: item.product.nameAr,
              product_name_en: item.product.nameEn,
              quantity: item.qty.toString(),
              unit_price: item.product.price.toFixed(4),
              discount_amount: '0.00',
              vat_rate: '15.00',
              vat_amount: (item.product.price * item.qty * 0.15).toFixed(2),
              line_total: (item.product.price * item.qty).toFixed(2),
            })),
          })
        } catch (err) {
          console.log('POS transaction save error:', err?.response?.data || err)
        }
      }

      // Success
      const receiptData = {
        invoice_number: invRes.data.invoice_number,
        date: new Date().toLocaleDateString(lang === 'ar' ? 'ar-SA' : 'en-SA'),
        time: new Date().toLocaleTimeString(lang === 'ar' ? 'ar-SA' : 'en-SA'),
        items: cart.map(i => ({ name: lang === 'ar' ? i.product.nameAr : i.product.nameEn, qty: i.qty, price: i.product.price, total: i.product.price * i.qty })),
        subtotal,
        vat,
        total,
        paymentMethod,
        amountPaid,
        change: Math.max(0, amountPaid - total),
        qr: invRes.data.qr_code_tlv || '',
      }

      setReceipt(receiptData)

      setRecentSales(prev => [{
        id: invRes.data.invoice_number,
        total,
        method: paymentMethod,
        time: new Date().toLocaleTimeString(lang === 'ar' ? 'ar-SA' : 'en-SA'),
        items: cart.length,
      }, ...prev].slice(0, 10))

      toast.success(lang === 'ar'
        ? `✓ تم البيع — فاتورة ${invRes.data.invoice_number}`
        : `✓ Sale complete — Invoice ${invRes.data.invoice_number}`)

      clearCart()
      setShowPayment(false)

    } catch (err) {
      console.error('Sale error:', err)
      toast.error(err.response?.data?.detail || JSON.stringify(err.response?.data) || (lang === 'ar' ? 'خطأ في إتمام البيع' : 'Error completing sale'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex gap-4 h-[calc(100vh-120px)]">
      {/* Left: Products */}
      <div className="flex-1 flex flex-col min-w-0">
        <div className="flex gap-2 mb-3">
          <div className="relative flex-1">
            <Search size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input className="input ps-10 py-2" placeholder={lang === 'ar' ? 'بحث عن منتج...' : 'Search products...'} value={search} onChange={e => setSearch(e.target.value)} />
          </div>
        </div>

        <div className="flex gap-1.5 mb-3 overflow-x-auto pb-1">
          {CATEGORIES.map(c => (
            <button key={c.id} onClick={() => setCategory(c.id)}
              className={`px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap transition-all ${category === c.id ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
              {lang === 'ar' ? c.labelAr : c.labelEn}
            </button>
          ))}
        </div>

        <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-2 overflow-y-auto flex-1">
          {filtered.map(p => (
            <button key={p.id} onClick={() => addToCart(p)}
              className="bg-white rounded-xl p-3 text-start border border-slate-100 hover:border-brand-300 hover:shadow-md transition-all group">
              <div className="w-full aspect-square bg-slate-50 rounded-lg mb-2 flex items-center justify-center">
                <ShoppingBag size={24} className="text-slate-300 group-hover:text-brand-400 transition-colors" />
              </div>
              <div className="font-medium text-sm truncate">{lang === 'ar' ? p.nameAr : p.nameEn}</div>
              <div className="text-brand-600 font-bold num text-sm mt-0.5">{p.price} SAR</div>
            </button>
          ))}
        </div>
      </div>

      {/* Right: Cart */}
      <div className="w-80 lg:w-96 bg-white rounded-2xl shadow-sm border border-slate-100 flex flex-col">
        <div className="p-4 border-b border-slate-100">
          <div className="flex items-center justify-between">
            <h2 className="font-bold text-lg">{lang === 'ar' ? 'السلة' : 'Cart'}</h2>
            {cart.length > 0 && (
              <button onClick={clearCart} className="text-xs text-red-500 hover:text-red-700">
                {lang === 'ar' ? 'مسح' : 'Clear'}
              </button>
            )}
          </div>
          <div className="text-xs text-slate-400 mt-0.5">{cart.reduce((s, i) => s + i.qty, 0)} {lang === 'ar' ? 'عنصر' : 'items'}</div>
        </div>

        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {cart.length === 0 ? (
            <div className="text-center py-12 text-slate-300">
              <ShoppingBag size={36} className="mx-auto mb-2" />
              <p className="text-sm">{lang === 'ar' ? 'السلة فارغة' : 'Cart is empty'}</p>
            </div>
          ) : cart.map(item => (
            <div key={item.product.id} className="flex items-center gap-2 bg-slate-50 rounded-lg p-2">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium truncate">{lang === 'ar' ? item.product.nameAr : item.product.nameEn}</div>
                <div className="text-xs text-slate-500 num">{item.product.price} × {item.qty} = {fmt(item.product.price * item.qty)}</div>
              </div>
              <div className="flex items-center gap-1">
                <button onClick={() => updateQty(item.product.id, -1)} className="w-7 h-7 rounded-md bg-white border flex items-center justify-center hover:bg-slate-100">
                  <Minus size={14} />
                </button>
                <span className="w-8 text-center text-sm font-semibold num">{item.qty}</span>
                <button onClick={() => updateQty(item.product.id, 1)} className="w-7 h-7 rounded-md bg-white border flex items-center justify-center hover:bg-slate-100">
                  <Plus size={14} />
                </button>
                <button onClick={() => updateQty(item.product.id, -item.qty)} className="w-7 h-7 rounded-md bg-red-50 text-red-500 flex items-center justify-center hover:bg-red-100 ms-1">
                  <Trash2 size={14} />
                </button>
              </div>
            </div>
          ))}
        </div>

        {/* Totals */}
        <div className="p-4 border-t border-slate-100 space-y-2">
          <div className="flex justify-between text-sm"><span className="text-slate-500">{lang === 'ar' ? 'المجموع' : 'Subtotal'}</span><span className="num">{fmt(subtotal)} SAR</span></div>
          <div className="flex justify-between text-sm"><span className="text-slate-500">{lang === 'ar' ? 'ضريبة 15%' : 'VAT 15%'}</span><span className="num">{fmt(vat)} SAR</span></div>
          <div className="flex justify-between text-lg font-bold border-t pt-2"><span>{lang === 'ar' ? 'الإجمالي' : 'Total'}</span><span className="num text-brand-600">{fmt(total)} SAR</span></div>

          <button disabled={cart.length === 0} onClick={() => setShowPayment(true)}
            className="btn btn-primary w-full py-3 text-base justify-center mt-2 disabled:opacity-50">
            {lang === 'ar' ? 'إتمام البيع' : 'Complete Sale'}
          </button>
        </div>

        {/* Recent Sales */}
        {recentSales.length > 0 && (
          <div className="p-3 border-t border-slate-100 max-h-32 overflow-y-auto">
            <div className="text-xs font-medium text-slate-400 mb-1">{lang === 'ar' ? 'مبيعات أخيرة' : 'Recent Sales'}</div>
            {recentSales.map((sale, i) => (
              <div key={i} className="flex justify-between text-xs py-1 border-b border-slate-50 last:border-0">
                <span className="text-slate-500">{sale.time} · {sale.method}</span>
                <span className="font-semibold num">{fmt(sale.total)} SAR</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {showPayment && (
        <PaymentModal
          total={total}
          onClose={() => setShowPayment(false)}
          onComplete={completeSale}
          lang={lang}
          loading={loading}
        />
      )}

      {receipt && (
        <ReceiptModal receipt={receipt} lang={lang} onClose={() => setReceipt(null)} />
      )}
    </div>
  )
}

function ReceiptModal({ receipt, lang, onClose }) {
  const fmt = (n) => n.toFixed(2)

  const handlePrint = () => {
    const el = document.getElementById('pos-receipt')
    const win = window.open('', '_blank', 'width=400,height=600')
    win.document.write(`
      <html><head><title>${receipt.invoice_number}</title>
      <style>
        body { font-family: 'Courier New', monospace; width: 300px; margin: 0 auto; padding: 20px; font-size: 12px; }
        .center { text-align: center; }
        .bold { font-weight: bold; }
        .line { border-top: 1px dashed #000; margin: 8px 0; }
        .row { display: flex; justify-content: space-between; }
        .qr { text-align: center; margin: 10px 0; }
        .qr img { width: 150px; height: 150px; }
        @media print { body { width: 100%; } }
      </style></head><body>
        ${el.innerHTML}
        <script>window.print(); window.close();</script>
      </body></html>
    `)
    win.document.close()
  }

  const payLabels = {
    cash: lang === 'ar' ? 'نقدي' : 'Cash',
    mada: 'Mada',
    stc_pay: 'STC Pay',
    credit_card: lang === 'ar' ? 'بطاقة ائتمان' : 'Credit Card',
    apple_pay: 'Apple Pay',
  }

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-sm p-0 overflow-hidden" onClick={e => e.stopPropagation()}>
        {/* Receipt Content */}
        <div id="pos-receipt" className="p-6 text-sm" style={{ fontFamily: "'Courier New', monospace" }}>
          <div className="text-center mb-3">
            <div className="text-lg font-bold">{lang === 'ar' ? 'نظام ERP' : 'ERP System'}</div>
            <div className="text-xs text-slate-500">{lang === 'ar' ? 'فاتورة ضريبية مبسطة' : 'Simplified Tax Invoice'}</div>
            <div className="text-xs text-slate-400">VAT: 300000000000003</div>
          </div>

          <div className="border-t border-dashed border-slate-300 my-2"></div>

          <div className="flex justify-between text-xs text-slate-500 mb-2">
            <span>{receipt.date}</span>
            <span>{receipt.time}</span>
          </div>

          <div className="text-xs font-bold mb-2 text-center">{receipt.invoice_number}</div>

          <div className="border-t border-dashed border-slate-300 my-2"></div>

          {/* Items */}
          <div className="space-y-1.5 mb-2">
            {receipt.items.map((item, i) => (
              <div key={i}>
                <div className="font-medium">{item.name}</div>
                <div className="flex justify-between text-slate-600">
                  <span>{item.qty} × {fmt(item.price)}</span>
                  <span>{fmt(item.total)} SAR</span>
                </div>
              </div>
            ))}
          </div>

          <div className="border-t border-dashed border-slate-300 my-2"></div>

          {/* Totals */}
          <div className="space-y-1">
            <div className="flex justify-between"><span>{lang === 'ar' ? 'المجموع' : 'Subtotal'}</span><span>{fmt(receipt.subtotal)} SAR</span></div>
            <div className="flex justify-between"><span>{lang === 'ar' ? 'ضريبة 15%' : 'VAT 15%'}</span><span>{fmt(receipt.vat)} SAR</span></div>
            <div className="border-t border-dashed border-slate-300 my-1"></div>
            <div className="flex justify-between font-bold text-base"><span>{lang === 'ar' ? 'الإجمالي' : 'TOTAL'}</span><span>{fmt(receipt.total)} SAR</span></div>
          </div>

          <div className="border-t border-dashed border-slate-300 my-2"></div>

          {/* Payment */}
          <div className="space-y-1 text-xs">
            <div className="flex justify-between"><span>{lang === 'ar' ? 'طريقة الدفع' : 'Payment'}</span><span>{payLabels[receipt.paymentMethod] || receipt.paymentMethod}</span></div>
            {receipt.paymentMethod === 'cash' && <>
              <div className="flex justify-between"><span>{lang === 'ar' ? 'المدفوع' : 'Paid'}</span><span>{fmt(receipt.amountPaid)} SAR</span></div>
              {receipt.change > 0 && <div className="flex justify-between font-bold"><span>{lang === 'ar' ? 'الباقي' : 'Change'}</span><span>{fmt(receipt.change)} SAR</span></div>}
            </>}
          </div>

          {/* QR Code */}
          {receipt.qr && (
            <div className="text-center mt-3">
              <img
                src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(receipt.qr)}`}
                alt="QR" className="w-28 h-28 mx-auto"
              />
              <div className="text-[10px] text-slate-400 mt-1">ZATCA QR</div>
            </div>
          )}

          <div className="text-center text-xs text-slate-400 mt-3">
            {lang === 'ar' ? 'شكراً لزيارتكم' : 'Thank you for your visit'}
          </div>
        </div>

        {/* Buttons */}
        <div className="flex gap-2 p-4 border-t bg-slate-50">
          <button onClick={onClose} className="btn btn-secondary flex-1">{lang === 'ar' ? 'إغلاق' : 'Close'}</button>
          <button onClick={handlePrint} className="btn btn-primary flex-1 flex items-center justify-center gap-2">
            <Printer size={16} /> {lang === 'ar' ? 'طباعة' : 'Print'}
          </button>
        </div>
      </div>
    </div>
  )
}
