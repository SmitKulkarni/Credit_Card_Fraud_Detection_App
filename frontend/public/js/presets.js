/**
 * Production transaction scenario definitions for Sentinel Triage Studio.
 */

export const PRESETS = {
  legitimate_grocery: {
    title: "Standard Retail ($24.50)",
    description: "Routine low-value physical retail purchase with card present.",
    transactionId: "TX-892104",
    amount: 24.50,
    time: 450.0,
    features: {
      V1: 0.05, V2: -0.12, V3: 0.45, V4: -0.22, V5: 0.15,
      V6: -0.05, V7: 0.18, V8: 0.02, V9: -0.10, V10: 0.05,
      V11: -0.30, V12: 0.12, V13: -0.05, V14: 0.15, V15: 0.20,
      V16: -0.08, V17: 0.10, V18: 0.02, V19: -0.04, V20: 0.01,
      V21: -0.02, V22: 0.04, V23: -0.01, V24: 0.02, V25: -0.03,
      V26: 0.01, V27: 0.00, V28: 0.01
    }
  },

  suspicious_velocity: {
    title: "Suspicious Velocity ($680.00)",
    description: "Elevated transaction amount with rapid consecutive authorization attempts.",
    transactionId: "TX-492105",
    amount: 680.00,
    time: 1200.0,
    features: {
      V1: -0.45, V2: 0.85, V3: -0.65, V4: 1.95, V5: -0.35,
      V6: -0.55, V7: -0.45, V8: 0.35, V9: -0.80, V10: -1.25,
      V11: 1.80, V12: -1.90, V13: 0.15, V14: -1.85, V15: -0.45,
      V16: -0.90, V17: -1.10, V18: -0.60, V19: 0.80, V20: 0.25,
      V21: 0.18, V22: -0.25, V23: 0.12, V24: -0.15, V25: 0.20,
      V26: 0.30, V27: 0.08, V28: 0.04
    }
  },

  confirmed_fraud: {
    title: "High Risk Compromise ($1,489.00)",
    description: "Severe behavioral deviations on V14, V12, V17 with rapid velocity indicator.",
    transactionId: "TX-792106",
    amount: 1489.00,
    time: 800.0,
    features: {
      V1: -3.20, V2: 2.80, V3: -4.50, V4: 4.10, V5: -2.10,
      V6: -1.80, V7: -3.90, V8: 1.90, V9: -2.80, V10: -4.80,
      V11: 3.50, V12: -6.20, V13: -0.80, V14: -7.10, V15: -0.95,
      V16: -4.20, V17: -4.90, V18: -2.10, V19: 1.80, V20: 0.75,
      V21: 0.65, V22: -0.45, V23: -0.30, V24: 0.10, V25: 0.40,
      V26: 0.65, V27: 0.35, V28: 0.15
    }
  }
};

/**
 * Generates randomized production transaction parameters for stress-testing.
 */
export function generateRandomTransaction() {
  const isFraud = Math.random() < 0.3;
  const amount = isFraud 
    ? Math.round((Math.random() * 1500 + 200) * 100) / 100
    : Math.round((Math.random() * 80 + 5) * 100) / 100;
  
  const features = {};
  for (let i = 1; i <= 28; i++) {
    let val = (Math.random() - 0.5) * 2;
    if (isFraud) {
      if (i === 14) val = -(Math.random() * 4 + 3);
      if (i === 12) val = -(Math.random() * 3 + 2.5);
      if (i === 4) val = (Math.random() * 3 + 1.5);
      if (i === 11) val = (Math.random() * 3 + 1.5);
    }
    features[`V${i}`] = Math.round(val * 100) / 100;
  }

  const randomNum = Math.floor(10000000 + Math.random() * 90000000);
  return {
    transactionId: `TX-${randomNum}`,
    amount: amount,
    time: Math.round(Math.random() * 10000),
    features: features
  };
}
