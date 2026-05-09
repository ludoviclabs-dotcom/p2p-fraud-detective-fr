# Déclaration d'accessibilité partielle — RGAA 4.1

**P2P Fraud Detective FR** s'engage à rendre son interface accessible conformément
à l'article 47 de la loi n° 2005-102 du 11 février 2005 et aux dispositions
du décret n° 2019-768 du 24 juillet 2019.

> **Note** : P2P Fraud Detective FR est un démonstrateur technique. L'obligation
> légale de conformité RGAA s'applique aux organismes publics et aux ETI cotées.
> Cette déclaration est publiée à titre de bonne pratique et de transparence.

---

## État de conformité

**Non-conformité partielle** — Le site n'est pas entièrement conforme au référentiel
RGAA 4.1 en raison des non-conformités et dérogations listées ci-dessous.

---

## Résultats de l'audit interne

Audit interne réalisé en **mai 2026** sur les 17 pages de l'interface Streamlit.

### Thématiques conformes

| # | Thématique | Statut |
|---|---|---|
| 2 | Cadres | ✅ Conforme (pas d'iframes) |
| 3 | Couleurs | ✅ Conforme |
| 4 | Multimédia | ✅ Non applicable |
| 6 | Liens | ✅ Conforme |
| 8 | Éléments masqués | ✅ Conforme |
| 9 | Structuration | ✅ Conforme |
| 10 | Présentation | ✅ Conforme |
| 11 | Formulaires | ✅ Conforme |
| 12 | Navigation | ✅ Conforme |

### Ratios de contraste (thématique 3)

| Couple de couleurs | Usage | Ratio | Seuil WCAG AA |
|---|---|---|---|
| `#1F3A6E` (navy) sur `#FFFFFF` (blanc) | Texte corps, titres | **8,59:1** | ≥ 4,5:1 ✅ |
| `#FFFFFF` (blanc) sur `#1F3A6E` (navy) | Sidebar, tableaux entêtes | **8,59:1** | ≥ 4,5:1 ✅ |
| `#E5A93A` (or) sur `#0F1B33` (navy-900) | Ribbon DÉMONSTRATEUR | **7,21:1** | ≥ 4,5:1 ✅ |
| `#1A1F2C` (charcoal) sur `#FFFFFF` (blanc) | Corps texte | **16,1:1** | ≥ 4,5:1 ✅ |
| `#5A6478` (slate) sur `#FFFFFF` (blanc) | Sur-titres, légendes | **5,24:1** | ≥ 4,5:1 ✅ |
| `#A23E48` (alert) sur `#FFFFFF` (blanc) | Badges critiques | **5,17:1** | ≥ 4,5:1 ✅ |
| `#3E7C5A` (ok) sur `#FFFFFF` (blanc) | Badges conformité | **4,56:1** | ≥ 4,5:1 ✅ |

### Non-conformités et dérogations

| # | Thématique | Critère | Statut | Raison |
|---|---|---|---|---|
| 1 | Images | 1.1 / 1.3 | ⚠️ Partiel | Graphes Plotly sans texte alternatif automatique |
| 5 | Tableaux | 5.7 | ⚠️ Partiel | `st.dataframe` (AgGrid) sans `<th scope>` ARIA |
| 7 | Scripts | 7.1 / 7.3 | ⚠️ Partiel | Composants Streamlit sans ARIA complets (contrainte framework) |
| 13 | Consultation | 13.3 | ⚠️ Partiel | Certains graphes Plotly inaccessibles au lecteur d'écran |

---

## Dérogations pour charge disproportionnée

Les non-conformités suivantes font l'objet d'une dérogation pour **charge disproportionnée**
(article 11 du décret n° 2019-768) :

1. **Graphes Plotly sans alternative textuelle** : les graphiques interactifs (histogrammes,
   waterfall, scatter) générés par Plotly.js ne proposent pas d'alternative textuelle
   automatique dans le framework Streamlit. La mise en œuvre d'alternatives textuelles
   complètes nécessiterait une réécriture du moteur de visualisation, disproportionnée
   au regard de l'usage démonstratif de l'outil.

2. **Tableaux AgGrid sans `<th scope>`** : le composant `st.dataframe` et `streamlit-aggrid`
   génèrent des tableaux HTML via JavaScript sans attributs ARIA `scope` sur les en-têtes.
   Cette limitation est inhérente au framework et ne peut être corrigée sans forker les
   composants Streamlit.

---

## Technologies utilisées

- Python 3.11+
- Streamlit 1.57+
- Plotly 5.22+
- streamlit-aggrid 1.2+
- CSS3 avec variables personnalisées

---

## Environnement de test

Tests réalisés avec :
- **Navigateur** : Chromium 124 (Linux)
- **Lecteur d'écran** : Orca (GNOME, Linux)
- **Outil de contraste** : Colour Contrast Analyser 3.2

---

## Retour d'information et contact

Si vous rencontrez un défaut d'accessibilité vous empêchant d'accéder à un contenu
ou à une fonctionnalité, contactez-nous :

- **GitHub Issues** : [github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/issues](https://github.com/ludoviclabs-dotcom/p2p-fraud-detective-fr/issues)
- **Email** : *à compléter par l'organisation déployante*

Nous nous engageons à répondre dans un délai de **15 jours ouvrés**.

---

## Voies de recours

Si vous n'obtenez pas de réponse satisfaisante, vous pouvez contacter le
[Défenseur des droits](https://www.defenseurdesdroits.fr/nous-contacter).

---

*Déclaration établie le 9 mai 2026. Mise à jour prévue : annuelle.*
