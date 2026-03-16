/**
 * API service — centralized API calls for all modules.
 * Uses the axios instance from AuthContext (JWT auto-attached).
 */

// HR Module
export const hrAPI = {
  getDepartments: (api) => api.get('/hr/departments/'),
  createDepartment: (api, data) => api.post('/hr/departments/', data),

  getEmployees: (api) => api.get('/hr/employees/'),
  getEmployee: (api, id) => api.get(`/hr/employees/${id}/`),
  createEmployee: (api, data) => api.post('/hr/employees/', data),
  getGOSI: (api, id) => api.get(`/hr/employees/${id}/gosi/`),
  getEOSB: (api, id) => api.get(`/hr/employees/${id}/eosb/`),
  terminateEmployee: (api, id, data) => api.post(`/hr/employees/${id}/terminate/`, data),

  getPayrollRuns: (api) => api.get('/hr/payroll-runs/'),
  createPayrollRun: (api, data) => api.post('/hr/payroll-runs/', data),
  calculatePayroll: (api, id) => api.post(`/hr/payroll-runs/${id}/calculate/`),
  approvePayroll: (api, id) => api.post(`/hr/payroll-runs/${id}/approve/`),

  getSaudization: (api) => api.get('/hr/saudization/'),
  generateSaudization: (api) => api.post('/hr/saudization/generate/'),
}

// Accounting Module
export const accountingAPI = {
  getChartOfAccounts: (api) => api.get('/accounting/chart-of-accounts/?page_size=100'),
  createAccount: (api, data) => api.post('/accounting/chart-of-accounts/', data),

  getJournalEntries: (api) => api.get('/accounting/journal-entries/'),
  createJournalEntry: (api, data) => api.post('/accounting/journal-entries/', data),
  postJournalEntry: (api, id) => api.post(`/accounting/journal-entries/${id}/post_entry/`),
  reverseJournalEntry: (api, id) => api.post(`/accounting/journal-entries/${id}/reverse_entry/`),

  getVATReturns: (api) => api.get('/accounting/vat-returns/'),
  getZakatReturns: (api) => api.get('/accounting/zakat-returns/'),
}

// ZATCA Module
export const zatcaAPI = {
  getInvoices: (api) => api.get('/zatca/invoices/'),
  getInvoice: (api, id) => api.get(`/zatca/invoices/${id}/`),
  createInvoice: (api, data) => api.post('/zatca/invoices/', data),
  processInvoice: (api, id) => api.post(`/zatca/invoices/${id}/process/`),
  submitInvoice: (api, id) => api.post(`/zatca/invoices/${id}/submit/`),
  cancelInvoice: (api, id) => api.post(`/zatca/invoices/${id}/cancel/`),
  getAuditLog: (api) => api.get('/zatca/audit-log/'),
  getCredentials: (api) => api.get('/zatca/credentials/'),
}

// POS Module
export const posAPI = {
  getBranches: (api) => api.get('/pos/branches/'),
  getTerminals: (api) => api.get('/pos/terminals/'),
  setupDefault: (api) => api.post('/pos/terminals/setup_default/'),

  getSessions: (api) => api.get('/pos/sessions/'),
  createSession: (api, data) => api.post('/pos/sessions/', data),
  closeSession: (api, id, data) => api.post(`/pos/sessions/${id}/close/`, data),

  getTransactions: (api) => api.get('/pos/transactions/'),
  createTransaction: (api, data) => api.post('/pos/transactions/', data),
}

// Reports Module
export const reportsAPI = {
  getTrialBalance: (api, params) => api.get('/reports/trial-balance/', { params }),
  getIncomeStatement: (api, params) => api.get('/reports/income-statement/', { params }),
  getBalanceSheet: (api, params) => api.get('/reports/balance-sheet/', { params }),
  getVAT103: (api, params) => api.get('/reports/vat-103/', { params }),
  getHRSummary: (api) => api.get('/reports/hr-summary/'),
  getZATCAStatus: (api, params) => api.get('/reports/zatca-status/', { params }),
  getPOSDaily: (api, params) => api.get('/reports/pos-daily/', { params }),
}

// Users Module
export const usersAPI = {
  getUsers: (api) => api.get('/users/'),
  getUser: (api, id) => api.get(`/users/${id}/`),
  createUser: (api, data) => api.post('/users/', data),
  updateUser: (api, id, data) => api.patch(`/users/${id}/`, data),
  deleteUser: (api, id) => api.delete(`/users/${id}/`),
  changePassword: (api, id, data) => api.post(`/users/${id}/change_password/`, data),
  getMe: (api) => api.get('/users/me/'),
}
