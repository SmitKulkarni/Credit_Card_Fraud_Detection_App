import type { Metadata } from 'next';
import React from 'react';

export const metadata: Metadata = {
  title: 'Sentinel Enterprise — Credit Card Fraud Detection Studio',
  description: 'Zero-Trust Fraud Detection & Risk Intelligence Workstation powered by Next.js & XGBoost',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1.0" />
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap"
          rel="stylesheet"
        />
      </head>
      <body style={{ margin: 0, padding: 0, background: '#090d16', color: '#f8fafc', fontFamily: 'Inter, sans-serif' }}>
        {children}
      </body>
    </html>
  );
}
