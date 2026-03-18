import { NavLink, useNavigate } from 'react-router-dom'
import { useState } from 'react'
import {
  LayoutDashboard, FileText, ShoppingCart, Users,
  BookOpen, Package, Settings, LogOut, Menu, X,
  Building2, Globe, FileBarChart
} from 'lucide-react'
import { useLang } from '../../contexts/LangContext'
import { useAuth } from '../../contexts/AuthContext'

const NAV = [
  { key: 'dashboard',  icon: LayoutDashboard, path: '/dashboard',  module: 'dashboard' },
  { key: 'invoicing',  icon: FileText,         path: '/invoicing',  module: 'invoicing' },
  { key: 'pos',        icon: ShoppingCart,      path: '/pos',        module: 'pos' },
  { key: 'hr',         icon: Users,             path: '/hr',         module: 'hr' },
  { key: 'accounting', icon: BookOpen,          path: '/accounting', module: 'accounting' },
  { key: 'inventory',  icon: Package,           path: '/inventory',  module: 'inventory' },
  { key: 'reports',    icon: FileBarChart,      path: '/reports',    module: 'reports' },
]

// hr_self employees can see HR (limited) but label it differently
const MODULE_ALIAS = { hr_self: 'hr' }

function Sidebar({ open, onClose }) {
  const { t, toggle, lang } = useLang()
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  const handleLogout = () => { logout(); navigate('/login') }

  // Get user's allowed modules
  const modules = user?.modules || ['dashboard']
  const expandedModules = modules.map(m => MODULE_ALIAS[m] || m)
  const isAdmin = user?.role === 'super_admin'

  // Filter nav items based on role
  const visibleNav = NAV.filter(item => expandedModules.includes(item.module))

  // Role badge
  const roleBadge = {
    super_admin: { label: lang === 'ar' ? 'مدير النظام' : 'Admin', color: 'bg-red-500/20 text-red-300' },
    hr_manager: { label: lang === 'ar' ? 'مدير HR' : 'HR Manager', color: 'bg-blue-500/20 text-blue-300' },
    accountant: { label: lang === 'ar' ? 'محاسب' : 'Accountant', color: 'bg-green-500/20 text-green-300' },
    pos_cashier: { label: lang === 'ar' ? 'كاشير' : 'Cashier', color: 'bg-yellow-500/20 text-yellow-300' },
    employee: { label: lang === 'ar' ? 'موظف' : 'Employee', color: 'bg-slate-500/20 text-slate-300' },
  }

  const badge = roleBadge[user?.role] || roleBadge.employee

  return (
    <>
      {open && (
        <div className="fixed inset-0 bg-black/50 z-30 lg:hidden" onClick={onClose} />
      )}

      <aside className={`sidebar transition-transform duration-200
        ${open ? 'translate-x-0' : 'lg:translate-x-0'}
        ${!open ? 'max-lg:-translate-x-full rtl:max-lg:translate-x-full' : ''}
      `}>
        {/* Logo */}
        <div className="flex items-center gap-3 px-5 py-5 border-b border-white/10">
          <div className="w-9 h-9 rounded-xl bg-brand-500 flex items-center justify-center flex-shrink-0">
            <Building2 size={18} className="text-white" />
          </div>
          <div>
            <div className="text-white font-semibold text-sm leading-tight">
              {lang === 'ar' ? 'نظام ERP' : 'ERP System'}
            </div>
            <div className="text-white/40 text-xs">
              {user?.company || (lang === 'ar' ? 'لوحة التحكم' : 'Dashboard')}
            </div>
          </div>
          <button onClick={onClose} className="lg:hidden ms-auto text-white/40 hover:text-white">
            <X size={18} />
          </button>
        </div>

        {/* Nav — filtered by role */}
        <nav className="flex-1 py-3 overflow-y-auto">
          {visibleNav.map(({ key, icon: Icon, path }) => (
            <NavLink
              key={key}
              to={path}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}
              onClick={onClose}
            >
              <Icon size={18} />
              <span>{t(key)}</span>
            </NavLink>
          ))}
        </nav>

        {/* Bottom */}
        <div className="p-3 border-t border-white/10 space-y-1">
          <button onClick={toggle} className="nav-item w-full text-start">
            <Globe size={18} />
            <span>{lang === 'ar' ? 'English' : 'العربية'}</span>
          </button>

          {isAdmin && (
            <button onClick={() => { navigate('/settings'); onClose() }} className="nav-item w-full text-start">
              <Settings size={18} />
              <span>{t('settings')}</span>
            </button>
          )}

          <button onClick={handleLogout} className="nav-item w-full text-start text-red-400 hover:!bg-red-500/10">
            <LogOut size={18} />
            <span>{t('logout')}</span>
          </button>
        </div>

        {/* User + Role */}
        <div className="px-4 py-3 border-t border-white/10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-brand-600 flex items-center justify-center text-white text-sm font-semibold flex-shrink-0">
              {user?.email?.[0]?.toUpperCase() || 'U'}
            </div>
            <div className="min-w-0">
              <div className="text-white text-sm font-medium truncate">{user?.username || user?.email}</div>
              <span className={`text-[10px] px-1.5 py-0.5 rounded-full ${badge.color}`}>{badge.label}</span>
            </div>
          </div>
        </div>
      </aside>
    </>
  )
}

export default function AppShell({ children }) {
  const [sidebarOpen, setSidebarOpen] = useState(false)

  return (
    <div className="min-h-screen bg-surface-50">
      <Sidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} />

      <div className="main-content">
        <header className="topbar">
          <button
            onClick={() => setSidebarOpen(true)}
            className="lg:hidden p-2 rounded-lg text-slate-500 hover:bg-slate-100"
          >
            <Menu size={20} />
          </button>
          <div className="flex-1" />
        </header>

        <main className="p-6">
          <div className="page-enter">
            {children}
          </div>
        </main>
      </div>
    </div>
  )
}
