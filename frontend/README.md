# ERP Frontend — React SPA

## Stack
- **React 18** + **Vite** — fast HMR dev, optimized production build
- **Tailwind CSS** — utility-first, RTL-aware styling
- **Recharts** — KPI and analytics charts
- **React Router v6** — client-side routing
- **Framer Motion** — page transitions
- **react-hot-toast** — notifications
- **Zustand** — lightweight state management
- **Axios** — API calls with JWT auto-refresh

## Screens
| Screen | Path | Description |
|--------|------|-------------|
| Login | `/app/login` | Bilingual auth with split layout |
| Dashboard | `/app/dashboard` | KPIs, revenue chart, ZATCA donut, quick actions |
| Invoicing | `/app/invoicing` | ZATCA Phase 2 invoice list + new invoice modal |
| POS | `/app/pos` | Touchscreen POS terminal with payment modal |
| HR | `/app/hr` | Employees, payroll run, saudization tracker |

## Language / RTL
Toggle between **Arabic (RTL)** and **English (LTR)** live via the sidebar or login page.  
The `dir` attribute and font family switch automatically.

---

## Local Development

```bash
# 1. Install
cd frontend
npm install

# 2. Start Vite dev server (proxies API to Django on :8000)
npm run dev
# → http://localhost:5173/app/login

# 3. Run Django alongside (separate terminal)
python manage.py runserver
```

---

## Production Build

```bash
cd frontend
npm run build
# Output: ../static/spa/  (Django picks this up via STATICFILES_DIRS)
```

Docker builds React automatically in Stage 1 before Django starts.

---

## File Structure

```
frontend/
├── index.html                  # Entry HTML
├── vite.config.js              # Build config — output → ../static/spa/
├── tailwind.config.js          # Design tokens (brand, sand, surface colors)
├── src/
│   ├── main.jsx                # React entry
│   ├── App.jsx                 # Router + providers
│   ├── index.css               # Global styles, CSS vars, component classes
│   ├── contexts/
│   │   ├── LangContext.jsx     # AR/EN translations + RTL/LTR switching
│   │   └── AuthContext.jsx     # JWT auth + axios interceptors
│   ├── components/
│   │   └── layout/
│   │       └── AppShell.jsx    # Sidebar + topbar shell
│   └── pages/
│       ├── auth/LoginPage.jsx
│       ├── dashboard/DashboardPage.jsx
│       ├── invoicing/InvoicingPage.jsx
│       ├── pos/POSPage.jsx
│       └── hr/HRPage.jsx
```

---

## Connecting to Real API

All API calls use `/api/v1/` prefix (proxied in dev, same-origin in prod).  
Replace mock data in each page with `useEffect` + `api.get(...)` calls from `AuthContext`.

Example:
```jsx
import { useAuth } from '../../contexts/AuthContext'

const { api } = useAuth()
const [invoices, setInvoices] = useState([])

useEffect(() => {
  api.get('/api/v1/zatca/invoices/').then(r => setInvoices(r.data.results))
}, [])
```

JWT tokens are auto-refreshed by the Axios interceptor in `AuthContext.jsx`.
