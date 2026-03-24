import { useState, useEffect } from 'react'
import { Package, Plus, Search, Loader2, RefreshCw, AlertTriangle, ArrowRight, Warehouse, BarChart2, Truck } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'products', labelAr: 'المنتجات', labelEn: 'Products' },
  { id: 'warehouses', labelAr: 'المستودعات', labelEn: 'Warehouses' },
  { id: 'stock', labelAr: 'مستويات المخزون', labelEn: 'Stock Levels' },
  { id: 'movements', labelAr: 'حركات المخزون', labelEn: 'Movements' },
  { id: 'alerts', labelAr: 'تنبيهات', labelEn: 'Alerts' },
]

function Modal({ onClose, title, children }) {
  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 space-y-4 max-h-[90vh] overflow-y-auto" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold">{title}</h2>
        {children}
      </div>
    </div>
  )
}

export default function InventoryPage() {
  const { lang } = useLang()
  const { api } = useAuth()
  const [tab, setTab] = useState('products')
  const [loading, setLoading] = useState(true)
  const [products, setProducts] = useState([])
  const [warehouses, setWarehouses] = useState([])
  const [stockLevels, setStockLevels] = useState([])
  const [movements, setMovements] = useState([])
  const [lowStock, setLowStock] = useState([])
  const [categories, setCategories] = useState([])
  const [modal, setModal] = useState(null)
  const [search, setSearch] = useState('')

  const fmt = (n) => new Intl.NumberFormat(lang === 'ar' ? 'ar-SA' : 'en-SA', { minimumFractionDigits: 2 }).format(parseFloat(n || 0))

  const safe = async (fn) => { try { return await fn() } catch(e) { console.warn('Inv:', e); return null } }

  const fetchAll = async () => {
    setLoading(true)
    const [p, w, sl, mv, ls, cat] = await Promise.all([
      safe(() => api.get('/inventory/products/')),
      safe(() => api.get('/inventory/warehouses/')),
      safe(() => api.get('/inventory/stock-levels/')),
      safe(() => api.get('/inventory/movements/')),
      safe(() => api.get('/inventory/products/low_stock/')),
      safe(() => api.get('/inventory/categories/')),
    ])
    if (p) setProducts(p.data.results || [])
    if (w) setWarehouses(w.data.results || [])
    if (sl) setStockLevels(sl.data.results || [])
    if (mv) setMovements(mv.data.results || [])
    if (ls) setLowStock(ls.data.alerts || [])
    if (cat) setCategories(cat.data.results || [])
    setLoading(false)
  }

  useEffect(() => { fetchAll() }, [])

  const addProduct = async (form) => {
    try { await api.post('/inventory/products/', form); toast.success('Product added'); setModal(null); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const addWarehouse = async (form) => {
    try { await api.post('/inventory/warehouses/', form); toast.success('Warehouse added'); setModal(null); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const receiveStock = async (form) => {
    try { await api.post('/inventory/movements/receive/', form); toast.success('Stock received'); setModal(null); fetchAll() }
    catch (err) { toast.error(JSON.stringify(err.response?.data || 'Error')) }
  }

  const filtered = products.filter(p =>
    p.name_ar?.includes(search) || p.name_en?.toLowerCase().includes(search.toLowerCase()) || p.sku?.includes(search)
  )

  const renderTab = () => {
    if (loading) return <div className="flex justify-center py-12"><Loader2 size={32} className="animate-spin text-brand-500" /></div>

    switch (tab) {
      case 'products': return (
        <div className="card">
          <div className="mb-4 relative">
            <Search size={16} className="absolute start-3 top-1/2 -translate-y-1/2 text-slate-400" />
            <input className="input ps-10" placeholder={lang === 'ar' ? 'بحث عن منتج...' : 'Search products...'} value={search} onChange={e => setSearch(e.target.value)} />
          </div>
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-200">
                <th className="text-start py-3 px-2 font-medium text-slate-500">SKU</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'المنتج' : 'Product'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'النوع' : 'Type'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'التكلفة' : 'Cost'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'السعر' : 'Price'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'المخزون' : 'Stock'}</th>
              </tr></thead>
              <tbody>{filtered.map(p => (
                <tr key={p.id} className="border-b border-slate-100 hover:bg-slate-50">
                  <td className="py-3 px-2 font-mono text-xs">{p.sku}</td>
                  <td className="py-3 px-2">
                    <div className="font-medium">{lang === 'ar' ? p.name_ar : p.name_en}</div>
                    <div className="text-xs text-slate-400">{p.category_name}</div>
                  </td>
                  <td className="py-3 px-2"><span className={`text-xs px-2 py-0.5 rounded-full ${p.product_type === 'goods' ? 'bg-blue-100 text-blue-700' : p.product_type === 'service' ? 'bg-green-100 text-green-700' : 'bg-orange-100 text-orange-700'}`}>{p.product_type}</span></td>
                  <td className="py-3 px-2 num">{fmt(p.cost_price)}</td>
                  <td className="py-3 px-2 num font-semibold">{fmt(p.selling_price)}</td>
                  <td className="py-3 px-2 num">{p.total_stock || '0'}</td>
                </tr>
              ))}</tbody>
            </table>
            {filtered.length === 0 && <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا توجد منتجات' : 'No products'}</p>}
          </div>
        </div>
      )

      case 'warehouses': return (
        <div className="card">
          {warehouses.length === 0 ? (
            <div className="text-center py-12">
              <Warehouse size={48} className="mx-auto text-slate-300 mb-4" />
              <p className="text-slate-400 mb-3">{lang === 'ar' ? 'لا توجد مستودعات' : 'No warehouses'}</p>
              <button onClick={async () => {
                try { await api.post('/inventory/warehouses/setup_default/'); toast.success('Default warehouse created'); fetchAll() }
                catch { toast.error('Error') }
              }} className="btn btn-primary">{lang === 'ar' ? 'إنشاء مستودع افتراضي' : 'Create Default Warehouse'}</button>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {warehouses.map(w => (
                <div key={w.id} className="bg-slate-50 rounded-xl p-4">
                  <div className="flex items-center justify-between mb-2">
                    <div className="font-semibold">{lang === 'ar' ? w.name_ar : w.name_en}</div>
                    <span className="font-mono text-xs text-slate-500">{w.code}</span>
                  </div>
                  <div className="text-sm text-slate-500">{w.city}</div>
                  <div className="flex justify-between mt-3 text-sm">
                    <span>{w.product_count} {lang === 'ar' ? 'منتج' : 'products'}</span>
                    <span className="font-semibold num">{fmt(w.total_value)} SAR</span>
                  </div>
                  {w.is_default && <span className="text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full mt-2 inline-block">{lang === 'ar' ? 'افتراضي' : 'Default'}</span>}
                </div>
              ))}
            </div>
          )}
        </div>
      )

      case 'stock': return (
        <div className="card">
          {stockLevels.length === 0 ? <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا يوجد مخزون' : 'No stock records'}</p> : (
            <table className="w-full text-sm">
              <thead><tr className="border-b">
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'المنتج' : 'Product'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'المستودع' : 'Warehouse'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'الكمية' : 'Qty'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'محجوز' : 'Reserved'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'متاح' : 'Available'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'الحالة' : 'Status'}</th>
              </tr></thead>
              <tbody>{stockLevels.map(sl => (
                <tr key={sl.id} className="border-b border-slate-100">
                  <td className="py-2 px-2"><span className="font-mono text-xs">{sl.product_sku}</span> {sl.product_name}</td>
                  <td className="py-2 px-2 text-sm">{sl.warehouse_name}</td>
                  <td className="py-2 px-2 num font-semibold">{sl.quantity}</td>
                  <td className="py-2 px-2 num text-orange-600">{sl.reserved}</td>
                  <td className="py-2 px-2 num text-green-600 font-semibold">{sl.available}</td>
                  <td className="py-2 px-2">
                    {sl.needs_reorder
                      ? <span className="text-xs px-2 py-0.5 rounded-full bg-red-100 text-red-700">{lang === 'ar' ? 'إعادة طلب' : 'Reorder'}</span>
                      : <span className="text-xs px-2 py-0.5 rounded-full bg-green-100 text-green-700">{lang === 'ar' ? 'كافي' : 'OK'}</span>
                    }
                  </td>
                </tr>
              ))}</tbody>
            </table>
          )}
        </div>
      )

      case 'movements': return (
        <div className="card">
          {movements.length === 0 ? <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا توجد حركات' : 'No movements'}</p> : (
            <table className="w-full text-sm">
              <thead><tr className="border-b">
                <th className="text-start py-2 px-2">#</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'النوع' : 'Type'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'المنتج' : 'Product'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'المستودع' : 'Warehouse'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'الكمية' : 'Qty'}</th>
                <th className="text-start py-2 px-2">{lang === 'ar' ? 'التاريخ' : 'Date'}</th>
              </tr></thead>
              <tbody>{movements.map(m => {
                const typeColors = { receive: 'bg-green-100 text-green-700', issue: 'bg-red-100 text-red-700', transfer: 'bg-blue-100 text-blue-700', adjustment: 'bg-yellow-100 text-yellow-700', return: 'bg-purple-100 text-purple-700', pos_sale: 'bg-orange-100 text-orange-700' }
                return (
                  <tr key={m.id} className="border-b border-slate-100">
                    <td className="py-2 px-2 font-mono text-xs">{m.movement_number}</td>
                    <td className="py-2 px-2"><span className={`text-xs px-2 py-0.5 rounded-full ${typeColors[m.movement_type] || 'bg-slate-100'}`}>{m.movement_type}</span></td>
                    <td className="py-2 px-2">{m.product_name}</td>
                    <td className="py-2 px-2 text-sm">{m.warehouse_name}</td>
                    <td className="py-2 px-2 num font-semibold">{m.quantity}</td>
                    <td className="py-2 px-2 num text-xs">{m.created_at?.substring(0, 10)}</td>
                  </tr>
                )
              })}</tbody>
            </table>
          )}
        </div>
      )

      case 'alerts': return (
        <div className="card">
          {lowStock.length === 0 ? (
            <div className="text-center py-12">
              <span className="text-4xl">✅</span>
              <p className="text-lg font-semibold text-green-600 mt-2">{lang === 'ar' ? 'جميع المنتجات في مستوى آمن' : 'All products at safe stock levels'}</p>
            </div>
          ) : (
            <div className="space-y-2">
              <h3 className="font-semibold text-red-600 flex items-center gap-2"><AlertTriangle size={18} /> {lowStock.length} {lang === 'ar' ? 'تنبيهات مخزون منخفض' : 'low stock alerts'}</h3>
              {lowStock.map((a, i) => (
                <div key={i} className="flex items-center justify-between p-3 bg-red-50 rounded-xl border border-red-200">
                  <div>
                    <div className="font-medium">{a.product_name} <span className="font-mono text-xs text-slate-500">({a.product_sku})</span></div>
                    <div className="text-xs text-slate-500">{a.warehouse}</div>
                  </div>
                  <div className="text-end">
                    <div className="text-red-700 font-bold num">{a.current_qty} {lang === 'ar' ? 'متبقي' : 'remaining'}</div>
                    <div className="text-xs text-slate-500">{lang === 'ar' ? 'حد إعادة الطلب:' : 'Reorder at:'} {a.reorder_level}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )

      default: return null
    }
  }

  const tabActions = () => {
    switch (tab) {
      case 'products': return <button onClick={() => setModal({ type: 'add_product' })} className="btn btn-primary flex items-center gap-2 text-sm"><Plus size={14} />{lang === 'ar' ? 'منتج' : 'Product'}</button>
      case 'warehouses': return <button onClick={() => setModal({ type: 'add_warehouse' })} className="btn btn-primary flex items-center gap-2 text-sm"><Plus size={14} />{lang === 'ar' ? 'مستودع' : 'Warehouse'}</button>
      case 'movements': return <button onClick={() => setModal({ type: 'receive' })} className="btn btn-primary flex items-center gap-2 text-sm"><Truck size={14} />{lang === 'ar' ? 'استلام' : 'Receive'}</button>
      default: return null
    }
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'إدارة المخزون' : 'Inventory'}</h1>
        <div className="flex gap-2">
          <button onClick={fetchAll} className="btn btn-secondary"><RefreshCw size={16} /></button>
          {tabActions()}
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center"><Package size={20} /></div>
          <div><div className="text-2xl font-bold">{products.length}</div><div className="text-xs text-slate-500">{lang === 'ar' ? 'منتجات' : 'Products'}</div></div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-green-50 text-green-600 flex items-center justify-center"><Warehouse size={20} /></div>
          <div><div className="text-2xl font-bold">{warehouses.length}</div><div className="text-xs text-slate-500">{lang === 'ar' ? 'مستودعات' : 'Warehouses'}</div></div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-purple-50 text-purple-600 flex items-center justify-center"><BarChart2 size={20} /></div>
          <div><div className="text-2xl font-bold">{movements.length}</div><div className="text-xs text-slate-500">{lang === 'ar' ? 'حركات' : 'Movements'}</div></div>
        </div>
        <div className="card flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-red-50 text-red-600 flex items-center justify-center"><AlertTriangle size={20} /></div>
          <div><div className="text-2xl font-bold">{lowStock.length}</div><div className="text-xs text-slate-500">{lang === 'ar' ? 'تنبيهات' : 'Alerts'}</div></div>
        </div>
      </div>

      <div className="flex gap-1.5 overflow-x-auto pb-1">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`px-3 py-2 rounded-xl text-xs font-medium whitespace-nowrap transition-all ${tab === t.id ? 'bg-brand-500 text-white' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'}`}>
            {lang === 'ar' ? t.labelAr : t.labelEn}
          </button>
        ))}
      </div>

      {renderTab()}

      {/* Modals */}
      {modal?.type === 'add_product' && (
        <Modal onClose={() => setModal(null)} title={lang === 'ar' ? 'إضافة منتج' : 'Add Product'}>
          <AddProductForm categories={categories} lang={lang} onSave={addProduct} onClose={() => setModal(null)} />
        </Modal>
      )}
      {modal?.type === 'add_warehouse' && (
        <Modal onClose={() => setModal(null)} title={lang === 'ar' ? 'إضافة مستودع' : 'Add Warehouse'}>
          <AddWarehouseForm lang={lang} onSave={addWarehouse} onClose={() => setModal(null)} />
        </Modal>
      )}
      {modal?.type === 'receive' && (
        <Modal onClose={() => setModal(null)} title={lang === 'ar' ? 'استلام مخزون' : 'Receive Stock'}>
          <ReceiveForm products={products} warehouses={warehouses} lang={lang} onSave={receiveStock} onClose={() => setModal(null)} />
        </Modal>
      )}
    </div>
  )
}

function AddProductForm({ categories, lang, onSave, onClose }) {
  const [f, setF] = useState({ sku: '', name_ar: '', name_en: '', product_type: 'goods', cost_price: '', selling_price: '', unit: 'EA', reorder_level: '10', category: '' })
  const s = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <input className="input" placeholder="SKU" value={f.sku} onChange={e => s('sku', e.target.value)} dir="ltr" />
        <select className="input" value={f.product_type} onChange={e => s('product_type', e.target.value)}>
          <option value="goods">{lang === 'ar' ? 'بضاعة' : 'Goods'}</option>
          <option value="service">{lang === 'ar' ? 'خدمة' : 'Service'}</option>
          <option value="consumable">{lang === 'ar' ? 'مواد استهلاكية' : 'Consumable'}</option>
        </select>
        <input className="input" placeholder={lang === 'ar' ? 'اسم المنتج (عربي)' : 'Name (Arabic)'} value={f.name_ar} onChange={e => s('name_ar', e.target.value)} />
        <input className="input" placeholder="Name (English)" value={f.name_en} onChange={e => s('name_en', e.target.value)} dir="ltr" />
        <input className="input" type="number" placeholder={lang === 'ar' ? 'سعر التكلفة' : 'Cost Price'} value={f.cost_price} onChange={e => s('cost_price', e.target.value)} dir="ltr" />
        <input className="input" type="number" placeholder={lang === 'ar' ? 'سعر البيع' : 'Selling Price'} value={f.selling_price} onChange={e => s('selling_price', e.target.value)} dir="ltr" />
        <select className="input" value={f.unit} onChange={e => s('unit', e.target.value)}>
          <option value="EA">{lang === 'ar' ? 'قطعة' : 'Each'}</option>
          <option value="KG">{lang === 'ar' ? 'كيلو' : 'KG'}</option>
          <option value="LTR">{lang === 'ar' ? 'لتر' : 'Liter'}</option>
          <option value="BOX">{lang === 'ar' ? 'صندوق' : 'Box'}</option>
          <option value="PKG">{lang === 'ar' ? 'عبوة' : 'Package'}</option>
        </select>
        <input className="input" type="number" placeholder={lang === 'ar' ? 'حد إعادة الطلب' : 'Reorder Level'} value={f.reorder_level} onChange={e => s('reorder_level', e.target.value)} dir="ltr" />
      </div>
      {categories.length > 0 && (
        <select className="input" value={f.category} onChange={e => s('category', e.target.value)}>
          <option value="">{lang === 'ar' ? '— تصنيف (اختياري) —' : '— Category (optional) —'}</option>
          {categories.map(c => <option key={c.id} value={c.id}>{lang === 'ar' ? c.name_ar : c.name_en}</option>)}
        </select>
      )}
      <div className="flex gap-3 justify-end">
        <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
        <button className="btn btn-primary" onClick={() => { const d = {...f}; if (!d.category) delete d.category; onSave(d) }}>{lang === 'ar' ? 'حفظ' : 'Save'}</button>
      </div>
    </div>
  )
}

function AddWarehouseForm({ lang, onSave, onClose }) {
  const [f, setF] = useState({ code: '', name_ar: '', name_en: '', city: 'Riyadh', address: '' })
  const s = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <div className="space-y-3">
      <div className="grid grid-cols-2 gap-3">
        <input className="input" placeholder={lang === 'ar' ? 'رمز المستودع' : 'Code'} value={f.code} onChange={e => s('code', e.target.value)} dir="ltr" />
        <input className="input" placeholder={lang === 'ar' ? 'المدينة' : 'City'} value={f.city} onChange={e => s('city', e.target.value)} />
        <input className="input" placeholder={lang === 'ar' ? 'اسم المستودع (عربي)' : 'Name (Arabic)'} value={f.name_ar} onChange={e => s('name_ar', e.target.value)} />
        <input className="input" placeholder="Name (English)" value={f.name_en} onChange={e => s('name_en', e.target.value)} dir="ltr" />
      </div>
      <textarea className="input" rows={2} placeholder={lang === 'ar' ? 'العنوان' : 'Address'} value={f.address} onChange={e => s('address', e.target.value)} />
      <div className="flex gap-3 justify-end">
        <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
        <button className="btn btn-primary" onClick={() => onSave(f)}>{lang === 'ar' ? 'حفظ' : 'Save'}</button>
      </div>
    </div>
  )
}

function ReceiveForm({ products, warehouses, lang, onSave, onClose }) {
  const [f, setF] = useState({ product: products[0]?.id || '', warehouse: warehouses[0]?.id || '', quantity: '', unit_cost: '', reference: '' })
  const s = (k, v) => setF(p => ({ ...p, [k]: v }))
  return (
    <div className="space-y-3">
      <select className="input" value={f.product} onChange={e => s('product', e.target.value)}>
        {products.map(p => <option key={p.id} value={p.id}>{p.name_en || p.name_ar} ({p.sku})</option>)}
      </select>
      <select className="input" value={f.warehouse} onChange={e => s('warehouse', e.target.value)}>
        {warehouses.map(w => <option key={w.id} value={w.id}>{w.name_en || w.name_ar} ({w.code})</option>)}
      </select>
      <div className="grid grid-cols-2 gap-3">
        <input className="input" type="number" placeholder={lang === 'ar' ? 'الكمية' : 'Quantity'} value={f.quantity} onChange={e => s('quantity', e.target.value)} dir="ltr" />
        <input className="input" type="number" placeholder={lang === 'ar' ? 'تكلفة الوحدة' : 'Unit Cost'} value={f.unit_cost} onChange={e => s('unit_cost', e.target.value)} dir="ltr" />
      </div>
      <input className="input" placeholder={lang === 'ar' ? 'المرجع (رقم PO)' : 'Reference (PO number)'} value={f.reference} onChange={e => s('reference', e.target.value)} dir="ltr" />
      <div className="flex gap-3 justify-end">
        <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
        <button className="btn btn-primary" onClick={() => onSave(f)}>{lang === 'ar' ? 'استلام' : 'Receive'}</button>
      </div>
    </div>
  )
}
