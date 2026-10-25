/**
 * Visual rendering engine for Risk Gauge & Tree SHAP Explainability.
 */

const CIRCUMFERENCE = 2 * Math.PI * 90; // ~565.48px

/**
 * Updates the circular SVG gauge with animated stroke and numeric counter.
 */
export function updateRiskGauge(probability, decision) {
  const bar = document.getElementById('gauge-bar');
  const percentText = document.getElementById('gauge-percent');
  const badge = document.getElementById('decision-badge');
  const badgeText = document.getElementById('decision-text');

  if (!bar || !percentText) return;

  const pct = Math.max(0, Math.min(100, probability * 100));
  const offset = CIRCUMFERENCE - (pct / 100) * CIRCUMFERENCE;

  // Color selection based on risk
  let color = '#10b981';
  let badgeClass = 'decision-badge--legit';
  let decisionLabel = 'APPROVE TRANSACTION';

  if (probability >= 0.35) {
    color = '#ef4444';
    badgeClass = 'decision-badge--fraud';
    decisionLabel = 'BLOCK TRANSACTION (FRAUD)';
  } else if (probability >= 0.20) {
    color = '#f59e0b';
    badgeClass = 'decision-badge--review';
    decisionLabel = 'MANUAL REVIEW (SUSPICIOUS)';
  }

  // Update SVG
  bar.style.stroke = color;
  bar.style.strokeDashoffset = offset;

  // Animate counter
  animateValue(percentText, 0, pct, 800);

  // Update Decision Badge
  if (badge && badgeText) {
    badge.className = `decision-badge ${badgeClass}`;
    badgeText.textContent = decisionLabel;
  }
}

/**
 * Renders the Tree SHAP Waterfall factors into the explanation container.
 */
export function renderExplainabilityWaterfall(factors) {
  const container = document.getElementById('factors-container');
  if (!container) return;

  if (!factors || factors.length === 0) {
    container.innerHTML = `
      <div style="padding: 1.5rem; text-align: center; color: var(--text-muted); font-size: 0.85rem;">
        No factor anomalies detected. Transaction fits standard consumer patterns.
      </div>`;
    return;
  }

  const maxImpact = Math.max(...factors.map(f => Math.abs(f.impact)), 1.0);

  let html = '<div class="factor-list">';
  factors.forEach(f => {
    const isUp = f.direction === 'INCREASES_RISK' || f.impact > 0;
    const widthPct = Math.min(100, (Math.abs(f.impact) / maxImpact) * 100);
    const sign = f.impact > 0 ? '+' : '';
    const colorClass = isUp ? 'factor-impact--up' : 'factor-impact--down';
    const fillClass = isUp ? 'factor-bar-fill--up' : 'factor-bar-fill--down';
    const tag = isUp ? '▲ Increases Risk' : '▼ Decreases Risk';

    html += `
      <div class="factor-item">
        <div class="factor-header">
          <span class="factor-name">${escapeHtml(f.feature)}</span>
          <span class="factor-impact ${colorClass}">${sign}${f.impact.toFixed(3)} (${tag})</span>
        </div>
        <div class="factor-bar-bg">
          <div class="factor-bar-fill ${fillClass}" style="width: ${widthPct}%"></div>
        </div>
        <span class="factor-desc">${escapeHtml(f.description)}</span>
      </div>`;
  });
  html += '</div>';

  container.innerHTML = html;
}

function animateValue(elem, start, end, duration) {
  let startTime = null;
  function step(timestamp) {
    if (!startTime) startTime = timestamp;
    const progress = Math.min((timestamp - startTime) / duration, 1);
    const current = start + progress * (end - start);
    elem.textContent = `${current.toFixed(2)}%`;
    if (progress < 1) {
      window.requestAnimationFrame(step);
    }
  }
  window.requestAnimationFrame(step);
}

function escapeHtml(str) {
  if (!str) return '';
  return str.replace(/[&<>'"]/g, 
    tag => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;' }[tag] || tag)
  );
}
