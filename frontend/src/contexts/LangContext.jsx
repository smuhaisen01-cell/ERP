import { createContext, useContext, useState, useEffect } from 'react'

const translations = {
  ar: {
    // Navigation
    dashboard: 'لوحة التحكم',
    invoicing: 'الفواتير',
    pos: 'نقطة البيع',
    hr: 'الموارد البشرية',
    accounting: 'المحاسبة',
    inventory: 'المخزون',
    reports: 'التقارير',
    settings: 'الإعدادات',
    logout: 'تسجيل الخروج',

    // Dashboard
    totalRevenue: 'إجمالي الإيرادات',
    vatDue: 'ضريبة القيمة المضافة المستحقة',
    activeEmployees: 'الموظفون النشطون',
    todaySales: 'مبيعات اليوم',
    thisMonth: 'هذا الشهر',
    vsLastMonth: 'مقارنة بالشهر الماضي',
    recentInvoices: 'الفواتير الأخيرة',
    quickActions: 'إجراءات سريعة',
    newInvoice: 'فاتورة جديدة',
    runPayroll: 'معالجة الرواتب',
    vatReturn: 'إقرار ضريبي',
    inventory: 'المخزون',

    // Auth
    signIn: 'تسجيل الدخول',
    email: 'البريد الإلكتروني',
    password: 'كلمة المرور',
    rememberMe: 'تذكرني',
    forgotPassword: 'نسيت كلمة المرور؟',
    welcomeBack: 'مرحباً بعودتك',
    signInSubtitle: 'سجّل دخولك للوصول إلى نظام إدارة الأعمال',

    // Invoice
    invoiceNumber: 'رقم الفاتورة',
    issueDate: 'تاريخ الإصدار',
    dueDate: 'تاريخ الاستحقاق',
    customer: 'العميل',
    amount: 'المبلغ',
    vat: 'ضريبة القيمة المضافة',
    total: 'الإجمالي',
    status: 'الحالة',
    cleared: 'مُصفّاة',
    pending: 'معلّقة',
    draft: 'مسودة',
    rejected: 'مرفوضة',

    // POS
    newSale: 'بيع جديد',
    cart: 'السلة',
    subtotal: 'المجموع الفرعي',
    discount: 'الخصم',
    payNow: 'الدفع الآن',
    cash: 'نقداً',
    card: 'بطاقة',
    mada: 'مدى',
    receipt: 'إيصال',

    // HR
    employees: 'الموظفون',
    payroll: 'الرواتب',
    saudization: 'السعودة',
    newEmployee: 'موظف جديد',
    department: 'القسم',
    nationality: 'الجنسية',
    salary: 'الراتب',
    hireDate: 'تاريخ التعيين',
    saudi: 'سعودي',
    expat: 'وافد',

    // Common
    save: 'حفظ',
    cancel: 'إلغاء',
    delete: 'حذف',
    edit: 'تعديل',
    view: 'عرض',
    search: 'بحث',
    filter: 'تصفية',
    export: 'تصدير',
    print: 'طباعة',
    loading: 'جارٍ التحميل...',
    noData: 'لا توجد بيانات',
    sar: 'ر.س',
    all: 'الكل',
  },
  en: {
    // Navigation
    dashboard: 'Dashboard',
    invoicing: 'Invoicing',
    pos: 'Point of Sale',
    hr: 'Human Resources',
    accounting: 'Accounting',
    inventory: 'Inventory',
    reports: 'Reports',
    settings: 'Settings',
    logout: 'Sign Out',

    // Dashboard
    totalRevenue: 'Total Revenue',
    vatDue: 'VAT Due',
    activeEmployees: 'Active Employees',
    todaySales: "Today's Sales",
    thisMonth: 'This Month',
    vsLastMonth: 'vs last month',
    recentInvoices: 'Recent Invoices',
    quickActions: 'Quick Actions',
    newInvoice: 'New Invoice',
    runPayroll: 'Run Payroll',
    vatReturn: 'VAT Return',
    inventory: 'Inventory',

    // Auth
    signIn: 'Sign In',
    email: 'Email',
    password: 'Password',
    rememberMe: 'Remember me',
    forgotPassword: 'Forgot password?',
    welcomeBack: 'Welcome back',
    signInSubtitle: 'Sign in to access your business management system',

    // Invoice
    invoiceNumber: 'Invoice #',
    issueDate: 'Issue Date',
    dueDate: 'Due Date',
    customer: 'Customer',
    amount: 'Amount',
    vat: 'VAT',
    total: 'Total',
    status: 'Status',
    cleared: 'Cleared',
    pending: 'Pending',
    draft: 'Draft',
    rejected: 'Rejected',

    // POS
    newSale: 'New Sale',
    cart: 'Cart',
    subtotal: 'Subtotal',
    discount: 'Discount',
    payNow: 'Pay Now',
    cash: 'Cash',
    card: 'Card',
    mada: 'Mada',
    receipt: 'Receipt',

    // HR
    employees: 'Employees',
    payroll: 'Payroll',
    saudization: 'Saudization',
    newEmployee: 'New Employee',
    department: 'Department',
    nationality: 'Nationality',
    salary: 'Salary',
    hireDate: 'Hire Date',
    saudi: 'Saudi',
    expat: 'Expatriate',

    // Common
    save: 'Save',
    cancel: 'Cancel',
    delete: 'Delete',
    edit: 'Edit',
    view: 'View',
    search: 'Search',
    filter: 'Filter',
    export: 'Export',
    print: 'Print',
    loading: 'Loading...',
    noData: 'No data available',
    sar: 'SAR',
    all: 'All',
  }
}

const LangContext = createContext()

export function LangProvider({ children }) {
  const [lang, setLang] = useState(() => localStorage.getItem('erp_lang') || 'ar')

  useEffect(() => {
    const dir = lang === 'ar' ? 'rtl' : 'ltr'
    document.documentElement.setAttribute('dir', dir)
    document.documentElement.setAttribute('lang', lang)
    localStorage.setItem('erp_lang', lang)
  }, [lang])

  const t = (key) => translations[lang][key] || key
  const toggle = () => setLang(l => l === 'ar' ? 'en' : 'ar')
  const isRTL = lang === 'ar'

  return (
    <LangContext.Provider value={{ lang, t, toggle, isRTL }}>
      {children}
    </LangContext.Provider>
  )
}

export const useLang = () => useContext(LangContext)
