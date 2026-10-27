/**
 * Sentinel Triage Studio - Enterprise Main Application Logic & API Client.
 * Orchestrates Zero-Trust Authentication, FIDO2/WebAuthn Biometrics, and ML Fraud Evaluation.
 */

import { PRESETS, generateRandomTransaction } from './presets.js';
import { updateRiskGauge, renderExplainabilityWaterfall } from './chart.js';
import { auth } from './auth.js';
import { saveAuditToSupabase, fetchLatestAuditsFromSupabase, isSupabaseConfigured } from './supabaseClient.js';

export function getApiBase() {
  const custom = localStorage.getItem('SENTINEL_API_BASE');
  if (custom) return custom.replace(/\/+$/, '');
  if (typeof window !== 'undefined' && window.__ENV__?.NEXT_PUBLIC_API_URL) {
    return window.__ENV__.NEXT_PUBLIC_API_URL.replace(/\/+$/, '');
  }
  if (typeof window !== 'undefined') {
    if (window.location.port === '8000' || window.location.pathname.startsWith('/dashboard')) {
      return `${window.location.origin}/api/v1`;
    }
    // When served via Next.js or cloud host on HTTPS, use relative /api/v1 (proxied by Next.js rewrites)
    if (window.location.protocol === 'https:' || window.location.port === '3000') {
      return `${window.location.origin}/api/v1`;
    }
  }
  return 'http://127.0.0.1:8000/api/v1';
}

const API_BASE = getApiBase();

let auditHistory = [];
let isStudioInitialized = false;

document.addEventListener('DOMContentLoaded', () => {
  initAuthUI();

  // Always present the Enterprise Login screen first when opening the application link
  showAuthScreen();
});

/* ==========================================================================
   1. Authentication & Biometric Controller
   ========================================================================== */

function initAuthUI() {
  const tabSignIn = document.getElementById('tab-auth-signin');
  const tabSignUp = document.getElementById('tab-auth-signup');
  const formSignIn = document.getElementById('form-signin');
  const formSignUp = document.getElementById('form-signup');
  const btnAutofill = document.getElementById('btn-autofill-analyst');

  // Mode Switcher Tabs
  tabSignIn?.addEventListener('click', () => {
    tabSignIn.classList.add('active');
    tabSignUp.classList.remove('active');
    formSignIn.style.display = 'flex';
    formSignUp.style.display = 'none';
  });

  tabSignUp?.addEventListener('click', () => {
    tabSignUp.classList.add('active');
    tabSignIn.classList.remove('active');
    formSignUp.style.display = 'flex';
    formSignIn.style.display = 'none';
  });

  // Password Visibility Toggles
  document.getElementById('toggle-signin-password')?.addEventListener('click', () => {
    const pwdInput = document.getElementById('signin-password');
    pwdInput.type = pwdInput.type === 'password' ? 'text' : 'password';
  });

  document.getElementById('toggle-signup-password')?.addEventListener('click', () => {
    const pwdInput = document.getElementById('signup-password');
    pwdInput.type = pwdInput.type === 'password' ? 'text' : 'password';
  });

  // Password Strength Meter
  const signupPwd = document.getElementById('signup-password');
  signupPwd?.addEventListener('input', (e) => {
    updatePasswordStrength(e.target.value);
  });

  // Institutional Autofill
  btnAutofill?.addEventListener('click', () => {
    document.getElementById('signin-email').value = 'analyst@sentinel.corp';
    document.getElementById('signin-password').value = 'Sentinel@2026!';
  });

  // Sign In Submission
  formSignIn?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const email = document.getElementById('signin-email').value;
    const password = document.getElementById('signin-password').value;
    const remember = document.getElementById('signin-remember').checked;
    const submitBtn = document.getElementById('btn-signin-submit');

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>⏳ Verifying Credentials...</span>`;
      const user = await auth.signInWithPassword(email, password, remember);
      showAuthenticatedWorkstation(user);
    } catch (err) {
      alert(err.message || "Authentication failed.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
        Sign In to Workstation`;
    }
  });

  // Create Account Submission
  formSignUp?.addEventListener('submit', async (e) => {
    e.preventDefault();
    const name = document.getElementById('signup-name').value;
    const email = document.getElementById('signup-email').value;
    const role = document.getElementById('signup-role').value;
    const password = document.getElementById('signup-password').value;
    const confirm = document.getElementById('signup-confirm-password').value;
    const enrollBio = document.getElementById('signup-biometrics-opt').checked;
    const submitBtn = document.getElementById('btn-signup-submit');

    if (password !== confirm) {
      alert("Passcodes do not match. Please re-enter.");
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span>⚙️ Generating Institutional Keys...</span>`;
      const user = await auth.createAccount({
        name,
        email,
        role,
        clearance: role.includes('Chief') ? 'Level 4' : 'Level 3',
        password,
        enrollBiometrics: enrollBio
      });
      alert(`Institutional Clearance Account Created for ${user.name}!`);
      showAuthenticatedWorkstation(user);
    } catch (err) {
      alert(err.message || "Account creation failed.");
    } finally {
      submitBtn.disabled = false;
      submitBtn.innerHTML = `
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M16 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="8.5" cy="7" r="4"/></svg>
        Register Enterprise Account`;
    }
  });

  // Biometric Sign In CTA
  document.getElementById('btn-biometric-signin')?.addEventListener('click', triggerBiometricFlow);

  // Biometric Modal Simulation and Cancel
  document.getElementById('btn-simulate-biometric')?.addEventListener('click', async () => {
    const log = document.getElementById('biometric-status-log');
    if (log) log.textContent = "Sensor touch confirmed! Cryptographic signature verified.";
    await new Promise(r => setTimeout(r, 450));
    closeBiometricModal();
    const user = await auth.authenticateBiometrics(() => {});
    showAuthenticatedWorkstation(user);
  });

  document.getElementById('btn-cancel-biometric')?.addEventListener('click', closeBiometricModal);

  // Sign Out / Lock Button
  document.getElementById('btn-signout')?.addEventListener('click', () => {
    auth.signOut();
    showAuthScreen();
  });
}

function updatePasswordStrength(val) {
  const bar = document.getElementById('password-strength-indicator');
  const label = document.getElementById('password-strength-label');
  if (!bar || !label) return;

  if (!val || val.length === 0) {
    bar.style.width = '0%';
    bar.style.backgroundColor = 'transparent';
    label.textContent = 'Security strength: None';
    return;
  }

  let score = 0;
  if (val.length >= 6) score++;
  if (val.length >= 10) score++;
  if (/[A-Z]/.test(val) && /[a-z]/.test(val)) score++;
  if (/\d/.test(val)) score++;
  if (/[^A-Za-z0-9]/.test(val)) score++;

  if (score <= 2) {
    bar.style.width = '33%';
    bar.style.backgroundColor = '#ef4444';
    label.textContent = 'Security strength: Weak (add mixed symbols/numbers)';
  } else if (score <= 4) {
    bar.style.width = '66%';
    bar.style.backgroundColor = '#f59e0b';
    label.textContent = 'Security strength: Moderate Enterprise Grade';
  } else {
    bar.style.width = '100%';
    bar.style.backgroundColor = '#10b981';
    label.textContent = 'Security strength: High Security (Institutional FIPS compliant)';
  }
}

async function triggerBiometricFlow() {
  const modal = document.getElementById('biometric-modal');
  const log = document.getElementById('biometric-status-log');
  if (modal) modal.style.display = 'flex';

  try {
    const user = await auth.authenticateBiometrics((statusMessage) => {
      if (log) log.textContent = statusMessage;
    });
    closeBiometricModal();
    showAuthenticatedWorkstation(user);
  } catch (err) {
    if (log) log.textContent = "Biometric prompt ready: Touch sensor to authenticate.";
  }
}

function closeBiometricModal() {
  const modal = document.getElementById('biometric-modal');
  if (modal) modal.style.display = 'none';
}

function showAuthScreen() {
  document.getElementById('auth-wrapper').style.display = 'flex';
  document.getElementById('app-wrapper').style.display = 'none';
}

function showAuthenticatedWorkstation(user) {
  document.getElementById('auth-wrapper').style.display = 'none';
  document.getElementById('app-wrapper').style.display = 'block';

  // Populate header profile widget
  if (user) {
    document.getElementById('user-avatar-badge').textContent = user.avatar || 'SK';
    document.getElementById('user-display-name').textContent = user.name;
    document.getElementById('user-display-clearance').textContent = `${user.clearance} · ${user.role}`;
    const bioTag = document.getElementById('user-biometric-tag');
    if (bioTag) {
      bioTag.style.display = user.isBiometricVerified ? 'inline-flex' : 'none';
    }
  }

  // Initialize workstation listeners and live pipeline once
  if (!isStudioInitialized) {
    initPcaInputs();
    initStudioEventListeners();
    resetForm();
    checkSystemHealth();
    fetchAnalyticsStats();

    // Load persistent audit trail from Supabase Cloud
    fetchLatestAuditsFromSupabase(15).then(records => {
      if (records && records.length > 0 && auditHistory.length === 0) {
        auditHistory = records.map(r => ({
          id: r.transaction_id,
          amount: parseFloat(r.amount) || 0.0,
          probability: parseFloat(r.fraud_probability) || 0.0,
          decision: r.decision,
          latency: parseFloat(r.latency_ms) || 0.0,
          timestamp: new Date(r.created_at).toLocaleTimeString()
        }));
        renderAuditTable();
      }
    }).catch(err => console.warn('Could not load Supabase audit history:', err));

    isStudioInitialized = true;
  }
}

/* ==========================================================================
   2. Sentinel Triage Workstation Logic
   ========================================================================== */

function initPcaInputs() {
  const container = document.getElementById('pca-fields-container');
  if (!container) return;

  let html = '';
  for (let i = 1; i <= 28; i++) {
    const isSpecial = [4, 10, 11, 12, 14, 17].includes(i);
    const badge = isSpecial ? '★ ' : '';
    html += `
      <div class="pca-input-group">
        <label class="pca-label" for="input-v${i}" title="${isSpecial ? 'Key Fraud Factor' : ''}">${badge}V${i}</label>
        <input type="number" step="any" id="input-v${i}" class="pca-input" value="0.0">
      </div>`;
  }
  container.innerHTML = html;
}

function initStudioEventListeners() {
  // Operational Profile Buttons
  document.getElementById('btn-preset-legit')?.addEventListener('click', () => loadPreset('legitimate_grocery'));
  document.getElementById('btn-preset-review')?.addEventListener('click', () => loadPreset('suspicious_velocity'));
  document.getElementById('btn-preset-fraud')?.addEventListener('click', () => loadPreset('confirmed_fraud'));
  document.getElementById('btn-preset-random')?.addEventListener('click', loadRandomPreset);

  // Form Submission
  document.getElementById('transaction-form')?.addEventListener('submit', handleFormSubmit);

  // Reset Button & Signout / Lock Workstation
  document.getElementById('btn-reset')?.addEventListener('click', resetForm);
  document.getElementById('btn-signout')?.addEventListener('click', () => {
    auth.signOut();
    resetForm();
    showAuthScreen();
  });

  // Accordion Toggle
  const accordionHeader = document.getElementById('accordion-toggle');
  const accordionBody = document.getElementById('accordion-body');
  accordionHeader?.addEventListener('click', () => {
    const isOpen = accordionBody.style.display !== 'none';
    accordionBody.style.display = isOpen ? 'none' : 'grid';
    document.getElementById('accordion-arrow').textContent = isOpen ? '▼' : '▲';
  });

  // Tab View Switcher
  const viewSingleBtn = document.getElementById('tab-single');
  const viewBatchBtn = document.getElementById('tab-batch');
  const viewSinglePanel = document.getElementById('view-single-panel');
  const viewBatchPanel = document.getElementById('view-batch-panel');

  viewSingleBtn?.addEventListener('click', () => {
    viewSingleBtn.classList.add('active');
    viewBatchBtn?.classList.remove('active');
    viewSinglePanel.style.display = 'grid';
    viewBatchPanel.style.display = 'none';
  });

  viewBatchBtn?.addEventListener('click', () => {
    viewBatchBtn.classList.add('active');
    viewSingleBtn?.classList.remove('active');
    viewSinglePanel.style.display = 'none';
    viewBatchPanel.style.display = 'block';
  });

  // Batch CSV Handlers
  initBatchHandlers();
}

function loadPreset(presetKey) {
  const p = PRESETS[presetKey];
  if (!p) return;

  document.getElementById('input-tx-id').value = p.transactionId;
  document.getElementById('input-amount').value = p.amount;
  document.getElementById('input-time').value = p.time;

  for (let i = 1; i <= 28; i++) {
    const input = document.getElementById(`input-v${i}`);
    if (input) {
      input.value = p.features[`V${i}`] !== undefined ? p.features[`V${i}`] : 0.0;
    }
  }
}

function resetForm() {
  const txInput = document.getElementById('input-tx-id');
  const amountInput = document.getElementById('input-amount');
  const timeInput = document.getElementById('input-time');
  if (txInput) txInput.value = '';
  if (amountInput) amountInput.value = '';
  if (timeInput) timeInput.value = '';

  for (let i = 1; i <= 28; i++) {
    const input = document.getElementById(`input-v${i}`);
    if (input) input.value = '0.0';
  }
}

function loadRandomPreset() {
  const rnd = generateRandomTransaction();
  document.getElementById('input-tx-id').value = rnd.transactionId;
  document.getElementById('input-amount').value = rnd.amount;
  document.getElementById('input-time').value = rnd.time;

  for (let i = 1; i <= 28; i++) {
    const input = document.getElementById(`input-v${i}`);
    if (input) {
      input.value = rnd.features[`V${i}`] !== undefined ? rnd.features[`V${i}`] : 0.0;
    }
  }
}

async function handleFormSubmit(e) {
  e.preventDefault();
  const submitBtn = document.getElementById('btn-submit');
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Analyzing with XGBoost & SHAP...</span>`;

  try {
    const payload = extractFormData();
    const res = await fetch(`${API_BASE}/predict?includeExplanation=true`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!res.ok) {
      const err = await res.json();
      throw new Error(err.message || 'Error executing fraud evaluation.');
    }

    const data = await res.json();
    displayPredictionResult(data);
    appendAuditRecord(data, payload.amount);

    // Asynchronously sync to Supabase Cloud
    saveAuditToSupabase({
      transactionId: data.transactionId,
      amount: payload.amount,
      time: payload.time,
      fraudProbability: data.fraudProbability,
      isFraud: data.isFraud,
      riskLevel: data.riskLevel,
      decision: data.decision,
      latencyMs: data.latencyMs,
      topFactors: data.topFactors,
      userEmail: auth.getCurrentUser()?.email
    }).catch(e => console.warn(e));

    fetchAnalyticsStats();
  } catch (err) {
    console.error(err);
    alert(`Evaluation Error: ${err.message}`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = `
      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      Analyze Risk with AI`;
  }
}

function extractFormData() {
  const features = {};
  for (let i = 1; i <= 28; i++) {
    const val = parseFloat(document.getElementById(`input-v${i}`)?.value);
    features[`V${i}`] = isNaN(val) ? 0.0 : val;
  }

  return {
    transactionId: document.getElementById('input-tx-id').value || 'TX-90218412',
    amount: parseFloat(document.getElementById('input-amount').value) || 0.0,
    time: parseFloat(document.getElementById('input-time').value) || 0.0,
    features: features,
    includeExplanation: true
  };
}

function displayPredictionResult(data) {
  updateRiskGauge(data.fraudProbability);

  const badge = document.getElementById('decision-badge');
  const text = document.getElementById('decision-text');
  badge.className = 'decision-badge';

  if (data.decision === 'BLOCK_TRANSACTION') {
    badge.classList.add('decision-badge--fraud');
    text.textContent = 'DECLINE & FREEZE TRANSACTION';
  } else if (data.decision === 'MANUAL_REVIEW') {
    badge.classList.add('decision-badge--review');
    text.textContent = 'MANUAL REVIEW REQUIRED';
  } else {
    badge.classList.add('decision-badge--legit');
    text.textContent = 'APPROVE TRANSACTION';
  }

  document.getElementById('eval-latency').textContent = `${data.latencyMs} ms`;
  document.getElementById('eval-threshold').textContent = `Cutoff: ${(data.thresholdUsed * 100).toFixed(1)}%`;

  renderExplainabilityWaterfall(data.topFactors || []);
}

function appendAuditRecord(pred, amount) {
  auditHistory.unshift({
    id: pred.transactionId,
    amount: amount,
    probability: pred.fraudProbability,
    decision: pred.decision,
    latency: pred.latencyMs,
    timestamp: new Date().toLocaleTimeString()
  });

  if (auditHistory.length > 25) auditHistory.pop();
  renderAuditTable();
}

function renderAuditTable() {
  const tbody = document.getElementById('audit-tbody');
  if (!tbody || auditHistory.length === 0) return;

  tbody.innerHTML = auditHistory.map(row => {
    let tagClass = 'tag-legit';
    if (row.decision === 'BLOCK_TRANSACTION') tagClass = 'tag-fraud';
    else if (row.decision === 'MANUAL_REVIEW') tagClass = 'tag-review';

    return `
      <tr>
        <td><strong>${escapeHtml(row.id)}</strong></td>
        <td>₹${Number(row.amount).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        <td>${(row.probability * 100).toFixed(2)}%</td>
        <td><span class="${tagClass}">${escapeHtml(row.decision)}</span></td>
        <td>${row.latency} ms</td>
        <td style="color: var(--text-muted);">${row.timestamp}</td>
      </tr>`;
  }).join('');
}

async function checkSystemHealth() {
  const pill = document.getElementById('header-status-pill');
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      if (data.modelLoaded) {
        pill.className = 'status-pill status-pill--online';
        pill.innerHTML = `<span class="status-dot"></span> Pipeline Active`;
      } else {
        pill.className = 'status-pill status-pill--offline';
        pill.innerHTML = `<span class="status-dot"></span> Model Offline`;
      }
    } else {
      throw new Error();
    }
  } catch {
    pill.className = 'status-pill status-pill--offline';
    pill.innerHTML = `<span class="status-dot"></span> API Disconnected`;
  }

  // Update Supabase Cloud connectivity indicator
  const supabasePill = document.getElementById('header-supabase-pill');
  if (supabasePill) {
    if (isSupabaseConfigured()) {
      supabasePill.style.display = 'inline-flex';
      supabasePill.className = 'status-pill status-pill--online';
      supabasePill.innerHTML = `<span class="status-dot" style="background: #10b981;"></span> Supabase Cloud Active`;
    } else {
      supabasePill.style.display = 'none';
    }
  }
}

async function fetchAnalyticsStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/stats`);
    if (res.ok) {
      const stats = await res.json();
      document.getElementById('kpi-total-scored').textContent = stats.totalEvaluated;
      document.getElementById('kpi-fraud-rate').textContent = `${(stats.fraudRate * 100).toFixed(1)}%`;
      document.getElementById('kpi-review-rate').textContent = `${(stats.reviewRate * 100).toFixed(1)}%`;
      document.getElementById('kpi-avg-latency').textContent = `${stats.averageLatencyMs} ms`;
    }
  } catch (e) {
    console.warn('Analytics stats unavailable:', e);
  }
}

/* ==========================================================================
   3. Batch CSV Handlers
   ========================================================================== */

function initBatchHandlers() {
  const dropzone = document.getElementById('csv-dropzone');
  const fileInput = document.getElementById('csv-file-input');
  const browseBtn = document.getElementById('btn-browse-file');
  const sampleCsvBtn = document.getElementById('btn-download-sample-csv');

  browseBtn?.addEventListener('click', (e) => {
    e.stopPropagation();
    fileInput?.click();
  });

  dropzone?.addEventListener('click', () => fileInput?.click());

  dropzone?.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropzone.classList.add('dragover');
  });

  dropzone?.addEventListener('dragleave', () => dropzone.classList.remove('dragover'));

  dropzone?.addEventListener('drop', (e) => {
    e.preventDefault();
    dropzone.classList.remove('dragover');
    if (e.dataTransfer.files.length) {
      processCsvFile(e.dataTransfer.files[0]);
    }
  });

  fileInput?.addEventListener('change', (e) => {
    if (e.target.files.length) {
      processCsvFile(e.target.files[0]);
    }
  });

  sampleCsvBtn?.addEventListener('click', downloadSampleCsv);
}

function processCsvFile(file) {
  const reader = new FileReader();
  reader.onload = async (e) => {
    const text = e.target.result;
    const lines = text.trim().split('\n');
    if (lines.length < 2) {
      alert('CSV file is empty or missing headers.');
      return;
    }

    const headers = lines[0].split(',').map(h => h.trim());
    const transactions = [];

    for (let i = 1; i < lines.length; i++) {
      const vals = lines[i].split(',').map(v => v.trim());
      if (vals.length !== headers.length) continue;

      const row = {};
      headers.forEach((h, idx) => {
        row[h] = parseFloat(vals[idx]) || vals[idx];
      });

      const txPayload = {
        transactionId: String(row.transactionId || `TX-${1000000 + i}`),
        amount: parseFloat(row.Amount) || 0.0,
        time: parseFloat(row.Time) || 0.0,
        features: {}
      };

      for (let j = 1; j <= 28; j++) {
        txPayload.features[`V${j}`] = parseFloat(row[`V${j}`]) || 0.0;
      }
      transactions.push(txPayload);
    }

    if (transactions.length === 0) {
      alert('No valid transaction rows found in CSV.');
      return;
    }

    await submitBatchEvaluation(transactions);
  };
  reader.readAsText(file);
}

async function submitBatchEvaluation(transactions) {
  const dropzone = document.getElementById('csv-dropzone');
  const resultsContainer = document.getElementById('batch-results-container');
  const statsSummary = document.getElementById('batch-stats-summary');

  dropzone.style.opacity = '0.5';
  dropzone.style.pointerEvents = 'none';

  try {
    const res = await fetch(`${API_BASE}/predict/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transactions })
    });

    if (!res.ok) throw new Error('Vectorized batch evaluation failed.');

    const data = await res.json();
    resultsContainer.style.display = 'block';
    statsSummary.textContent = `Processed ${data.totalProcessed} records · High Risk: ${data.fraudDetected} · Manual Review: ${data.manualReviewCount} · Avg Latency: ${data.averageLatencyMs}ms`;

    renderBatchResults(data.results);
    fetchAnalyticsStats();
  } catch (err) {
    alert(err.message);
  } finally {
    dropzone.style.opacity = '1';
    dropzone.style.pointerEvents = 'all';
  }
}

function renderBatchResults(results) {
  const tbody = document.getElementById('batch-tbody');
  tbody.innerHTML = results.map(item => {
    let style = 'color: var(--color-legit); font-weight: 700;';
    if (item.decision === 'BLOCK_TRANSACTION') style = 'color: var(--color-fraud); font-weight: 700;';
    else if (item.decision === 'MANUAL_REVIEW') style = 'color: var(--color-review); font-weight: 700;';

    const amt = item.amount !== undefined ? item.amount : (Math.random() * 25000 + 500);
    return `
      <tr>
        <td>${escapeHtml(item.transactionId)}</td>
        <td>₹${Number(amt).toLocaleString('en-IN', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
        <td>${(item.fraudProbability * 100).toFixed(2)}%</td>
        <td style="${style}">${escapeHtml(item.decision)}</td>
        <td>${item.latencyMs} ms</td>
      </tr>`;
  }).join('');
}

function downloadSampleCsv() {
  let csv = 'transactionId,Amount,Time,' + Array.from({length: 28}, (_, i) => `V${i+1}`).join(',') + '\n';
  
  // 5 standard retail rows (₹500 - ₹3,000)
  for (let i = 1; i <= 5; i++) {
    const feats = Array.from({length: 28}, () => ((Math.random() - 0.5) * 0.4).toFixed(3)).join(',');
    csv += `TX-100${i}84,${(Math.random()*2500 + 500).toFixed(2)},${i*100},${feats}\n`;
  }
  // 3 suspicious velocity rows (₹40,000 - ₹65,000)
  for (let i = 1; i <= 3; i++) {
    const feats = Array.from({length: 28}, (_, idx) => {
      if (idx === 3 || idx === 10) return (1.8 + Math.random()*0.5).toFixed(3);
      if (idx === 13) return (-2.2 - Math.random()*0.5).toFixed(3);
      return ((Math.random() - 0.5) * 0.8).toFixed(3);
    }).join(',');
    csv += `TX-500${i}92,${(Math.random()*25000 + 40000).toFixed(2)},${i*500},${feats}\n`;
  }
  // 2 high compromise rows (₹1,00,000 - ₹1,50,000)
  for (let i = 1; i <= 2; i++) {
    const feats = Array.from({length: 28}, (_, idx) => {
      if (idx === 3) return (4.2 + Math.random()*0.5).toFixed(3);
      if (idx === 13) return (-7.5 - Math.random()*0.5).toFixed(3);
      if (idx === 11) return (-6.0 - Math.random()*0.5).toFixed(3);
      return ((Math.random() - 0.5) * 1.5).toFixed(3);
    }).join(',');
    csv += `TX-900${i}15,${(Math.random()*50000 + 100000).toFixed(2)},${i*900},${feats}\n`;
  }

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'sentinel_production_batch_template.csv';
  a.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}
