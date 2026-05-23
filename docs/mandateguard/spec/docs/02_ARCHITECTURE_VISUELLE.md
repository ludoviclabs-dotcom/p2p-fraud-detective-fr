# 02 — Architecture visuelle

## Vue macro

```mermaid
flowchart LR
    U[Utilisateur / entreprise] --> WEB[App Next.js sur Vercel]
    ADMIN[Admin / Analyste risque] --> WEB

    WEB --> API[API Backend / BFF]
    API --> AUTH[Auth + RBAC]
    API --> DB[(Postgres)]
    API --> OBJ[(Stockage objets chiffré)]
    API --> QUEUE[Queue / jobs async]
    API --> AI[LLM Gateway redacted]

    QUEUE --> W1[Worker normalisation SEPA]
    QUEUE --> W2[Worker analyse risque]
    QUEUE --> W3[Worker ledger / preuve]
    QUEUE --> W4[Worker evidence pack]
    QUEUE --> PY[Worker Python analytics]

    W1 --> DB
    W2 --> DB
    W3 --> DB
    W3 --> LEDGER[Registre d'intégrité]
    W4 --> OBJ
    PY --> DB

    CSV[CSV / Sandbox / API bancaire future] --> API
    PSP[Créancier / PSP futur] --> API
    BANK[Banque future] --> VERIFY[API vérification pré-débit]
    VERIFY --> API
```

## Plateforme à deux rails

```mermaid
flowchart TB
    PLATFORM[Payment Integrity Platform]

    PLATFORM --> SDD[SEPA Mandate Guard]
    PLATFORM --> P2P[P2P / Supplier Payment Guard]
    PLATFORM --> CORE[Risk Core]
    PLATFORM --> EVIDENCE[Evidence Pack]
    PLATFORM --> LEDGER[Audit Ledger]

    SDD --> MANDATES[Mandate Vault]
    SDD --> DEBITS[Direct Debit Events]
    SDD --> SEPARULES[Règles ICS/RUM/mandat]

    P2P --> BENEF[Beneficiary Vault]
    P2P --> PAYMENTS[Payment Instructions]
    P2P --> P2PRULES[Règles RIB/fournisseur/facture]

    CORE --> SCORE[Scoring]
    CORE --> REASONS[Reason Codes]
    CORE --> DECISION[Decision Engine]

    EVIDENCE --> PACK[Dossier exportable]
    LEDGER --> AUDIT[Hash chain]
```

## Flux de création d’un mandat

```mermaid
sequenceDiagram
    participant User as Utilisateur
    participant App as App
    participant API as API Mandates
    participant Crypto as Crypto Service
    participant Vault as Mandate Vault
    participant Ledger as Audit Ledger

    User->>App: Crée un mandat
    App->>API: POST /api/v1/mandates
    API->>Crypto: Normalise + fingerprint IBAN
    Crypto-->>API: ibanFingerprint + ibanCiphertext
    API->>Vault: Sauvegarde mandat DRAFT
    API->>Ledger: Audit MANDATE_CREATED
    API-->>App: mandateId
    User->>App: Active / signe / confirme
    App->>API: POST /api/v1/mandates/:id/sign
    API->>Vault: Statut ACTIVE + preuve
    API->>Ledger: Audit MANDATE_SIGNED
    API-->>App: Mandat actif
```

## Flux d’analyse d’un prélèvement

```mermaid
sequenceDiagram
    participant Source as Source prélèvement
    participant API as API Ingestion
    participant Norm as SEPA Normalizer
    participant DB as Postgres
    participant Risk as Risk Engine
    participant Alert as Alerting
    participant Evidence as Evidence Builder

    Source->>API: Prélèvement observé
    API->>Norm: Normalisation
    Norm->>DB: DebitEvent idempotent
    API->>Risk: Analyse
    Risk->>DB: Recherche mandat actif
    Risk->>Risk: Règles déterministes
    Risk->>Risk: Scoring
    Risk->>DB: RiskAssessment

    alt Risque faible
        Risk-->>API: ALLOW
    else Risque moyen
        Risk->>Alert: Crée alerte
    else Risque critique
        Risk->>Alert: Alerte critique
        Risk->>Evidence: Prépare dossier
    end
```

## Flux d’analyse P2P / fournisseur

```mermaid
sequenceDiagram
    participant User as DAF / Analyste
    participant App as App
    participant API as API Risk
    participant Core as Risk Core
    participant P2P as P2P Engine
    participant Py as Worker Python optionnel
    participant Evidence as Evidence

    User->>App: Importe paiement/facture
    App->>API: POST /api/v1/risk/assess
    API->>Core: Orchestration
    Core->>P2P: Règles rapides TS
    P2P-->>Core: Findings

    alt Batch lourd
        Core->>Py: Job graph/fuzzy/ML
        Py-->>Core: Findings additionnels
    end

    Core->>Evidence: Evidence pack si risque élevé
    Core-->>API: score + décision + signaux
    API-->>App: Résultat explicable
```

## Déploiement

```mermaid
flowchart LR
    DEV[GitHub] --> VERCEL[Vercel]
    VERCEL --> WEB[Next.js Web]
    VERCEL --> FN[Vercel Functions]
    VERCEL --> CRON[Cron Jobs]
    VERCEL --> QUEUE[Queue]

    FN --> DB[(Postgres)]
    FN --> STORAGE[Object Storage]
    FN --> KMS[KMS / Secrets]
    QUEUE --> TS[Workers TS]
    QUEUE --> PY[Worker Python externe]
```

