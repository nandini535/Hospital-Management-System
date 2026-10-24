/**
 * =========================================================
 * Hospital Management System - api.js
 * Central API client and reusable UI helper functions
 * =========================================================
 */

// Base URL for the Flask backend
const API_BASE_URL = 'http://localhost:5000';

// ---------------------------------------------------------
// Path & Navigation Helpers (supports both file:// and http://)
// ---------------------------------------------------------
function getRootPrefix() {
  const path = window.location.pathname.replace(/\\/g, '/');
  if (path.includes('/patient/') || path.includes('/doctor/') || path.includes('/admin/')) {
    return '../';
  }
  return './';
}

function navigateTo(relativePath) {
  const prefix = getRootPrefix();
  window.location.href = prefix + relativePath;
}

// ---------------------------------------------------------
// Session & Auth Storage Helpers
// ---------------------------------------------------------
function saveSession(data) {
  if (data.token) localStorage.setItem('token', data.token);
  if (data.role) localStorage.setItem('role', data.role);
  if (data.name) localStorage.setItem('name', data.name);
  if (data.username) localStorage.setItem('username', data.username);
  if (data.DoctorID !== undefined && data.DoctorID !== null) {
    localStorage.setItem('DoctorID', String(data.DoctorID));
  }
  if (data.PatientID !== undefined && data.PatientID !== null) {
    localStorage.setItem('PatientID', String(data.PatientID));
  }
}

function clearSession() {
  localStorage.removeItem('token');
  localStorage.removeItem('role');
  localStorage.removeItem('name');
  localStorage.removeItem('username');
  localStorage.removeItem('DoctorID');
  localStorage.removeItem('PatientID');
}

function getToken() {
  return localStorage.getItem('token');
}

function getRole() {
  return localStorage.getItem('role');
}

function getUser() {
  return {
    token: localStorage.getItem('token'),
    role: localStorage.getItem('role'),
    name: localStorage.getItem('name'),
    username: localStorage.getItem('username'),
    DoctorID: localStorage.getItem('DoctorID'),
    PatientID: localStorage.getItem('PatientID'),
  };
}

function isLoggedIn() {
  return Boolean(getToken());
}

function logout() {
  clearSession();
  navigateTo('index.html');
}

function redirectByRole(role) {
  const r = (role || getRole() || '').toLowerCase();
  if (r === 'admin') {
    navigateTo('admin/index.html');
  } else if (r === 'doctor') {
    navigateTo('doctor/index.html');
  } else if (r === 'patient') {
    navigateTo('patient/index.html');
  } else {
    navigateTo('index.html');
  }
}

// ---------------------------------------------------------
// Central API Fetch Helper
// - Adds Authorization header
// - Handles JSON body and response
// - Catches errors and formats message
// - On 401, clears storage and redirects to login
// ---------------------------------------------------------
async function apiFetch(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const headers = Object.assign({}, options.headers || {});

  const token = getToken();
  if (token) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  if (options.body && typeof options.body === 'object' && !(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json';
    options.body = JSON.stringify(options.body);
  }

  const fetchConfig = {
    ...options,
    headers,
  };

  let response;
  try {
    response = await fetch(url, fetchConfig);
  } catch (netErr) {
    throw new Error('Cannot connect to server. Ensure Flask API is running at ' + API_BASE_URL);
  }

  // Check 401 Unauthorized
  if (response.status === 401) {
    clearSession();
    const currentPath = window.location.pathname;
    const isAuthPage = currentPath.endsWith('index.html') || currentPath.endsWith('register.html') || currentPath === '/' || currentPath === '';
    if (!isAuthPage) {
      navigateTo('index.html');
    }
  }

  let data = null;
  const contentType = response.headers.get('content-type') || '';
  if (contentType.includes('application/json')) {
    try {
      data = await response.json();
    } catch (e) {
      data = null;
    }
  } else {
    const text = await response.text();
    data = { message: text };
  }

  if (!response.ok) {
    let errMsg = 'Request failed';
    if (data && typeof data === 'object') {
      errMsg = data.error || data.detail || data.message || `Error ${response.status}`;
    } else {
      errMsg = `HTTP error ${response.status}`;
    }
    const err = new Error(errMsg);
    err.status = response.status;
    err.data = data;
    throw err;
  }

  return data;
}

// ---------------------------------------------------------
// Reusable UI Helpers
// ---------------------------------------------------------

/**
 * Escapes unsafe HTML characters to prevent XSS.
 */
function escapeHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

/**
 * Displays a small alert box (never alert() popup).
 * @param {string|HTMLElement} container - container id or element
 * @param {'error'|'success'|'warning'|'info'} type
 * @param {string} text
 */
function showMessage(container, type, text) {
  const el = typeof container === 'string' ? document.getElementById(container) : container;
  if (!el) return;
  const safeText = escapeHtml(text);
  el.innerHTML = `<div class="alert alert-${type}" role="alert">${safeText}</div>`;
  el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
}

/**
 * Clears any alert box in the given container.
 */
function clearMessage(container) {
  const el = typeof container === 'string' ? document.getElementById(container) : container;
  if (el) el.innerHTML = '';
}

/**
 * Formats YYYY-MM-DD or date object into a readable date string.
 */
function formatDate(dateVal) {
  if (!dateVal) return '-';
  const str = String(dateVal).split('T')[0];
  const parts = str.split('-');
  if (parts.length === 3) {
    const months = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'];
    const yr = parts[0];
    const mIdx = parseInt(parts[1], 10) - 1;
    const day = parseInt(parts[2], 10);
    if (!isNaN(mIdx) && mIdx >= 0 && mIdx < 12) {
      return `${day} ${months[mIdx]} ${yr}`;
    }
  }
  return str;
}

/**
 * Formats HH:MM:SS or HH:MM to clean time string.
 */
function formatTime(timeVal) {
  if (!timeVal) return '-';
  const parts = String(timeVal).split(':');
  if (parts.length >= 2) {
    let hours = parseInt(parts[0], 10);
    const minutes = parts[1];
    const ampm = hours >= 12 ? 'PM' : 'AM';
    hours = hours % 12;
    hours = hours ? hours : 12; // 0 becomes 12
    return `${hours}:${minutes} ${ampm}`;
  }
  return String(timeVal);
}

/**
 * Formats currency amount.
 */
function formatCurrency(amount) {
  const num = Number(amount || 0);
  return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 });
}

/**
 * Generates an HTML badge for various entity statuses.
 */
function statusBadge(status) {
  if (!status) return '-';
  const clean = String(status).trim();
  const cls = clean.toLowerCase();
  return `<span class="badge badge-${escapeHtml(cls)}">${escapeHtml(clean)}</span>`;
}

/**
 * Renders an HTML table from column specifications and rows array.
 * @param {Array<{ key: string, label: string, render?: (val, row) => string }>} columns
 * @param {Array<Object>} rows
 * @param {Object} options
 */
function renderTable(columns, rows, options = {}) {
  const emptyText = options.emptyText || 'No records found.';
  if (!rows || rows.length === 0) {
    return `
      <div class="table-responsive">
        <table class="table">
          <thead>
            <tr>${columns.map(c => `<th>${escapeHtml(c.label)}</th>`).join('')}</tr>
          </thead>
          <tbody>
            <tr>
              <td colspan="${columns.length}" class="table-empty">${escapeHtml(emptyText)}</td>
            </tr>
          </tbody>
        </table>
      </div>`;
  }

  const thead = `<tr>${columns.map(c => `<th>${escapeHtml(c.label)}</th>`).join('')}</tr>`;
  const tbody = rows.map(row => {
    const cells = columns.map(c => {
      let content = '';
      if (typeof c.render === 'function') {
        content = c.render(row[c.key], row);
      } else {
        content = escapeHtml(row[c.key] !== undefined && row[c.key] !== null ? row[c.key] : '-');
      }
      return `<td>${content}</td>`;
    }).join('');
    return `<tr>${cells}</tr>`;
  }).join('');

  return `
    <div class="table-responsive">
      <table class="table">
        <thead>${thead}</thead>
        <tbody>${tbody}</tbody>
      </table>
    </div>`;
}
