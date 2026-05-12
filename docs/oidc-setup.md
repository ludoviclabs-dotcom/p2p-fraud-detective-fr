# Guide setup OIDC — Entra ID, Auth0, Keycloak

Configuration pas-à-pas pour activer l'authentification fédérée OIDC sur le
déploiement P2P Fraud Detective FR.

Le flow implémenté est **Authorization Code + PKCE** (RFC 7636), avec
validation cryptographique du `id_token` via JWKS et sessions signées côté
serveur (itsdangerous HMAC-SHA256). Pas d'access token persistant.

## Variables d'environnement (toutes nécessaires)

```bash
OIDC_ISSUER=                 # URL issuer (sans trailing slash, sans /authorize)
OIDC_CLIENT_ID=              # Application ID côté IdP
OIDC_CLIENT_SECRET=          # Secret applicatif (vide si PKCE pur sans secret)
OIDC_REDIRECT_URI=           # URL absolue du callback (= https://api.<domain>/oidc/callback)
OIDC_SCOPES=openid email profile
OIDC_SESSION_SECRET=         # Clé HMAC ≥ 32 octets — `python -c 'import secrets; print(secrets.token_urlsafe(48))'`
OIDC_POST_LOGIN_URL=         # URL absolue où rediriger après login (= https://streamlit.<domain>/)
OIDC_SESSION_MAX_AGE=28800   # 8h par défaut
OIDC_ROLE_MAP=               # JSON : {"DG-Audit":"admin","Audit-Senior":"manager",...}
```

## Microsoft Entra ID (Azure AD)

### 1. Créer l'application

1. Portal Azure → **Microsoft Entra ID** → **App registrations** → **New registration**.
2. Name : `P2P Fraud Detective FR — Pilot`.
3. Supported account types : **Single tenant** (recommandé pour pilote ETI).
4. Redirect URI : type **Web**, URL `https://api.<your-domain>/oidc/callback`.
5. Cliquer **Register**.

### 2. Configurer les claims

1. **Token configuration** → **Add optional claim** → cocher `email`, `groups`, `preferred_username`.
2. **Manifest** → vérifier `"groupMembershipClaims": "SecurityGroup"`.

### 3. Créer un client secret

1. **Certificates & secrets** → **New client secret** → durée 24 mois.
2. Copier la valeur (visible une seule fois) → `OIDC_CLIENT_SECRET`.

### 4. Récupérer les URLs

L'issuer Entra ID se construit ainsi :
```
OIDC_ISSUER=https://login.microsoftonline.com/<tenant-id>/v2.0
```

Vérifier le discovery doc :
```bash
curl https://login.microsoftonline.com/<tenant-id>/v2.0/.well-known/openid-configuration | jq .
```

### 5. Mapper les groupes vers les rôles RBAC

Si l'org utilise les groupes Entra ID `DG-Audit`, `Audit-Senior`, `Audit-Junior` :

```bash
OIDC_ROLE_MAP='{"DG-Audit":"admin","Audit-Senior":"manager","Audit-Junior":"analyst"}'
```

Les `groups` arrivent sous forme d'IDs GUID dans le claim — pour les mapper par nom,
activer **App roles** dans Entra ID puis utiliser le claim `roles`.

## Auth0

1. Auth0 Dashboard → **Applications** → **Create Application** → type **Regular Web App**.
2. **Settings** → Allowed Callback URLs : `https://api.<domain>/oidc/callback`.
3. **Settings** → Advanced → **Grant Types** : cocher `Authorization Code`.
4. Copier `Domain`, `Client ID`, `Client Secret` :
   ```bash
   OIDC_ISSUER=https://<your-tenant>.eu.auth0.com/
   OIDC_CLIENT_ID=<client_id>
   OIDC_CLIENT_SECRET=<client_secret>
   ```
5. Pour les groupes : **Actions** → **Login** → ajouter une action qui ajoute `https://p2pfd.example.com/groups` au token (custom claim). Adapter `parse_userinfo()` si besoin.

## Keycloak (self-hosted)

1. Realm → **Clients** → **Create** → Client ID = `p2pfd`.
2. Settings : Access Type = **confidential**, Valid Redirect URIs = `https://api.<domain>/oidc/callback`.
3. **Credentials** → copier le secret.
4. URLs :
   ```bash
   OIDC_ISSUER=https://keycloak.<domain>/realms/<realm-name>
   ```
5. **Mappers** → ajouter un mapper "Group Membership" type `Group` → claim name `groups`.

## Tester en local

```bash
export OIDC_ISSUER="https://login.microsoftonline.com/<tenant>/v2.0"
export OIDC_CLIENT_ID="..."
export OIDC_CLIENT_SECRET="..."
export OIDC_REDIRECT_URI="http://localhost:8000/oidc/callback"
export OIDC_SESSION_SECRET="$(python -c 'import secrets; print(secrets.token_urlsafe(48))')"
export OIDC_POST_LOGIN_URL="http://localhost:8501/"

uvicorn p2p_fraud.api.main:app --port 8000 &
streamlit run streamlit_app.py --server.port 8501 &

# Aller sur http://localhost:8501/, cliquer "🔑 Se connecter (OIDC)"
# → redirige vers l'IdP → login → callback → session ouverte
# → la page Collaboration affiche l'identité OIDC + rôle mappé
```

## Vérification post-déploiement

```bash
# 1. Discovery accessible
curl -fsS "$OIDC_ISSUER/.well-known/openid-configuration" | jq .issuer

# 2. /oidc/login redirige vers l'IdP
curl -sI "https://api.<domain>/oidc/login" | grep -i location
# → Location: https://login.microsoftonline.com/<tenant>/oauth2/v2.0/authorize?...

# 3. /oidc/me sans session
curl -s "https://api.<domain>/oidc/me"
# → {"detail":"Non authentifié."}
```

## Sécurité

- **`OIDC_SESSION_SECRET`** : ≥ 32 octets aléatoires, **différent par environnement** (dev/staging/prod). Rotation possible mais déconnecte tous les utilisateurs actifs.
- **HTTPS obligatoire en prod** : le cookie de session est marqué `secure=true` quand le scheme est `https`. Sans TLS, les cookies ne sont pas envoyés et le login échoue silencieusement.
- **Domaine partagé api + streamlit** : indispensable pour que Streamlit lise le cookie de session. Mettre les deux derrière le même reverse proxy / Load Balancer.
- **PKCE obligatoire** : implémenté en S256 (SHA-256). Compatible avec tous les IdPs majeurs.
- **Nonce + state** : générés aléatoirement à chaque login, stockés dans un cookie state signé (TTL 10 min).
