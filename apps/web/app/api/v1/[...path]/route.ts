import { NextRequest, NextResponse } from "next/server";
import {
  demoAuditEntries,
  demoCases,
  demoDailySeries,
  demoFindings,
  demoModeMeta,
  demoScenarios,
} from "@/lib/demo-data";

export const dynamic = "force-dynamic";

type RouteContext = {
  params: Promise<{ path: string[] }>;
};

const jsonHeaders = {
  "x-p2pfd-data-origin": "synthetic",
  "x-p2pfd-live-sources": "false",
};

export async function GET(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const path = params.path.join("/");
  const url = new URL(req.url);

  if (path === "cockpit/kpis") {
    const exposureTotal = demoCases.reduce((sum, c) => sum + c.exposure_eur, 0);
    const exposureCritical = demoCases
      .filter((c) => c.severity === "critical")
      .reduce((sum, c) => sum + c.exposure_eur, 0);
    return json({
      exposure_total_eur: exposureTotal,
      exposure_critical_eur: exposureCritical,
      n_cases_open: demoCases.filter((c) => !c.status.startsWith("closed")).length,
      n_cases_overdue: 1,
      n_cases_unassigned_critical: demoCases.filter(
        (c) => c.severity === "critical" && !c.assignee && !c.status.startsWith("closed"),
      ).length,
      trend_cases_created: demoDailySeries("created"),
      trend_cases_closed: demoDailySeries("closed"),
      trend_critical_alerts: demoDailySeries("critical"),
      trend_audit_activity: demoDailySeries("audit"),
      _meta: demoModeMeta,
    });
  }

  if (path === "cockpit/top-vendors") {
    const limit = numberParam(url.searchParams.get("limit"), 10);
    return json(
      [...demoCases]
        .filter((c) => c.vendor_id)
        .sort((a, b) => b.exposure_eur - a.exposure_eur)
        .slice(0, limit)
        .map((c) => ({
          vendor_id: c.vendor_id,
          vendor_name: vendorName(c.vendor_id),
          exposure_eur: c.exposure_eur,
          n_findings: 1,
          max_severity: c.severity,
        })),
    );
  }

  if (path === "scenarios") {
    return json(demoScenarios);
  }

  if (path === "cases") {
    const severity = url.searchParams.get("severity");
    const status = url.searchParams.get("status");
    const assignee = url.searchParams.get("assignee");
    const limit = numberParam(url.searchParams.get("limit"), 200);
    return json(
      demoCases
        .filter((c) => !severity || c.severity === severity)
        .filter((c) => !status || c.status === status)
        .filter((c) => !assignee || c.assignee === assignee)
        .slice(0, limit),
    );
  }

  if (path === "findings") {
    const severity = url.searchParams.get("severity");
    const ruleId = url.searchParams.get("rule_id");
    const limit = numberParam(url.searchParams.get("limit"), 100);
    return json(
      demoFindings()
        .filter((f) => !severity || f.severity === severity)
        .filter((f) => !ruleId || f.rule_id === ruleId)
        .slice(0, limit),
    );
  }

  if (path === "audit") {
    const cursor = numberParam(url.searchParams.get("cursor"), 0);
    const limit = numberParam(url.searchParams.get("limit"), 100);
    const entries = demoAuditEntries().filter((e) => e.seq > cursor).slice(0, limit);
    return json({
      entries,
      total: demoAuditEntries().length,
      cursor_next: entries.length === limit ? entries[entries.length - 1]?.seq : null,
      _meta: demoModeMeta,
    });
  }

  if (path === "audit/verify") {
    return json({
      valid: true,
      invalid_seqs: [],
      n_total: demoAuditEntries().length,
      n_signed: 0,
      public_key_b64: "",
      _meta: {
        ...demoModeMeta,
        signature_enabled: false,
        note: "Mode demo: hash chain synthetique, signatures Ed25519 desactivees.",
      },
    });
  }

  if (path === "rings") {
    return json(demoRingsGraph(url.searchParams.get("scenario") ?? "anneau_fraude"));
  }

  if (path === "exports/dossier.pdf") {
    const caseId = url.searchParams.get("case_id") ?? "";
    const selected = demoCases.find((c) => c.case_id === caseId);
    if (!selected) {
      return json({ detail: `Case inconnue: ${caseId}` }, 404);
    }
    const pdf = buildDemoPdf([
      "P2P Fraud Detective FR - dossier demo",
      `Case: ${selected.case_id}`,
      `Titre: ${selected.title}`,
      `Vendor: ${selected.vendor_id}`,
      `Severite: ${selected.severity}`,
      `Exposition: ${selected.exposure_eur} EUR`,
      "Donnees synthetiques - non transmissible a une autorite.",
    ]);
    return new NextResponse(pdf, {
      headers: {
        "content-type": "application/pdf",
        "content-disposition": `attachment; filename="dossier_${selected.case_id}.pdf"`,
        ...jsonHeaders,
      },
    });
  }

  if (path.startsWith("vendors/")) {
    const parts = path.split("/");
    const vendorId = decodeURIComponent(parts[1] ?? "");
    if (parts.length === 3 && parts[2] === "timeline") {
      return json(demoVendorTimeline(vendorId));
    }
    return json(demoVendorSummary(vendorId));
  }

  return json({ detail: `Endpoint demo inconnu: /api/v1/${path}` }, 404);
}

export async function POST(req: NextRequest, context: RouteContext) {
  const params = await context.params;
  const path = params.path.join("/");

  if (path === "llm/narrative") {
    const body = await safeJson(req);
    const vendor = String(body.vendor_name ?? body.vendor_id ?? "fournisseur");
    const text =
      `Mode demo: ${vendor} presente un risque a qualifier. ` +
      "Les signaux sont synthetiques; en production, verifier la source, la piece comptable, le journal ERP et le statut du connecteur avant decision.";
    return new Response(`data: ${JSON.stringify({ text })}\n\ndata: [DONE]\n\n`, {
      headers: {
        "content-type": "text/event-stream; charset=utf-8",
        "cache-control": "no-cache",
        ...jsonHeaders,
      },
    });
  }

  if (path === "cases/bulk/assign" || path === "cases/bulk/close") {
    const body = await safeJson(req);
    const caseIds = Array.isArray(body.case_ids) ? body.case_ids : [];
    return json({
      n_ok: caseIds.length,
      n_errors: 0,
      error_case_ids: [],
      demo_notice: "Mutation non persistante en mode demo Vercel.",
    });
  }

  if (path.match(/^cases\/[^/]+\/comment$/)) {
    return json({
      ok: true,
      demo_notice: "Commentaire accepte mais non persiste en mode demo Vercel.",
    });
  }

  return json({ detail: `Endpoint demo POST inconnu: /api/v1/${path}` }, 404);
}

function json(data: unknown, status = 200) {
  return NextResponse.json(data, {
    status,
    headers: jsonHeaders,
  });
}

async function safeJson(req: NextRequest): Promise<Record<string, unknown>> {
  try {
    return (await req.json()) as Record<string, unknown>;
  } catch {
    return {};
  }
}

function numberParam(value: string | null, fallback: number) {
  const parsed = Number(value);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

function vendorName(vendorId: string) {
  return (
    {
      "V-FOURNISSEUR-789": "Acme Industries SAS",
      "V-PRESTA-456": "Prestation Conseil SA",
      "V-SOUS-SEUIL-321": "Maintenance Express SARL",
      "V-SANC-007": "Volkov Trading Ltd",
      "V-LEGITIME-100": "Societe Generale Services",
    }[vendorId] ?? vendorId
  );
}

function demoVendorSummary(vendorId: string) {
  const rows = demoCases.filter((c) => c.vendor_id === vendorId);
  const sanctioned = rows.some((c) => c.rule_id.includes("SANCTIONS"));
  return {
    vendor_id: vendorId,
    vendor_name: vendorName(vendorId),
    siren: vendorId === "V-SANC-007" ? "000000007" : "123456789",
    total_paid_eur: rows.reduce((sum, c) => sum + c.exposure_eur, 0),
    n_invoices: rows.length,
    is_sanctioned: sanctioned,
    is_pep: false,
    data_origin: "synthetic",
  };
}

function demoVendorTimeline(vendorId: string) {
  return demoCases
    .filter((c) => c.vendor_id === vendorId)
    .flatMap((c) => [
      {
        at: c.created_at,
        kind: "case",
        label: c.title,
        amount_eur: c.exposure_eur,
        severity: c.severity,
      },
      {
        at: c.created_at,
        kind: "finding",
        label: c.signal,
        amount_eur: c.exposure_eur,
        severity: c.severity,
      },
    ]);
}

function demoRingsGraph(scenario: string) {
  const iban = "IBAN::FR-DEMO-SHARED-001";
  const vendors = ["V-ANNEAU-101", "V-ANNEAU-102", "V-ANNEAU-103"];
  return {
    nodes: [
      { id: iban, kind: "iban", label: "IBAN partage" },
      ...vendors.map((vendor) => ({ id: `VENDOR::${vendor}`, kind: "vendor", label: vendor })),
    ],
    edges: vendors.map((vendor) => ({ source: `VENDOR::${vendor}`, target: iban })),
    n_shared_iban_rings: scenario === "anneau_fraude" ? 1 : 0,
    n_vendor_clusters: 1,
    largest_cluster_size: 4,
    scenario,
  };
}

function buildDemoPdf(lines: string[]) {
  const escaped = lines.map((line) =>
    line.replace(/\\/g, "\\\\").replace(/\(/g, "\\(").replace(/\)/g, "\\)"),
  );
  const stream = [
    "BT",
    "/F1 12 Tf",
    "72 760 Td",
    ...escaped.flatMap((line, index) =>
      index === 0 ? [`(${line}) Tj`] : ["0 -18 Td", `(${line}) Tj`],
    ),
    "ET",
  ].join("\n");
  const objects = [
    "<< /Type /Catalog /Pages 2 0 R >>",
    "<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
    "<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 4 0 R >> >> /Contents 5 0 R >>",
    "<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    `<< /Length ${stream.length} >>\nstream\n${stream}\nendstream`,
  ];
  let pdf = "%PDF-1.4\n";
  const offsets = [0];
  objects.forEach((obj, index) => {
    offsets.push(pdf.length);
    pdf += `${index + 1} 0 obj\n${obj}\nendobj\n`;
  });
  const xrefOffset = pdf.length;
  pdf += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`;
  for (let i = 1; i < offsets.length; i++) {
    pdf += `${String(offsets[i]).padStart(10, "0")} 00000 n \n`;
  }
  pdf += `trailer << /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xrefOffset}\n%%EOF`;
  return new TextEncoder().encode(pdf);
}
