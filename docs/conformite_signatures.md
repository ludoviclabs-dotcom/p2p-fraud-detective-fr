# Conformité — signatures cryptographiques + archivage légal

> **PR P5-5** — signatures Ed25519 sur l'audit trail, doctrine d'archivage.
> Document mis à jour mai 2026.

## Pourquoi des signatures Ed25519

Le hash chain SHA-256 existant (v0.3) garantit l'**intégrité** de la chaîne : impossible d'altérer une entrée passée sans casser le maillage des `prev_hash`. Mais il ne garantit pas la **non-répudiation** : un attaquant qui obtient l'accès au backend peut reconstruire un nouveau hash chain cohérent.

Les signatures cryptographiques Ed25519 (RFC 8032) ajoutent :

1. **Non-répudiation** : la signature ne peut être produite que par le détenteur de la clé privée. Stockée hors ligne (Vault / KMS / fichier 0600 root-only), elle reste protégée même si le backend est compromis.
2. **Vérifiabilité externe** : la clé publique peut être communiquée à un tiers (CAC, ACPR, Cour des comptes, magistrat) qui vérifie indépendamment chaque entrée sans accès au backend ni à la clé privée.
3. **Standardisation** : Ed25519 est référencé dans la doctrine ANSSI RGS B1 + B2 (signature électronique), et accepté en jurisprudence européenne (eIDAS 2024/1183).

## Choix technique

| Critère | Ed25519 | RSA-2048 | ECDSA P-256 |
|---|---|---|---|
| Taille clé publique | **32 octets** | 256 octets | 64 octets |
| Taille signature | **64 octets** | 256 octets | 64 octets |
| Performance signature | ~1 µs | ~1 ms | ~10 µs |
| Performance vérification | ~3 µs | ~50 µs | ~100 µs |
| Déterminisme | ✅ | ❌ | ❌ (nonce aléatoire) |
| Risque nonce faible | ✅ aucun | n/a | ⚠️ historique |
| Conformité RGS | ✅ B1 + B2 | ✅ B1 + B2 | ✅ B1 + B2 |

Ed25519 a été retenu pour ses signatures déterministes (pas de fuite via nonce mal randomisé) et son couple performance/sécurité optimal.

Implémentation : **PyNaCl** (≥ 1.5), wrapper Python de la bibliothèque libsodium. Alternative équivalente : `cryptography.hazmat.primitives.asymmetric.ed25519` (déjà présent dans nos dépendances).

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Génération hors ligne (admin sécurité)                   │
│    $ python -c "from p2p_fraud.security.signing import \\   │
│                Ed25519Signer; kp = Ed25519Signer.generate();│
│                print(kp.private_key_b64)"                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 2. Stockage coffre-fort                                     │
│    Vault / KMS / fichier 0600 root-only                     │
│    JAMAIS dans Git, JAMAIS dans les logs                    │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 3. Injection runtime                                        │
│    export P2PFD_ED25519_PRIVATE_KEY=<base64>                │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 4. Signature automatique de chaque entrée audit log         │
│    AuditLog.append() → sign(hash) → store signature col     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│ 5. Vérification externe                                     │
│    Tiers (CAC, ACPR, magistrat) :                           │
│    a. récupère la clé publique : GET /security/public-key   │
│    b. récupère l'audit log : GET /api/v1/audit              │
│    c. vérifie chaque entrée : verify_signature(             │
│         message=entry.hash, signature_hex=entry.signature,  │
│         public_key_b64=...)                                 │
└─────────────────────────────────────────────────────────────┘
```

## Mode démo public

Sur la démo Streamlit Cloud, **la variable `P2PFD_ED25519_PRIVATE_KEY` n'est PAS définie**. Le signer est désactivé, les entrées sont écrites avec `signature=NULL`, et `verify_chain()` valide uniquement le hash chain SHA-256 (comportement v0.4 inchangé).

Cela évite :
- d'exposer une clé privée en public,
- d'introduire une fragilité (cold start signer + désynchronisation).

Pour activer en pilote ETI :
1. Générer une paire de clés hors ligne (admin sécurité).
2. Stocker la clé privée en coffre-fort.
3. Injecter `P2PFD_ED25519_PRIVATE_KEY` au boot du conteneur.
4. Publier la clé publique sur le portail interne du pilote.

## Backward compatibility v0.4 → v0.5

- La colonne `audit_log.signature` est **nullable** : les entrées historiques v0.4 restent valides.
- `verify_chain()` accepte un mélange d'entrées signées et non signées :
  - Si `public_key_b64` est fourni ET `entry.signature` est non vide → vérification cryptographique.
  - Sinon → vérification du hash chain SHA-256 uniquement (équivalent v0.4).
- Pas de migration Alembic forcée : un `ALTER TABLE ... ADD COLUMN signature` défensif est exécuté au boot.

## Endpoint `GET /security/public-key`

```bash
$ curl http://api.example.com/security/public-key
{
  "public_key_b64": "ABC123...defg=",
  "enabled": "true",
  "algorithm": "Ed25519"
}
```

À publier sur :
- Le portail interne du pilote (intranet ETI).
- La page Gouvernance > Cryptographie de l'app.
- Le site institutionnel (entête transparence).

## Code de vérification externe (Python)

```python
import base64
import requests
from nacl.signing import VerifyKey

# 1. Récupérer la clé publique
resp = requests.get("https://api.example.com/security/public-key").json()
public_key = VerifyKey(base64.b64decode(resp["public_key_b64"]))

# 2. Récupérer l'audit log
audit = requests.get(
    "https://api.example.com/api/v1/audit",
    headers={"Authorization": f"Bearer {token}"},
).json()

# 3. Vérifier chaque entrée
for entry in audit["entries"]:
    if not entry.get("signature"):
        continue  # entrée v0.4, hash chain uniquement
    try:
        public_key.verify(
            entry["hash"].encode("utf-8"),
            bytes.fromhex(entry["signature"]),
        )
    except Exception:
        print(f"⚠️ Signature invalide pour seq={entry['seq']}")
```

## Cadre réglementaire

| Référence | Apport |
|---|---|
| **eIDAS 2014/910 + 2024/1183** | Cadre européen signature électronique. Ed25519 conforme. |
| **ANSSI RGS v2.0** | Référentiel Général de Sécurité — niveaux B1 et B2 acceptent Ed25519. |
| **CMF L. 561-32** | Conservation des documents LCB-FT 5 ans (signature non requise mais valorisée). |
| **AMLD6 art. 22** | Conservation 5 ans + intégrité prouvable. Signatures crypto renforcent l'opposabilité. |
| **CRPC art. L. 312-1 + art. L. 322-2** | Archivage public soumis à intégrité prouvable — Ed25519 ratifié. |
| **CGI art. L. 102 B** | Conservation 6 ans + 1 an des pièces justificatives. Signatures = traçabilité audit. |
| **Sapin 2 art. 17** | Plan de prévention corruption — audit trail signé = preuve de diligence. |

## Roadmap WORM + backup (hors P5-5 — reporté v0.6)

Le plan d'origine prévoyait également :
- Archivage WORM S3 Object Lock COMPLIANCE retention 10 ans (`exports/worm_s3.py`)
- Backup PostgreSQL quotidien `pg_dump | gzip | s3 cp` sur Glacier Instant Retrieval (`scheduler/backup.py`)

**Statut P5-5** : non implémentés faute de budget AWS dans le contexte free tier. Les fonctions sont documentées ici comme **roadmap v0.6** quand un pilote ETI couvrira les coûts S3 (~1-5 €/mois pour 100 Go d'audit log + 30 j de backups quotidiens compressés).

### Spécification roadmap

```python
# Roadmap v0.6 — exports/worm_s3.py
def export_audit_log_to_worm(
    bucket: str,
    key_prefix: str = "audit/",
    *,
    object_lock_mode: Literal["COMPLIANCE", "GOVERNANCE"] = "COMPLIANCE",
    retention_years: int = 10,
    aws_profile: str | None = None,
) -> ExportResult:
    """Upload JSONL signé Ed25519 vers S3 avec Object Lock COMPLIANCE.

    Idempotent (skip si l'objet existe déjà avec le même hash).
    Conformité Sapin 2 (10 ans), AMLD6 (5 ans + buffer), CGI (6 ans + 1).
    """
```

```python
# Roadmap v0.6 — scheduler/backup.py
def backup_postgres_to_s3(
    *,
    schedule: str = "0 2 * * *",  # 02:00 Europe/Paris
    bucket: str,
    retention_days: int = 30,
    storage_class: str = "GLACIER_IR",
) -> None:
    """Job APScheduler : pg_dump | gzip | s3 cp.

    Rotation 30 jours sur Glacier Instant Retrieval (~ 0.004 $/GB-mois).
    """
```

### Alternatives self-hosted (sans budget AWS)

Si le pilote refuse AWS pour souveraineté :
- **MinIO + Object Lock** auto-hébergé (compatible API S3, gratuit).
- **OVHcloud Object Storage** (~ 5 €/mois pour 100 Go).
- **Scaleway Object Storage** (~ 3 €/mois pour 75 Go, Cold tier).
- **OUTSCALE OOS** (qualifié SecNumCloud) — pour clients régaliens DGFiP / DGE.

## Cadre probatoire (général)

Le standard Ed25519 (RFC 8032) combiné au référentiel ANSSI RGS B1/B2 et au règlement eIDAS (UE 2014/910, mis à jour par le règlement (UE) 2024/1183) constitue le socle technique européen reconnu pour la signature électronique avancée. La **qualification probatoire** d'un audit trail signé dans un contentieux ou un contrôle dépend du contexte d'usage, du déployeur et des règles sectorielles applicables : elle doit être validée au cas par cas par le conseil juridique, le commissaire aux comptes et, le cas échéant, l'autorité de tutelle.

Aucune jurisprudence n'est citée dans ce document : les exemples de décisions judiciaires ou administratives présentés en démonstrateur sont indicatifs et doivent être sourcés (Légifrance, sites institutionnels) avant tout usage en argumentaire commercial ou juridique.

## Synthèse — sécurité par défaut

| Couche | v0.3 | v0.4 | **v0.5 (actuel)** | v0.6 (roadmap) |
|---|---|---|---|---|
| Hash chain SHA-256 | ✅ | ✅ | ✅ | ✅ |
| OIDC fédéré | — | ✅ | ✅ | ✅ |
| RBAC 4 rôles | ✅ | ✅ | ✅ | ✅ |
| Chiffrement IBAN au repos | ✅ | ✅ | ✅ | ✅ |
| **Signatures Ed25519** | — | — | ✅ | ✅ |
| **Endpoint public-key** | — | — | ✅ | ✅ |
| Audit log signé bout-en-bout | — | — | ✅ | ✅ |
| WORM S3 Object Lock 10 ans | — | — | 🟡 doc | ✅ |
| Backup PG automatique S3 Glacier | — | — | 🟡 doc | ✅ |
| Qualification SecNumCloud | — | — | — | 🟡 v1.0 |
