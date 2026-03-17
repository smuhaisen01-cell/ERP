import { useState, useEffect } from 'react'
import { Loader2 } from 'lucide-react'
import { useAuth } from '../../contexts/AuthContext'

export default function HRPage() {
  const { api } = useAuth()
  const [status, setStatus] = useState('loading...')
  const [employees, setEmployees] = useState([])
  const [departments, setDepartments] = useState([])

  useEffect(() => {
    const load = async () => {
      try {
        const empRes = await api.get('/hr/employees/')
        setEmployees(empRes.data.results || [])
        const deptRes = await api.get('/hr/departments/')
        setDepartments(deptRes.data.results || [])
        setStatus('loaded')
      } catch (err) {
        setStatus('error: ' + (err.response?.status || err.message))
      }
    }
    load()
  }, [])

  return (
    <div className="p-6">
      <h1 className="text-2xl font-bold mb-4">HR Debug</h1>
      <p className="mb-4">Status: <strong>{status}</strong></p>
      <p className="mb-2">Employees: {employees.length}</p>
      <p className="mb-2">Departments: {departments.length}</p>
      <ul className="space-y-1">
        {employees.map(e => (
          <li key={e.id} className="text-sm">{e.employee_number} — {e.name_en} — {e.basic_salary} SAR</li>
        ))}
      </ul>
    </div>
  )
}