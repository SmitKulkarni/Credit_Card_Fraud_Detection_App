import { createClient } from '@/utils/supabase/server';
import { cookies } from 'next/headers';

export default async function Page() {
  const cookieStore = await cookies();
  const supabase = createClient(cookieStore);

  const { data: audits, error: auditError } = await supabase
    .from('fraud_audit_records')
    .select('*')
    .order('created_at', { ascending: false })
    .limit(10);

  const { data: analysts } = await supabase
    .from('analyst_profiles')
    .select('*')
    .order('created_at', { ascending: false });

  return (
    <div style={{ padding: '2rem', fontFamily: 'Inter, sans-serif', background: '#090d16', color: '#f8fafc', minHeight: '100vh' }}>
      <h1 style={{ fontSize: '1.75rem', fontWeight: 800, marginBottom: '0.5rem' }}>
        Sentinel Fraud Intelligence — Supabase Cloud
      </h1>
      <p style={{ color: '#94a3b8', fontSize: '0.9rem', marginBottom: '1.5rem' }}>
        Real-time audit log queried directly from Supabase PostgreSQL (Project: <code>credit_card_fraud_detection</code>).
      </p>

      <h2 style={{ fontSize: '1.25rem', marginBottom: '0.75rem', color: '#38bdf8' }}>
        Cloud Fraud Audit Records ({audits?.length ?? 0})
      </h2>
      {auditError ? (
        <p style={{ color: '#ef4444' }}>Supabase Query Error: {auditError.message}</p>
      ) : (
        <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '1rem', background: '#0f172a', borderRadius: '8px', overflow: 'hidden' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid #334155', color: '#94a3b8', fontSize: '0.8rem' }}>
              <th style={{ padding: '0.75rem 1rem' }}>Transaction ID</th>
              <th style={{ padding: '0.75rem 1rem' }}>Amount</th>
              <th style={{ padding: '0.75rem 1rem' }}>Risk Probability</th>
              <th style={{ padding: '0.75rem 1rem' }}>Decision</th>
              <th style={{ padding: '0.75rem 1rem' }}>Timestamp</th>
            </tr>
          </thead>
          <tbody>
            {audits && audits.length > 0 ? (
              audits.map((a: any) => (
                <tr key={a.id} style={{ borderBottom: '1px solid #1e293b' }}>
                  <td style={{ padding: '0.75rem 1rem', fontWeight: 600 }}>{a.transaction_id}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>${Number(a.amount).toFixed(2)}</td>
                  <td style={{ padding: '0.75rem 1rem' }}>{(Number(a.fraud_probability) * 100).toFixed(2)}%</td>
                  <td style={{ padding: '0.75rem 1rem', color: a.decision === 'APPROVE' ? '#10b981' : '#ef4444' }}>
                    {a.decision}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: '#64748b' }}>{new Date(a.created_at).toLocaleString()}</td>
                </tr>
              ))
            ) : (
              <tr>
                <td colSpan={5} style={{ padding: '1.5rem', textAlign: 'center', color: '#64748b' }}>
                  No fraud audit records stored in Supabase cloud yet.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      )}

      <h2 style={{ fontSize: '1.25rem', marginTop: '2.5rem', marginBottom: '0.75rem', color: '#38bdf8' }}>
        Registered Analyst Clearance Profiles ({analysts?.length ?? 0})
      </h2>
      <ul style={{ listStyle: 'none', padding: 0 }}>
        {analysts && analysts.length > 0 ? (
          analysts.map((u: any) => (
            <li key={u.id} style={{ margin: '0.5rem 0', padding: '0.75rem 1rem', background: '#0f172a', borderRadius: '6px' }}>
              <strong>{u.full_name}</strong> ({u.email}) — <span style={{ color: '#38bdf8' }}>{u.clearance_level} ({u.role})</span> {u.biometric_enrolled && '🛡️ Biometric Active'}
            </li>
          ))
        ) : (
          <li style={{ color: '#64748b' }}>No registered analyst profiles found in Supabase.</li>
        )}
      </ul>
    </div>
  );
}
