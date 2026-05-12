// k6 load test — smoke test sur l'API P2P Fraud Detective FR.
//
// Run :
//   k6 run tests/load/api_smoke.js
//
// SLO ciblés :
//   - p95 latency  < 500ms sur /detect et /score
//   - error rate   < 1%
//   - 50 VUs concurrents pendant 60s
//
// Variables d'env :
//   API_BASE_URL  (default http://localhost:8000)
//   API_SECRET    (bearer token statique pour FastAPI)

import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE = __ENV.API_BASE_URL || 'http://localhost:8000';
const TOKEN = __ENV.API_SECRET || '';

export const options = {
  scenarios: {
    smoke: {
      executor: 'constant-vus',
      vus: 50,
      duration: '60s',
    },
  },
  thresholds: {
    http_req_failed: ['rate<0.01'],          // < 1% d'erreurs
    http_req_duration: ['p(95)<500'],        // p95 < 500ms
    'http_req_duration{endpoint:detect}': ['p(95)<500'],
    'http_req_duration{endpoint:score}': ['p(95)<500'],
  },
};

const HEADERS = {
  'Content-Type': 'application/json',
  ...(TOKEN ? { Authorization: `Bearer ${TOKEN}` } : {}),
};

const PAYLOAD = JSON.stringify({
  invoices: [
    {
      invoice_id: 'INV-LOAD-1',
      vendor_name: 'Load Test Vendor',
      amount: 1234.56,
      invoice_date: '2026-01-15',
      siren: '552120222',
      iban: 'FR7630004000010000000000123',
      currency: 'EUR',
    },
  ],
  detectors: ['duplicates', 'thresholds', 'sanctions'],
});

export default function () {
  // /health
  const h = http.get(`${BASE}/health`);
  check(h, { 'health 200': (r) => r.status === 200 });

  // /detect
  const d = http.post(`${BASE}/detect`, PAYLOAD, {
    headers: HEADERS,
    tags: { endpoint: 'detect' },
  });
  check(d, {
    'detect 200': (r) => r.status === 200,
    'detect has n_findings': (r) => r.json('n_findings') !== undefined,
  });

  // /score
  const s = http.post(
    `${BASE}/score`,
    JSON.stringify({ invoices: JSON.parse(PAYLOAD).invoices }),
    { headers: HEADERS, tags: { endpoint: 'score' } },
  );
  check(s, {
    'score 200': (r) => r.status === 200,
    'score returns array': (r) => Array.isArray(r.json('scores')),
  });

  sleep(0.5);
}
