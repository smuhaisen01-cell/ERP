import { useState, useEffect } from 'react'
import { Plus, Minus, Trash2, Search, CreditCard, Banknote, Smartphone, Check, ShoppingBag, Loader2 } from 'lucide-react'
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
      // 1. Ensure we have a session (create one if not)
      let sessionId = session?.id
      if (!sessionId) {
        try {
          const sessRes = await posAPI.createSession(api, {
            terminal: 1,
            opening_cash: '0.00',
          })
          setSession(sessRes.data)
          sessionId = sessRes.data.id
        } catch (err) {
          // If terminal doesn't exist, create branch + terminal first
          try {
            await posAPI.getBranches(api) // check if any exist
          } catch {
            // Ignore — we'll create the transaction with just the invoice
          }
        }
      }

      // 2. Create ZATCA simplified invoice (B2C) directly
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

      // 3. Also create POS transaction if we have a session
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
          console.log('POS transaction save skipped:', err)
        }
      }

      // Success
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
    </div>
  )
}
