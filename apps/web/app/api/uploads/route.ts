/**
 * Upload route.
 *
 * If NEXT_PUBLIC_API_URL is configured, the request is streamed to FastAPI.
 * Otherwise Vercel serves a deliberately limited CSV/TSV demo parser so the
 * public site stays testable without pretending to run live enrichment.
 */

import { type NextRequest, NextResponse } from "next/server";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "";
const SECRET = process.env.FRAUD_API_SECRET ?? "";

export const runtime = "nodejs";

export async function POST(req: NextRequest) {
  if (!API_BASE) {
    return handleDemoUpload(req);
  }

  const url = `${API_BASE}/detect/csv`;
  const headers = new Headers();
  if (SECRET) headers.set("Authorization", `Bearer ${SECRET}`);
  const contentType = req.headers.get("content-type");
  if (contentType) headers.set("content-type", contentType);

  const upstream = await fetch(url, {
    method: "POST",
    headers,
    body: req.body,
    // @ts-expect-error: duplex is required for request streams in Node.
    duplex: "half",
  });

  const body = await upstream.arrayBuffer();
  return new NextResponse(body, {
    status: upstream.status,
    headers: {
      "content-type": upstream.headers.get("content-type") ?? "application/json",
    },
  });
}

async function handleDemoUpload(req: NextRequest) {
  const form = await req.formData();
  const file = form.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json(
      { error: "Aucun fichier recu.", mode: "demo" },
      { status: 400 },
    );
  }

  const name = file.name.toLowerCase();
  if (!name.endsWith(".csv") && !name.endsWith(".tsv")) {
    return NextResponse.json(
      {
        error:
          "Mode demo Vercel: seuls les CSV/TSV sont parses localement. Configurez NEXT_PUBLIC_API_URL pour l'analyse Excel/Parquet via FastAPI.",
        mode: "demo",
      },
      { status: 422 },
    );
  }

  const text = await file.text();
  const rows = parseDelimited(text, name.endsWith(".tsv") ? "\t" : ",");
  const findings = buildDemoFindings(rows);

  return NextResponse.json(
    {
      n_invoices: rows.length,
      detectors_run: ["duplicates", "thresholds", "sanctions"],
      findings,
      mode: "demo",
      data_origin: "uploaded_csv_synthetic_detection",
      notice:
        "Analyse locale simplifiee pour demo. Les connecteurs publics live ne sont pas appeles.",
    },
    {
      headers: {
        "x-p2pfd-data-origin": "uploaded-demo",
        "x-p2pfd-live-sources": "false",
      },
    },
  );
}

function parseDelimited(text: string, delimiter: string) {
  const lines = text
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter(Boolean);
  if (lines.length <= 1) return [];
  const headers = splitLine(lines[0], delimiter).map((header) => header.trim());
  return lines.slice(1).map((line) => {
    const cells = splitLine(line, delimiter);
    return Object.fromEntries(headers.map((header, i) => [header, cells[i] ?? ""]));
  });
}

function splitLine(line: string, delimiter: string) {
  const cells: string[] = [];
  let current = "";
  let quoted = false;
  for (const char of line) {
    if (char === '"') quoted = !quoted;
    else if (char === delimiter && !quoted) {
      cells.push(current);
      current = "";
    } else current += char;
  }
  cells.push(current);
  return cells.map((cell) => cell.trim().replace(/^"|"$/g, ""));
}

function buildDemoFindings(rows: Record<string, string>[]) {
  const findings = [];
  const seen = new Map<string, number>();
  for (const [index, row] of rows.entries()) {
    const invoiceId = row.invoice_id || row.invoice || `ROW-${index + 1}`;
    const vendor = row.vendor_name || row.vendor || row.supplier || "";
    const amount = Number(
      (row.amount || row.montant || "0").replace(/\s/g, "").replace(",", "."),
    );
    const key = `${vendor.toLowerCase()}::${Math.round(amount * 100)}`;

    if (seen.has(key)) {
      findings.push({
        invoice_id: invoiceId,
        rule_id: "DUP_LOCAL_DEMO",
        severity: "high",
        signal: "Doublon potentiel montant + fournisseur dans le CSV",
        detector: "duplicates",
        evidence: {
          matched_row: seen.get(key),
          vendor_name: vendor,
          exposure_eur: amount,
        },
      });
    }
    seen.set(key, index + 1);

    if (amount >= 900 && amount < 1000) {
      findings.push({
        invoice_id: invoiceId,
        rule_id: "UNDER_THRESHOLD_DEMO",
        severity: "medium",
        signal: "Montant juste sous 1 000 EUR",
        detector: "thresholds",
        evidence: { vendor_name: vendor, exposure_eur: amount },
      });
    }

    if (/volkov|sanction|ofac|pep/i.test(vendor)) {
      findings.push({
        invoice_id: invoiceId,
        rule_id: "SANCTIONS_SNAPSHOT_DEMO",
        severity: "critical",
        signal: "Nom rapproche du snapshot sanctions de demonstration",
        detector: "sanctions",
        evidence: { vendor_name: vendor, exposure_eur: amount },
      });
    }
  }
  return findings;
}
