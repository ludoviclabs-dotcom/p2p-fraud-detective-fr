# 06 — Moteur d’analyse et de détection

## Objectif

Le moteur doit produire une décision explicable à partir d’un événement financier.

Formule :

```txt
event + context + rules = signals + score + decision + evidence
```

## Domaines de risque

```ts
export type RiskDomain =
  | "SEPA_DIRECT_DEBIT"
  | "SUPPLIER_PAYMENT"
  | "SEPA_CREDIT_TRANSFER"
  | "P2P_TRANSFER"
  | "QR_PAYMENT"
  | "MANDATE_EVENT";
```

## Types de base

```ts
export type Severity = "info" | "low" | "medium" | "high" | "critical";

export type RiskSignal = {
  code: string;
  title: string;
  message: string;
  severity: Severity;
  score: number;
  evidence: Record<string, unknown>;
};

export type RiskDecision =
  | "ALLOW"
  | "ALLOW_MONITOR"
  | "ALERT_USER"
  | "REVIEW"
  | "BLOCK_RECOMMENDED"
  | "DISPUTE_READY";

export type RiskAssessmentResult = {
  score: number;
  level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  decision: RiskDecision;
  signals: RiskSignal[];
  engineVersion: string;
};
```

## Interface d’une règle

```ts
export type RiskRule<TContext> = {
  id: string;
  version: string;
  domain: RiskDomain;
  evaluate(ctx: TContext): Promise<RiskSignal[]>;
};
```

## Engine générique

```ts
export class RiskEngine<TContext> {
  constructor(
    private readonly rules: RiskRule<TContext>[],
    private readonly engineVersion: string,
  ) {}

  async assess(ctx: TContext): Promise<RiskAssessmentResult> {
    const signalsNested = await Promise.all(
      this.rules.map((rule) => rule.evaluate(ctx)),
    );

    const signals = signalsNested.flat();
    const score = combineSignals(signals);
    const level = toLevel(score, signals);
    const decision = decide(score, signals);

    return {
      score,
      level,
      decision,
      signals,
      engineVersion: this.engineVersion,
    };
  }
}
```

## Scoring v0

Le scoring v0 est simple, explicable et déterministe.

```ts
export function combineSignals(signals: RiskSignal[]): number {
  const raw = signals.reduce((sum, signal) => sum + signal.score, 0);
  return Math.max(0, Math.min(100, raw));
}

export function toLevel(score: number, signals: RiskSignal[]) {
  if (signals.some((s) => s.severity === "critical") || score >= 80) return "CRITICAL";
  if (score >= 60) return "HIGH";
  if (score >= 30) return "MEDIUM";
  return "LOW";
}

export function decide(score: number, signals: RiskSignal[]): RiskDecision {
  const critical = signals.some((s) => s.severity === "critical");
  if (critical && score >= 80) return "DISPUTE_READY";
  if (score >= 75) return "BLOCK_RECOMMENDED";
  if (score >= 60) return "REVIEW";
  if (score >= 30) return "ALERT_USER";
  if (score >= 15) return "ALLOW_MONITOR";
  return "ALLOW";
}
```

## Reason codes unifiés

### Mandate / SEPA

- `NO_ACTIVE_MANDATE`
- `MANDATE_REVOKED`
- `MANDATE_UNSIGNED`
- `MANDATE_AMOUNT_EXCEEDED`
- `MANDATE_FREQUENCY_EXCEEDED`
- `RUM_MISMATCH`
- `ICS_MISMATCH`
- `CREDITOR_NAME_MISMATCH`

### IBAN / Beneficiary

- `NEW_BENEFICIARY`
- `NEW_IBAN`
- `IBAN_RECENTLY_ADDED`
- `IBAN_NAME_MISMATCH`
- `SHARED_IBAN`
- `IBAN_COUNTRY_CHANGED`

### Supplier

- `SUPPLIER_RIB_RECENT_CHANGE`
- `SUPPLIER_DORMANT_REACTIVATED`
- `SIREN_INACTIVE`
- `SIREN_NAME_MISMATCH`
- `FOUR_EYES_BREACH`
- `DUPLICATE_INVOICE`

### Velocity

- `UNUSUAL_AMOUNT`
- `SPLIT_PAYMENTS`
- `MULTIPLE_SMALL_DEBITS`
- `UNUSUAL_FREQUENCY`
- `FIRST_DEBIT_AFTER_MANDATE_CREATION`

### Graph

- `GRAPH_HIGH_RISK_CLUSTER`
- `GRAPH_SHARED_IBAN`
- `GRAPH_MULE_LINKED_PAYERS`
- `GRAPH_CREDITOR_DISPUTE_CLUSTER`

### AML / conformité B2B

- `SANCTIONS_POSSIBLE_HIT`
- `PEP_POSSIBLE_HIT`
- `HIGH_RISK_COUNTRY`

## Règles SEPA v0

| Règle | Gravité | Score |
|---|---:|---:|
| Aucun mandat actif | critical | 80 |
| Mandat révoqué | critical | 75 |
| Montant supérieur au plafond | critical | 70 |
| RUM inconnue | high | 55 |
| ICS différent | critical | 80 |
| Nouveau créancier | medium | 25 |
| Fréquence inhabituelle | high | 45 |
| Plusieurs petits prélèvements | high | 50 |

## Règles P2P v0

| Règle | Gravité | Score |
|---|---:|---:|
| Nouveau bénéficiaire | medium | 25 |
| IBAN récemment ajouté | high | 45 |
| Changement RIB juste avant paiement | critical | 70 |
| Même personne modifie et approuve | high | 50 |
| Doublon facture | high | 55 |
| Fractionnement sous seuil | high | 50 |
| SIREN inactif | high | 60 |

## Règle exemple — aucun mandat actif

```ts
export const noActiveMandateRule: RiskRule<SepaRiskContext> = {
  id: "NO_ACTIVE_MANDATE",
  version: "1.0.0",
  domain: "SEPA_DIRECT_DEBIT",

  async evaluate(ctx) {
    if (ctx.mandate) return [];

    return [
      {
        code: "NO_ACTIVE_MANDATE",
        title: "Aucun mandat actif trouvé",
        message: "Ce prélèvement ne correspond à aucun mandat actif connu.",
        severity: "critical",
        score: 80,
        evidence: {
          creditorIcs: ctx.event.creditorIcs,
          rumPresent: Boolean(ctx.event.rum),
          amountCents: ctx.event.amountCents,
        },
      },
    ];
  },
};
```

## Règle exemple — changement RIB fournisseur récent

```ts
export const supplierRibRecentChangeRule: RiskRule<SupplierPaymentContext> = {
  id: "SUPPLIER_RIB_RECENT_CHANGE",
  version: "1.0.0",
  domain: "SUPPLIER_PAYMENT",

  async evaluate(ctx) {
    const hours = ctx.event.ribChangedHoursAgo;
    if (hours == null || hours > 72) return [];

    return [
      {
        code: "SUPPLIER_RIB_RECENT_CHANGE",
        title: "RIB fournisseur modifié récemment",
        message: "Le paiement vise un IBAN ajouté ou modifié récemment.",
        severity: hours <= 24 ? "critical" : "high",
        score: hours <= 24 ? 70 : 45,
        evidence: { ribChangedHoursAgo: hours },
      },
    ];
  },
};
```

## Rôle du ML

Le ML ne vient qu’après le moteur v0.

Approche recommandée :

1. collecter des données propres ;
2. labelliser faux positifs / vrais positifs ;
3. ajouter des scores statistiques simples ;
4. ajouter des modèles batch non décisionnels ;
5. comparer au moteur déterministe ;
6. ne jamais rendre le modèle opaque unique décideur.

