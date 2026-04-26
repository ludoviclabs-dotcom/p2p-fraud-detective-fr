# Script vidéo Loom — démo 5 minutes

**Cible** : recruteurs Big 4 / banque / CAC 40, RCSI, responsables audit interne.
**Durée cible** : 4-5 minutes. Caméra optionnelle. **OBS / Loom écran + voix off**.

---

## Ouverture (0:00 – 0:30)

> « Bonjour, je suis Ludovic Labeaut, je vous présente **P2P Fraud Detective FR** —
> un outil open-source que j'ai construit pour détecter la fraude fournisseurs
> dans les ETI françaises. C'est un mini-MindBridge en Python, qui exploite
> nativement Sirene v3 et la DECP, ce qu'aucun outil anglo-saxon ne fait.
> Démo en 5 minutes. »

**À l'écran** : page d'accueil Streamlit avec les KPI (7 détecteurs, 2 sources publiques FR).

---

## 1. Upload + dataset synthétique (0:30 – 1:15)

- Page **📤 Upload**, onglet « Générer un dataset ».
- Garder 50 000 factures, 5 000 fournisseurs, seed 42.
- Cliquer **🎲 Générer**.

**Voix off** :
> « Je génère un dataset de 50 000 factures réalistes avec **7 patterns de fraude
> étiquetés** (doublons exact + fuzzy, sous-seuils, shell companies, anneaux IBAN,
> outliers, écritures week-end). Cette ground truth me permet de mesurer la
> performance de chaque détecteur en F1 — un argument différenciant que peu
> de portfolios audit-data offrent. »

---

## 2. Benford (1:15 – 2:00)

- Page **🔢 Benford**, onglet F2D.

**Voix off** :
> « Le test des 2 premiers chiffres est le plus diagnostique en audit selon Nigrini.
> Ici le MAD est calculé, l'interprétation est conforme aux seuils académiques.
> En bas de la page, les **factures les plus suspectes** — top 1 % des chiffres
> sur-représentés. »

---

## 3. Doublons fuzzy (2:00 – 2:30)

- Page **♊ Doublons**.
- Slider à 90, fenêtre date 2 jours, lancer.

**Voix off** :
> « Le détecteur fait du **bucket par fenêtre date + RapidFuzz token_set_ratio**
> sur le nom fournisseur. Sur ce dataset il atteint un **Recall de 100 %** sur
> les doublons étiquetés — toutes les fraudes injectées sont détectées. »

---

## 4. Sirene cross-check (2:30 – 3:00)

- Page **🇫🇷 Sirene check** (avec token configuré).

**Voix off** :
> « Je vérifie chaque SIREN contre l'API officielle INSEE : statut administratif,
> date de création vs première facture, code APE. Le client respecte le quota
> 30 req/s, cache les résultats 30 jours en SQLite local pour ne pas re-payer
> les appels. **C'est ce que les Big 4 et MindBridge ne font pas par défaut**. »

---

## 5. Isolation Forest + Anneaux (3:00 – 3:45)

- Page **🤖 Anomalies ML** : contamination 1 %, lancer.
- Page **🕸️ Anneaux fraude** : cluster_min 3, lancer.

**Voix off** :
> « Pipeline scikit-learn — StandardScaler + IsolationForest sur 6 features
> comportementales. Le score est normalisé 0-100, le top 1 % est flaggé.
> Et le détecteur graphe NetworkX trouve les **anneaux d'IBAN partagés** entre
> fournisseurs — Recall mesuré à 100 % sur la ground truth. C'est le signal
> le plus fort de fraude organisée. »

---

## 6. Synthèse + export (3:45 – 4:30)

- Page **📊 Synthèse / export**.

**Voix off** :
> « Le risk engine consolide les 6 détecteurs en un score 0-100 par facture
> via des pondérations YAML éditables. Trois exports : CSV, **workbook Excel
> auditeur** avec hyperliens internes vers les pièces, et **bundle Parquet**
> pour le dashboard Power BI joint au repo. »

- Cliquer télécharger Excel, ouvrir dans Excel pour montrer les 4 onglets et
  les hyperliens des findings.

---

## Closing (4:30 – 5:00)

> « 4 week-ends de développement, 60+ tests pytest avec ground truth, F1 mesurés
> par détecteur, déployable en un clic sur Streamlit Cloud. Le code est sur
> GitHub, MIT. La méthodologie d'audit est mappée sur ISA 240, AS 2401, Sapin 2,
> DORA. Si vous recrutez des profils audit × data en 2026, on peut parler. »

**À l'écran** : repo GitHub URL + LinkedIn.

---

## Checklist enregistrement

- [ ] Token Sirene configuré dans `.env`
- [ ] Tests verts (`pytest -q`)
- [ ] Streamlit lancé en local (`streamlit run streamlit_app.py`)
- [ ] Dataset 50k pré-généré pour ne pas attendre
- [ ] Power BI Desktop ouvert avec le `.pbix` rafraîchi (optionnel — bonus 30 s)
- [ ] Mode **Présentateur** activé (pas de notifications)
- [ ] Résolution 1920×1080, zoom navigateur 110 %

## Post-production

- Ajouter une intro texte 3 s : « P2P Fraud Detective FR · Ludovic Labeaut · 2026 »
- Ajouter URL GitHub en bas de l'écran sur les 5 dernières secondes
- Couper les silences, garder le rythme < 5 min
- Uploader sur Loom + lien dans le README + LinkedIn post
