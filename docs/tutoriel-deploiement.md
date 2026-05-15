# Tutoriel déploiement — P2P Fraud Detective FR v0.6.0

Guide étape par étape pour mettre la plateforme en production sur une
infrastructure gratuite : **Neon** (PostgreSQL) + **Hugging Face Spaces**
(backend FastAPI) + **Vercel** (frontend Next.js).

**Temps total estimé : 30 à 45 minutes**

---

## Vue d'ensemble de l'architecture cible

```
Navigateur utilisateur
        │
        ▼
┌───────────────────────┐
│  Vercel               │   ← Frontend Next.js 15 (gratuit)
│  apps/web             │     URL : https://p2pfd.vercel.app
└──────────┬────────────┘
           │ REST API (NEXT_PUBLIC_API_URL)
           ▼
┌───────────────────────┐
│  Hugging Face Spaces  │   ← Backend FastAPI (gratuit, 16 GB RAM)
│  Docker (Dockerfile)  │     URL : https://your-space.hf.space
└──────────┬────────────┘
           │ DATABASE_URL
           ▼
┌───────────────────────┐
│  Neon PostgreSQL      │   ← Base de données (gratuit, 0.5 GB)
│  (cloud managé)       │     Régions EU disponibles
└───────────────────────┘
```

---

## Prérequis — comptes à créer avant de commencer

Créez les comptes gratuits suivants (5 minutes) :

| Service | URL inscription | Usage |
|---|---|---|
| **Neon** | https://neon.tech | Base PostgreSQL managée |
| **Hugging Face** | https://huggingface.co/join | Backend FastAPI Docker |
| **Vercel** | https://vercel.com/signup | Frontend Next.js |
| **INSEE** | https://api.insee.fr/catalogue/ | Token SIRENE (gratuit) |

> **Note** : Pour Vercel et Hugging Face, l'inscription avec votre compte
> GitHub est la méthode la plus rapide — elle connecte directement le dépôt.

---

## Étape 1 — Obtenir le token SIRENE (INSEE)

Le token SIRENE permet de vérifier les entreprises fournisseurs via l'API
officielle INSEE. Sans lui, la plateforme fonctionne mais la page
"Vérification Sirene" renvoie des erreurs 401.

1. Rendez-vous sur **https://api.insee.fr/catalogue/**
2. Cliquez sur **S'identifier** → créez un compte INSEE
3. Une fois connecté, allez dans **Mes applications** → **Ajouter une application**
4. Nom : `P2P Fraud Detective` — cochez l'API **Sirene v3**
5. Cliquez **Créer** → vous obtenez une clé consommateur et un secret
6. Générez votre **Bearer token** :

```bash
# Sur votre machine locale (remplacez les valeurs entre guillemets)
curl -X POST https://api.insee.fr/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials" \
  -u "VOTRE_CLE_CONSOMMATEUR:VOTRE_SECRET"
```

La réponse contient `"access_token": "votre_token_ici"`.

**Conservez ce token** — vous en aurez besoin à l'étape 3.

---

## Étape 2 — Créer la base de données PostgreSQL (Neon)

1. Connectez-vous sur **https://neon.tech**
2. Cliquez **Create project**
3. Remplissez :
   - **Project name** : `p2pfd-prod`
   - **Database name** : `p2pfd`
   - **Region** : choisissez `AWS eu-west-3 (Paris)` pour minimiser la latence
4. Cliquez **Create project**

Neon crée automatiquement un utilisateur et une base. Sur la page du projet :

5. Cliquez sur l'onglet **Connection Details**
6. Dans le menu déroulant, sélectionnez **psycopg2** (format SQLAlchemy)
7. Copiez la chaîne de connexion — elle ressemble à :

```
postgresql://p2pfd_owner:AbCdEfGh12345@ep-bold-moon-a2b3c4d5.eu-west-3.aws.neon.tech/p2pfd?sslmode=require
```

**Conservez cette URL** — c'est votre `DATABASE_URL`.

### Vérifier la connexion (optionnel, sur votre machine locale)

Si vous avez Python 3.12 et le projet cloné localement :

```bash
cd p2p-fraud-detective-fr
pip install -e ".[dev]"

export DATABASE_URL="postgresql://p2pfd_owner:...@ep-....neon.tech/p2pfd?sslmode=require"

# Applique le schéma de base (tables cases, audit_log, alerts)
alembic upgrade head
```

Résultat attendu :
```
INFO  [alembic.runtime.migration] Running upgrade  -> a1b2c3d4e5f6, initial schema
```

> Si vous n't avez pas Python en local, ne vous inquiétez pas : Alembic
> s'exécute automatiquement au démarrage du container Hugging Face Spaces
> (voir Étape 3).

---

## Étape 3 — Déployer le backend sur Hugging Face Spaces

Hugging Face Spaces permet d'héberger gratuitement un container Docker avec
16 GB de RAM — parfait pour notre backend FastAPI.

### 3.1 Créer le Space

1. Connectez-vous sur **https://huggingface.co**
2. Cliquez sur votre avatar → **New Space**
3. Remplissez :
   - **Space name** : `p2pfd-api`
   - **License** : MIT
   - **SDK** : choisissez **Docker** (pas Streamlit, pas Gradio)
   - **Visibility** : `Public` (le plan gratuit impose le public pour Docker)
4. Cliquez **Create Space**

Hugging Face crée un dépôt Git vide pour ce Space.

### 3.2 Connecter votre dépôt GitHub au Space

Hugging Face Spaces peut se synchroniser avec GitHub via des GitHub Actions.
Votre dépôt contient déjà le workflow `.github/workflows/hf-sync.yml`.

1. Allez dans votre Space HF → onglet **Settings**
2. Section **Repository secrets** → ajoutez un secret :
   - **Name** : `HF_TOKEN`
   - **Value** : votre token Hugging Face (Profile → Settings → Access Tokens → New token avec scope `write`)
3. Sur GitHub, dans votre dépôt → **Settings** → **Secrets and variables** → **Actions** → **New repository secret** :
   - **Name** : `HF_TOKEN`
   - **Value** : le même token HF

Le workflow se déclenche automatiquement à chaque push sur `main` et synchronise le code vers HF Spaces.

> **Alternative manuelle** : si vous ne voulez pas configurer GitHub Actions,
> vous pouvez pousser directement vers le dépôt HF Space :
> ```bash
> git remote add space https://huggingface.co/spaces/VOTRE_USERNAME/p2pfd-api
> git push space main
> ```

### 3.3 Configurer les variables d'environnement du Space

Dans votre Space HF → **Settings** → **Repository secrets**, ajoutez les variables suivantes une par une :

| Variable | Valeur | Obligatoire |
|---|---|---|
| `DATABASE_URL` | URL PostgreSQL Neon copiée à l'étape 2 | ✅ Oui |
| `SIRENE_API_TOKEN` | Token INSEE de l'étape 1 | ✅ Oui |
| `FRAUD_API_SECRET` | Mot de passe API (inventez-en un fort : `openssl rand -hex 32`) | ✅ Oui |
| `ANTHROPIC_API_KEY` | Clé API Anthropic (pour les narrations LLM) | 🟡 Optionnel |
| `P2P_FRAUD_DATA_KEY` | Clé de chiffrement IBAN (`python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'`) | 🟡 Optionnel |
| `OIDC_SESSION_SECRET` | Secret HMAC sessions (`python -c 'import secrets; print(secrets.token_urlsafe(48))'`) | 🟡 Optionnel |
| `LOG_FORMAT` | `json` | 🟢 Recommandé |
| `LOG_LEVEL` | `INFO` | 🟢 Recommandé |

> **Générer les secrets rapidement** — sur votre terminal local :
> ```bash
> # FRAUD_API_SECRET
> python -c 'import secrets; print(secrets.token_hex(32))'
>
> # P2P_FRAUD_DATA_KEY
> python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())'
>
> # OIDC_SESSION_SECRET
> python -c 'import secrets; print(secrets.token_urlsafe(48))'
> ```

### 3.4 Ajouter le fichier README.md pour HF Spaces

Hugging Face Spaces a besoin d'un fichier `README.md` spécial à la racine
avec des métadonnées YAML. Vérifiez que le `README.md` du dépôt contient
bien ce bloc en tête de fichier :

```yaml
---
title: P2P Fraud Detective FR API
emoji: 🔍
colorFrom: blue
colorTo: indigo
sdk: docker
pinned: false
app_port: 8000
---
```

Si ce bloc est absent, ajoutez-le manuellement en tête du `README.md` et
committez.

### 3.5 Vérifier le démarrage du backend

Une fois le build HF Spaces terminé (2-5 minutes), testez l'endpoint de
santé. L'URL de votre Space est visible dans l'onglet **App** de HF Spaces.

```bash
# Remplacez par votre URL réelle
export API_URL="https://your-username-p2pfd-api.hf.space"

# Test de santé
curl "$API_URL/health"
```

Résultat attendu :
```json
{"status": "ok", "version": "0.6.0", "at": "2026-05-15T10:00:00Z"}
```

```bash
# Test d'authentification (doit retourner 401)
curl "$API_URL/api/v1/cockpit/kpis"
# {"detail": "Not authenticated"}  ← normal, le token n'est pas fourni
```

**Notez l'URL de votre Space** (`https://votre-username-p2pfd-api.hf.space`)
— vous en aurez besoin à l'étape suivante.

---

## Étape 4 — Déployer le frontend sur Vercel

### 4.1 Connecter le dépôt à Vercel

1. Connectez-vous sur **https://vercel.com**
2. Cliquez **Add New... → Project**
3. Sélectionnez votre dépôt GitHub `p2p-fraud-detective-fr`
4. Vercel détecte automatiquement le monorepo. Configurez :
   - **Framework Preset** : `Next.js` (auto-détecté)
   - **Root Directory** : cliquez **Edit** → tapez `apps/web`
   - **Build Command** : `next build` (par défaut, ne pas changer)
   - **Output Directory** : `.next` (par défaut)
5. **Ne cliquez pas encore sur Deploy** — configurez d'abord les variables d'environnement.

### 4.2 Configurer les variables d'environnement Vercel

Toujours sur la page de configuration du projet Vercel, section
**Environment Variables**, ajoutez :

| Variable | Valeur | Environnements |
|---|---|---|
| `NEXT_PUBLIC_API_URL` | URL de votre HF Space (ex: `https://votre-username-p2pfd-api.hf.space`) | Production, Preview, Development |
| `FRAUD_API_SECRET` | Le même `FRAUD_API_SECRET` qu'à l'étape 3.3 | Production, Preview, Development |

> `NEXT_PUBLIC_API_URL` est préfixé `NEXT_PUBLIC_` car il est exposé côté
> client (navigateur). `FRAUD_API_SECRET` reste côté serveur (route API proxy).

### 4.3 Lancer le déploiement

6. Cliquez **Deploy**

Vercel installe les dépendances pnpm, compile le projet TypeScript, et déploie
en ~2-3 minutes. Vous verrez les logs en temps réel.

### 4.4 Vérifier le frontend

Une fois déployé, Vercel vous donne une URL de type `https://p2p-fraud-detective-fr.vercel.app`.

Ouvrez cette URL dans votre navigateur :

- La page d'accueil (Cockpit) doit s'afficher avec les KPIs à zéro (base vide)
- La barre de navigation doit être visible avec tous les modules
- Pas d'erreurs dans la console du navigateur (F12 → Console)

Pour vérifier que le frontend parle bien au backend :

```bash
# Depuis votre terminal, simulez ce que fait le navigateur
curl "https://p2p-fraud-detective-fr.vercel.app/api/uploads" \
  -X POST \
  -H "Content-Type: multipart/form-data"
# Doit retourner une erreur 400 (pas de fichier fourni) — le proxy fonctionne
```

---

## Étape 5 — Premier test end-to-end

Validez que la chaîne complète fonctionne en chargeant le jeu de données
synthétique inclus dans le projet.

### 5.1 Générer le dataset de test (optionnel — déjà présent dans `data/`)

Si vous souhaitez un jeu de données frais (50 000 factures) :

```bash
# Sur votre machine locale
cd p2p-fraud-detective-fr
make dataset-50k
# Génère data/synthetic/dataset_50k.csv
```

Le fichier `data/synthetic/dataset_50k.csv` est déjà inclus dans le dépôt.

### 5.2 Uploader le fichier de test

1. Ouvrez votre frontend Vercel dans le navigateur
2. Allez sur la page **Upload** (icône nuage dans le menu)
3. Glissez-déposez le fichier `data/synthetic/dataset_50k.csv`
4. Vercel proxy → HF Spaces API → parsing + détection automatique

Vous devriez voir :
- La détection du preset `generic CSV`
- Les colonnes mappées au schéma canonique
- Un message de confirmation avec le nombre de factures chargées

### 5.3 Lancer l'analyse

1. Revenez sur le **Cockpit** (`/`)
2. Les KPIs doivent maintenant afficher des chiffres (nombre d'anomalies, fournisseurs, etc.)
3. Naviguez vers **Doublons** → des paires de factures suspectes apparaissent
4. Naviguez vers **Sous-seuils** → des factures juste sous les seuils d'approbation
5. Naviguez vers **Score Explorer** → le waterfall de scoring par fournisseur

---

## Étape 6 — Configurer le déploiement Streamlit (optionnel)

Le frontend Streamlit (v0.5) reste disponible pour les utilisateurs qui
préfèrent l'interface legacy. Il peut être déployé séparément.

### Option A : Hugging Face Spaces (Streamlit natif)

1. Créez un second Space HF → SDK : **Streamlit**
2. Le `Dockerfile.streamlit` sera utilisé automatiquement
3. Ajoutez les mêmes variables d'environnement qu'à l'étape 3.3

### Option B : Docker local (pilote interne)

```bash
# Sur votre serveur ou VM interne
docker build -f Dockerfile.streamlit -t p2pfd-ui:0.6.0 .

docker run -d \
  --name p2pfd-streamlit \
  -p 8501:8501 \
  -e DATABASE_URL="postgresql://..." \
  -e SIRENE_API_TOKEN="..." \
  -e FRAUD_API_SECRET="..." \
  p2pfd-ui:0.6.0
```

Accédez à `http://votre-serveur:8501`

---

## Étape 7 — Configurer l'authentification OIDC (optionnel mais recommandé)

Sans OIDC, la plateforme fonctionne en mode "anonymous OK" — tout le monde
peut accéder. Pour un pilote avec un vrai client, activez l'authentification.

### Avec Microsoft Entra ID (Azure AD)

1. **Portail Azure** → Microsoft Entra ID → **App registrations** → **New registration**
2. Nom : `P2P Fraud Detective FR`
3. Redirect URI : `https://votre-username-p2pfd-api.hf.space/oidc/callback`
4. Créez un **client secret** (Certificates & secrets → New client secret)
5. Récupérez le **Tenant ID** dans Overview

Ajoutez ces variables dans les **secrets HF Spaces** (étape 3.3) :

```
OIDC_ISSUER=https://login.microsoftonline.com/VOTRE_TENANT_ID/v2.0
OIDC_CLIENT_ID=VOTRE_APPLICATION_ID
OIDC_CLIENT_SECRET=VOTRE_CLIENT_SECRET
OIDC_REDIRECT_URI=https://votre-username-p2pfd-api.hf.space/oidc/callback
OIDC_SCOPES=openid email profile
OIDC_POST_LOGIN_URL=https://p2p-fraud-detective-fr.vercel.app/
OIDC_ROLE_MAP={"DG-Audit":"admin","Audit-Senior":"manager","Audit-Junior":"analyst"}
```

Consultez `docs/oidc-setup.md` pour le guide complet Auth0 / Keycloak.

---

## Récapitulatif des URLs et secrets

À la fin de ce tutoriel, vous devez avoir noté les informations suivantes :

| Élément | Exemple | Usage |
|---|---|---|
| URL Backend HF Spaces | `https://votreuser-p2pfd-api.hf.space` | `NEXT_PUBLIC_API_URL` dans Vercel |
| URL Frontend Vercel | `https://p2pfd.vercel.app` | Accès navigateur |
| `DATABASE_URL` | `postgresql://...@...neon.tech/p2pfd?sslmode=require` | HF Spaces secret |
| `SIRENE_API_TOKEN` | `eyJ0eXAiOiJKV1QiLCAiYWxnI...` | HF Spaces secret |
| `FRAUD_API_SECRET` | `3f8a9b2c1d4e5f6...` (hex 64 chars) | HF Spaces + Vercel |
| `P2P_FRAUD_DATA_KEY` | `gAAAAAB...=` (Fernet key) | HF Spaces secret |

---

## Résolution des problèmes courants

### Le backend HF Spaces ne démarre pas

**Symptôme** : Le Space reste en statut "Building" ou affiche une erreur.

**Causes fréquentes** :
- `DATABASE_URL` manquante ou mal formée → vérifiez dans Settings → Secrets
- Le `README.md` ne contient pas le bloc YAML frontmatter avec `app_port: 8000`
- Le `Dockerfile` a une dépendance système manquante

**Diagnostic** :
```
HF Spaces → Logs → Filtrez sur "ERROR"
```

### Le frontend affiche "Failed to fetch"

**Symptôme** : Le Cockpit affiche une erreur réseau.

**Cause** : `NEXT_PUBLIC_API_URL` pointe vers une mauvaise URL ou le backend
n'est pas démarré.

**Solution** :
1. Vérifiez que `curl https://votre-space.hf.space/health` répond
2. Dans Vercel → Project Settings → Environment Variables → vérifiez `NEXT_PUBLIC_API_URL`
3. Redéployez Vercel après correction : Deployments → ⋯ → Redeploy

### Erreur "alembic upgrade head" — table existe déjà

**Symptôme** : Le container démarre mais les logs montrent une erreur Alembic.

**Cause** : La migration a déjà été appliquée (normal au redémarrage).

**Solution** : C'est sans danger — Alembic vérifie la version courante et ne
ré-applique pas les migrations déjà passées. Ignorez ce message.

### Le token SIRENE retourne 401

**Cause** : Le token INSEE expire après un certain temps.

**Solution** : Régénérez un token via l'API INSEE (étape 1, commande `curl`)
et mettez à jour le secret dans HF Spaces.

---

## Prochaines étapes après le déploiement

Une fois la plateforme en ligne, voici les actions recommandées :

1. **Calibrage sur données réelles** (1-2 jours) : chargez un export AP réel
   du client et ajustez les seuils dans la page **Gouvernance** (poids YAML)
2. **Formation utilisateurs** : partagez l'URL Vercel et utilisez le
   **Tour guidé** (page `/tour`) qui présente les 5 étapes clés en ~10 minutes
3. **Activer les alertes** : configurez `SLACK_WEBHOOK_URL` dans HF Spaces
   pour recevoir les alertes de nouvelles anomalies en temps réel
4. **Activer le scheduler** : pour une analyse automatique quotidienne,
   déployez le `Dockerfile.scheduler` sur un second Space HF avec
   `CMD ["python", "-m", "p2p_fraud.scheduler", "--daily", "06:00"]`

---

*Tutoriel v0.6.0 — Mai 2026*
