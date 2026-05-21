"use client";

import { useEffect, useRef, useState, type ReactNode } from "react";
import { DETECTORS, EV_DATA, type EvPayloadValue } from "./data";
import { AnatomyPlate, InvestigatorSilhouette, VintageDetector } from "./illustrations";

function ActI() {
  return (
    <section className="act" id="acte-i" data-anchor="acte-i">
      <InvestigatorSilhouette size={70} className="act-corner-tl" />
      <div className="act-frame">
        <div className="act-num">Acte I · l&apos;événement</div>
        <h2>
          <span className="small">09:18, mardi.</span>
          <br />
          Un IBAN change.
          <br />
          <span className="italic">412 880 €</span> sont émis.
        </h2>
        <div className="act-meta">
          <span>USER-LDU221</span>
          <span className="sep">·</span>
          <span>Rôle unique · 4-eyes violé</span>
          <span className="sep">·</span>
          <span>Aucun ticket associé</span>
        </div>
      </div>
    </section>
  );
}

function ExhibitOne() {
  const paperRef = useRef<HTMLDivElement>(null);
  const [scanning, setScanning] = useState(false);

  // Trigger the scan sweep once when scrolled into view.
  useEffect(() => {
    const node = paperRef.current;
    if (!node) return;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            setScanning(true);
            setTimeout(() => setScanning(false), 3200);
            io.disconnect();
          }
        });
      },
      { threshold: 0.35 },
    );
    io.observe(node);
    return () => io.disconnect();
  }, []);

  // Subtle mouse parallax — the paper tilts toward the cursor.
  const onMove = (e: React.MouseEvent<HTMLDivElement>) => {
    const el = paperRef.current;
    if (!el) return;
    const r = el.getBoundingClientRect();
    const cx = r.left + r.width / 2;
    const cy = r.top + r.height / 2;
    const dx = (e.clientX - cx) / r.width;
    const dy = (e.clientY - cy) / r.height;
    const max = 3.2;
    el.style.transform = `rotate(-0.6deg) rotateX(${(-dy * max).toFixed(2)}deg) rotateY(${(dx * max).toFixed(2)}deg)`;
  };
  const onLeave = () => {
    const el = paperRef.current;
    if (!el) return;
    el.style.transform = "rotate(-0.6deg)";
  };

  return (
    <section className="exhibit" id="piece-1" data-anchor="piece-1">
      <div className="exhibit-row">
        <div className="margin-note left">
          <span className="arrow">regardez</span>
          La banque passe de BNP Paris à N26 Berlin — pour le <em>même</em> SIREN.
        </div>

        <div
          ref={paperRef}
          className={`exhibit-paper ${scanning ? "scanning" : ""}`}
          onMouseMove={onMove}
          onMouseLeave={onLeave}
          onClick={() => {
            setScanning(false);
            requestAnimationFrame(() => setScanning(true));
          }}
        >
          <div className="scan-bar" />
          <div className="scan-line" />

          <div className="exhibit-head">
            <div>
              <div className="ref">Pièce n°1 · diff master data</div>
              <div className="ttl">ALPHACOM SERVICES SAS</div>
            </div>
            <div className="stamp">Scellé · Ed25519</div>
          </div>
          <div className="exhibit-body">
            <div className="diff-row">
              <div className="k">SIREN</div>
              <div className="v">812 446 901</div>
            </div>
            <div className="diff-row changed">
              <div className="k">IBAN</div>
              <div className="v">
                <span className="strike">FR76 1027 8073 …2233 0</span>
                FR76 3000 4015 8800 0212 5847 9
              </div>
            </div>
            <div className="diff-row changed">
              <div className="k">Banque</div>
              <div className="v">
                <span className="strike">BNP Paribas · Paris</span>
                N26 Bank AG · Berlin
              </div>
            </div>
            <div className="diff-row">
              <div className="k">Adresse</div>
              <div className="v">14 rue de Provence · 75009 Paris</div>
            </div>
            <div className="diff-row changed">
              <div className="k">4-eyes</div>
              <div className="v">
                <span className="strike">USER-MNT × USER-VAL</span>
                USER-LDU221 (rôle unique)
              </div>
            </div>
            <div className="diff-row">
              <div className="k">Δt → règlement</div>
              <div className="v">18h · règlement immédiat sur F-2026-04419</div>
            </div>
          </div>
          <div className="exhibit-foot">
            <span>Hash · 0x7a9f3b2c8e4d…</span>
            <span>Détecteur 01 · master data history</span>
          </div>
        </div>

        <div className="margin-note right">
          <span className="arrow">et surtout</span>
          Un seul utilisateur signe pour <em>les deux rôles</em>. ISA 240, c&apos;est là.
        </div>
      </div>
    </section>
  );
}

function Filmstrip() {
  return (
    <div className="filmstrip-wrap" id="pipeline" data-anchor="pipeline">
      <div className="filmstrip-head">
        <div>
          <VintageDetector width={140} />
          <div className="lbl">Pipeline · ingestion LFA1 / RBKP / BSEG</div>
        </div>
        <div className="filmstrip-hint">faites défiler →</div>
      </div>
      <div className="filmstrip">
        {DETECTORS.map((d) => (
          <div className="frame" key={d.num}>
            <div className="frame-num">
              <span>[{d.num}]</span>
              <span className="arr">→</span>
            </div>
            <div className="frame-name">{d.name}</div>
            <div className="frame-method">{d.meta}</div>
            <div className="frame-perf">
              <span>{d.f1}</span>
              <span className="ref">{d.ref}</span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function ActII() {
  return (
    <>
      <section className="act" id="acte-ii" data-anchor="acte-ii">
        <div className="act-frame">
          <div className="act-num">Acte II · la cascade</div>
          <h2>
            Huit détecteurs.
            <br />
            <span className="italic">Trois minutes.</span>
          </h2>
          <div className="act-meta">
            <span>02:59:42 → 03:02:51</span>
            <span className="sep">·</span>
            <span>NON statistique exotique</span>
            <span className="sep">·</span>
            <span>Reason codes FR</span>
          </div>
        </div>
      </section>

      <Filmstrip />
    </>
  );
}

function BigNumber() {
  const ref = useRef<HTMLElement>(null);
  const [n, setN] = useState(0);

  // Animate from 0 to 92 as the section scrolls into view.
  useEffect(() => {
    const node = ref.current;
    if (!node) return;
    let raf = 0;
    const io = new IntersectionObserver(
      (entries) => {
        entries.forEach((e) => {
          if (e.isIntersecting) {
            const start = performance.now();
            const dur = 1200;
            const tick = (now: number) => {
              const k = Math.min(1, (now - start) / dur);
              const eased = 1 - Math.pow(1 - k, 4);
              setN(Math.round(92 * eased));
              if (k < 1) raf = requestAnimationFrame(tick);
            };
            raf = requestAnimationFrame(tick);
            io.disconnect();
          }
        });
      },
      { threshold: 0.35 },
    );
    io.observe(node);
    return () => {
      io.disconnect();
      if (raf) cancelAnimationFrame(raf);
    };
  }, []);

  return (
    <section className="bignum" ref={ref} id="score" data-anchor="score">
      <div className="bignum-frame">
        <div className="above">Risk Score · consolidé · niveau CRITIQUE</div>
        <div className="digits">{n}</div>
        <div className="below">
          Trois minutes après l&apos;événement, le moteur livre un score chiffré,
          <br />
          des reason codes en français, et le dossier signé.
        </div>
        <div className="footnote">— pondérations YAML · ajustables par règle métier —</div>
      </div>
    </section>
  );
}

function jsonHighlight(obj: Record<string, EvPayloadValue>, indent = 0): ReactNode[] {
  const pad = "  ".repeat(indent);
  return Object.entries(obj).map(([k, v]) => {
    let value: ReactNode;
    if (typeof v === "string") value = <span className="str">&quot;{v}&quot;</span>;
    else if (typeof v === "number") value = <span className="num">{v}</span>;
    else if (typeof v === "boolean") value = <span className="num">{String(v)}</span>;
    else if (Array.isArray(v))
      value = <span className="str">[{v.map((x) => `"${x}"`).join(", ")}]</span>;
    else value = JSON.stringify(v);
    return (
      <div key={k}>
        {pad}
        <span className="key">{k}</span>: {value}
      </div>
    );
  });
}

function ActIII() {
  const [expanded, setExpanded] = useState<number | null>(null);
  const [verifyStatus, setVerifyStatus] = useState<"idle" | "running" | "done">("idle");
  const [verifyIndex, setVerifyIndex] = useState(-1);
  const [tamperMode, setTamperMode] = useState(false);
  const [tamperedAt, setTamperedAt] = useState<number | null>(null);

  // Cancellation token for the verify cascade.
  const verifyToken = useRef(0);

  const runVerify = () => {
    if (verifyStatus === "running") return;
    const token = ++verifyToken.current;
    setTamperedAt(null);
    setVerifyStatus("running");
    setVerifyIndex(-1);
    let i = 0;
    const step = () => {
      if (verifyToken.current !== token) return;
      if (i >= EV_DATA.length) {
        setVerifyStatus("done");
        return;
      }
      setVerifyIndex(i);
      i++;
      setTimeout(step, 220);
    };
    step();
  };

  const reset = () => {
    verifyToken.current++;
    setVerifyStatus("idle");
    setVerifyIndex(-1);
    setTamperedAt(null);
    setTamperMode(false);
    setExpanded(null);
  };

  const enterTamper = () => {
    reset();
    setTimeout(() => setTamperMode(true), 0);
  };

  const onRowClick = (i: number) => {
    if (tamperMode) {
      setTamperedAt(i);
      setTamperMode(false);
      return;
    }
    setExpanded(expanded === i ? null : i);
  };

  const sealState =
    tamperedAt !== null ? "tampered" : verifyStatus === "done" ? "verified" : "";
  const progressCount =
    tamperedAt !== null
      ? tamperedAt
      : verifyStatus === "running"
        ? verifyIndex + 1
        : verifyStatus === "done"
          ? EV_DATA.length
          : 0;
  const progressPct = (progressCount / EV_DATA.length) * 100;
  const statusLabel =
    tamperedAt !== null
      ? "Altération détectée"
      : verifyStatus === "running"
        ? "Vérification en cours"
        : verifyStatus === "done"
          ? "Chaîne intègre"
          : "Prêt à vérifier";

  const R = 68;
  const C = 2 * Math.PI * R;
  const offset = C - (progressPct / 100) * C;

  return (
    <section className="evlog" id="evlog" data-anchor="evlog">
      <InvestigatorSilhouette size={70} className="act-corner-br" />
      <div className="evlog-head">
        <div className="lhs">
          <div className="eyebrow">Acte III · la signature</div>
          <div className="ttl">
            Le journal d&apos;enquête.
            <br />
            <span className="italic">Immuable.</span>
          </div>
        </div>
        <div
          style={{
            fontFamily: "var(--font-mono)",
            fontSize: 12,
            color: "var(--muted)",
            letterSpacing: "0.04em",
            lineHeight: 1.6,
          }}
        >
          Dix entrées · hash chaîné · clé publique vérifiable. Aucune ligne n&apos;est éditable.
          Cliquez <span style={{ color: "var(--fg-2)" }}>Simuler une altération</span> pour voir
          la chaîne casser.
        </div>
      </div>

      <div className="evlog-grid">
        <div>
          <div className="evlog-toolbar" role="toolbar">
            <button
              className="evlog-btn success"
              onClick={runVerify}
              disabled={verifyStatus === "running"}
            >
              <span className="glyph">⚡</span>
              {verifyStatus === "running"
                ? `Vérification ${verifyIndex + 1}/${EV_DATA.length}…`
                : verifyStatus === "done"
                  ? "Re-vérifier la chaîne"
                  : "Vérifier la chaîne"}
            </button>
            <button className="evlog-btn danger" onClick={enterTamper}>
              <span className="glyph">⚠</span>
              {tamperMode ? "Sélectionnez une ligne…" : "Simuler une altération"}
            </button>
            <button className="evlog-btn" onClick={reset}>
              <span className="glyph">↻</span>
              Réinitialiser
            </button>
          </div>

          <div className="evlog-log">
            {EV_DATA.map((e, i) => {
              const isExpanded = expanded === i;
              const isVerified =
                (verifyStatus === "running" && i <= verifyIndex) || verifyStatus === "done";
              const isVerifying = verifyStatus === "running" && i === verifyIndex + 1;
              const isTampered = tamperedAt === i;
              const isInvalid = tamperedAt !== null && i > tamperedAt;

              const rowCls = [
                "ev-row",
                e.level || "",
                tamperMode ? "tamper-mode" : "",
                isVerifying ? "verifying" : "",
                isVerified && tamperedAt === null ? "verified" : "",
                isTampered ? "tampered" : "",
                isInvalid ? "invalid" : "",
              ]
                .filter(Boolean)
                .join(" ");

              return (
                <div
                  className={rowCls}
                  key={i}
                  onClick={() => onRowClick(i)}
                  style={{ display: isExpanded ? "block" : undefined }}
                >
                  <div
                    style={
                      isExpanded
                        ? {
                            display: "grid",
                            gridTemplateColumns: "110px 22px 1fr 110px auto",
                            gap: 14,
                            alignItems: "center",
                          }
                        : { display: "contents" }
                    }
                  >
                    <div className="when">{e.when}</div>
                    <div className="glyph">{e.glyph}</div>
                    <div className="what">{e.what}</div>
                    <div className="hash">0x{e.hash}…</div>
                    <div className="who">{e.who}</div>
                  </div>

                  {isExpanded && (
                    <div className="ev-details">
                      <div className="dk">hash</div>
                      <div className="dv">0x{e.hash}3b2c8e4d · 5f29 · a17b · c33e · d4f8</div>
                      <div className="dk">prev_hash</div>
                      <div className="dv" style={{ color: "var(--muted)" }}>
                        {i === 0 ? "— genesis —" : `0x${EV_DATA[i - 1].hash}…`}
                      </div>
                      <div className="dk">algo</div>
                      <div className="dv">
                        Ed25519 · pubkey <span className="link">/audit/verify</span>
                      </div>
                      <div className="dk">payload</div>
                      <div className="dv">
                        <div className="json">
                          {"{\n"}
                          {jsonHighlight(e.payload, 1)}
                          {"}"}
                        </div>
                      </div>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {tamperedAt !== null && (
            <div
              style={{
                marginTop: 18,
                padding: 16,
                border: "1px solid var(--risk)",
                background: "var(--risk-soft)",
                fontFamily: "var(--font-mono)",
                fontSize: 12,
                color: "var(--risk)",
                letterSpacing: "0.04em",
              }}
            >
              <strong>✗ ALTÉRATION DÉTECTÉE</strong> · le hash de l&apos;entrée #{tamperedAt + 1}{" "}
              ne valide plus. Les {EV_DATA.length - tamperedAt - 1} entrées suivantes sont
              marquées <em>HASH INVALIDE</em>. Toute modification d&apos;une entrée signée Ed25519
              invalide la chaîne entière à partir de ce point.
            </div>
          )}
        </div>

        <div>
          <div className={`seal ${sealState}`}>
            <div className="crest">— Apposé le 15 avril 2026, 03:03 CET —</div>

            <div className="badge">
              <div className="ring ring-bg" />
              <div className="ring ring-fill">
                <svg viewBox="0 0 140 140">
                  <circle cx="70" cy="70" r={R} strokeDasharray={C} strokeDashoffset={offset} />
                </svg>
              </div>
              <div className="glyph-big">
                {tamperedAt !== null ? "✗" : sealState === "verified" ? "✓" : "§"}
              </div>
            </div>

            <div className="status">{statusLabel}</div>
            <div className="progress-text">
              {progressCount}/{EV_DATA.length}
            </div>
            <div
              style={{
                fontFamily: "var(--font-mono)",
                fontSize: 10,
                letterSpacing: "0.14em",
                color: "var(--muted)",
                textTransform: "uppercase",
              }}
            >
              entrées · signature Ed25519
            </div>

            <div className="hash-final">
              {tamperedAt !== null ? (
                <span style={{ color: "var(--risk)" }}>chaîne rompue · 0x???? · invalide</span>
              ) : sealState === "verified" ? (
                <>0x7a9f3b2c8e4d · 5f29 · a17b · c33e · d4f8 · 92ab · 0001 · ffff</>
              ) : (
                <span>chaîne en attente de vérification…</span>
              )}
            </div>

            <div className="key-row">
              <div>
                <div style={{ color: "var(--dim)" }}>PUB KEY</div>
                pgp · 4096
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ color: "var(--dim)" }}>BLOC</div>
                #8412
              </div>
            </div>

            {(verifyStatus !== "idle" || tamperedAt !== null) && (
              <button className="reset-btn" onClick={reset}>
                {tamperedAt !== null ? "Restaurer la chaîne" : "Réinitialiser"}
              </button>
            )}
          </div>

          <div
            style={{
              marginTop: 18,
              fontFamily: "var(--font-mono)",
              fontSize: 11,
              color: "var(--muted)",
              letterSpacing: "0.06em",
              lineHeight: 1.6,
            }}
          >
            La clé publique est servie sur{" "}
            <span style={{ color: "var(--fg-2)" }}>/audit/verify</span>. Un tiers (CAC,
            régulateur) peut re-calculer le hash de toute ligne, hors-ligne.
          </div>
        </div>
      </div>
    </section>
  );
}

function PullQuote() {
  return (
    <section className="pullquote" id="quote">
      <div className="pullquote-frame">
        <div className="mark">«</div>
        <div>
          <div className="text">
            Aucune fraude n&apos;est invisible.
            <br />
            <span className="italic">Toutes sont signables.</span>
          </div>
          <div className="cite">— manifeste · P2P Fraud Detective FR · v2.1</div>
        </div>
      </div>
    </section>
  );
}

export function Dossier() {
  return (
    <>
      <ActI />
      <ExhibitOne />
      <ActII />
      <AnatomyPlate />
      <BigNumber />
      <ActIII />
      <PullQuote />
    </>
  );
}
