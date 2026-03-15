import { useState } from 'react'
import { Package, Search, BarChart2, AlertTriangle } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'

export default function InventoryPage() {
  const { lang } = useLang()

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'إدارة المخزون' : 'Inventory Management'}</h1>
        <p className="text-sm text-slate-500">{lang === 'ar' ? 'المنتجات والمستودعات ومستويات المخزون' : 'Products, warehouses & stock levels'}</p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center">
            <Package size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">0</div>
            <div className="text-sm text-slate-500">{lang === 'ar' ? 'منتجات' : 'Products'}</div>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-green-50 text-green-600 flex items-center justify-center">
            <BarChart2 size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">0</div>
            <div className="text-sm text-slate-500">{lang === 'ar' ? 'مستودعات' : 'Warehouses'}</div>
          </div>
        </div>
        <div className="card flex items-center gap-4">
          <div className="w-12 h-12 rounded-xl bg-orange-50 text-orange-600 flex items-center justify-center">
            <AlertTriangle size={24} />
          </div>
          <div>
            <div className="text-2xl font-bold text-slate-900">0</div>
            <div className="text-sm text-slate-500">{lang === 'ar' ? 'تنبيهات مخزون' : 'Stock Alerts'}</div>
          </div>
        </div>
      </div>

      <div className="card">
        <div className="text-center py-16">
          <Package size={48} className="mx-auto text-slate-300 mb-4" />
          <h3 className="text-lg font-semibold text-slate-600 mb-2">
            {lang === 'ar' ? 'إدارة المخزون قيد التطوير' : 'Inventory Module Coming Soon'}
          </h3>
          <p className="text-sm text-slate-400 max-w-md mx-auto">
            {lang === 'ar'
              ? 'سيتم إضافة إدارة المنتجات والمستودعات وتتبع المخزون مع تنبيهات إعادة الطلب وتكامل مع نقاط البيع'
              : 'Product management, warehouse tracking, stock levels with reorder alerts and POS integration will be added soon'}
          </p>
        </div>
      </div>
    </div>
  )
}
