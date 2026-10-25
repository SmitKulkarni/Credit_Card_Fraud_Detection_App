/**
 * Sentinel Triage Studio - Main Application Logic & API Client.
 */

import { PRESETS, generateRandomTransaction } from './presets.js';
import { updateRiskGauge, renderExplainabilityWaterfall } from './chart.js';

const API_BASE = window.location.origin.includes('8000') 
  ? `${window.location.origin}/api/v1`
  : 'http://127.0.0.1:8000/api/v1';

let auditHistory = [];

document.addEventListener('DOMContentLoaded', () => {
  initPcaInputs();
  initEventListeners();
  loadPreset('legitimate_grocery');
  checkSystemHealth();
  fetchAnalyticsStats();
});

/**
 * Dynamically generates 28 input fields for PCA components V1 to V28.
 */
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

/**
 * Initializes button listeners, form submit, and tab switching.
 */
function initEventListeners() {
  // Preset Buttons
  document.getElementById('btn-preset-legit')?.addEventListener('click', () => loadPreset('legitimate_grocery'));
  document.getElementById('btn-preset-review')?.addEventListener('click', () => loadPreset('suspicious_velocity'));
  document.getElementById('btn-preset-fraud')?.addEventListener('click', () => loadPreset('confirmed_fraud'));
  document.getElementById('btn-preset-random')?.addEventListener('click', loadRandomPreset);

  // Form Submission
  document.getElementById('transaction-form')?.addEventListener('submit', handleFormSubmit);

  // Reset Button
  document.getElementById('btn-reset')?.addEventListener('click', () => loadPreset('legitimate_grocery'));

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

/**
 * Loads a named preset into form controls.
 */
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

  // Auto trigger prediction for immediate visual gratification
  document.getElementById('transaction-form')?.requestSubmit();
}

/**
 * Generates and loads a randomized test transaction.
 */
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
  document.getElementById('transaction-form')?.requestSubmit();
}

/**
 * Collects form inputs and calls /api/v1/predict.
 */
async function handleFormSubmit(e) {
  e.preventDefault();
  const submitBtn = document.getElementById('btn-submit');
  const originalText = submitBtn.innerHTML;
  submitBtn.disabled = true;
  submitBtn.innerHTML = `<span>Analyzing Neural Weights...</span>`;

  const payload = {
    transactionId: document.getElementById('input-tx-id').value || `tx_${Date.now()}`,
    amount: parseFloat(document.getElementById('input-amount').value) || 0.0,
    time: parseFloat(document.getElementById('input-time').value) || 0.0,
    features: {}
  };

  for (let i = 1; i <= 28; i++) {
    const input = document.getElementById(`input-v${i}`);
    payload.features[`V${i}`] = parseFloat(input?.value) || 0.0;
  }

  try {
    const response = await fetch(`${API_BASE}/predict?includeExplanation=true`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    const data = await response.json();
    displayPredictionResult(data);
    addToAuditTable(data, payload);
    fetchAnalyticsStats();
  } catch (err) {
    console.error('Inference error:', err);
    alert(`Inference failed: ${err.message}. Ensure backend is running.`);
  } finally {
    submitBtn.disabled = false;
    submitBtn.innerHTML = originalText;
  }
}

/**
 * Updates UI with prediction response.
 */
function displayPredictionResult(data) {
  updateRiskGauge(data.fraudProbability, data.decision);
  renderExplainabilityWaterfall(data.topFactors);

  const speedBadge = document.getElementById('eval-latency');
  if (speedBadge) {
    speedBadge.textContent = `${data.latencyMs} ms`;
  }
  const threshBadge = document.getElementById('eval-threshold');
  if (threshBadge) {
    threshBadge.textContent = `Cutoff: ${(data.thresholdUsed * 100).toFixed(1)}%`;
  }
}

/**
 * Appends record to the Audit Trail table.
 */
function addToAuditTable(data, payload) {
  const tbody = document.getElementById('audit-tbody');
  if (!tbody) return;

  auditHistory.unshift({ ...data, amount: payload.amount, time: payload.time });
  if (auditHistory.length > 25) auditHistory.pop();

  let html = '';
  auditHistory.forEach(item => {
    let badgeClass = 'color: var(--color-legit); font-weight: 700;';
    if (item.riskLevel === 'HIGH') badgeClass = 'color: var(--color-fraud); font-weight: 700;';
    else if (item.riskLevel === 'MEDIUM') badgeClass = 'color: var(--color-review); font-weight: 700;';

    html += `
      <tr>
        <td>${escapeHtml(item.transactionId)}</td>
        <td>$${item.amount.toFixed(2)}</td>
        <td>${(item.fraudProbability * 100).toFixed(2)}%</td>
        <td style="${badgeClass}">${escapeHtml(item.decision)}</td>
        <td>${item.latencyMs} ms</td>
        <td style="color: var(--text-muted); font-size: 0.75rem;">${new Date(item.evaluatedAt).toLocaleTimeString()}</td>
      </tr>`;
  });
  tbody.innerHTML = html;
}

/**
 * Checks system health and model registry info.
 */
async function checkSystemHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (res.ok) {
      const data = await res.json();
      const statusPill = document.getElementById('header-status-pill');
      if (statusPill && data.modelLoaded) {
        statusPill.innerHTML = `<span class="status-dot"></span> API Online (v${data.appVersion})`;
      }
    }
  } catch (err) {
    const statusPill = document.getElementById('header-status-pill');
    if (statusPill) {
      statusPill.innerHTML = `<span class="status-dot" style="background:#ef4444;box-shadow:none;"></span> Backend Offline`;
      statusPill.style.borderColor = 'rgba(239, 68, 68, 0.4)';
      statusPill.style.color = '#ef4444';
    }
  }
}

/**
 * Fetches rolling session statistics for KPI ribbon.
 */
async function fetchAnalyticsStats() {
  try {
    const res = await fetch(`${API_BASE}/analytics/stats`);
    if (res.ok) {
      const data = await res.json();
      document.getElementById('kpi-total-scored').textContent = data.totalTransactionsScored || '0';
      document.getElementById('kpi-fraud-rate').textContent = `${data.fraudBlockedRate || 0.0}%`;
      document.getElementById('kpi-review-rate').textContent = `${data.manualReviewRate || 0.0}%`;
      document.getElementById('kpi-avg-latency').textContent = `${data.latencyStats?.averageMs || 0.0} ms`;
    }
  } catch (err) {
    console.debug('Analytics stats fetch skipped:', err);
  }
}

/**
 * Batch CSV Upload and Simulation logic.
 */
function initBatchHandlers() {
  const dropzone = document.getElementById('csv-dropzone');
  const fileInput = document.getElementById('csv-file-input');
  const demoCsvBtn = document.getElementById('btn-download-sample-csv');

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

  demoCsvBtn?.addEventListener('click', downloadSampleCsv);
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
        transactionId: row.transactionId || `tx_batch_${i}`,
        amount: parseFloat(row.Amount || row.amount || 0.0),
        time: parseFloat(row.Time || row.time || 0.0),
        features: {}
      };

      for (let v = 1; v <= 28; v++) {
        const key = `V${v}`;
        txPayload.features[key] = parseFloat(row[key] !== undefined ? row[key] : row[key.toLowerCase()] || 0.0);
      }
      transactions.push(txPayload);
    }

    if (transactions.length > 0) {
      await submitBatch(transactions);
    }
  };
  reader.readAsText(file);
}

async function submitBatch(transactions) {
  const progressElem = document.getElementById('batch-progress');
  if (progressElem) progressElem.style.display = 'block';

  try {
    const res = await fetch(`${API_BASE}/predict/batch`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ transactions: transactions.slice(0, 500), includeExplanation: false })
    });

    if (!res.ok) throw new Error(`Batch scoring failed: ${res.statusText}`);

    const data = await res.json();
    renderBatchResults(data);
    fetchAnalyticsStats();
  } catch (err) {
    alert(`Batch processing error: ${err.message}`);
  } finally {
    if (progressElem) progressElem.style.display = 'none';
  }
}

function renderBatchResults(batchData) {
  const resultsCard = document.getElementById('batch-results-card');
  const tbody = document.getElementById('batch-results-tbody');
  if (!resultsCard || !tbody) return;

  resultsCard.style.display = 'block';
  document.getElementById('batch-stat-total').textContent = batchData.totalProcessed;
  document.getElementById('batch-stat-fraud').textContent = batchData.fraudDetected;
  document.getElementById('batch-stat-review').textContent = batchData.manualReviewCount;
  document.getElementById('batch-stat-approved').textContent = batchData.approvedCount;

  let html = '';
  batchData.results.forEach(item => {
    let style = 'color: var(--color-legit);';
    if (item.riskLevel === 'HIGH') style = 'color: var(--color-fraud); font-weight: 700;';
    else if (item.riskLevel === 'MEDIUM') style = 'color: var(--color-review); font-weight: 700;';

    html += `
      <tr>
        <td>${escapeHtml(item.transactionId)}</td>
        <td>${(item.fraudProbability * 100).toFixed(2)}%</td>
        <td style="${style}">${escapeHtml(item.decision)}</td>
        <td>${item.latencyMs} ms</td>
      </tr>`;
  });
  tbody.innerHTML = html;
}

function downloadSampleCsv() {
  let csv = 'transactionId,Amount,Time,' + Array.from({length: 28}, (_, i) => `V${i+1}`).join(',') + '\n';
  
  // 5 normal rows
  for (let i = 1; i <= 5; i++) {
    const feats = Array.from({length: 28}, () => ((Math.random() - 0.5) * 0.4).toFixed(3)).join(',');
    csv += `tx_sample_normal_${i},${(Math.random()*50 + 10).toFixed(2)},${i*100},${feats}\n`;
  }
  // 3 suspicious rows
  for (let i = 1; i <= 3; i++) {
    const feats = Array.from({length: 28}, (_, idx) => {
      if (idx === 3 || idx === 10) return (1.8 + Math.random()*0.5).toFixed(3);
      if (idx === 13) return (-2.2 - Math.random()*0.5).toFixed(3);
      return ((Math.random() - 0.5) * 0.8).toFixed(3);
    }).join(',');
    csv += `tx_sample_review_${i},${(Math.random()*400 + 500).toFixed(2)},${i*500},${feats}\n`;
  }
  // 2 high fraud rows
  for (let i = 1; i <= 2; i++) {
    const feats = Array.from({length: 28}, (_, idx) => {
      if (idx === 3) return (4.2 + Math.random()*0.5).toFixed(3);
      if (idx === 13) return (-7.5 - Math.random()*0.5).toFixed(3);
      if (idx === 11) return (-6.0 - Math.random()*0.5).toFixed(3);
      return ((Math.random() - 0.5) * 1.5).toFixed(3);
    }).join(',');
    csv += `tx_sample_fraud_${i},${(Math.random()*800 + 1200).toFixed(2)},${i*900},${feats}\n`;
  }

  const blob = new Blob([csv], { type: 'text/csv' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'sample_credit_card_batch.csv';
  a.click();
  URL.revokeObjectURL(url);
}

function escapeHtml(str) {
  if (!str) return '';
  return String(str).replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}
