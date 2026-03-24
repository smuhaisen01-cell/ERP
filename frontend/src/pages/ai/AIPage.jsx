import { useState, useEffect, useRef } from 'react'
import { Bot, Send, AlertTriangle, TrendingUp, Tag, Loader2, RefreshCw, Sparkles, ChevronRight } from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'
import toast from 'react-hot-toast'

const TABS = [
  { id: 'copilot', icon: Bot, labelAr: 'المساعد الذكي', labelEn: 'AI Copilot' },
  { id: 'alerts', icon: AlertTriangle, labelAr: 'التنبيهات', labelEn: 'Smart Alerts' },
  { id: 'forecast', icon: TrendingUp, labelAr: 'التوقعات', labelEn: 'Forecast' },
  { id: 'categorize', icon: Tag, labelAr: 'تصنيف تلقائي', labelEn: 'Auto-Categorize' },
]

const QUICK_QUESTIONS = [
  { ar: 'ما إجمالي مبيعات هذا الشهر؟', en: 'What are total sales this month?' },
  { ar: 'كم عدد الموظفين النشطين؟', en: 'How many active employees?' },
  { ar: 'ما نسبة السعودة الحالية؟', en: 'What is the current Saudization rate?' },
  { ar: 'ما حالة فواتير ZATCA؟', en: 'What is the ZATCA invoice status?' },
  { ar: 'ما إجمالي ضريبة القيمة المضافة المحصلة؟', en: 'What is total VAT collected?' },
  { ar: 'حلل التدفق النقدي الشهري', en: 'Analyze monthly cash flow' },
]

export default function AIPage() {
  const { lang } = useLang()
  const { api } = useAuth()
  const [tab, setTab] = useState('copilot')
  const [aiStatus, setAiStatus] = useState(null)

  useEffect(() => {
    const checkStatus = async () => {
      try {
        const res = await api.get('/ai/status/')
        setAiStatus(res.data)
      } catch { setAiStatus({ status: 'error' }) }
    }
    checkStatus()
  }, [])

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-purple-500 to-blue-500 flex items-center justify-center">
            <Sparkles size={20} className="text-white" />
          </div>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">{lang === 'ar' ? 'الذكاء الاصطناعي' : 'AI Platform'}</h1>
            <p className="text-sm text-slate-500">
              {aiStatus?.status === 'connected'
                ? (lang === 'ar' ? 'متصل — Claude AI' : 'Connected — Claude AI')
                : (lang === 'ar' ? 'يتطلب ANTHROPIC_API_KEY' : 'Requires ANTHROPIC_API_KEY')}
            </p>
          </div>
        </div>
        {aiStatus && (
          <span className={`text-xs px-3 py-1 rounded-full ${aiStatus.status === 'connected' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'}`}>
            {aiStatus.backend} — {aiStatus.status}
          </span>
        )}
      </div>

      <div className="flex gap-2 overflow-x-auto pb-1">
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)}
            className={`flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium whitespace-nowrap transition-all ${
              tab === t.id ? 'bg-purple-600 text-white shadow-sm' : 'bg-slate-100 text-slate-600 hover:bg-slate-200'
            }`}>
            <t.icon size={16} />
            {lang === 'ar' ? t.labelAr : t.labelEn}
          </button>
        ))}
      </div>

      {tab === 'copilot' && <CopilotTab lang={lang} api={api} />}
      {tab === 'alerts' && <AlertsTab lang={lang} api={api} />}
      {tab === 'forecast' && <ForecastTab lang={lang} api={api} />}
      {tab === 'categorize' && <CategorizeTab lang={lang} api={api} />}
    </div>
  )
}

// ─── Copilot Chat ─────────────────────────────────────────

function CopilotTab({ lang, api }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const chatRef = useRef(null)

  const sendMessage = async (text) => {
    const msg = text || input.trim()
    if (!msg) return

    const userMsg = { role: 'user', content: msg }
    setMessages(prev => [...prev, userMsg])
    setInput('')
    setLoading(true)

    try {
      const res = await api.post('/ai/chat/', {
        message: msg,
        history: messages.slice(-10),
      })
      setMessages(prev => [...prev, { role: 'assistant', content: res.data.response }])
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: lang === 'ar'
          ? 'عذراً — تأكد من إعداد ANTHROPIC_API_KEY في Railway'
          : 'Sorry — please configure ANTHROPIC_API_KEY in Railway'
      }])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    chatRef.current?.scrollTo({ top: chatRef.current.scrollHeight, behavior: 'smooth' })
  }, [messages])

  return (
    <div className="card flex flex-col" style={{ height: 'calc(100vh - 280px)' }}>
      {/* Quick questions */}
      {messages.length === 0 && (
        <div className="p-4 border-b">
          <p className="text-sm text-slate-500 mb-3">{lang === 'ar' ? 'أسئلة سريعة:' : 'Quick questions:'}</p>
          <div className="grid grid-cols-2 gap-2">
            {QUICK_QUESTIONS.map((q, i) => (
              <button key={i} onClick={() => sendMessage(lang === 'ar' ? q.ar : q.en)}
                className="text-start text-sm p-2.5 rounded-xl bg-purple-50 text-purple-700 hover:bg-purple-100 transition-colors flex items-center gap-2">
                <ChevronRight size={14} className="flex-shrink-0" />
                {lang === 'ar' ? q.ar : q.en}
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Messages */}
      <div ref={chatRef} className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.map((msg, i) => (
          <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${
              msg.role === 'user'
                ? 'bg-purple-600 text-white rounded-br-md'
                : 'bg-slate-100 text-slate-800 rounded-bl-md'
            }`}>
              {msg.role === 'assistant' && (
                <div className="flex items-center gap-1.5 mb-1.5">
                  <Bot size={14} className="text-purple-500" />
                  <span className="text-xs font-medium text-purple-600">AI</span>
                </div>
              )}
              <div className="whitespace-pre-wrap">{msg.content}</div>
            </div>
          </div>
        ))}
        {loading && (
          <div className="flex justify-start">
            <div className="bg-slate-100 rounded-2xl rounded-bl-md px-4 py-3 flex items-center gap-2">
              <Loader2 size={16} className="animate-spin text-purple-500" />
              <span className="text-sm text-slate-500">{lang === 'ar' ? 'جاري التحليل...' : 'Analyzing...'}</span>
            </div>
          </div>
        )}
      </div>

      {/* Input */}
      <div className="p-4 border-t">
        <div className="flex gap-2">
          <input className="input flex-1"
            placeholder={lang === 'ar' ? 'اسأل عن بيانات شركتك...' : 'Ask about your company data...'}
            value={input}
            onChange={e => setInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && !e.shiftKey && sendMessage()}
            disabled={loading}
          />
          <button onClick={() => sendMessage()} disabled={loading || !input.trim()}
            className="btn btn-primary px-4 disabled:opacity-50">
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  )
}

// ─── Smart Alerts ─────────────────────────────────────────

function AlertsTab({ lang, api }) {
  const [alerts, setAlerts] = useState(null)
  const [loading, setLoading] = useState(true)

  const fetchAlerts = async () => {
    setLoading(true)
    try {
      const res = await api.get('/ai/alerts/?enrich=true')
      setAlerts(res.data)
    } catch { setAlerts({ alerts: [], count: 0 }) }
    finally { setLoading(false) }
  }

  useEffect(() => { fetchAlerts() }, [])

  const severityConfig = {
    high: { color: 'bg-red-100 text-red-700 border-red-200', icon: '🔴', label: lang === 'ar' ? 'عالي' : 'High' },
    medium: { color: 'bg-yellow-100 text-yellow-700 border-yellow-200', icon: '🟡', label: lang === 'ar' ? 'متوسط' : 'Medium' },
    low: { color: 'bg-blue-100 text-blue-700 border-blue-200', icon: '🔵', label: lang === 'ar' ? 'منخفض' : 'Low' },
  }

  if (loading) return <div className="flex justify-center py-12"><Loader2 size={32} className="animate-spin text-purple-500" /></div>

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="flex gap-3">
          {['high', 'medium', 'low'].map(s => (
            <div key={s} className={`px-3 py-1.5 rounded-lg text-sm font-medium ${severityConfig[s].color}`}>
              {severityConfig[s].icon} {alerts?.severity_counts?.[s] || 0} {severityConfig[s].label}
            </div>
          ))}
        </div>
        <button onClick={fetchAlerts} className="btn btn-secondary"><RefreshCw size={16} /></button>
      </div>

      {alerts?.alerts?.length === 0 ? (
        <div className="card text-center py-12">
          <span className="text-4xl">✅</span>
          <p className="text-lg font-semibold text-green-600 mt-2">{lang === 'ar' ? 'لا توجد تنبيهات' : 'No alerts — all clear!'}</p>
        </div>
      ) : (
        <div className="space-y-3">
          {alerts?.alerts?.map((alert, i) => {
            const cfg = severityConfig[alert.severity] || severityConfig.low
            return (
              <div key={i} className={`card border ${cfg.color}`}>
                <div className="flex items-start gap-3">
                  <span className="text-xl">{cfg.icon}</span>
                  <div className="flex-1">
                    <div className="font-medium">{lang === 'ar' ? alert.message_ar : alert.message_en}</div>
                    {alert.ai_recommendation && (
                      <div className="mt-2 text-sm bg-white/50 rounded-lg p-2.5">
                        <span className="text-xs font-medium text-purple-600 flex items-center gap-1 mb-1">
                          <Bot size={12} /> AI Recommendation
                        </span>
                        {alert.ai_recommendation}
                      </div>
                    )}
                  </div>
                  <span className={`text-xs px-2 py-0.5 rounded-full ${cfg.color}`}>{cfg.label}</span>
                </div>
              </div>
            )
          })}
        </div>
      )}
    </div>
  )
}

// ─── Forecast ─────────────────────────────────────────────

function ForecastTab({ lang, api }) {
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetch = async () => {
      try {
        const res = await api.get('/ai/forecast/')
        setData(res.data)
      } catch { setData(null) }
      finally { setLoading(false) }
    }
    fetch()
  }, [])

  const fmt = (n) => new Intl.NumberFormat('en-SA', { minimumFractionDigits: 0 }).format(parseFloat(n || 0))

  if (loading) return <div className="flex justify-center py-12"><Loader2 size={32} className="animate-spin text-purple-500" /></div>

  if (!data?.historical?.length) {
    return (
      <div className="card text-center py-12">
        <TrendingUp size={48} className="mx-auto text-slate-300 mb-4" />
        <p className="text-slate-500">{lang === 'ar' ? 'بيانات غير كافية للتوقع (مطلوب شهرين على الأقل)' : 'Not enough data for forecasting (need at least 2 months)'}</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Historical */}
      <div className="card">
        <h3 className="font-semibold mb-3">{lang === 'ar' ? 'الإيرادات الشهرية' : 'Monthly Revenue'}</h3>
        <div className="space-y-2">
          {data.historical.map((m, i) => {
            const rev = parseFloat(m.revenue || 0)
            const maxRev = Math.max(...data.historical.map(h => parseFloat(h.revenue || 0)), 1)
            const pct = (rev / maxRev * 100).toFixed(0)
            return (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-slate-500 w-20">{m.month?.substring(0, 7)}</span>
                <div className="flex-1 bg-slate-100 rounded-full h-6 overflow-hidden">
                  <div className="bg-gradient-to-r from-purple-500 to-blue-500 h-full rounded-full flex items-center px-2"
                    style={{ width: `${Math.max(pct, 5)}%` }}>
                    <span className="text-[10px] text-white font-semibold">{fmt(rev)} SAR</span>
                  </div>
                </div>
                <span className="text-xs text-slate-400">{m.invoice_count} inv</span>
              </div>
            )
          })}
        </div>
      </div>

      {/* Forecast */}
      {data.simple_forecast_3m?.length > 0 && (
        <div className="card">
          <h3 className="font-semibold mb-3">{lang === 'ar' ? 'التوقعات (3 أشهر)' : '3-Month Forecast'}</h3>
          <div className="grid grid-cols-3 gap-3">
            {data.simple_forecast_3m.map((v, i) => (
              <div key={i} className="bg-purple-50 rounded-xl p-4 text-center">
                <div className="text-xs text-purple-600 mb-1">Month +{i + 1}</div>
                <div className="text-lg font-bold text-purple-800 num">{fmt(v)} SAR</div>
              </div>
            ))}
          </div>
          <div className="text-xs text-slate-400 mt-2">
            {lang === 'ar' ? 'متوسط النمو الشهري:' : 'Avg monthly growth:'} {fmt(data.avg_monthly_growth)} SAR
          </div>
        </div>
      )}

      {/* AI Analysis */}
      {data.ai_analysis && (
        <div className="card border border-purple-200 bg-purple-50/50">
          <div className="flex items-center gap-2 mb-2">
            <Bot size={16} className="text-purple-600" />
            <span className="text-sm font-medium text-purple-700">{lang === 'ar' ? 'تحليل الذكاء الاصطناعي' : 'AI Analysis'}</span>
          </div>
          <p className="text-sm text-slate-700 whitespace-pre-wrap">{data.ai_analysis}</p>
        </div>
      )}
    </div>
  )
}

// ─── Auto-Categorize ──────────────────────────────────────

function CategorizeTab({ lang, api }) {
  const [desc, setDesc] = useState('')
  const [amount, setAmount] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const categorize = async () => {
    if (!desc) return
    setLoading(true)
    setResult(null)
    try {
      const res = await api.post('/ai/categorize/', { description: desc, amount: parseFloat(amount) || 0 })
      setResult(res.data)
    } catch (err) {
      setResult({ error: 'AI unavailable' })
    } finally { setLoading(false) }
  }

  return (
    <div className="space-y-4">
      <div className="card">
        <h3 className="font-semibold mb-3">{lang === 'ar' ? 'تصنيف المصروفات تلقائياً' : 'Auto-Categorize Expenses'}</h3>
        <p className="text-sm text-slate-500 mb-4">{lang === 'ar' ? 'أدخل وصف المعاملة وسيقترح الذكاء الاصطناعي حساب GL المناسب' : 'Enter a transaction description and AI will suggest the correct GL account'}</p>

        <div className="flex gap-3 mb-4">
          <input className="input flex-1" placeholder={lang === 'ar' ? 'وصف المعاملة (مثال: لوازم مكتبية من جرير)' : 'Transaction description (e.g., Office supplies from Jarir)'}
            value={desc} onChange={e => setDesc(e.target.value)} />
          <input className="input w-32" type="number" placeholder={lang === 'ar' ? 'المبلغ' : 'Amount'} dir="ltr"
            value={amount} onChange={e => setAmount(e.target.value)} />
          <button onClick={categorize} disabled={loading || !desc} className="btn btn-primary px-6 disabled:opacity-50">
            {loading ? <Loader2 size={16} className="animate-spin" /> : <Tag size={16} />}
          </button>
        </div>

        {result && !result.error && (
          <div className="bg-green-50 border border-green-200 rounded-xl p-4">
            <div className="flex items-center gap-2 mb-2">
              <span className="text-green-600 font-bold text-lg">✓</span>
              <span className="font-semibold text-green-800">{lang === 'ar' ? 'الحساب المقترح' : 'Suggested Account'}</span>
            </div>
            <div className="grid grid-cols-2 gap-3 text-sm">
              <div><span className="text-slate-500">{lang === 'ar' ? 'رمز الحساب' : 'Account Code'}</span><div className="font-bold font-mono text-lg">{result.account_code}</div></div>
              <div><span className="text-slate-500">{lang === 'ar' ? 'اسم الحساب' : 'Account Name'}</span><div className="font-semibold">{result.account_name}</div></div>
              {result.confidence && <div><span className="text-slate-500">{lang === 'ar' ? 'الثقة' : 'Confidence'}</span><div className="font-semibold">{(result.confidence * 100).toFixed(0)}%</div></div>}
              {result.reason && <div><span className="text-slate-500">{lang === 'ar' ? 'السبب' : 'Reason'}</span><div>{result.reason}</div></div>}
            </div>
          </div>
        )}

        {result?.error && (
          <div className="bg-red-50 border border-red-200 rounded-xl p-4 text-red-700 text-sm">
            {result.error}
          </div>
        )}

        {result?.suggestion && !result?.account_code && (
          <div className="bg-blue-50 border border-blue-200 rounded-xl p-4 text-sm">{result.suggestion}</div>
        )}
      </div>

      {/* Example categorizations */}
      <div className="card">
        <h4 className="text-sm font-medium text-slate-500 mb-3">{lang === 'ar' ? 'أمثلة للتجربة:' : 'Try these examples:'}</h4>
        <div className="grid grid-cols-2 gap-2">
          {[
            { desc: 'Office supplies from Jarir Bookstore', amount: 500 },
            { desc: 'Electricity bill - SEC', amount: 2000 },
            { desc: 'Employee flight ticket to Jeddah', amount: 1200 },
            { desc: 'Monthly rent for office space', amount: 15000 },
            { desc: 'IT equipment - Dell laptop', amount: 4500 },
            { desc: 'Employee training course', amount: 3000 },
          ].map((ex, i) => (
            <button key={i} onClick={() => { setDesc(ex.desc); setAmount(String(ex.amount)); setResult(null) }}
              className="text-start text-xs p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors">
              <span className="text-slate-600">{ex.desc}</span>
              <span className="text-slate-400 ms-2">{ex.amount} SAR</span>
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
