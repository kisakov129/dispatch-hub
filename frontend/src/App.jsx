import { useCallback, useEffect, useMemo, useState } from 'react'
import './App.css'

const demoJobs = [
  { id: 'JOB-1048', customer: 'Acme Logistics', pickup: 'Dallas, TX', delivery: 'Austin, TX', date: '2026-11-03', status: 'Active', priority: 'High', driver: 'Marcus Johnson' },
  { id: 'JOB-1047', customer: 'Northstar Retail', pickup: 'Fort Worth, TX', delivery: 'Houston, TX', date: '2026-11-03', status: 'Pending', priority: 'Medium', driver: null },
  { id: 'JOB-1046', customer: 'Greenline Foods', pickup: 'Plano, TX', delivery: 'Waco, TX', date: '2026-11-02', status: 'Completed', priority: 'Low', driver: 'Sarah Williams' },
  { id: 'JOB-1045', customer: 'Summit Medical', pickup: 'Irving, TX', delivery: 'San Antonio, TX', date: '2026-11-02', status: 'Active', priority: 'High', driver: 'David Chen' },
  { id: 'JOB-1044', customer: 'Bluebird Commerce', pickup: 'Arlington, TX', delivery: 'Denton, TX', date: '2026-11-01', status: 'Completed', priority: 'Medium', driver: 'Marcus Johnson' },
]

const icons = { grid: '▦', jobs: '▤', drivers: '♙', dispatch: '⇄', reports: '▧', settings: '⚙', search: '⌕', bell: '♢', plus: '+', truck: '▰', check: '✓' }

function App() {
  const [authToken, setAuthToken] = useState(() => localStorage.getItem('dispatchhub_token'))
  const [currentUser, setCurrentUser] = useState(() => JSON.parse(localStorage.getItem('dispatchhub_user') || 'null'))
  const [jobs, setJobs] = useState([])
  const [drivers, setDrivers] = useState([])
  const [dispatches, setDispatches] = useState([])
  const [summary, setSummary] = useState(null)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('All statuses')
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [editingJob, setEditingJob] = useState(null)
  const [detailJob, setDetailJob] = useState(null)
  const [assigningJob, setAssigningJob] = useState(null)
  const [assignmentSaving, setAssignmentSaving] = useState(false)
  const [selectedDriver, setSelectedDriver] = useState('')

  const apiFetch = useCallback((url, options = {}) => fetch(url, { ...options, headers: { ...options.headers, Authorization: `Bearer ${authToken}` } }), [authToken])

  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ customer: '', pickup: '', delivery: '', date: new Date().toISOString().slice(0, 10), priority: 'Medium' })

  useEffect(() => {
    const load = async () => {
      try {
        const [jobsResponse, summaryResponse, driversResponse, dispatchesResponse] = await Promise.all([apiFetch('http://localhost:8000/api/jobs'), apiFetch('http://localhost:8000/api/dashboard'), apiFetch('http://localhost:8000/api/drivers'), apiFetch('http://localhost:8000/api/dispatches')])
        if (!jobsResponse.ok || !summaryResponse.ok || !driversResponse.ok || !dispatchesResponse.ok) throw new Error('API unavailable')
        setJobs(await jobsResponse.json())
        setSummary(await summaryResponse.json())
        setDrivers(await driversResponse.json())
        setDispatches(await dispatchesResponse.json())
      } catch {
        setJobs(demoJobs)
        setSummary({ total: 6, pending: 2, active: 2, completed: 2 })
        setDrivers([{ id: 'DRV-001', name: 'Marcus Johnson', phone: '(214) 555-0182', availability: 'On a job', assigned_jobs: 2 }, { id: 'DRV-002', name: 'Sarah Williams', phone: '(469) 555-0137', availability: 'Available', assigned_jobs: 1 }, { id: 'DRV-003', name: 'David Chen', phone: '(972) 555-0164', availability: 'On a job', assigned_jobs: 1 }, { id: 'DRV-004', name: 'Emily Rodriguez', phone: '(817) 555-0191', availability: 'Available', assigned_jobs: 0 }])
        setDispatches(demoJobs.filter((job) => job.driver))
      } finally { setLoading(false) }
    }
    load()
  }, [apiFetch])

  const filteredJobs = useMemo(() => jobs.filter((job) => {
    const matchesSearch = `${job.id} ${job.customer} ${job.pickup} ${job.delivery}`.toLowerCase().includes(search.toLowerCase())
    return matchesSearch && (status === 'All statuses' || job.status === status)
  }), [jobs, search, status])

  const stats = summary ? [
    { label: 'Total loads', value: summary.total, change: '+12.5%', icon: icons.jobs, tone: 'blue' },
    { label: 'Pending loads', value: summary.pending, change: '+4.2%', icon: '◷', tone: 'amber' },
    { label: 'Active loads', value: summary.active, change: '+8.1%', icon: icons.truck, tone: 'purple' },
    { label: 'Completed loads', value: summary.completed, change: '+16.8%', icon: icons.check, tone: 'green' },
  ] : []

  const updateForm = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  const openCreate = () => {
    setEditingJob(null)
    setForm({ customer: '', pickup: '', delivery: '', date: new Date().toISOString().slice(0, 10), priority: 'Medium', status: 'Pending' })
    setShowCreate(true)
  }

  const openEdit = (job) => {
    setEditingJob(job)
    setForm({ customer: job.customer, pickup: job.pickup, delivery: job.delivery, date: job.date, priority: job.priority, status: job.status })
    setShowCreate(true)
  }

  const saveJob = async (event) => {
    event.preventDefault()
    setSaving(true)
    try {
      const response = await apiFetch(`http://localhost:8000/api/jobs${editingJob ? `/${editingJob.id}` : ''}`, { method: editingJob ? 'PUT' : 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      if (!response.ok) throw new Error('Unable to create job')
      const job = await response.json()
      setJobs((current) => editingJob ? current.map((item) => item.id === job.id ? job : item) : [job, ...current])
      if (!editingJob) setSummary((current) => ({ ...current, total: current.total + 1, pending: current.pending + 1 }))
    } catch {
      const job = { ...form, id: editingJob?.id || `JOB-${1050 + jobs.length}`, driver: editingJob?.driver || null }
      setJobs((current) => editingJob ? current.map((item) => item.id === job.id ? job : item) : [job, ...current])
      if (!editingJob) setSummary((current) => ({ ...current, total: current.total + 1, pending: current.pending + 1 }))
    } finally {
      setSaving(false)
      setShowCreate(false)
      setForm({ customer: '', pickup: '', delivery: '', date: new Date().toISOString().slice(0, 10), priority: 'Medium' })
      setEditingJob(null)
    }
  }

  const deleteJob = async (job) => {
    if (!window.confirm(`Delete ${job.id}? This action cannot be undone.`)) return
    try { await apiFetch(`http://localhost:8000/api/jobs/${job.id}`, { method: 'DELETE' }) } catch { /* keep local state in offline mode */ }
    setJobs((current) => current.filter((item) => item.id !== job.id))
    setSummary((current) => ({ ...current, total: current.total - 1, pending: current.pending - (job.status === 'Pending' ? 1 : 0), active: current.active - (job.status === 'Active' ? 1 : 0), completed: current.completed - (job.status === 'Completed' ? 1 : 0) }))
  }

  const assignDriver = async (event) => {
    event.preventDefault()
    if (!selectedDriver) return
    setAssignmentSaving(true)
    try {
      const response = await apiFetch(`http://localhost:8000/api/jobs/${assigningJob.id}/assign`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ driver_id: selectedDriver }) })
      if (!response.ok) throw new Error('Unable to assign driver')
      const updatedJob = await response.json()
      setJobs((current) => current.map((job) => job.id === updatedJob.id ? updatedJob : job))
      setSummary((current) => ({ ...current, pending: Math.max(0, current.pending - (assigningJob.status === 'Pending' ? 1 : 0)), active: current.active + 1 }))
      setDrivers((current) => current.map((driver) => driver.id === selectedDriver ? { ...driver, availability: 'On a job', assigned_jobs: driver.assigned_jobs + 1 } : driver))
      setDispatches((current) => [updatedJob, ...current.filter((job) => job.id !== updatedJob.id)])
    } catch {
      const driver = drivers.find((item) => item.id === selectedDriver)
      if (driver?.availability !== 'Available') return
      setJobs((current) => current.map((job) => job.id === assigningJob.id ? { ...job, driver: driver.name, status: 'Active' } : job))
      setSummary((current) => ({ ...current, pending: Math.max(0, current.pending - (assigningJob.status === 'Pending' ? 1 : 0)), active: current.active + 1 }))
      setDrivers((current) => current.map((item) => item.id === selectedDriver ? { ...item, availability: 'On a job', assigned_jobs: item.assigned_jobs + 1 } : item))
      setDispatches((current) => [{ ...assigningJob, driver: driver.name, status: 'Active' }, ...current.filter((job) => job.id !== assigningJob.id)])
    } finally {
      setAssignmentSaving(false)
      setAssigningJob(null)
      setSelectedDriver('')
    }
  }

  if (!authToken) return <LoginScreen onLogin={(auth) => { localStorage.setItem('dispatchhub_token', auth.access_token); localStorage.setItem('dispatchhub_user', JSON.stringify(auth.user)); setAuthToken(auth.access_token); setCurrentUser(auth.user) }} />

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">D</span><span>Dispatch<span className="brand-accent">Hub</span></span></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav><NavItem icon={icons.grid} label="Dashboard" active /><NavItem icon={icons.jobs} label="Loads" /><NavItem icon={icons.drivers} label="Drivers" /><NavItem icon={icons.dispatch} label="Dispatches" /><NavItem icon={icons.reports} label="Reports" /></nav>
      <div className="sidebar-bottom"><NavItem icon={icons.settings} label="Settings" /><div className="help-card"><strong>Need a hand?</strong><span>Check out our help center</span><button>Visit help center <span>→</span></button></div><div className="user-card"><div className="avatar">JD</div><div><strong>Jordan Davis</strong><span>Administrator</span></div><span className="user-more">•••</span></div></div>
    </aside>
    <main className="main-content">
      <header className="topbar"><div className="breadcrumb"><span>Workspace</span><b>/</b><strong>Dashboard</strong></div><div className="topbar-actions"><div className="global-search"><span>{icons.search}</span><input placeholder="Search anything..." /><kbd>⌘ K</kbd></div><button className="icon-button">{icons.bell}<i /></button><div className="top-avatar">JD</div></div></header>
      <div className="page-content">
        <section className="page-heading"><div><div className="eyebrow">TUESDAY, NOVEMBER 3, 2026</div><h1>Good morning, Jordan <span>👋</span></h1><p>Here’s what’s happening with your dispatch operations today.</p></div><button className="primary-button" onClick={openCreate}><span>{icons.plus}</span> Create new job</button></section>
        <section className="stats-grid">{stats.map((stat) => <div className="stat-card" key={stat.label}><div className={`stat-icon ${stat.tone}`}>{stat.icon}</div><div className="stat-details"><span>{stat.label}</span><strong>{loading ? '—' : stat.value}</strong><small><em>{stat.change}</em> vs. last month</small></div><span className="stat-menu">•••</span></div>)}</section>
        <section className="dashboard-grid"><div className="panel status-panel"><div className="panel-heading"><div><h2>Jobs by status</h2><p>Overview of your current job pipeline</p></div><button className="select-button">This week <span>⌄</span></button></div><div className="chart-layout"><div className="donut"><div><strong>{summary?.total ?? '—'}</strong><span>Total jobs</span></div></div><div className="legend"><Legend color="blue" label="Completed" value={summary?.completed ?? '—'} percent="33.3%" /><Legend color="purple" label="Active" value={summary?.active ?? '—'} percent="33.3%" /><Legend color="amber" label="Pending" value={summary?.pending ?? '—'} percent="33.3%" /></div></div></div><div className="panel activity-panel"><div className="panel-heading"><div><h2>Recent activity</h2><p>Latest updates from your team</p></div><button className="link-button">View all <span>→</span></button></div><div className="activity-list"><Activity icon={icons.check} tone="green" title="Job completed" text="JOB-1046 was marked completed" time="12 min ago" /><Activity icon={icons.dispatch} tone="purple" title="New dispatch assigned" text="Marcus Johnson assigned to JOB-1048" time="38 min ago" /><Activity icon={icons.plus} tone="blue" title="New job created" text="JOB-1047 added by Jordan Davis" time="1 hr ago" /></div></div></section>
        <section className="panel jobs-panel"><div className="panel-heading jobs-heading"><div><h2>Recent jobs</h2><p>Manage and track your latest jobs</p></div><button className="link-button">View all jobs <span>→</span></button></div><div className="table-toolbar"><div className="table-search"><span>{icons.search}</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search jobs..." /></div><select value={status} onChange={(event) => setStatus(event.target.value)}><option>All statuses</option><option>Pending</option><option>Active</option><option>Completed</option></select><button className="filter-button">☷ Filters</button></div><div className="table-wrap"><table><thead><tr><th>JOB ID</th><th>CUSTOMER</th><th>ROUTE</th><th>DATE</th><th>PRIORITY</th><th>STATUS</th><th>DRIVER</th><th /></tr></thead><tbody>{filteredJobs.map((job) => <tr key={job.id}><td><button className="job-link" onClick={() => setDetailJob(job)}>{job.id}</button></td><td><strong>{job.customer}</strong></td><td><span className="route"><span>{job.pickup}</span><b>→</b><span>{job.delivery}</span></span></td><td>{new Date(`${job.date}T12:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</td><td><span className={`priority ${job.priority.toLowerCase()}`}><i />{job.priority}</span></td><td><span className={`status ${job.status.toLowerCase()}`}><i />{job.status}</span></td><td>{job.driver ? <span className="driver"><span className="mini-avatar">{job.driver.split(' ').map((part) => part[0]).join('')}</span>{job.driver}</span> : <button className="assign-link" onClick={() => { setAssigningJob(job); setSelectedDriver('') }}>Assign driver</button>}</td><td><div className="row-actions"><button onClick={() => openEdit(job)}>Edit</button>{currentUser?.role === 'admin' && <button onClick={() => deleteJob(job)}>Delete</button>}</div></td></tr>)}</tbody></table>{filteredJobs.length === 0 && <div className="empty-state">No jobs match your search.</div>}</div></section>
        <section className="panel drivers-panel"><div className="panel-heading"><div><h2>Driver availability</h2><p>See who is ready for the next dispatch</p></div><button className="link-button">Manage drivers <span>→</span></button></div><div className="driver-grid">{drivers.map((driver) => <div className="driver-card" key={driver.id}><div className="driver-card-top"><span className="driver-avatar">{driver.name.split(' ').map((part) => part[0]).join('')}</span><span className={`availability ${driver.availability.toLowerCase().replace(' ', '-')}`}><i />{driver.availability}</span></div><strong>{driver.name}</strong><span>{driver.phone}</span><small>{driver.assigned_jobs} assigned {driver.assigned_jobs === 1 ? 'job' : 'jobs'}</small></div>)}</div></section>
        {showCreate && <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setShowCreate(false)}><form className="job-modal" onSubmit={saveJob}><div className="modal-heading"><div><h2>{editingJob ? 'Edit job' : 'Create new job'}</h2><p>{editingJob ? 'Update job details and save your changes.' : 'Add a job to your dispatch pipeline.'}</p></div><button type="button" className="modal-close" onClick={() => setShowCreate(false)}>×</button></div><label>Customer<input name="customer" value={form.customer} onChange={updateForm} placeholder="e.g. Acme Logistics" required minLength="2" /></label><div className="form-row"><label>Pickup location<input name="pickup" value={form.pickup} onChange={updateForm} placeholder="e.g. Dallas, TX" required minLength="2" /></label><label>Delivery location<input name="delivery" value={form.delivery} onChange={updateForm} placeholder="e.g. Austin, TX" required minLength="2" /></label></div><div className="form-row"><label>Scheduled date<input type="date" name="date" value={form.date} onChange={updateForm} required /></label><label>Priority<select name="priority" value={form.priority} onChange={updateForm}><option>Low</option><option>Medium</option><option>High</option></select></label></div>{editingJob && <label>Status<select name="status" value={form.status} onChange={updateForm}><option>Pending</option><option>Active</option><option>Completed</option></select></label>}<div className="modal-actions"><button type="button" className="cancel-button" onClick={() => setShowCreate(false)}>Cancel</button><button type="submit" className="primary-button" disabled={saving}>{saving ? 'Saving...' : editingJob ? 'Save changes' : 'Create job'}</button></div></form></div>}
        {detailJob && <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setDetailJob(null)}><div className="job-modal detail-modal"><div className="modal-heading"><div><span className="eyebrow">JOB DETAILS</span><h2>{detailJob.id}</h2></div><button className="modal-close" onClick={() => setDetailJob(null)}>×</button></div><div className="detail-grid"><div><span>Customer</span><strong>{detailJob.customer}</strong></div><div><span>Status</span><strong className={`status ${detailJob.status.toLowerCase()}`}><i />{detailJob.status}</strong></div><div><span>Pickup</span><strong>{detailJob.pickup}</strong></div><div><span>Delivery</span><strong>{detailJob.delivery}</strong></div><div><span>Scheduled date</span><strong>{detailJob.date}</strong></div><div><span>Priority</span><strong>{detailJob.priority}</strong></div></div><div className="modal-actions"><button className="cancel-button" onClick={() => setDetailJob(null)}>Close</button><button className="primary-button" onClick={() => { setDetailJob(null); openEdit(detailJob) }}>Edit job</button></div></div></div>}
        {assigningJob && <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setAssigningJob(null)}><form className="job-modal" onSubmit={assignDriver}><div className="modal-heading"><div><h2>Assign driver</h2><p>Choose an available driver for {assigningJob.id}.</p></div><button type="button" className="modal-close" onClick={() => setAssigningJob(null)}>×</button></div><label>Available driver<select value={selectedDriver} onChange={(event) => setSelectedDriver(event.target.value)} required><option value="">Select a driver</option>{drivers.filter((driver) => driver.availability === 'Available').map((driver) => <option key={driver.id} value={driver.id}>{driver.name} · {driver.assigned_jobs} assigned {driver.assigned_jobs === 1 ? 'job' : 'jobs'}</option>)}</select></label>{drivers.filter((driver) => driver.availability === 'Available').length === 0 && <div className="empty-state">No drivers are currently available.</div>}<div className="modal-actions"><button type="button" className="cancel-button" onClick={() => setAssigningJob(null)}>Cancel</button><button type="submit" className="primary-button" disabled={assignmentSaving || !selectedDriver}>{assignmentSaving ? 'Assigning...' : 'Assign driver'}</button></div></form></div>}
        <section className="panel dispatch-panel"><div className="panel-heading"><div><h2>Active dispatches</h2><p>Track jobs currently assigned to drivers</p></div><span className="dispatch-count">{dispatches.length} active</span></div><div className="dispatch-list">{dispatches.length === 0 ? <div className="empty-state">No assigned dispatches yet.</div> : dispatches.map((dispatch) => <div className="dispatch-row" key={dispatch.id}><div className="dispatch-job"><strong>{dispatch.id}</strong><span>{dispatch.customer}</span></div><div className="dispatch-route"><span>{dispatch.pickup}</span><b>→</b><span>{dispatch.delivery}</span></div><div className="dispatch-driver"><span className="mini-avatar">{dispatch.driver.split(' ').map((part) => part[0]).join('')}</span>{dispatch.driver}</div><span className={`status ${dispatch.status.toLowerCase()}`}><i />{dispatch.status}</span></div>)}</div></section><button className="logout-button" onClick={() => { localStorage.removeItem('dispatchhub_token'); window.location.reload() }}>Sign out</button>
      </div>
    </main>
  </div>
}

function NavItem({ icon, label, active }) { return <a className={`nav-item ${active ? 'active' : ''}`} href={`#${label.toLowerCase()}`}><span>{icon}</span>{label}{label === 'Loads' && <b>6</b>}</a> }
function Legend({ color, label, value, percent }) { return <div className="legend-row"><i className={color} /><span>{label}</span><strong>{value}</strong><small>{percent}</small></div> }
function Activity({ icon, tone, title, text, time }) { return <div className="activity-row"><span className={`activity-icon ${tone}`}>{icon}</span><div><strong>{title}</strong><span>{text}</span></div><time>{time}</time></div> }

function LoginScreen({ onLogin }) {
  const [email, setEmail] = useState('admin@dispatchhub.local')
  const [password, setPassword] = useState('admin123')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const submit = async (event) => {
    event.preventDefault(); setLoading(true); setError('')
    try {
      const response = await fetch('http://localhost:8000/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ email, password }) })
      if (!response.ok) throw new Error('Invalid email or password')
      onLogin(await response.json())
    } catch (loginError) {
      if (email === 'admin@dispatchhub.local' && password === 'admin123') onLogin({ access_token: 'local-demo-token', user: { id: 'USR-001', name: 'Jordan Davis', email, role: 'admin' } })
      else setError(loginError.message)
    } finally { setLoading(false) }
  }
  return <div className="login-shell"><form className="login-card" onSubmit={submit}><div className="brand login-brand"><span className="brand-mark">D</span><span>Dispatch<span className="brand-accent">Hub</span></span></div><div className="login-heading"><h1>Welcome back</h1><p>Sign in to manage your dispatch operations.</p></div><label>Email address<input type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /></label><label>Password<input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required /></label>{error && <div className="login-error">{error}</div>}<button className="primary-button login-button" disabled={loading}>{loading ? 'Signing in...' : 'Sign in'}</button><small className="login-hint">Demo: admin@dispatchhub.local / admin123</small></form></div>
}

export default App
