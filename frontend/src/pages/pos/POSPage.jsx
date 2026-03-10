import { useState } from 'react'
import { Plus, Minus, Trash2, Search, CreditCard, Banknote, Smartphone, Printer, Check, ShoppingBag } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'

const PRODUCTS = [
  { id: 1, code: 'P001', nameAr: 'قهوة عربية', nameEn: 'Arabic Coffee', price: 15, category: 'beverages' },
  { id: 2, code: 'P002', nameAr: 'شاي أخضر', nameEn: 'Green Tea', price: 12, category: 'beverages' },
  { id: 3, code: 'P003', nameAr: 'كابتشينو', nameEn: 'Cappuccino', price: 20, category: 'beverages' },
  { id: 4, code: 'P004', nameAr: 'تمر ممتاز', nameEn: 'Premium Dates', price: 45, category: 'food' },
  { id: 5, code: 'P005', nameAr: 'معمول', nameEn: 'Ma\'amoul', price: 35, category: 'food' },
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

function PaymentModal({ total, onClose, onComplete, lang, t }) {
  const [method, setMethod] = useState('mada')
  const [cash, setCash] = useState('')
  const [done, setDone] = useState(false)

  const change = method === 'cash' ? (parseFloat(cash) || 0) - total : 0
  const fmt = n => n.toFixed(2)

  const handlePay = () => {
    setDone(true)
    setTimeout(() => { onComplete(); onClose() }, 2000)
  }

  if (done) return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center">
      <div className="bg-white rounded-3xl p-12 text-center shadow-2xl">
        <div className="w-20 h-20 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
          <Check size={40} className="text-green-600" />
        </div>
        <h2 className="text-2xl font-bold text-slate-900 mb-1">
          {lang === 'ar' ? 'تمت العملية!' : 'Payment Complete!'}
        </h2>
        <p className="text-slate-500">
          {lang === 'ar' ? 'جارٍ طباعة الإيصال...' : 'Printing receipt...'}
        </p>
      </div>
    </div>
  )

  return (
    <div className="fixed inset-0 bg-black/50 z-50 flex items-center justify-center p-4">
      <div className="bg-white rounded-2xl w-full max-w-md shadow-2xl">
        <div className="p-6 border-b border-slate-100 flex justify-between items-center">
          <h2 className="text-lg font-bold">{lang === 'ar' ? 'الدفع' : 'Payment'}</h2>
          <button onClick={onClose} className="text-slate-400 hover:text-slate-600 text-xl">✕</button>
        </div>
        <div className="p-6 space-y-5">
          <div className="text-center">
            <p className="text-slate-500 text-sm mb-1">{lang === 'ar' ? 'المبلغ المستحق' : 'Amount Due'}</p>
            <p className="text-4xl font-bold text-slate-900 num">{fmt(total)}</p>
            <p className="text-slate-400 text-sm">{t('sar')}</p>
          </div>

          {/* Payment methods */}
          <div className="grid grid-cols-3 gap-2">
            {[
              { id: 'mada',  icon: CreditCard,  labelAr: 'مدى',   labelEn: 'Mada' },
              { id: 'cash',  icon: Banknote,    labelAr: 'نقداً', labelEn: 'Cash' },
              { id: 'stcpay',icon: Smartphone,  labelAr: 'STC Pay', labelEn: 'STC Pay' },
            ].map(m => (
              <button key={m.id} onClick={() => setMethod(m.id)}
                className={`p-3 rounded-xl border-2 text-center transition-all ${
                  method === m.id
                    ? 'border-brand-600 bg-brand-50'
                    : 'border-slate-200 hover:border-slate-300'
                }`}>
                <m.icon size={20} className={`mx-auto mb-1 ${method === m.id ? 'text-brand-600' : 'text-slate-400'}`} />
                <span className={`text-xs font-medium ${method === m.id ? 'text-brand-700' : 'text-slate-500'}`}>
                  {lang === 'ar' ? m.labelAr : m.labelEn}
                </span>
              </button>
            ))}
          </div>

          {method === 'cash' && (
            <div>
              <label className="block text-sm font-medium text-slate-700 mb-1.5">
                {lang === 'ar' ? 'المبلغ المستلم' : 'Cash Received'}
              </label>
              <input type="number" className="input text-center text-xl font-bold num" dir="ltr"
                placeholder="0.00" value={cash} onChange={e => setCash(e.target.value)} />
              {parseFloat(cash) >= total && (
                <div className="mt-2 p-3 bg-green-50 rounded-lg text-center">
                  <span className="text-green-700 font-semibold text-sm">
                    {lang === 'ar' ? 'الباقي: ' : 'Change: '}
                    <span className="num">{fmt(change)} {t('sar')}</span>
                  </span>
                </div>
              )}
            </div>
          )}

          <button
            onClick={handlePay}
            disabled={method === 'cash' && parseFloat(cash) < total}
            className="btn btn-primary w-full justify-center py-4 text-lg disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Check size={20} />
            {lang === 'ar' ? 'تأكيد الدفع' : 'Confirm Payment'}
          </button>
        </div>
      </div>
    </div>
  )
}

export default function POSPage() {
  const { t, lang } = useLang()
  const [cart, setCart] = useState([])
  const [category, setCategory] = useState('all')
  const [search, setSearch] = useState('')
  const [showPayment, setShowPayment] = useState(false)

  const products = PRODUCTS.filter(p =>
    (category === 'all' || p.category === category) &&
    (search === '' || (lang === 'ar' ? p.nameAr : p.nameEn).toLowerCase().includes(search.toLowerCase()))
  )

  const addToCart = (product) => {
    setCart(c => {
      const ex = c.find(i => i.id === product.id)
      if (ex) return c.map(i => i.id === product.id ? { ...i, qty: i.qty + 1 } : i)
      return [...c, { ...product, qty: 1 }]
    })
  }

  const updateQty = (id, delta) => {
    setCart(c => c.map(i => i.id === id ? { ...i, qty: Math.max(0, i.qty + delta) } : i).filter(i => i.qty > 0))
  }

  const subtotal = cart.reduce((s, i) => s + i.price * i.qty, 0)
  const vat = subtotal * 0.15
  const total = subtotal + vat
  const fmt = n => n.toFixed(2)

  return (
    <div className="flex gap-4 h-[calc(100vh-120px)]" style={{ direction: 'ltr' }}>
      {showPayment && (
        <PaymentModal
          total={total}
          onClose={() => setShowPayment(false)}
          onComplete={() => setCart([])}
          lang={lang} t={t}
        />
      )}

      {/* ── Products panel ───────────────────────── */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Search + categories */}
        <div className="space-y-3 mb-4">
          <div className="relative">
            <Search size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input className="input ps-9 py-2.5"
              placeholder={lang === 'ar' ? 'بحث عن منتج...' : 'Search products...'}
              value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="flex gap-2 overflow-x-auto pb-1">
            {CATEGORIES.map(c => (
              <button key={c.id} onClick={() => setCategory(c.id)}
                className={`px-4 py-1.5 rounded-full text-sm font-medium whitespace-nowrap transition-all ${
                  category === c.id
                    ? 'bg-brand-600 text-white'
                    : 'bg-white border border-slate-200 text-slate-600 hover:border-brand-300'
                }`}>
                {lang === 'ar' ? c.labelAr : c.labelEn}
              </button>
            ))}
          </div>
        </div>

        {/* Product grid */}
        <div className="flex-1 overflow-y-auto">
          <div className="grid grid-cols-3 xl:grid-cols-4 gap-3">
            {products.map(p => (
              <button key={p.id} onClick={() => addToCart(p)}
                className="card card-hover p-3 text-start group active:scale-95 transition-transform">
                <div className="w-full aspect-square rounded-xl bg-slate-100 flex items-center justify-center mb-2 group-hover:bg-brand-50 transition-colors">
                  <ShoppingBag size={24} className="text-slate-300 group-hover:text-brand-400 transition-colors" />
                </div>
                <div className="font-medium text-xs text-slate-800 leading-tight mb-1">
                  {lang === 'ar' ? p.nameAr : p.nameEn}
                </div>
                <div className="text-brand-600 font-bold text-sm num">{fmt(p.price)}</div>
                <div className="text-slate-400 text-xs">{t('sar')}</div>
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* ── Cart panel ───────────────────────────── */}
      <div className="w-80 flex-shrink-0 flex flex-col card">
        <div className="p-4 border-b border-slate-100 flex items-center justify-between">
          <h3 className="font-bold text-slate-900">{t('cart')}</h3>
          {cart.length > 0 && (
            <button onClick={() => setCart([])} className="text-xs text-red-500 hover:text-red-700">
              {lang === 'ar' ? 'مسح الكل' : 'Clear all'}
            </button>
          )}
        </div>

        {/* Cart items */}
        <div className="flex-1 overflow-y-auto p-3 space-y-2">
          {cart.length === 0 ? (
            <div className="text-center py-12 text-slate-400">
              <ShoppingBag size={32} className="mx-auto mb-2 opacity-30" />
              <p className="text-sm">{lang === 'ar' ? 'السلة فارغة' : 'Cart is empty'}</p>
            </div>
          ) : cart.map(item => (
            <div key={item.id} className="flex items-center gap-2 p-2 rounded-xl hover:bg-slate-50">
              <div className="flex-1 min-w-0">
                <div className="text-sm font-medium text-slate-800 truncate">
                  {lang === 'ar' ? item.nameAr : item.nameEn}
                </div>
                <div className="text-xs text-slate-400 num">{fmt(item.price)} × {item.qty}</div>
              </div>
              <div className="flex items-center gap-1.5">
                <button onClick={() => updateQty(item.id, -1)}
                  className="w-6 h-6 rounded-full bg-slate-100 hover:bg-slate-200 flex items-center justify-center">
                  <Minus size={11} />
                </button>
                <span className="w-6 text-center text-sm font-bold num">{item.qty}</span>
                <button onClick={() => updateQty(item.id, 1)}
                  className="w-6 h-6 rounded-full bg-brand-100 hover:bg-brand-200 text-brand-700 flex items-center justify-center">
                  <Plus size={11} />
                </button>
              </div>
              <div className="text-sm font-semibold text-slate-800 w-14 text-end num">
                {fmt(item.price * item.qty)}
              </div>
            </div>
          ))}
        </div>

        {/* Totals */}
        {cart.length > 0 && (
          <div className="p-4 border-t border-slate-100 space-y-3">
            <div className="space-y-1.5">
              {[
                [t('subtotal'), fmt(subtotal)],
                [`${lang === 'ar' ? 'ضريبة 15%' : 'VAT 15%'}`, fmt(vat)],
              ].map(([l,v]) => (
                <div key={l} className="flex justify-between text-sm text-slate-600">
                  <span>{l}</span><span className="num">{v}</span>
                </div>
              ))}
              <div className="flex justify-between font-bold text-base text-slate-900 pt-1 border-t border-slate-200">
                <span>{t('total')}</span>
                <span className="num">{fmt(total)} {t('sar')}</span>
              </div>
            </div>

            <button
              onClick={() => setShowPayment(true)}
              className="btn btn-primary w-full justify-center py-3.5 text-base"
            >
              <CreditCard size={18} />
              {t('payNow')}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
