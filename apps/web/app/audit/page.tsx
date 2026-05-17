"use client";

import { useQuery } from "@tanstack/react-query";
import { useState } from "react";
import { listAudit, verifyAudit } from "@/lib/api-client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CheckCircle2, AlertCircle, Fingerprint } from "lucide-react";
import { formatDate } from "@/lib/utils";

export default function AuditPage() {
  const [cursor, setCursor] = useState(0);
  const [verifyRun, setVerifyRun] = useState(false);

  const auditQuery = useQuery({
    queryKey: ["audit", cursor],
    queryFn: () => listAudit(cursor, 50),
  });

  const verifyQuery = useQuery({
    queryKey: ["audit-verify"],
    queryFn: verifyAudit,
    enabled: verifyRun,
    staleTime: 0,
  });

  const entries = auditQuery.data?.entries ?? [];
  const total = auditQuery.data?.total ?? 0;
  const nextCursor = auditQuery.data?.cursor_next;

  return (
    <div className="px-8 py-10">
      <div className="mb-1 text-xs uppercase tracking-wider text-[#5a6478]">
        Investigation
      </div>
      <h1 className="mb-1 text-3xl font-bold text-[#0f1b33] dark:text-white">
        Piste d'audit
      </h1>
      <p className="mb-6 text-sm text-[#5a6478]">
        Journal hash-chaîné SHA-256. En mode demo, les signatures Ed25519 sont
        désactivées; en pilote, la clé publique permet la vérification via{" "}
        <code className="rounded bg-[#f4f6fa] px-1 py-0.5 text-xs">
          GET /security/public-key
        </code>
        .
      </p>

      <Card className="mb-4">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Fingerprint size={18} /> Vérification d'intégrité
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-wrap items-center gap-3">
          <Button onClick={() => setVerifyRun(true)} disabled={verifyQuery.isFetching}>
            {verifyQuery.isFetching ? "Vérification…" : "Recalculer la chaîne"}
          </Button>
          {verifyQuery.data ? (
            <div className="flex flex-col gap-1 text-sm">
              <div
                className={
                  verifyQuery.data.valid
                    ? "flex items-center gap-2 text-[#3e7c5a]"
                    : "flex items-center gap-2 text-[#a23e48]"
                }
              >
                {verifyQuery.data.valid ? (
                  <CheckCircle2 size={16} />
                ) : (
                  <AlertCircle size={16} />
                )}
                <span>
                  {verifyQuery.data.valid
                    ? "✅ Chaîne valide"
                    : `❌ Séquences invalides : ${(verifyQuery.data.invalid_seqs ?? []).join(", ")}`}
                </span>
              </div>
              <div className="text-xs text-[#5a6478]">
                {verifyQuery.data.n_total} entrées · {verifyQuery.data.n_signed} signées
                Ed25519
              </div>
              {verifyQuery.data.public_key_b64 ? (
                <div className="font-mono text-[10px] text-[#5a6478]">
                  Clé publique : {verifyQuery.data.public_key_b64.slice(0, 24)}…
                  {verifyQuery.data.public_key_b64.slice(-8)}
                </div>
              ) : null}
            </div>
          ) : null}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>
            Entrées {entries.length} / {total}
          </CardTitle>
        </CardHeader>
        <div className="overflow-x-auto">
          {auditQuery.isLoading ? (
            <div className="p-4 text-sm text-[#5a6478]">Chargement…</div>
          ) : auditQuery.error ? (
            <div className="p-4 text-sm text-[#a23e48]">
              API indisponible : {(auditQuery.error as Error).message}
            </div>
          ) : (
            <table className="w-full text-sm">
              <thead className="bg-[#f4f6fa] text-[#5a6478]">
                <tr>
                  <th className="px-3 py-2 text-left">Seq</th>
                  <th className="px-3 py-2 text-left">Quand</th>
                  <th className="px-3 py-2 text-left">Acteur</th>
                  <th className="px-3 py-2 text-left">Type</th>
                  <th className="px-3 py-2 text-left">Hash (8)</th>
                  <th className="px-3 py-2 text-left">Signature</th>
                </tr>
              </thead>
              <tbody>
                {entries.map((e: import("@p2pfd/shared-types").AuditEntryOut) => (
                  <tr key={e.seq} className="border-t border-[#e1e5ee]">
                    <td className="px-3 py-2 font-mono text-xs">{e.seq}</td>
                    <td className="px-3 py-2 text-xs text-[#5a6478]">
                      {formatDate(e.at)}
                    </td>
                    <td className="px-3 py-2 text-xs">{e.actor}</td>
                    <td className="px-3 py-2 font-mono text-xs">{e.kind}</td>
                    <td className="px-3 py-2 font-mono text-xs">
                      {e.hash.slice(0, 8)}…
                    </td>
                    <td className="px-3 py-2 text-xs">
                      {e.signature ? (
                        <span className="text-[#3e7c5a]">✅</span>
                      ) : (
                        <span className="text-[#9aa3b2]">—</span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
        <CardContent className="flex items-center justify-between">
          <div className="text-xs text-[#5a6478]">
            Cursor : {cursor} · Suivant : {nextCursor ?? "—"}
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setCursor(Math.max(0, cursor - 50))}
              disabled={cursor === 0}
            >
              ← Précédent
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => nextCursor && setCursor(nextCursor)}
              disabled={!nextCursor}
            >
              Suivant →
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
