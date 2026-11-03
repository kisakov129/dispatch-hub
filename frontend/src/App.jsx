import { useEffect, useMemo, useState } from 'react'
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
  const [jobs, setJobs] = useState([])
  const [summary, setSummary] = useState(null)
  const [search, setSearch] = useState('')
  const [status, setStatus] = useState('All statuses')
  const [loading, setLoading] = useState(true)
  const [showCreate, setShowCreate] = useState(false)
  const [saving, setSaving] = useState(false)
  const [form, setForm] = useState({ customer: '', pickup: '', delivery: '', date: new Date().toISOString().slice(0, 10), priority: 'Medium' })

  useEffect(() => {
    const load = async () => {
      try {
        const [jobsResponse, summaryResponse] = await Promise.all([fetch('http://localhost:8000/api/jobs'), fetch('http://localhost:8000/api/dashboard')])
        if (!jobsResponse.ok || !summaryResponse.ok) throw new Error('API unavailable')
        setJobs(await jobsResponse.json())
        setSummary(await summaryResponse.json())
      } catch {
        setJobs(demoJobs)
        setSummary({ total: 6, pending: 2, active: 2, completed: 2 })
      } finally { setLoading(false) }
    }
    load()
  }, [])

  const filteredJobs = useMemo(() => jobs.filter((job) => {
    const matchesSearch = `${job.id} ${job.customer} ${job.pickup} ${job.delivery}`.toLowerCase().includes(search.toLowerCase())
    return matchesSearch && (status === 'All statuses' || job.status === status)
  }), [jobs, search, status])

  const stats = summary ? [
    { label: 'Total jobs', value: summary.total, change: '+12.5%', icon: icons.jobs, tone: 'blue' },
    { label: 'Pending jobs', value: summary.pending, change: '+4.2%', icon: '◷', tone: 'amber' },
    { label: 'Active jobs', value: summary.active, change: '+8.1%', icon: icons.truck, tone: 'purple' },
    { label: 'Completed jobs', value: summary.completed, change: '+16.8%', icon: icons.check, tone: 'green' },
  ] : []

  const updateForm = (event) => setForm({ ...form, [event.target.name]: event.target.value })

  const createJob = async (event) => {
    event.preventDefault()
    setSaving(true)
    try {
      const response = await fetch('http://localhost:8000/api/jobs', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(form) })
      if (!response.ok) throw new Error('Unable to create job')
      const job = await response.json()
      setJobs((current) => [job, ...current])
      setSummary((current) => ({ ...current, total: current.total + 1, pending: current.pending + 1 }))
    } catch {
      const job = { ...form, id: `JOB-${1050 + jobs.length}`, status: 'Pending', driver: null }
      setJobs((current) => [job, ...current])
      setSummary((current) => ({ ...current, total: current.total + 1, pending: current.pending + 1 }))
    } finally {
      setSaving(false)
      setShowCreate(false)
      setForm({ customer: '', pickup: '', delivery: '', date: new Date().toISOString().slice(0, 10), priority: 'Medium' })
    }
  }

  return <div className="app-shell">
    <aside className="sidebar">
      <div className="brand"><span className="brand-mark">D</span><span>Dispatch<span className="brand-accent">Hub</span></span></div>
      <div className="workspace-label">WORKSPACE</div>
      <nav><NavItem icon={icons.grid} label="Dashboard" active /><NavItem icon={icons.jobs} label="Jobs" /><NavItem icon={icons.drivers} label="Drivers" /><NavItem icon={icons.dispatch} label="Dispatches" /><NavItem icon={icons.reports} label="Reports" /></nav>
      <div className="sidebar-bottom"><NavItem icon={icons.settings} label="Settings" /><div className="help-card"><strong>Need a hand?</strong><span>Check out our help center</span><button>Visit help center <span>→</span></button></div><div className="user-card"><div className="avatar">JD</div><div><strong>Jordan Davis</strong><span>Administrator</span></div><span className="user-more">•••</span></div></div>
    </aside>
    <main className="main-content">
      <header className="topbar"><div className="breadcrumb"><span>Workspace</span><b>/</b><strong>Dashboard</strong></div><div className="topbar-actions"><div className="global-search"><span>{icons.search}</span><input placeholder="Search anything..." /><kbd>⌘ K</kbd></div><button className="icon-button">{icons.bell}<i /></button><div className="top-avatar">JD</div></div></header>
      <div className="page-content">
        <section className="page-heading"><div><div className="eyebrow">TUESDAY, NOVEMBER 3, 2026</div><h1>Good morning, Jordan <span>👋</span></h1><p>Here’s what’s happening with your dispatch operations today.</p></div><button className="primary-button" onClick={() => setShowCreate(true)}><span>{icons.plus}</span> Create new job</button></section>
        <section className="stats-grid">{stats.map((stat) => <div className="stat-card" key={stat.label}><div className={`stat-icon ${stat.tone}`}>{stat.icon}</div><div className="stat-details"><span>{stat.label}</span><strong>{loading ? '—' : stat.value}</strong><small><em>{stat.change}</em> vs. last month</small></div><span className="stat-menu">•••</span></div>)}</section>
        <section className="dashboard-grid"><div className="panel status-panel"><div className="panel-heading"><div><h2>Jobs by status</h2><p>Overview of your current job pipeline</p></div><button className="select-button">This week <span>⌄</span></button></div><div className="chart-layout"><div className="donut"><div><strong>{summary?.total ?? '—'}</strong><span>Total jobs</span></div></div><div className="legend"><Legend color="blue" label="Completed" value={summary?.completed ?? '—'} percent="33.3%" /><Legend color="purple" label="Active" value={summary?.active ?? '—'} percent="33.3%" /><Legend color="amber" label="Pending" value={summary?.pending ?? '—'} percent="33.3%" /></div></div></div><div className="panel activity-panel"><div className="panel-heading"><div><h2>Recent activity</h2><p>Latest updates from your team</p></div><button className="link-button">View all <span>→</span></button></div><div className="activity-list"><Activity icon={icons.check} tone="green" title="Job completed" text="JOB-1046 was marked completed" time="12 min ago" /><Activity icon={icons.dispatch} tone="purple" title="New dispatch assigned" text="Marcus Johnson assigned to JOB-1048" time="38 min ago" /><Activity icon={icons.plus} tone="blue" title="New job created" text="JOB-1047 added by Jordan Davis" time="1 hr ago" /></div></div></section>
        <section className="panel jobs-panel"><div className="panel-heading jobs-heading"><div><h2>Recent jobs</h2><p>Manage and track your latest jobs</p></div><button className="link-button">View all jobs <span>→</span></button></div><div className="table-toolbar"><div className="table-search"><span>{icons.search}</span><input value={search} onChange={(event) => setSearch(event.target.value)} placeholder="Search jobs..." /></div><select value={status} onChange={(event) => setStatus(event.target.value)}><option>All statuses</option><option>Pending</option><option>Active</option><option>Completed</option></select><button className="filter-button">☷ Filters</button></div><div className="table-wrap"><table><thead><tr><th>JOB ID</th><th>CUSTOMER</th><th>ROUTE</th><th>DATE</th><th>PRIORITY</th><th>STATUS</th><th>DRIVER</th><th /></tr></thead><tbody>{filteredJobs.map((job) => <tr key={job.id}><td><strong className="job-id">{job.id}</strong></td><td><strong>{job.customer}</strong></td><td><span className="route"><span>{job.pickup}</span><b>→</b><span>{job.delivery}</span></span></td><td>{new Date(`${job.date}T12:00:00`).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</td><td><span className={`priority ${job.priority.toLowerCase()}`}><i />{job.priority}</span></td><td><span className={`status ${job.status.toLowerCase()}`}><i />{job.status}</span></td><td>{job.driver ? <span className="driver"><span className="mini-avatar">{job.driver.split(' ').map((part) => part[0]).join('')}</span>{job.driver}</span> : <span className="unassigned">Unassigned</span>}</td><td><button className="row-more">•••</button></td></tr>)}</tbody></table>{filteredJobs.length === 0 && <div className="empty-state">No jobs match your search.</div>}</div></section>
        {showCreate && <div className="modal-backdrop" onMouseDown={(event) => event.target === event.currentTarget && setShowCreate(false)}><form className="job-modal" onSubmit={createJob}><div className="modal-heading"><div><h2>Create new job</h2><p>Add a job to your dispatch pipeline.</p></div><button type="button" className="modal-close" onClick={() => setShowCreate(false)}>×</button></div><label>Customer<input name="customer" value={form.customer} onChange={updateForm} placeholder="e.g. Acme Logistics" required minLength="2" /></label><div className="form-row"><label>Pickup location<input name="pickup" value={form.pickup} onChange={updateForm} placeholder="e.g. Dallas, TX" required minLength="2" /></label><label>Delivery location<input name="delivery" value={form.delivery} onChange={updateForm} placeholder="e.g. Austin, TX" required minLength="2" /></label></div><div className="form-row"><label>Scheduled date<input type="date" name="date" value={form.date} onChange={updateForm} required /></label><label>Priority<select name="priority" value={form.priority} onChange={updateForm}><option>Low</option><option>Medium</option><option>High</option></select></label></div><div className="modal-actions"><button type="button" className="cancel-button" onClick={() => setShowCreate(false)}>Cancel</button><button type="submit" className="primary-button" disabled={saving}>{saving ? 'Creating...' : 'Create job'}</button></div></form></div>}
      </div>
    </main>
  </div>
}

function NavItem({ icon, label, active }) { return <a className={`nav-item ${active ? 'active' : ''}`} href={`#${label.toLowerCase()}`}><span>{icon}</span>{label}{label === 'Jobs' && <b>6</b>}</a> }
function Legend({ color, label, value, percent }) { return <div className="legend-row"><i className={color} /><span>{label}</span><strong>{value}</strong><small>{percent}</small></div> }
function Activity({ icon, tone, title, text, time }) { return <div className="activity-row"><span className={`activity-icon ${tone}`}>{icon}</span><div><strong>{title}</strong><span>{text}</span></div><time>{time}</time></div> }

export default App
