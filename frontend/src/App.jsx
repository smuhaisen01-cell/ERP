import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { Toaster } from 'react-hot-toast'
import { LangProvider } from './contexts/LangContext'
import { AuthProvider, useAuth } from './contexts/AuthContext'
import AppShell from './components/layout/AppShell'
import LoginPage from './pages/auth/LoginPage'
import DashboardPage from './pages/dashboard/DashboardPage'
import InvoicingPage from './pages/invoicing/InvoicingPage'
import POSPage from './pages/pos/POSPage'
import HRPage from './pages/hr/HRPage'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  return isAuthenticated ? children : <Navigate to="/login" replace />
}

export default function App() {
  return (
    <LangProvider>
      <AuthProvider>
        <BrowserRouter basename="/app">
          <Routes>
            <Route path="/login" element={<LoginPage />} />
            <Route path="/*" element={
              <ProtectedRoute>
                <AppShell>
                  <Routes>
                    <Route index element={<Navigate to="dashboard" replace />} />
                    <Route path="dashboard" element={<DashboardPage />} />
                    <Route path="invoicing/*" element={<InvoicingPage />} />
                    <Route path="pos" element={<POSPage />} />
                    <Route path="hr/*" element={<HRPage />} />
                  </Routes>
                </AppShell>
              </ProtectedRoute>
            } />
            <Route path="*" element={<Navigate to="/dashboard" replace />} />
          </Routes>
        </BrowserRouter>
        <Toaster position="top-center" toastOptions={{
          style: { fontFamily: 'var(--font-primary)', borderRadius: '10px' }
        }} />
      </AuthProvider>
    </LangProvider>
  )
}
