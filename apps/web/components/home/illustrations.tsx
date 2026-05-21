"use client";

// Forensic illustrations — investigator silhouette (watermark),
// vintage detector ornament, and the anatomical fraud plate.

export function InvestigatorSilhouette({
  size = 80,
  className = "",
}: {
  size?: number;
  className?: string;
}) {
  return (
    <svg
      viewBox="0 0 100 140"
      className={`silhouette ${className}`}
      width={size}
      height={size * 1.4}
      aria-hidden
    >
      <path d="M 30 65 L 28 130 L 72 130 L 70 65 Z" fill="currentColor" />
      <path
        d="M 24 70 L 30 60 L 70 60 L 76 70 L 76 95 L 70 90 L 70 65 L 30 65 L 30 90 L 24 95 Z"
        fill="currentColor"
      />
      <rect x="45" y="50" width="10" height="14" fill="currentColor" />
      <circle cx="50" cy="38" r="14" fill="currentColor" />
      <ellipse cx="50" cy="24" rx="22" ry="4" fill="currentColor" />
      <path d="M 38 24 L 38 12 Q 38 8 50 8 Q 62 8 62 12 L 62 24 Z" fill="currentColor" />
      <rect x="38" y="20" width="24" height="2" fill="var(--bg)" opacity="0.5" />
      <circle cx="78" cy="92" r="12" fill="none" stroke="currentColor" strokeWidth="2.5" />
      <line x1="86" y1="100" x2="96" y2="115" stroke="currentColor" strokeWidth="3" strokeLinecap="round" />
      <circle cx="78" cy="92" r="2" fill="var(--risk)" />
      <path d="M 68 78 Q 73 84 78 86 L 75 92 Q 68 90 64 84 Z" fill="currentColor" />
    </svg>
  );
}

export function VintageDetector({ width = 180 }: { width?: number }) {
  return (
    <svg
      viewBox="0 0 240 100"
      width={width}
      height={width * (100 / 240)}
      className="vintage-detector"
      aria-hidden
    >
      <rect x="20" y="20" width="200" height="60" fill="none" stroke="currentColor" strokeWidth="1.2" />
      {[
        [24, 24],
        [216, 24],
        [24, 76],
        [216, 76],
      ].map(([x, y], i) => (
        <circle key={i} cx={x} cy={y} r="1.5" fill="currentColor" />
      ))}

      <circle cx="50" cy="50" r="14" fill="none" stroke="currentColor" strokeWidth="1" />
      <circle cx="50" cy="50" r="9" fill="none" stroke="currentColor" strokeWidth="0.6" opacity="0.5" />
      {Array.from({ length: 12 }).map((_, i) => {
        const a = (i / 12) * Math.PI * 2 - Math.PI / 2;
        const r1 = 13;
        const r2 = 10;
        return (
          <line
            key={i}
            x1={50 + Math.cos(a) * r1}
            y1={50 + Math.sin(a) * r1}
            x2={50 + Math.cos(a) * r2}
            y2={50 + Math.sin(a) * r2}
            stroke="currentColor"
            strokeWidth="0.8"
          />
        );
      })}
      <line x1="50" y1="50" x2="58" y2="40" stroke="var(--risk)" strokeWidth="1.5" strokeLinecap="round" />
      <circle cx="50" cy="50" r="1.8" fill="var(--risk)" />

      <rect x="78" y="35" width="86" height="30" fill="none" stroke="currentColor" strokeWidth="1" />
      <line x1="84" y1="42" x2="158" y2="42" stroke="currentColor" strokeWidth="0.6" opacity="0.4" />
      <line x1="84" y1="48" x2="140" y2="48" stroke="currentColor" strokeWidth="0.6" opacity="0.4" />
      <line x1="84" y1="54" x2="150" y2="54" stroke="currentColor" strokeWidth="0.6" opacity="0.4" />
      <line x1="84" y1="60" x2="130" y2="60" stroke="var(--risk)" strokeWidth="0.8" />

      <circle cx="180" cy="35" r="3" fill="currentColor" />
      <circle cx="190" cy="35" r="3" fill="none" stroke="currentColor" strokeWidth="0.8" />
      <circle cx="200" cy="35" r="3" fill="var(--risk)" />
      <rect x="178" y="50" width="28" height="20" fill="var(--bg-2)" stroke="currentColor" strokeWidth="1" />
      <line x1="182" y1="56" x2="202" y2="56" stroke="currentColor" strokeWidth="0.4" opacity="0.5" />
      <line x1="182" y1="60" x2="198" y2="60" stroke="currentColor" strokeWidth="0.4" opacity="0.5" />
      <line x1="182" y1="64" x2="202" y2="64" stroke="currentColor" strokeWidth="0.4" opacity="0.5" />

      <line x1="40" y1="80" x2="40" y2="86" stroke="currentColor" strokeWidth="1" />
      <line x1="60" y1="80" x2="60" y2="86" stroke="currentColor" strokeWidth="1" />
      <line x1="180" y1="80" x2="180" y2="86" stroke="currentColor" strokeWidth="1" />
      <line x1="200" y1="80" x2="200" y2="86" stroke="currentColor" strokeWidth="1" />
      <line x1="30" y1="86" x2="210" y2="86" stroke="currentColor" strokeWidth="1" />

      <line x1="120" y1="20" x2="120" y2="8" stroke="currentColor" strokeWidth="0.8" />
      <circle cx="120" cy="6" r="2" fill="currentColor" />

      <text x="50" y="74" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="5" fill="currentColor" opacity="0.6" letterSpacing="0.1em">
        RISK
      </text>
      <text x="121" y="74" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="5" fill="currentColor" opacity="0.6" letterSpacing="0.1em">
        CASCADE
      </text>
      <text x="192" y="80" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="5" fill="currentColor" opacity="0.6" letterSpacing="0.1em">
        OUT
      </text>
    </svg>
  );
}

export function AnatomyPlate() {
  return (
    <section className="anatomy" id="anatomy" data-anchor="anatomy">
      <div className="anatomy-head">
        <div className="anatomy-eyebrow">
          <span>Planche n°I</span>
          <span className="filet" />
          <span>Tracé clinique · échelle 1:1</span>
        </div>
        <div className="anatomy-title">
          Anatomie d&apos;une
          <br />
          <span className="italic">fraude P2P.</span>
        </div>
        <div className="anatomy-sub">
          Six points de défaillance, recoupés par les huit détecteurs.
          <br />
          Aucun n&apos;est statistique exotique. Tous laissent une trace dans le master data.
        </div>
      </div>

      <div className="anatomy-svg-wrap">
        <svg viewBox="0 0 900 620" className="anatomy-svg" aria-hidden>
          <defs>
            <pattern id="anatomy-grid" width="20" height="20" patternUnits="userSpaceOnUse">
              <path d="M 20 0 L 0 0 0 20" fill="none" stroke="currentColor" strokeWidth="0.3" opacity="0.08" />
            </pattern>
            <marker id="anatomy-dot" markerWidth="6" markerHeight="6" refX="3" refY="3">
              <circle cx="3" cy="3" r="2" fill="currentColor" />
            </marker>
          </defs>
          <rect width="900" height="620" fill="url(#anatomy-grid)" />

          <rect x="20" y="20" width="860" height="580" fill="none" stroke="currentColor" strokeWidth="0.6" opacity="0.4" />
          <rect x="32" y="32" width="836" height="556" fill="none" stroke="currentColor" strokeWidth="0.4" opacity="0.25" />

          {[
            [20, 20],
            [880, 20],
            [20, 600],
            [880, 600],
          ].map(([x, y], i) => {
            const dx = x === 20 ? 1 : -1;
            const dy = y === 20 ? 1 : -1;
            return (
              <g key={i}>
                <line x1={x} y1={y} x2={x + 14 * dx} y2={y} stroke="var(--risk)" strokeWidth="1.5" />
                <line x1={x} y1={y} x2={x} y2={y + 14 * dy} stroke="var(--risk)" strokeWidth="1.5" />
              </g>
            );
          })}

          <g transform="translate(360, 180)">
            <rect x="0" y="0" width="180" height="240" fill="var(--panel)" stroke="currentColor" strokeWidth="1.5" />
            <line x1="0" y1="36" x2="180" y2="36" stroke="currentColor" strokeWidth="0.8" />
            <text x="14" y="22" fontFamily="var(--font-mono)" fontSize="9" fill="currentColor" letterSpacing="0.1em">
              FACTURE F-2026-04419
            </text>
            <text x="14" y="32" fontFamily="var(--font-mono)" fontSize="7" fill="currentColor" opacity="0.6" letterSpacing="0.06em">
              émise · 14 avril 2026 · 09:24
            </text>

            <text x="14" y="54" fontFamily="var(--font-mono)" fontSize="7" fill="currentColor" opacity="0.5" letterSpacing="0.06em">
              FOURNISSEUR
            </text>
            <text x="14" y="68" fontFamily="var(--font-mono)" fontSize="9" fill="currentColor" letterSpacing="0.04em">
              ALPHACOM SERVICES SAS
            </text>

            <text x="14" y="88" fontFamily="var(--font-mono)" fontSize="7" fill="currentColor" opacity="0.5" letterSpacing="0.06em">
              SIREN
            </text>
            <text x="14" y="102" fontFamily="var(--font-mono)" fontSize="9" fill="currentColor" letterSpacing="0.04em">
              812 446 901
            </text>

            <text x="14" y="122" fontFamily="var(--font-mono)" fontSize="7" fill="currentColor" opacity="0.5" letterSpacing="0.06em">
              IBAN
            </text>
            <text x="14" y="136" fontFamily="var(--font-mono)" fontSize="9" fill="var(--risk)" letterSpacing="0.04em">
              FR76 3000 4015 …
            </text>

            <text x="14" y="156" fontFamily="var(--font-mono)" fontSize="7" fill="currentColor" opacity="0.5" letterSpacing="0.06em">
              BANQUE
            </text>
            <text x="14" y="170" fontFamily="var(--font-mono)" fontSize="9" fill="var(--risk)" letterSpacing="0.04em">
              N26 Bank · Berlin
            </text>

            <text x="14" y="190" fontFamily="var(--font-mono)" fontSize="7" fill="currentColor" opacity="0.5" letterSpacing="0.06em">
              MONTANT · NET 0
            </text>
            <text x="14" y="208" fontFamily="serif" fontSize="22" fill="currentColor" fontStyle="italic">
              412 880 €
            </text>

            <rect x="14" y="216" width="152" height="18" fill="none" stroke="currentColor" strokeWidth="0.5" strokeDasharray="3 2" opacity="0.5" />
            <text x="90" y="228" textAnchor="middle" fontFamily="var(--font-mono)" fontSize="7" fill="var(--risk)" letterSpacing="0.1em">
              USER-LDU221 (×2)
            </text>
          </g>

          <g>
            <line x1="160" y1="92" x2="360" y2="220" stroke="currentColor" strokeWidth="0.6" strokeDasharray="2 3" opacity="0.7" />
            <circle cx="360" cy="220" r="3" fill="var(--risk)" />
            <g transform="translate(40, 80)">
              <text fontFamily="var(--font-mono)" fontSize="9" fill="var(--risk)" letterSpacing="0.16em">
                [ I ]
              </text>
              <text y="14" fontFamily="serif" fontSize="18" fill="currentColor" fontStyle="italic">
                Identité légale
              </text>
              <text y="30" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Cross-check Sirene v3 ·
              </text>
              <text y="42" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                statut actif · date de création.
              </text>
              <text y="58" fontFamily="var(--font-mono)" fontSize="7" fill="var(--muted)" letterSpacing="0.1em">
                DÉT · 04
              </text>
            </g>
          </g>

          <g>
            <line x1="160" y1="240" x2="360" y2="316" stroke="var(--risk)" strokeWidth="0.8" strokeDasharray="2 3" />
            <circle cx="360" cy="316" r="4" fill="var(--risk)" />
            <circle cx="360" cy="316" r="9" fill="none" stroke="var(--risk)" strokeWidth="0.6" opacity="0.5" />
            <g transform="translate(40, 228)">
              <text fontFamily="var(--font-mono)" fontSize="9" fill="var(--risk)" letterSpacing="0.16em">
                [ II ]
              </text>
              <text y="14" fontFamily="serif" fontSize="18" fill="currentColor" fontStyle="italic">
                Coordonnées bancaires
              </text>
              <text y="30" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Diff vs historique master data.
              </text>
              <text y="42" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Zone SEPA habituelle ?
              </text>
              <text y="58" fontFamily="var(--font-mono)" fontSize="7" fill="var(--muted)" letterSpacing="0.1em">
                DÉT · 01 — point principal
              </text>
            </g>
          </g>

          <g>
            <line x1="160" y1="408" x2="360" y2="350" stroke="currentColor" strokeWidth="0.6" strokeDasharray="2 3" opacity="0.7" />
            <circle cx="360" cy="350" r="3" fill="var(--risk)" />
            <g transform="translate(40, 396)">
              <text fontFamily="var(--font-mono)" fontSize="9" fill="var(--risk)" letterSpacing="0.16em">
                [ III ]
              </text>
              <text y="14" fontFamily="serif" fontSize="18" fill="currentColor" fontStyle="italic">
                Juridiction banque
              </text>
              <text y="30" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                FR → DE ? FR → CY ?
              </text>
              <text y="42" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Match sanctions OFAC / PEP.
              </text>
              <text y="58" fontFamily="var(--font-mono)" fontSize="7" fill="var(--muted)" letterSpacing="0.1em">
                DÉT · 05
              </text>
            </g>
          </g>

          <g>
            <line x1="740" y1="92" x2="540" y2="382" stroke="currentColor" strokeWidth="0.6" strokeDasharray="2 3" opacity="0.7" />
            <circle cx="540" cy="382" r="3" fill="var(--risk)" />
            <g transform="translate(680, 80)">
              <text fontFamily="var(--font-mono)" fontSize="9" fill="var(--risk)" letterSpacing="0.16em">
                [ IV ]
              </text>
              <text y="14" fontFamily="serif" fontSize="18" fill="currentColor" fontStyle="italic">
                Montant
              </text>
              <text y="30" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Sous seuil de délégation ?
              </text>
              <text y="42" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Bucket doublon ± 0.01 €.
              </text>
              <text y="58" fontFamily="var(--font-mono)" fontSize="7" fill="var(--muted)" letterSpacing="0.1em">
                DÉT · 02 + 03
              </text>
            </g>
          </g>

          <g>
            <line x1="740" y1="240" x2="540" y2="436" stroke="var(--risk)" strokeWidth="0.8" strokeDasharray="2 3" />
            <circle cx="540" cy="436" r="4" fill="var(--risk)" />
            <circle cx="540" cy="436" r="9" fill="none" stroke="var(--risk)" strokeWidth="0.6" opacity="0.5" />
            <g transform="translate(680, 228)">
              <text fontFamily="var(--font-mono)" fontSize="9" fill="var(--risk)" letterSpacing="0.16em">
                [ V ]
              </text>
              <text y="14" fontFamily="serif" fontSize="18" fill="currentColor" fontStyle="italic">
                Contre-signature
              </text>
              <text y="30" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                4-eyes principle.
              </text>
              <text y="42" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Rôle maintainer ≠ validator.
              </text>
              <text y="58" fontFamily="var(--font-mono)" fontSize="7" fill="var(--muted)" letterSpacing="0.1em">
                DÉT · 01 — ISA 240
              </text>
            </g>
          </g>

          <g>
            <line x1="740" y1="408" x2="540" y2="300" stroke="currentColor" strokeWidth="0.6" strokeDasharray="2 3" opacity="0.7" />
            <circle cx="540" cy="300" r="3" fill="var(--risk)" />
            <g transform="translate(680, 396)">
              <text fontFamily="var(--font-mono)" fontSize="9" fill="var(--risk)" letterSpacing="0.16em">
                [ VI ]
              </text>
              <text y="14" fontFamily="serif" fontSize="18" fill="currentColor" fontStyle="italic">
                Temporalité
              </text>
              <text y="30" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Δt modif IBAN → règlement.
              </text>
              <text y="42" fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.7">
                Pic horaire suspect.
              </text>
              <text y="58" fontFamily="var(--font-mono)" fontSize="7" fill="var(--muted)" letterSpacing="0.1em">
                DÉT · 06 + 07
              </text>
            </g>
          </g>

          <g transform="translate(40, 555)">
            <text fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.5" letterSpacing="0.12em">
              DESSINÉ POUR LE DOSSIER N° 2026/041 · CAS ALPHACOM · 15.04.2026
            </text>
          </g>
          <g transform="translate(720, 555)">
            <text fontFamily="var(--font-mono)" fontSize="8" fill="currentColor" opacity="0.5" letterSpacing="0.12em">
              VÉRIFIÉ · ED25519 · ✓
            </text>
          </g>
        </svg>
      </div>
    </section>
  );
}
