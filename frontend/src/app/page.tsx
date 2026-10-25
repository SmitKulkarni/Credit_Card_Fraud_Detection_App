import { createClient } from '@/utils/supabase/server';
import { cookies } from 'next/headers';

export const dynamic = 'force-dynamic';

export default async function Page() {
  let audits: any[] | null = null;
  let auditError: any = null;
  let analysts: any[] | null = null;

  try {
    const cookieStore = await cookies();
    const supabase = createClient(cookieStore);

    const { data: auditData, error: aErr } = await supabase
      .from('fraud_audit_records')
      .select('*')
      .order('created_at', { ascending: false })
      .limit(10);

    audits = auditData;
    auditError = aErr;

    const { data: analystData } = await supabase
      .from('analyst_profiles')
      .select('*')
      .order('created_at', { ascending: false });

    analysts = analystData;
  } catch (err: any) {
    auditError = { message: err?.message || 'Failed connecting to database' };
  }

  return (
    <div style={{ minHeight: '100vh', background: 'radial-gradient(circle at 50% 0%, #1e293b 0%, #090d16 65%)', color: '#f8fafc', padding: '2rem 3rem' }}>
      {/* Header Bar */}
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid rgba(255,255,255,0.08)', paddingBottom: '1.5rem', marginBottom: '2rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: 44, height: 44, borderRadius: 12, background: 'linear-gradient(135deg, #0ea5e9, #6366f1)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 20px rgba(14,165,233,0.3)' }}>
            <span style={{ fontSize: '1.5rem' }}>🛡️</span>
          </div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(180deg, #ffffff 0%, #94a3b8 100%)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
              Sentinel Enterprise Fraud Intelligence
            </h1>
            <p style={{ margin: '0.25rem 0 0', color: '#94a3b8', fontSize: '0.85rem' }}>
              Dual Tier Architecture · Next.js 15 Client & FastAPI / XGBoost Machine Learning Microservice
            </p>
          </div>
        </div>

        {/* Action Navigation */}
        <div style={{ display: 'flex', gap: '0.75rem' }}>
          <a
            href="/index.html"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.6rem 1.2rem',
              borderRadius: 8,
              background: '#0284c7',
              color: '#ffffff',
              textDecoration: 'none',
              fontWeight: 600,
              fontSize: '0.85rem',
              boxShadow: '0 4px 14px rgba(2,132,199,0.35)',
              transition: 'background 0.2s',
            }}
          >
            <span>⚡ Open Triage Studio</span>
          </a>
          <a
            href="http://127.0.0.1:8000/docs"
            target="_blank"
            rel="noreferrer"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.6rem 1.2rem',
              borderRadius: 8,
              background: 'rgba(255,255,255,0.06)',
              color: '#e2e8f0',
              textDecoration: 'none',
              fontWeight: 600,
              fontSize: '0.85rem',
              border: '1px solid rgba(255,255,255,0.12)',
            }}
          >
            <span>📑 FastAPI Docs</span>
          </a>
        </div>
      </header>

      {/* Quick Launch Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1.25rem', marginBottom: '2.5rem' }}>
        <div style={{ background: 'rgba(15, 23, 42, 0.65)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#38bdf8', fontWeight: 700 }}>Frontend Server</span>
            <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: 999, background: 'rgba(16,185,129,0.15)', color: '#34d399', fontWeight: 600 }}>Active · :3000</span>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
            Next.js App Router running locally with SSR hydration & static asset pipeline.
          </p>
        </div>

        <div style={{ background: 'rgba(15, 23, 42, 0.65)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#a78bfa', fontWeight: 700 }}>ML Inference Engine</span>
            <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: 999, background: 'rgba(16,185,129,0.15)', color: '#34d399', fontWeight: 600 }}>FastAPI · :8000</span>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
            XGBoost calibrated risk engine with Tree SHAP explainability and SQLite / Supabase sync.
          </p>
        </div>

        <div style={{ background: 'rgba(15, 23, 42, 0.65)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 12, padding: '1.25rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.05em', color: '#34d399', fontWeight: 700 }}>Database Tier</span>
            <span style={{ fontSize: '0.75rem', padding: '0.2rem 0.5rem', borderRadius: 999, background: 'rgba(56,189,248,0.15)', color: '#38bdf8', fontWeight: 600 }}>Supabase Cloud</span>
          </div>
          <p style={{ margin: 0, fontSize: '0.85rem', color: '#94a3b8' }}>
            PostgreSQL instance connected via PostgREST and SSR server-side client.
          </p>
        </div>
      </div>

      {/* Main Content Sections */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '2rem' }}>
        {/* Left Column: Live Audit Records */}
        <section style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '1.5rem', backdropFilter: 'blur(12px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 700, color: '#f1f5f9' }}>
              Real-Time Supabase Audit Records ({audits?.length ?? 0})
            </h2>
            <a href="/index.html" style={{ color: '#38bdf8', fontSize: '0.8rem', textDecoration: 'none', fontWeight: 600 }}>
              Live Triage Studio →
            </a>
          </div>

          {auditError ? (
            <div style={{ padding: '1rem', borderRadius: 8, background: 'rgba(239,68,68,0.1)', border: '1px solid rgba(239,68,68,0.25)', color: '#fca5a5', fontSize: '0.85rem' }}>
              ⚠️ Supabase Connection Notice: {auditError.message}
            </div>
          ) : (
            <div style={{ overflowX: 'auto' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '0.85rem' }}>
                <thead>
                  <tr style={{ borderBottom: '1px solid rgba(255,255,255,0.08)', color: '#64748b', fontSize: '0.75rem', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Transaction</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Amount</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Risk Score</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Decision</th>
                    <th style={{ padding: '0.75rem 0.5rem' }}>Timestamp</th>
                  </tr>
                </thead>
                <tbody>
                  {audits && audits.length > 0 ? (
                    audits.map((a: any) => (
                      <tr key={a.id} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                        <td style={{ padding: '0.75rem 0.5rem', fontFamily: 'JetBrains Mono, monospace', fontWeight: 600 }}>{a.transaction_id}</td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>${Number(a.amount).toFixed(2)}</td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>
                          <span style={{ padding: '0.15rem 0.45rem', borderRadius: 4, background: Number(a.fraud_probability) > 0.35 ? 'rgba(239,68,68,0.15)' : 'rgba(16,185,129,0.15)', color: Number(a.fraud_probability) > 0.35 ? '#f87171' : '#34d399', fontWeight: 600, fontFamily: 'JetBrains Mono, monospace', fontSize: '0.8rem' }}>
                            {(Number(a.fraud_probability) * 100).toFixed(1)}%
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem' }}>
                          <span style={{ fontWeight: 700, color: a.decision === 'APPROVE' ? '#10b981' : a.decision === 'REVIEW' ? '#f59e0b' : '#ef4444' }}>
                            {a.decision}
                          </span>
                        </td>
                        <td style={{ padding: '0.75rem 0.5rem', color: '#64748b', fontSize: '0.78rem' }}>
                          {new Date(a.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={5} style={{ padding: '2rem 1rem', textAlign: 'center', color: '#64748b' }}>
                        No audit records currently found. Submit a transaction from the <a href="/index.html" style={{ color: '#38bdf8' }}>Triage Studio</a> to generate records.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          )}
        </section>

        {/* Right Column: Security Profiles & Quick Access */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          <section style={{ background: 'rgba(15, 23, 42, 0.8)', border: '1px solid rgba(255,255,255,0.08)', borderRadius: 14, padding: '1.5rem' }}>
            <h2 style={{ margin: '0 0 1rem', fontSize: '1.1rem', fontWeight: 700, color: '#f1f5f9' }}>
              Analyst Clearance Profiles ({analysts?.length ?? 0})
            </h2>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {analysts && analysts.length > 0 ? (
                analysts.map((u: any) => (
                  <div key={u.id} style={{ background: 'rgba(30, 41, 59, 0.5)', padding: '0.75rem', borderRadius: 8, border: '1px solid rgba(255,255,255,0.05)' }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                      <span style={{ fontWeight: 600, fontSize: '0.85rem' }}>{u.full_name}</span>
                      <span style={{ fontSize: '0.72rem', padding: '0.15rem 0.4rem', borderRadius: 4, background: '#0284c7', color: '#fff', fontWeight: 600 }}>{u.clearance_level}</span>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.35rem', fontSize: '0.75rem', color: '#94a3b8' }}>
                      <span>{u.role}</span>
                      <span>{u.biometric_enrolled ? '🛡️ Passkey' : 'Password'}</span>
                    </div>
                  </div>
                ))
              ) : (
                <p style={{ margin: 0, fontSize: '0.85rem', color: '#64748b' }}>
                  No registered profiles.
                </p>
              )}
            </div>
          </section>

          <section style={{ background: 'linear-gradient(135deg, rgba(14,165,233,0.1), rgba(99,102,241,0.05))', border: '1px solid rgba(56,189,248,0.25)', borderRadius: 14, padding: '1.5rem' }}>
            <h3 style={{ margin: '0 0 0.5rem', fontSize: '1rem', color: '#38bdf8' }}>Interactive Workstation</h3>
            <p style={{ margin: '0 0 1rem', fontSize: '0.82rem', color: '#94a3b8', lineHeight: 1.5 }}>
              Launch the full Sentinel Triage Studio for real-time single and batch transaction scoring, dynamic $V_1-V_{28}$ features, and Tree SHAP waterfall explainability charts.
            </p>
            <a
              href="/index.html"
              style={{
                display: 'block',
                textAlign: 'center',
                padding: '0.65rem 1rem',
                borderRadius: 8,
                background: '#0ea5e9',
                color: '#fff',
                textDecoration: 'none',
                fontWeight: 600,
                fontSize: '0.85rem',
              }}
            >
              Launch Sentinel Studio →
            </a>
          </section>
        </div>
      </div>
    </div>
  );
}
