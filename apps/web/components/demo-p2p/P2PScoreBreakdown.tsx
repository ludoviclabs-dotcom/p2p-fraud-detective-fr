"use client";

import { DEMO_REASON_CODES, DEMO_SUPPLIER } from "./p2p-demo-data";
import type { DemoContent } from "./p2p-demo-content";

export function P2PScoreBreakdown({ content }: { content: DemoContent }) {
  const scoreItems = DEMO_REASON_CODES.map((reason, index) => ({
    reason,
    cumulative: DEMO_REASON_CODES.slice(0, index + 1).reduce(
      (total, item) => total + item.points,
      0,
    ),
  }));

  return (
    <div className="p2p-demo-score-layout">
      <div className="p2p-demo-panel p2p-demo-score-breakdown">
        <div className="p2p-demo-eyebrow">{content.scoreBreakdown.subtitle}</div>
        <div className="p2p-demo-score-total">
          <span>{DEMO_SUPPLIER.score}</span>
          <span>/100</span>
        </div>
        <h2>{content.scoreBreakdown.title}</h2>
        <div className="p2p-demo-score-track" aria-hidden>
          <span style={{ width: `${DEMO_SUPPLIER.score}%` }} />
        </div>
        <div className="p2p-demo-score-items">
          {scoreItems.map(({ reason, cumulative }, index) => {
            const copy = content.reasonCodes[reason.code];
            return (
              <div
                key={reason.code}
                className="p2p-demo-score-item"
                style={{ animationDelay: `${index * 130}ms` }}
              >
                <span>+{reason.points}</span>
                <div>
                  <strong>{copy?.label ?? reason.code}</strong>
                  <p>{copy?.description}</p>
                </div>
                <code>{String(Math.min(cumulative, DEMO_SUPPLIER.score)).padStart(2, "0")}</code>
              </div>
            );
          })}
        </div>
        <p className="p2p-demo-score-note">{content.scoreBreakdown.illustrative}</p>
      </div>
      <P2PMicroVisuals content={content} />
    </div>
  );
}

function P2PMicroVisuals({ content }: { content: DemoContent }) {
  return (
    <div className="p2p-demo-micro-grid">
      <div className="p2p-demo-micro-card iban">
        <div className="p2p-demo-eyebrow">{content.microVisuals.ibanTitle}</div>
        <div className="p2p-demo-iban-graph">
          <span>V00474</span>
          <i />
          <strong>IBAN ****7821</strong>
          <i />
          <span>V00231</span>
          <span>V00118</span>
        </div>
        <p>{content.microVisuals.ibanLabel}</p>
      </div>

      <div className="p2p-demo-micro-card threshold">
        <div className="p2p-demo-eyebrow">{content.microVisuals.thresholdTitle}</div>
        <div className="p2p-demo-threshold-strip">
          {Array.from({ length: 14 }).map((_, index) => (
            <span key={index} style={{ left: `${8 + index * 6.4}%` }} />
          ))}
        </div>
        <p>{content.microVisuals.thresholdLabel}</p>
      </div>

      <div className="p2p-demo-micro-card rbe">
        <div className="p2p-demo-eyebrow">{content.microVisuals.rbeTitle}</div>
        <div className="p2p-demo-rbe-compare">
          <span>{content.microVisuals.rbeInternal}</span>
          <span>{content.microVisuals.rbeOfficial}</span>
        </div>
        <p>{content.microVisuals.rbeMismatch}</p>
      </div>

      <div className="p2p-demo-micro-card eyes">
        <div className="p2p-demo-eyebrow">{content.microVisuals.fourEyesTitle}</div>
        <div className="p2p-demo-four-eyes">
          {content.microVisuals.fourEyesSteps.map((step) => (
            <span key={step}>{step}</span>
          ))}
        </div>
        <p>{content.microVisuals.fourEyesLabel}</p>
      </div>
    </div>
  );
}
