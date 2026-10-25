/**
 * Sentinel Triage Studio - Supabase Cloud Client Integration.
 * Provides direct PostgREST & Auth synchronization with Supabase Postgres.
 */

export const SUPABASE_CONFIG = {
  url: "https://eufrawprayanwthhuvaj.supabase.co",
  publishableKey: "sb_publishable_3YczReP6yNU8WPGQuS8V9A_CFJaeYA1"
};

/**
 * Checks if Supabase credentials are configured and reachable.
 */
export function isSupabaseConfigured() {
  return Boolean(SUPABASE_CONFIG.url && SUPABASE_CONFIG.publishableKey);
}

/**
 * Saves a scored transaction into the Supabase fraud_audit_records table.
 */
export async function saveAuditToSupabase(record) {
  if (!isSupabaseConfigured()) return null;

  try {
    const payload = {
      transaction_id: record.transactionId,
      amount: parseFloat(record.amount) || 0.0,
      time_delta: parseFloat(record.time) || 0.0,
      fraud_probability: parseFloat(record.fraudProbability) || 0.0,
      is_fraud: Boolean(record.isFraud),
      risk_level: record.riskLevel,
      decision: record.decision,
      latency_ms: parseFloat(record.latencyMs) || 0.0,
      top_factors: record.topFactors || [],
      user_email: record.userEmail || "analyst@sentinel.corp"
    };

    const res = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/fraud_audit_records`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_CONFIG.publishableKey,
        'Authorization': `Bearer ${SUPABASE_CONFIG.publishableKey}`,
        'Content-Type': 'application/json',
        'Prefer': 'return=representation'
      },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      console.log('Synchronized to Supabase:', data);
      return data[0];
    }
  } catch (err) {
    console.warn('Supabase cloud audit sync warning:', err);
  }
  return null;
}

/**
 * Fetches latest audit records from Supabase Postgres.
 */
export async function fetchLatestAuditsFromSupabase(limit = 25) {
  if (!isSupabaseConfigured()) return [];

  try {
    const res = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/fraud_audit_records?order=created_at.desc&limit=${limit}&select=*`, {
      method: 'GET',
      headers: {
        'apikey': SUPABASE_CONFIG.publishableKey,
        'Authorization': `Bearer ${SUPABASE_CONFIG.publishableKey}`
      }
    });

    if (res.ok) {
      return await res.json();
    }
  } catch (err) {
    console.warn('Could not fetch from Supabase:', err);
  }
  return [];
}

/**
 * Registers or updates an analyst profile in Supabase analyst_profiles.
 */
export async function syncAnalystProfileToSupabase(profile) {
  if (!isSupabaseConfigured()) return null;

  try {
    const payload = {
      full_name: profile.name,
      email: profile.email.toLowerCase().trim(),
      role: profile.role,
      clearance_level: profile.clearance,
      biometric_enrolled: Boolean(profile.isBiometricVerified),
      updated_at: new Date().toISOString()
    };

    const res = await fetch(`${SUPABASE_CONFIG.url}/rest/v1/analyst_profiles`, {
      method: 'POST',
      headers: {
        'apikey': SUPABASE_CONFIG.publishableKey,
        'Authorization': `Bearer ${SUPABASE_CONFIG.publishableKey}`,
        'Content-Type': 'application/json',
        'Prefer': 'resolution=merge-duplicates,return=representation'
      },
      body: JSON.stringify(payload)
    });

    if (res.ok) {
      const data = await res.json();
      return data[0];
    }
  } catch (err) {
    console.warn('Supabase analyst profile sync warning:', err);
  }
  return null;
}
