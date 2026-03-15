import { useState, useEffect } from 'react'
import { BookOpen, Plus, Loader2, RefreshCw } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import { accountingAPI } from '../../services/api'
import toast from 'react-hot-toast'

const TAB = ['coa', 'journal', 'vat']

function AddAccountModal({ onClose, onSave, lang }) {
  const [form, setForm] = useState({
    code: '', name_ar: '', name_en: '', account_type: 'asset',
    socpa_category: 'current_assets', normal_balance: 'debit', is_leaf: true,
  })
  const set = (k, v) => setForm(f => ({ ...f, [k]: v }))

  return (
    <div className="fixed inset-0 bg-black/40 flex items-center justify-center z-50 p-4" onClick={onClose}>
      <div className="bg-white rounded-2xl w-full max-w-lg p-6 space-y-4" onClick={e => e.stopPropagation()}>
        <h2 className="text-xl font-bold">{lang === 'ar' ? 'إضافة حساب' : 'Add Account'}</h2>
        <div className="grid grid-cols-2 gap-3">
          <input className="input" placeholder={lang === 'ar' ? 'رمز الحساب' : 'Account Code'} value={form.code} onChange={e => set('code', e.target.value)} dir="ltr" />
          <select className="input" value={form.account_type} onChange={e => set('account_type', e.target.value)}>
            <option value="asset">{lang === 'ar' ? 'أصول' : 'Asset'}</option>
            <option value="liability">{lang === 'ar' ? 'خصوم' : 'Liability'}</option>
            <option value="equity">{lang === 'ar' ? 'حقوق ملكية' : 'Equity'}</option>
            <option value="revenue">{lang === 'ar' ? 'إيرادات' : 'Revenue'}</option>
            <option value="expense">{lang === 'ar' ? 'مصروفات' : 'Expense'}</option>
          </select>
          <input className="input col-span-2" placeholder={lang === 'ar' ? 'اسم الحساب (عربي)' : 'Account Name (Arabic)'} value={form.name_ar} onChange={e => set('name_ar', e.target.value)} />
          <input className="input col-span-2" placeholder="Account Name (English)" value={form.name_en} onChange={e => set('name_en', e.target.value)} dir="ltr" />
          <select className="input" value={form.socpa_category} onChange={e => set('socpa_category', e.target.value)}>
            <option value="current_assets">Current Assets</option>
            <option value="non_current_assets">Non-Current Assets</option>
            <option value="current_liabilities">Current Liabilities</option>
            <option value="long_term_liabilities">Long-Term Liabilities</option>
            <option value="equity">Equity</option>
            <option value="revenue">Revenue</option>
            <option value="cogs">COGS</option>
            <option value="operating_expenses">Operating Expenses</option>
            <option value="other_expenses">Other Expenses</option>
          </select>
          <select className="input" value={form.normal_balance} onChange={e => set('normal_balance', e.target.value)}>
            <option value="debit">{lang === 'ar' ? 'مدين' : 'Debit'}</option>
            <option value="credit">{lang === 'ar' ? 'دائن' : 'Credit'}</option>
          </select>
        </div>
        <div className="flex gap-3 justify-end">
          <button className="btn btn-secondary" onClick={onClose}>{lang === 'ar' ? 'إلغاء' : 'Cancel'}</button>
          <button className="btn btn-primary" onClick={() => onSave(form)}>{lang === 'ar' ? 'حفظ' : 'Save'}</button>
        </div>
      </div>
    </div>
  )
}

export default function AccountingPage() {
  const { lang } = useLang()
  const { api } = useAuth()
  const [tab, setTab] = useState('coa')
  const [loading, setLoading] = useState(true)
  const [accounts, setAccounts] = useState([])
  const [journals, setJournals] = useState([])
  const [showAdd, setShowAdd] = useState(false)

  const fetchData = async () => {
    setLoading(true)
    try {
      const [coaRes, jeRes] = await Promise.allSettled([
        accountingAPI.getChartOfAccounts(api),
        accountingAPI.getJournalEntries(api),
      ])
      if (coaRes.status === 'fulfilled') setAccounts(coaRes.value.data.results || [])
      if (jeRes.status === 'fulfilled') setJournals(jeRes.value.data.results || [])
    } catch (err) { console.error(err) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchData() }, [])

  const handleAddAccount = async (form) => {
    try {
      await accountingAPI.createAccount(api, form)
      toast.success(lang === 'ar' ? 'تم إضافة الحساب' : 'Account added')
      setShowAdd(false)
      fetchData()
    } catch (err) {
      toast.error(err.response?.data?.detail || JSON.stringify(err.response?.data) || 'Error')
    }
  }

  const tabLabels = {
    coa: lang === 'ar' ? 'دليل الحسابات' : 'Chart of Accounts',
    journal: lang === 'ar' ? 'قيود اليومية' : 'Journal Entries',
    vat: lang === 'ar' ? 'إقرارات الضريبة' : 'VAT Returns',
  }

  const typeColors = {
    asset: 'bg-blue-100 text-blue-700',
    liability: 'bg-red-100 text-red-700',
    equity: 'bg-purple-100 text-purple-700',
    revenue: 'bg-green-100 text-green-700',
    expense: 'bg-orange-100 text-orange-700',
  }

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'المحاسبة' : 'Accounting'}</h1>
          <p className="text-sm text-slate-500">{lang === 'ar' ? 'دليل حسابات SOCPA والقيود المحاسبية' : 'SOCPA Chart of Accounts & General Ledger'}</p>
        </div>
        <div className="flex gap-2">
          <button onClick={fetchData} className="btn btn-secondary"><RefreshCw size={16} /></button>
          {tab === 'coa' && <button onClick={() => setShowAdd(true)} className="btn btn-primary flex items-center gap-2"><Plus size={16} />{lang === 'ar' ? 'حساب جديد' : 'New Account'}</button>}
        </div>
      </div>

      <div className="flex gap-1 bg-slate-100 rounded-xl p-1">
        {TAB.map(t => (
          <button key={t} onClick={() => setTab(t)}
            className={`flex-1 py-2 px-4 rounded-lg text-sm font-medium transition-all ${tab === t ? 'bg-white text-slate-900 shadow-sm' : 'text-slate-500 hover:text-slate-700'}`}>
            {tabLabels[t]}
          </button>
        ))}
      </div>

      {loading ? (
        <div className="flex justify-center py-12"><Loader2 size={32} className="animate-spin text-brand-500" /></div>
      ) : tab === 'coa' ? (
        <div className="card">
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead><tr className="border-b border-slate-200">
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الرمز' : 'Code'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'اسم الحساب' : 'Account Name'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'النوع' : 'Type'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'التصنيف' : 'Category'}</th>
                <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الطبيعة' : 'Balance'}</th>
              </tr></thead>
              <tbody>
                {accounts.map(acc => (
                  <tr key={acc.id} className="border-b border-slate-100 hover:bg-slate-50">
                    <td className="py-3 px-2 font-mono font-semibold text-slate-700">{acc.code}</td>
                    <td className="py-3 px-2">
                      <div className="font-medium">{lang === 'ar' ? acc.name_ar : acc.name_en}</div>
                      <div className="text-xs text-slate-400">{lang === 'ar' ? acc.name_en : acc.name_ar}</div>
                    </td>
                    <td className="py-3 px-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${typeColors[acc.account_type] || 'bg-slate-100'}`}>{acc.account_type}</span>
                    </td>
                    <td className="py-3 px-2 text-xs text-slate-500">{acc.socpa_category?.replace(/_/g, ' ')}</td>
                    <td className="py-3 px-2 text-xs">{acc.normal_balance}</td>
                  </tr>
                ))}
              </tbody>
            </table>
            {accounts.length === 0 && <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا توجد حسابات — قم بتشغيل seed_socpa_coa' : 'No accounts — run seed_socpa_coa'}</p>}
          </div>
        </div>
      ) : tab === 'journal' ? (
        <div className="card">
          {journals.length === 0 ? (
            <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'لا توجد قيود يومية بعد' : 'No journal entries yet'}</p>
          ) : (
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead><tr className="border-b border-slate-200">
                  <th className="text-start py-3 px-2 font-medium text-slate-500">#</th>
                  <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'التاريخ' : 'Date'}</th>
                  <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'البيان' : 'Description'}</th>
                  <th className="text-start py-3 px-2 font-medium text-slate-500">{lang === 'ar' ? 'الحالة' : 'Status'}</th>
                </tr></thead>
                <tbody>
                  {journals.map(je => (
                    <tr key={je.id} className="border-b border-slate-100 hover:bg-slate-50">
                      <td className="py-3 px-2 num">{je.entry_number}</td>
                      <td className="py-3 px-2 num">{je.entry_date}</td>
                      <td className="py-3 px-2">{je.description_ar}</td>
                      <td className="py-3 px-2">
                        <span className={`text-xs px-2 py-0.5 rounded-full ${je.status === 'posted' ? 'bg-green-100 text-green-700' : je.status === 'reversed' ? 'bg-red-100 text-red-700' : 'bg-slate-100 text-slate-600'}`}>{je.status}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      ) : (
        <div className="card">
          <p className="text-center py-8 text-slate-400">{lang === 'ar' ? 'قريباً — إقرارات ضريبة القيمة المضافة' : 'Coming soon — VAT Returns'}</p>
        </div>
      )}

      {showAdd && <AddAccountModal onClose={() => setShowAdd(false)} onSave={handleAddAccount} lang={lang} />}
    </div>
  )
}
