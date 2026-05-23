# 11 — Module IA

## Rôle de l’IA

L’IA améliore l’expérience et la productivité, mais ne décide pas seule.

Usages autorisés :

- expliquer une alerte ;
- reformuler des reason codes ;
- générer une lettre de contestation ;
- résumer un dossier ;
- aider à classifier un libellé bancaire bruité ;
- générer des scénarios de test synthétiques.

Usages interdits :

- décider seule qu’un paiement est frauduleux ;
- remplacer le moteur de règles ;
- inventer des preuves ;
- recevoir des IBAN ou documents bruts ;
- produire une conclusion juridique définitive.

## Redaction obligatoire

Avant tout appel LLM :

```ts
export function redactRiskInput(input: {
  creditorIcs?: string;
  creditorName?: string;
  amountCents: number;
  rum?: string;
  signals: Array<{ code: string; title: string; severity: string }>;
}) {
  return {
    creditorIcsMasked: input.creditorIcs
      ? `${input.creditorIcs.slice(0, 4)}…${input.creditorIcs.slice(-3)}`
      : undefined,
    creditorName: input.creditorName,
    amountCents: input.amountCents,
    rumPresent: Boolean(input.rum),
    signals: input.signals,
  };
}
```

## Prompt — explication d’alerte

```txt
Tu es un assistant d’explication de risques financiers.
Tu dois expliquer les signaux fournis sans ajouter de faits non présents.
Ne donne pas de conseil juridique définitif.
Ne dis pas qu’une fraude est certaine.
Explique le niveau de risque, les raisons, et les actions prudentes.

Données redacted :
{{redacted_json}}
```

## Prompt — lettre de contestation

```txt
Rédige un brouillon de courrier de contestation pour un prélèvement SEPA.
Utilise uniquement les faits fournis.
N’invente aucune date, aucun mandat, aucun interlocuteur.
Garde un ton sobre et factuel.
Ajoute des champs à compléter si nécessaire.

Faits structurés :
{{facts_json}}
```

## Interface de service

```ts
export type AiExplanationInput = {
  assessmentId: string;
  redactedFacts: Record<string, unknown>;
};

export type AiExplanationResult = {
  summary: string;
  recommendedActions: string[];
  caveats: string[];
};

export interface AiRiskExplainer {
  explain(input: AiExplanationInput): Promise<AiExplanationResult>;
}
```

## Contrôles qualité

- Tests de redaction.
- Snapshots prompts.
- Liste de champs interdits.
- Refus si payload contient un pattern IBAN.
- Logging coût/usage sans PII.
- Timeout et fallback sans IA.

## Fallback sans IA

Toute fonctionnalité IA doit avoir un fallback template :

- résumé basé sur reason codes ;
- lettre de contestation template ;
- explication standard par code.

