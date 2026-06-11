# Spécification proof-manifest/v1 — pack de preuve vérifiable hors-ligne

> Format commun de pack de preuve, conçu pour être adopté tel quel par
> d'autres produits (KYB Graph, CarbonCo…). La mutualisation se fait **au
> niveau du format**, pas du code : chaque produit le génère dans sa propre
> stack, n'importe quel tiers le vérifie avec le même protocole.
> Implémentation de référence : `src/p2p_fraud/export/case_pack.py` +
> vérificateur autonome `scripts/verify_case_pack.py`.

## Objectif

Permettre à un tiers (CAC, ACPR, auditeur, client) de vérifier l'intégrité
et l'origine d'un export de preuve **sans aucun accès au produit** : ni
compte, ni API, ni code propriétaire — uniquement le ZIP, la clé publique
et un script en bibliothèque standard.

## Structure du pack

```
<pack-name>.zip
├── manifest.json        # inventaire hashé + métadonnées (ce document)
├── signature.sig        # signature Ed25519 hex du manifeste ("" si non signé)
├── README.txt           # procédure de vérification + clé publique
├── <fichiers de preuve> # ex. case.json, audit-trail.jsonl, dossier-ia.json
```

Convention de nommage : `<type>-pack-<project>-<entityId>.zip`
(ex. `case-pack-p2p-CASE-X.zip`, `diligence-pack-kyb-DOSSIER-Y.zip`,
`evidence-pack-carbonco-REPORT-Z.zip`).

## manifest.json

```json
{
  "schemaVersion": "proof-manifest/v1",
  "exportId": "exp_3f9c2e7a1b4d5a60",
  "project": "p2p",
  "entityType": "case",
  "entityId": "CASE-...",
  "generatedAt": "2026-06-11T10:24:00.000000+00:00",
  "chainHead": "a8e6b4…(64 hex)",
  "signerPublicKeyB64": "…(32 octets base64, \"\" si non signé)",
  "algorithms": { "hash": "SHA-256", "signature": "Ed25519" },
  "files": [
    { "path": "audit-trail.jsonl", "sha256": "…", "kind": "jsonl" },
    { "path": "case.json", "sha256": "…", "kind": "json" }
  ]
}
```

Règles :

- `files` est trié par `path` (ordre lexicographique) et inventorie **tous**
  les fichiers du ZIP sauf `manifest.json`, `signature.sig` et `README.txt`.
  Un fichier présent dans le ZIP mais absent de l'inventaire invalide le pack.
- `chainHead` ancre le pack sur la dernière entrée du journal append-only du
  produit au moment de l'export (chaîne SHA-256, voir § Chaîne d'audit).
- `project` identifie le produit émetteur (`p2p`, `kyb`, `carbonco`, …) ;
  `entityType`/`entityId` identifient l'objet exporté (case, dossier, report).

## Canonicalisation et signature

1. **Forme canonique** d'un objet JSON : sérialisation avec clés triées,
   séparateurs compacts `(",", ":")`, UTF-8 non échappé
   (`json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)`).
2. **Hash du manifeste** : SHA-256 de la forme canonique du manifeste parsé.
   Le fichier `manifest.json` peut être indenté pour lisibilité humaine : le
   vérificateur parse le JSON puis re-canonicalise — les octets du fichier ne
   sont pas la référence.
3. **Signature** : Ed25519 (RFC 8032) de la **chaîne hex du hash** encodée
   UTF-8 (même patron que les entrées d'audit), écrite en hex (128 caractères)
   dans `signature.sig`. Clé publique dans `signerPublicKeyB64` et publiée
   par le produit (`GET /security/public-key` pour P2P).
4. **Mode non signé** : un produit sans clé configurée (démo) émet
   `signature.sig` vide et `signerPublicKeyB64: ""`. Les contrôles de hash
   restent intégralement vérifiables ; le vérificateur émet un avertissement.

## Chaîne d'audit embarquée (audit-trail.jsonl)

Une entrée JSON par ligne, champs : `seq`, `at`, `actor`, `kind`, `payload`,
`prev_hash`, `hash`, `signature`.

- `hash` = SHA-256 de la forme canonique de
  `{"actor","at","kind","payload","prev_hash","seq"}`.
- `prev_hash` = `hash` de l'entrée précédente ; genesis = 64 zéros.
- `signature` (optionnelle par entrée) = Ed25519 de la chaîne hex du `hash`.
- L'export lui-même est journalisé (`kind: "case.pack_exported"`) **avant**
  la capture, donc le pack contient sa propre trace. Le hash du manifeste
  n'est pas dans cette entrée (circularité) — l'ancrage se fait par
  `chainHead`.

## Procédure de vérification (normative)

1. Pour chaque entrée de `manifest.files` : recalculer le SHA-256 du fichier
   et comparer. Échec si différent ou fichier manquant. Échec si le ZIP
   contient un fichier de preuve non inventorié.
2. Re-canonicaliser le manifeste, calculer son SHA-256, vérifier
   `signature.sig` avec `signerPublicKeyB64` (sauf mode non signé).
3. Rejouer la chaîne de `audit-trail.jsonl` (recalcul de chaque hash,
   continuité des `prev_hash`, signatures d'entrées si présentes) et vérifier
   que le hash de la dernière entrée égale `chainHead`.
4. Verdict global = ET logique de tous les contrôles.

Implémentation de référence : `scripts/verify_case_pack.py` (Python 3,
stdlib ; PyNaCl optionnel pour Ed25519).

## Note de conception

Ce format est né d'un rapport d'architecture externe proposant un socle de
preuve commun aux trois produits. Divergences assumées vis-à-vis de ce
rapport : la signature Ed25519 est **native** (réutilise la clé de l'audit
log du produit, pas un mécanisme parallèle), et la chaîne de preuve est
portée par le journal append-only **existant** plutôt que par une nouvelle
table `proof_events` — on standardise le format d'échange, pas
l'implémentation interne.
