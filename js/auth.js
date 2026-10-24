/**
 * =========================================================
 * Hospital Management System - auth.js
 * Role guard and shared navigation bar setup
 * =========================================================
 */

/**
 * Ensures user is authenticated and matches the allowed role.
 * If not authenticated, redirects to login (index.html).
 * If authenticated with a different role, redirects to their own portal.
 * @param {string} [expectedRole] - 'Patient', 'Doctor', or 'Admin'
 */
function requireAuth(expectedRole) {
  const token = getToken();
  if (!token) {
    navigateTo('index.html');
    return false;
  }

  const role = getRole();
  if (!role) {
    clearSession();
    navigateTo('index.html');
    return false;
  }

  if (expectedRole && role.toLowerCase() !== expectedRole.toLowerCase()) {
    redirectByRole(role);
    return false;
  }

  return true;
}

/**
 * Renders the top navigation bar with brand, portal links, user info, and logout.
 * Target element can be #navbar or a custom container.
 * @param {string} activePage - key of the currently active navigation item
 */
function renderNavbar(activePage = 'dashboard') {
  const navContainer = document.getElementById('navbar') || document.querySelector('.navbar');
  if (!navContainer) return;

  const user = getUser();
  const role = user.role || '';
  const prefix = getRootPrefix();

  // Navigation tabs definition by role
  let navItems = [];
  let homeLink = prefix + 'index.html';

  if (role.toLowerCase() === 'patient') {
    homeLink = prefix + 'patient/index.html';
    navItems = [
      { key: 'dashboard', label: 'Dashboard', href: prefix + 'patient/index.html' },
      { key: 'book', label: 'Book Appointment', href: prefix + 'patient/book.html' },
      { key: 'appointments', label: 'My Appointments', href: prefix + 'patient/appointments.html' },
      { key: 'prescriptions', label: 'Prescriptions', href: prefix + 'patient/prescriptions.html' },
      { key: 'lab-tests', label: 'Lab Tests', href: prefix + 'patient/lab-tests.html' },
      { key: 'admissions', label: 'Admissions', href: prefix + 'patient/admissions.html' },
      { key: 'bills', label: 'Bills', href: prefix + 'patient/bills.html' },
      { key: 'profile', label: 'Profile', href: prefix + 'patient/profile.html' },
    ];
  } else if (role.toLowerCase() === 'doctor') {
    homeLink = prefix + 'doctor/index.html';
    navItems = [
      { key: 'dashboard', label: 'Appointments', href: prefix + 'doctor/index.html' },
      { key: 'schedule', label: 'My Timetable', href: prefix + 'doctor/schedule.html' },
      { key: 'patients', label: 'My Patients', href: prefix + 'doctor/patients.html' },
      { key: 'prescribe', label: 'Write Prescription', href: prefix + 'doctor/prescribe.html' },
      { key: 'lab-tests', label: 'Lab Tests', href: prefix + 'doctor/lab-tests.html' },
    ];
  } else if (role.toLowerCase() === 'admin') {
    homeLink = prefix + 'admin/index.html';
    navItems = [
      { key: 'dashboard', label: 'Dashboard', href: prefix + 'admin/index.html' },
      { key: 'approvals', label: 'Approvals', href: prefix + 'admin/approvals.html' },
      { key: 'users', label: 'Users', href: prefix + 'admin/users.html' },
      { key: 'patients', label: 'Patients', href: prefix + 'admin/patients.html' },
      { key: 'appointments', label: 'Appointments', href: prefix + 'admin/appointments.html' },
      { key: 'admissions', label: 'Admissions & Rooms', href: prefix + 'admin/admissions.html' },
      { key: 'billing', label: 'Billing', href: prefix + 'admin/billing.html' },
      { key: 'medicines', label: 'Medicines', href: prefix + 'admin/medicines.html' },
      { key: 'master', label: 'Master Data', href: prefix + 'admin/master.html' },
    ];
  }

  const linksHtml = navItems.map(item => `
    <li>
      <a href="${item.href}" class="nav-link ${item.key === activePage ? 'active' : ''}">
        ${escapeHtml(item.label)}
      </a>
    </li>
  `).join('');

  const displayName = user.name || user.username || 'User';

  navContainer.className = 'navbar';
  navContainer.innerHTML = `
    <a href="${homeLink}" class="navbar-brand">
      <span>🏥</span>
      <span>City Hospital</span>
    </a>
    <ul class="navbar-nav">
      ${linksHtml}
    </ul>
    <div class="navbar-user">
      <span class="user-tag">
        <span class="user-name">${escapeHtml(displayName)}</span>
        <span class="badge badge-role">${escapeHtml(role)}</span>
      </span>
      <button type="button" class="btn btn-outline btn-sm" id="logoutBtn" onclick="logout()">
        Log Out
      </button>
    </div>
  `;
}
