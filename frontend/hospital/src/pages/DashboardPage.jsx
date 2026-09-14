import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { Auth } from '../services/auth';
import { apiFetch } from '../services/api';
import './dashboard.css';

// ===== Role Config Data (from dashboard.js) =====
const roleConfig = {
  'hospital-admin': {
    icon: '🏥', label: 'Hospital Admin', title: 'Hospital Dashboard',
    navItems: [
      { icon: '📊', label: 'Overview', active: true },
      { icon: '🛏️', label: 'Bed Management' },
      { icon: '🏥', label: 'Equipment Status' },
      { icon: '👤', label: 'Staff on Duty' },
      { icon: '📢', label: 'Transfer Requests', badge: 3 },
      { icon: '📈', label: 'Analytics' },
    ],
    metrics: [
      { icon: '🛏️', label: 'ICU Occupancy', value: '18/24', subtext: '75% occupied', trend: 'up', trendText: '+2 today' },
      { icon: '🏥', label: 'OT Rooms Active', value: '4/6', subtext: '2 available', trend: 'neutral', trendText: 'Stable' },
      { icon: '🛏️', label: 'Ward Occupancy', value: '142/180', subtext: '79% occupied', trend: 'up', trendText: '+5 today' },
      { icon: '👤', label: 'Staff On Duty', value: '56', subtext: 'Across all departments', trend: 'neutral', trendText: 'Full shift' },
      { icon: '📋', label: 'Equipment Active', value: '89%', subtext: '3 units in maintenance', trend: 'down', trendText: '-2 units' },
    ],
    mapTitle: 'Hospital Floor Plan', mapBadge: 'Live Occupancy',
    markers: [
      { icon: '🛏️', label: 'ICU Wing A', top: '20%', left: '15%', type: 'busy' },
      { icon: '🛏️', label: 'ICU Wing B', top: '20%', left: '45%', type: 'critical' },
      { icon: '🏥', label: 'OT Complex', top: '50%', left: '30%', type: 'hospital' },
      { icon: '🛏️', label: 'Ward 1', top: '70%', left: '20%', type: 'available' },
      { icon: '🛏️', label: 'Ward 2', top: '70%', left: '55%', type: 'busy' },
    ],
    legend: [{ color: '#16a34a', label: 'Available' }, { color: '#f59e0b', label: 'Busy' }, { color: '#dc2626', label: 'Critical' }, { color: '#1B4332', label: 'In Use' }],
    alerts: [
      { type: 'critical', title: 'ICU Wing B at 95% capacity', desc: 'Only 1 bed remaining. Consider diverting incoming patients.', time: '2 min ago' },
      { type: 'warning', title: 'Ventilator #VNT-04 maintenance due', desc: 'Scheduled maintenance overdue by 3 days.', time: '15 min ago' },
      { type: 'info', title: 'Transfer request: Cardiac patient', desc: 'From Metro General — requesting ICU bed for post-op recovery.', time: '22 min ago' },
      { type: 'success', title: 'Staff shift change complete', desc: 'Night shift fully staffed. 56 personnel on duty.', time: '1 hr ago' },
    ],
    bottomPanels: [
      { title: 'Pending Transfer Requests', badge: '3 Pending', type: 'table', headers: ['Patient', 'From', 'Condition', 'Status'], rows: [['R. Patel', 'Metro General', 'Cardiac Post-Op', 'critical:Urgent'], ['S. Kumar', 'City Clinic', 'Orthopedic', 'occupied:Pending'], ['M. Johnson', "St. Mary's", 'Neurology Consult', 'idle:Review']] },
      { title: 'Equipment Status', badge: '34 Total', type: 'stats', items: [{ icon: '💊', label: 'Ventilators', value: '12/14', bg: '#dcfce7' }, { icon: '🖥️', label: 'Monitors', value: '28/30', bg: '#e0e7ff' }, { icon: '💉', label: 'Infusion Pumps', value: '8/10', bg: '#fef3c7' }, { icon: '❤️', label: 'Defibrillators', value: '6/6', bg: '#fce7f3' }] }
    ]
  },
  'doctor': {
    icon: '💉', label: 'Doctor / Specialist', title: 'My Dashboard',
    navItems: [
      { icon: '📊', label: 'Overview', active: true }, { icon: '👤', label: 'My Patients' }, { icon: '🛏️', label: 'Find Beds' }, { icon: '📋', label: 'Consult Requests', badge: 5 }, { icon: '📢', label: 'Quick Transfer' }, { icon: '📅', label: 'Schedule' },
    ],
    metrics: [
      { icon: '👤', label: 'My Patients', value: '12', subtext: 'Currently admitted', trend: 'up', trendText: '+2 today' },
      { icon: '🛏️', label: 'Nearby Beds', value: '23', subtext: 'Within 10km radius', trend: 'down', trendText: '-4 since AM' },
      { icon: '📋', label: 'Consult Requests', value: '5', subtext: '2 urgent, 3 routine', trend: 'up', trendText: '+3 new' },
      { icon: '🏥', label: 'Dept. Occupancy', value: '82%', subtext: 'Cardiology Wing', trend: 'up', trendText: '+6%' },
    ],
    mapTitle: 'Nearby Available Beds', mapBadge: '23 beds found',
    markers: [
      { icon: '🏥', label: 'St. Jude — 8 beds', top: '30%', left: '25%', type: 'available' },
      { icon: '🏥', label: 'Metro Gen — 2 beds', top: '25%', left: '60%', type: 'busy' },
      { icon: '🏥', label: 'City Hospital — 6 beds', top: '55%', left: '40%', type: 'available' },
      { icon: '📍', label: 'You', top: '50%', left: '50%', type: 'hospital' },
    ],
    legend: [{ color: '#16a34a', label: '5+ Beds' }, { color: '#f59e0b', label: '1-4 Beds' }, { color: '#1B4332', label: 'Your Location' }],
    alerts: [
      { type: 'critical', title: 'Urgent consult: Neuro case', desc: 'Patient A. Singh, ICU-3, seizure activity — immediate consult needed.', time: '5 min ago' },
      { type: 'warning', title: 'Patient R. Patel labs ready', desc: 'Troponin levels elevated — review and update care plan.', time: '18 min ago' },
      { type: 'info', title: 'Bed available at St. Jude', desc: 'ICU bed opened up. Good match for transfer case #TR-441.', time: '30 min ago' },
      { type: 'success', title: 'Patient M. Lee discharged', desc: 'Recovery complete. Bed freed in Ward 2B.', time: '1 hr ago' },
    ],
    bottomPanels: [
      { title: 'My Patients', badge: '12 Active', type: 'table', headers: ['Patient', 'Room', 'Condition', 'Status'], rows: [['A. Singh', 'ICU-3', 'Seizure Disorder', 'critical:Critical'], ['R. Patel', 'CCU-1', 'MI Recovery', 'occupied:Monitoring'], ['J. Williams', 'Ward 2B-4', 'Post-CABG', 'available:Stable']] },
      { title: 'Quick Actions', type: 'actions', actions: [{ icon: '📢', label: 'Initiate Transfer', style: 'primary' }, { icon: '📋', label: 'View All Consults', style: 'outline' }, { icon: '🛏️', label: 'Search Beds', style: 'outline' }, { icon: '📞', label: 'Call Specialist', style: 'outline' }] }
    ]
  },
  'dispatcher': {
    icon: '🚑', label: 'Ambulance Dispatcher', title: 'Dispatch Center',
    navItems: [
      { icon: '📊', label: 'Overview', active: true }, { icon: '🚑', label: 'Fleet Status' }, { icon: '📍', label: 'City Map' }, { icon: '📞', label: 'Call Queue', badge: 4 }, { icon: '🏥', label: 'Hospital Capacity' },
    ],
    metrics: [
      { icon: '🚑', label: 'Active Ambulances', value: '14/20', subtext: '6 idle, 14 en-route', trend: 'up', trendText: '+3 dispatched' },
      { icon: '⏱️', label: 'Avg Response Time', value: '8.2 min', subtext: 'City average', trend: 'down', trendText: '-1.3 min' },
      { icon: '📞', label: 'Incoming Calls', value: '4', subtext: 'In queue right now', trend: 'up', trendText: '+2 new' },
      { icon: '🏥', label: 'Hospitals at Capacity', value: '3/18', subtext: '15 accepting patients', trend: 'neutral', trendText: 'Stable' },
    ],
    mapTitle: 'Active Ambulances & Hospitals', mapBadge: '14 En-Route',
    markers: [
      { icon: '🚑', label: 'AMB-01 → St. Jude', top: '25%', left: '20%', type: 'ambulance' },
      { icon: '🚑', label: 'AMB-05 → Metro Gen', top: '40%', left: '65%', type: 'ambulance' },
      { icon: '🏥', label: 'Metro Gen (Full)', top: '35%', left: '80%', type: 'critical' },
      { icon: '🏥', label: 'City Hospital (8)', top: '55%', left: '50%', type: 'available' },
    ],
    legend: [{ color: '#ef4444', label: 'En-Route' }, { color: '#16a34a', label: 'Available' }, { color: '#f59e0b', label: 'Low Capacity' }, { color: '#dc2626', label: 'At Capacity' }],
    alerts: [
      { type: 'critical', title: 'Multi-vehicle accident — Sector 7', desc: '3 casualties reported. Deploy 2 additional units.', time: '1 min ago' },
      { type: 'critical', title: 'Metro General at full capacity', desc: 'Divert incoming ambulances to City Hospital or Central Med.', time: '8 min ago' },
      { type: 'warning', title: 'AMB-03 mechanical issue', desc: 'Unit reporting engine warning. En-route to base for swap.', time: '20 min ago' },
      { type: 'success', title: 'Shift change complete', desc: '8 fresh crews deployed. Evening shift fully staffed.', time: '1 hr ago' },
    ],
    bottomPanels: [
      { title: 'Hospital Capacities', badge: '18 Hospitals', type: 'table', headers: ['Hospital', 'ICU', 'ER', 'General', 'Status'], rows: [['St. Jude Medical', '2/10', '4/8', '22/40', 'available:Open'], ['Metro General', '0/8', '0/6', '35/35', 'critical:Full'], ['City Hospital', '5/12', '3/10', '18/30', 'available:Open']] },
      { title: 'Call Queue', badge: '4 Waiting', type: 'table', headers: ['Priority', 'Location', 'Type', 'Wait'], rows: [['critical:P1', 'Sector 7, Main Rd', 'Accident', '0:42'], ['critical:P1', '12 Oak Street', 'Cardiac', '1:15'], ['occupied:P2', 'Mall Complex, B2', 'Fall Injury', '3:20']] }
    ]
  },
  'coordinator': {
    icon: '🌐', label: 'City Coordinator', title: 'City Command Center',
    navItems: [
      { icon: '📊', label: 'City Overview', active: true }, { icon: '📍', label: 'Hospital Map' }, { icon: '📈', label: 'City KPIs' }, { icon: '🔔', label: 'Active Alerts', badge: 7 }, { icon: '⚠️', label: 'Emergency Control' },
    ],
    metrics: [
      { icon: '🏥', label: 'Total Hospitals', value: '18', subtext: 'In network', trend: 'neutral', trendText: 'All connected' },
      { icon: '🛏️', label: 'City-Wide Beds', value: '1,247', subtext: '82% occupied', trend: 'up', trendText: '+56 today' },
      { icon: '🚑', label: 'Active Ambulances', value: '42/60', subtext: 'Across all providers', trend: 'up', trendText: '+5 dispatched' },
      { icon: '⚠️', label: 'Active Alerts', value: '7', subtext: '2 critical, 5 warnings', trend: 'up', trendText: '+3 new' },
    ],
    mapTitle: 'City-Wide Hospital Network', mapBadge: '18 Hospitals',
    markers: [
      { icon: '🏥', label: 'St. Jude (78%)', top: '15%', left: '25%', type: 'available' },
      { icon: '🏥', label: 'Metro Gen (100%)', top: '25%', left: '55%', type: 'critical' },
      { icon: '🏥', label: 'City Hospital (62%)', top: '45%', left: '40%', type: 'available' },
      { icon: '🏥', label: 'Central Med (91%)', top: '55%', left: '72%', type: 'busy' },
    ],
    legend: [{ color: '#16a34a', label: '<80% Capacity' }, { color: '#f59e0b', label: '80-95%' }, { color: '#dc2626', label: '>95% / Full' }],
    alerts: [
      { type: 'critical', title: 'Metro General at 100% capacity', desc: 'All beds occupied. Patient diversions active.', time: '5 min ago' },
      { type: 'critical', title: 'Mass casualty event — Sector 7', desc: 'Multi-vehicle accident. MCI Level 2 activated.', time: '8 min ago' },
      { type: 'warning', title: 'Central Medical at 91%', desc: 'Approaching capacity. Monitor for diversion need.', time: '20 min ago' },
      { type: 'info', title: 'New hospital joined network', desc: 'Hope Medical Center now live on MedGrid.', time: '2 hrs ago' },
    ],
    bottomPanels: [
      { title: 'City-Wide KPIs', badge: 'This Week', type: 'stats', items: [{ icon: '📢', label: 'Total Transfers', value: '234', bg: '#dcfce7' }, { icon: '⏱️', label: 'Avg Transfer Time', value: '18 min', bg: '#e0e7ff' }, { icon: '❤️', label: 'Mortality Rate', value: '1.2%', bg: '#fef2f2' }, { icon: '📊', label: 'Bed Utilization', value: '82%', bg: '#fef3c7' }] },
      { title: 'Emergency Control', type: 'actions', actions: [{ icon: '⚠️', label: 'Activate Emergency Mode', style: 'danger' }, { icon: '📢', label: 'City-Wide Alert', style: 'primary' }, { icon: '📋', label: 'Generate Report', style: 'outline' }, { icon: '📞', label: 'Contact All Hospitals', style: 'outline' }] }
    ]
  }
};

// Role mapping from auth roles to dashboard config keys
const roleMap = {
  'admin': 'hospital-admin',
  'hospital-admin': 'hospital-admin',
  'doctor': 'doctor',
  'supervisor': 'coordinator',
  'dispatcher': 'dispatcher',
  'patient': 'doctor', // fallback
};

// Status badge renderer
const StatusBadge = ({ value }) => {
  if (!value || !value.includes(':')) return <span>{value}</span>;
  const [cls, label] = value.split(':');
  return <span className={`status-badge ${cls}`}>{label}</span>;
};

// Render panel body
const PanelBody = ({ panel, onAction }) => {
  if (panel.type === 'table') {
    return (
      <table className="data-table">
        <thead><tr>{panel.headers.map(h => <th key={h}>{h}</th>)}</tr></thead>
        <tbody>{panel.rows.map((row, ri) => <tr key={ri}>{row.map((cell, ci) => <td key={ci}><StatusBadge value={cell} /></td>)}</tr>)}</tbody>
      </table>
    );
  }
  if (panel.type === 'stats') {
    return (
      <ul className="quick-stat-list">
        {panel.items.map(item => (
          <li key={item.label} className="quick-stat-item">
            <div className="stat-left">
              <div className="stat-icon" style={{ background: item.bg }}>{item.icon}</div>
              <span className="stat-label">{item.label}</span>
            </div>
            <span className="stat-value">{item.value}</span>
          </li>
        ))}
      </ul>
    );
  }
  if (panel.type === 'actions') {
    return (
      <div style={{ display: 'grid', gap: '10px', padding: '4px 0' }}>
        {panel.actions.map(a => (
          <button key={a.label} className={`action-btn ${a.style}`} onClick={() => onAction(a.label)}>
            <span>{a.icon}</span> {a.label}
          </button>
        ))}
      </div>
    );
  }
  return null;
};

const DashboardPage = () => {
  const navigate = useNavigate();
  const user = Auth.user;
  const session = (() => { try { return JSON.parse(localStorage.getItem('medgrid_session') || 'null'); } catch { return null; } })();

  useEffect(() => {
    if (!user && !session) {
      navigate('/');
    }
  }, []);

  const ROLE = session?.role || user?.role || 'hospital-admin';
  const USER_NAME = session?.name || user?.name || 'User';
  const configKey = roleMap[ROLE] || 'hospital-admin';
  const config = roleConfig[configKey] || roleConfig['hospital-admin'];

  const [metrics, setMetrics] = useState(config.metrics);
  const [mapMeta, setMapMeta] = useState({ title: config.mapTitle, badge: config.mapBadge });
  const [alerts, setAlerts] = useState(config.alerts);
  const [bottomPanels, setBottomPanels] = useState(config.bottomPanels);
  const [gridHospitals, setGridHospitals] = useState([]);
  const [gridLoading, setGridLoading] = useState(false);
  const [pageLoading, setPageLoading] = useState(true);
  const [gridError, setGridError] = useState('');

  const [time, setTime] = useState('');
  const [emergencyActive, setEmergencyActive] = useState(false);
  const [toast, setToast] = useState({ show: false, message: '' });

  useEffect(() => {
    const tick = () => setTime(new Date().toLocaleString('en-US', { weekday: 'short', hour: '2-digit', minute: '2-digit', second: '2-digit' }));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, []);

  useEffect(() => {
    const fetchAnalytics = async () => {
      setPageLoading(true);
      try {
        // Platform-level admin/coordinator
        if (ROLE === 'platform-admin' || configKey === 'coordinator' || configKey === 'dispatcher') {
          const res = await apiFetch('/api/analytics/dashboard/');
          if (!res.ok) return;
          const data = await res.json();
          setMetrics([
            {
              icon: '🏥',
              label: 'Hospitals on Grid',
              value: String(data.hospitals?.total ?? 0),
              subtext: `${data.hospitals?.verified ?? 0} verified`,
              trend: 'neutral',
              trendText: '',
            },
            {
              icon: '🛏️',
              label: 'Beds Occupied',
              value: `${data.beds?.occupied ?? 0}/${data.beds?.total ?? 0}`,
              subtext: `${data.beds?.occupancy_rate ?? 0}% occupancy`,
              trend: 'neutral',
              trendText: '',
            },
            {
              icon: '🚑',
              label: 'Ambulances Active',
              value: `${data.ambulances?.available ?? 0}/${data.ambulances?.total ?? 0}`,
              subtext: `${data.ambulances?.trips_today ?? 0} trips today`,
              trend: 'neutral',
              trendText: '',
            },
            {
              icon: '⚠️',
              label: 'Open Alerts',
              value: String(data.alerts?.open ?? 0),
              subtext: `${data.alerts?.high ?? 0} high severity`,
              trend: data.alerts?.open ? 'up' : 'neutral',
              trendText: '',
            },
          ]);
          setMapMeta({
            title: 'Platform Overview',
            badge: `${data.hospitals?.active ?? 0} active hospitals`,
          });
          setAlerts([
            {
              type: 'critical',
              title: 'High severity alerts',
              desc: `${data.alerts?.high ?? 0} high severity alerts open across the grid.`,
              time: 'Live',
            },
            {
              type: 'info',
              title: 'Transfers today',
              desc: `${data.transfers?.total ?? 0} transfers; ${data.transfers?.pending ?? 0} pending.`,
              time: 'Today',
            },
          ]);
        } else if (configKey === 'hospital-admin') {
          // Hospital-level admin / reception dashboard
          const res = await apiFetch('/api/analytics/my-hospital/');
          if (!res.ok) return;
          const data = await res.json();
          setMetrics([
            {
              icon: '🛏️',
              label: 'Bed Occupancy',
              value: `${data.beds?.occupied ?? 0}/${data.beds?.total ?? 0}`,
              subtext: `${data.beds?.occupancy_rate ?? 0}% occupancy`,
              trend: 'neutral',
              trendText: '',
            },
            {
              icon: '📅',
              label: 'Admissions (period)',
              value: String(data.patients?.admitted ?? 0),
              subtext: `${data.patients?.still_in ?? 0} still admitted`,
              trend: 'neutral',
              trendText: '',
            },
            {
              icon: '↔️',
              label: 'Transfers',
              value: `${data.transfers?.sent ?? 0} out / ${data.transfers?.received ?? 0} in`,
              subtext: 'Current period',
              trend: 'neutral',
              trendText: '',
            },
            {
              icon: '⚠️',
              label: 'Open Alerts',
              value: String(data.open_alerts ?? 0),
              subtext: 'For your hospital',
              trend: data.open_alerts ? 'up' : 'neutral',
              trendText: '',
            },
          ]);
          setMapMeta({
            title: data.hospital || baseConfig.mapTitle,
            badge: `${data.beds?.available ?? 0} beds available`,
          });
        }
      } catch {
        // fall back to config
      } finally {
        setPageLoading(false);
      }
    };
    fetchAnalytics();
  }, [ROLE, configKey, config.mapTitle, config.mapBadge]);

  // Public "Real-Time Grid" hospitals list for dashboard
  useEffect(() => {
    const fetchGridHospitals = async () => {
      setGridLoading(true);
      setGridError('');
      try {
        const city = (configKey === 'coordinator' || configKey === 'dispatcher') ? 'Indore' : 'Bhopal';
        const res = await apiFetch(`/api/hospitals/search/?city=${encodeURIComponent(city)}`);
        const data = await res.json().catch(() => ({}));
        if (!res.ok) throw new Error(data.detail || 'Failed to load hospitals');
        const list = Array.isArray(data) ? data : data.results || [];

        // attach live bed availability (Redis TTL)
        const enriched = await Promise.all(list.slice(0, 12).map(async (h) => {
          try {
            const bedsRes = await apiFetch(`/api/beds/availability/${h.id}/`);
            if (bedsRes.ok) {
              const beds = await bedsRes.json();
              return { ...h, bed_snapshot: beds };
            }
          } catch {}
          return { ...h, bed_snapshot: null };
        }));
        setGridHospitals(enriched);
      } catch (e) {
        setGridHospitals([]);
        setGridError(e.message || 'Failed to load grid hospitals');
      }
      setGridLoading(false);
    };
    fetchGridHospitals();
  }, [configKey]);

  const showToast = useCallback((message) => {
    setToast({ show: true, message });
    setTimeout(() => setToast({ show: false, message: '' }), 3500);
  }, []);

  const handleAction = (action) => {
    if (action === 'Activate Emergency Mode') {
      setEmergencyActive(v => {
        showToast(!v ? '🚨 Emergency Mode ACTIVATED' : 'Emergency Mode deactivated');
        return !v;
      });
    } else {
      showToast(`${action} — Feature coming soon`);
    }
  };

  const handleLogout = async () => {
    await Auth.logout();
    navigate('/');
  };

  if (pageLoading) {
    return (
      <div className="dashboard-page" style={{ justifyContent: 'center', alignItems: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div className="loader-pulse">
            <div className="logo-circle" style={{ width: 60, height: 60, fontSize: 30, margin: '0 auto 20px' }}>+</div>
          </div>
          <h2 style={{ color: '#1B4332', fontStyle: 'italic', fontWeight: 900 }}>Synchronizing Grid Analytics...</h2>
          <p style={{ color: '#64748b', fontSize: 13, fontWeight: 600, marginTop: 8 }}>Securing your session and fetching live metrics.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="dashboard-page">
      {emergencyActive && <div className="emergency-banner active">⚠️ EMERGENCY MODE ACTIVE — All units on high alert</div>}

      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-logo">
          <div className="logo-circle">+</div>
          <span>MedGrid</span>
        </div>
        <div className="sidebar-role">
          <span className="role-emoji">{config.icon}</span>
          <div className="role-info">
            <div className="role-name">{config.label}</div>
            <div className="role-user">{USER_NAME}</div>
          </div>
        </div>
        <nav className="sidebar-nav">
          <div className="nav-section-label">Navigation</div>
          {config.navItems.map(item => (
            <a key={item.label} className={`nav-item ${item.active ? 'active' : ''}`} href="#">
              <span className="nav-icon">{item.icon}</span>
              {item.label}
              {item.badge && <span className="nav-badge">{item.badge}</span>}
            </a>
          ))}
        </nav>
        <div className="sidebar-footer">
          <button className="logout-btn" onClick={handleLogout}>
            <span>🚪</span> Sign Out
          </button>
        </div>
      </aside>

      {/* Main Content */}
      <div className="main-content">
        {/* Topbar */}
        <header className="topbar">
          <div className="topbar-left">
            <h1>{config.title}</h1>
            <div className="live-badge">
              <div className="live-dot"></div>
              LIVE
            </div>
          </div>
          <div className="topbar-right">
            <span className="topbar-time">{time}</span>
            <button className="topbar-btn" title="Notifications">🔔<span className="notif-dot"></span></button>
            <button className="topbar-btn" title="Settings">⚙️</button>
          </div>
        </header>

        {/* Dashboard Body */}
        <div className="dashboard-body">
          {/* Metrics Row */}
          <div className="metrics-row">
            {metrics.map(m => (
              <div key={m.label} className="metric-card">
                <div className="metric-icon">{m.icon}</div>
                <div className="metric-label">{m.label}</div>
                <div className="metric-value">{m.value}</div>
                <div className="metric-subtext">{m.subtext}</div>
                <div className={`metric-trend ${m.trend}`}>{m.trend === 'up' ? '↑' : m.trend === 'down' ? '↓' : '→'} {m.trendText}</div>
              </div>
            ))}
          </div>

          {/* Main Grid */}
          <div className="main-grid">
            {/* Map Panel */}
            <div className="panel map-panel">
              <div className="panel-header">
                <h3>{mapMeta.title}</h3>
                <span className="panel-badge">{mapMeta.badge}</span>
              </div>
              <div className="panel-body">
                <div className="map-container">
                  <div className="map-grid"></div>
                  {config.markers.map(m => (
                    <div key={m.label} className="map-marker" style={{ top: m.top, left: m.left }}>
                      <div className={`marker-dot ${m.type}`}>{m.icon}</div>
                      <span className="marker-label">{m.label}</span>
                    </div>
                  ))}
                  <div className="map-legend">
                    {config.legend.map(l => (
                      <div key={l.label} className="legend-item">
                        <div className="legend-dot" style={{ background: l.color }}></div>
                        {l.label}
                      </div>
                    ))}
                  </div>
                </div>

                {/* Real-Time Grid (public hospitals API) */}
                <div style={{ marginTop: 14, padding: 12, background: '#fff', borderRadius: 14, border: '1px solid rgba(27,67,50,0.08)' }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, marginBottom: 10 }}>
                    <div>
                      <div style={{ fontSize: 13, fontWeight: 900, color: '#1B4332' }}>Real-Time Grid</div>
                      <div style={{ fontSize: 11, fontWeight: 600, color: '#64748b' }}>
                        Synced hospitals in your current geographic cluster.
                      </div>
                    </div>
                    <button
                      className="action-btn outline"
                      onClick={() => window.location.reload()}
                      title="Refresh grid list"
                      style={{ padding: '8px 10px' }}
                    >
                      🔄 Refresh
                    </button>
                  </div>

                  {gridLoading && <div style={{ fontSize: 12, color: '#64748b', fontWeight: 700 }}>Loading hospitals…</div>}
                  {!gridLoading && gridError && <div style={{ fontSize: 12, color: '#dc2626', fontWeight: 700 }}>{gridError}</div>}
                  {!gridLoading && !gridError && (
                    <div style={{ display: 'grid', gap: 8 }}>
                      {gridHospitals.map((h) => {
                        const snap = h.bed_snapshot;
                        const available = snap?.available_beds ?? h.available_beds ?? 0;
                        const total = snap?.total_beds ?? h.total_beds ?? 0;
                        const icuAvail = snap?.by_type?.icu?.available ?? 0;
                        const badgeBg = available > 0 ? 'rgba(22,163,74,0.12)' : 'rgba(220,38,38,0.12)';
                        const badgeFg = available > 0 ? '#16a34a' : '#dc2626';
                        return (
                          <div key={h.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, padding: '10px 12px', background: '#f8fafc', borderRadius: 12, border: '1px solid rgba(2,6,23,0.06)' }}>
                            <div style={{ minWidth: 0 }}>
                              <div style={{ fontSize: 13, fontWeight: 900, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                                🏥 {h.name}
                              </div>
                              <div style={{ fontSize: 11, color: '#64748b', fontWeight: 700 }}>
                                {h.city || ''}{h.category ? ` · ${h.category}` : ''}{icuAvail ? ` · ICU ${icuAvail}` : ''}
                              </div>
                            </div>
                            <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexShrink: 0 }}>
                              <div style={{ padding: '6px 10px', borderRadius: 999, background: badgeBg, color: badgeFg, fontSize: 11, fontWeight: 900 }}>
                                {available}/{total} beds
                              </div>
                            </div>
                          </div>
                        );
                      })}
                      {gridHospitals.length === 0 && (
                        <div style={{ fontSize: 12, color: '#64748b', fontWeight: 700 }}>No hospitals found for this cluster.</div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Alerts Panel */}
            <div className="panel alerts-panel">
              <div className="panel-header">
                <h3>Alerts & Activity</h3>
                <span className="panel-badge">{alerts.length} Active</span>
              </div>
              <div className="panel-body">
                {alerts.map((a, i) => (
                  <div key={i} className={`alert-item ${a.type}`}>
                    <div className="alert-title">{a.title}</div>
                    <div className="alert-desc">{a.desc}</div>
                    <div className="alert-time">{a.time}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Bottom Panels */}
          <div className="bottom-grid">
            {bottomPanels.map((p, i) => (
              <div key={i} className="panel">
                <div className="panel-header">
                  <h3>{p.title}</h3>
                  {p.badge && <span className="panel-badge">{p.badge}</span>}
                </div>
                <div className="panel-body">
                  <PanelBody panel={p} onAction={handleAction} />
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Toast */}
      <div className={`toast success ${toast.show ? 'show' : ''}`}>{toast.message}</div>
    </div>
  );
};

export default DashboardPage;
