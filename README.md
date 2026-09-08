# Dashboard d'analyse nutrition/santé

Analyse d'un jeu de données synthétique de suivi nutritionnel (2500 patients) et
construction d'un dashboard de visualisation pour un service de diététique.

> Données synthétiques — aucune donnée réelle de patient. Le dashboard est un outil de
> visualisation, sans recommandation clinique automatisée.

## Structure

```
data/patients_nutrition.csv           Jeu de données source (15 colonnes)
data/patients_nutrition_clean.csv     Jeu nettoyé (sortie de l'étape 2, 18 colonnes)
data/patients_nutrition_features.csv  Jeu enrichi (sortie de l'étape 3, 27 colonnes)
notebooks/01_eda.ipynb                Analyse exploratoire (exécutée)
notebooks/02_cleaning.ipynb           Nettoyage (exécuté)
notebooks/03_features.ipynb           Feature engineering (exécuté)
_build_01_eda.py                      Générateur du notebook d'EDA
_build_02_cleaning.py                 Générateur du notebook de nettoyage
_build_03_features.py                 Générateur du notebook de feature engineering
app.py                                Dashboard Streamlit
requirements.txt                      Dépendances d'exécution du dashboard
DECISIONS.md                          Journal des décisions méthodologiques
```

## Lancer le dashboard

```
pip install -r requirements.txt
streamlit run app.py
```

Lit `data/patients_nutrition_features.csv`. Filtres (barre latérale) : régime,
pathologie, catégorie d'IMC, tranche d'âge, et un interrupteur « exclure les valeurs
imputées / scores incomplets » (activé par défaut). L'ensemble de l'application est
épinglé en thème clair (`.streamlit/config.toml`) : les graphiques sont dessinés en
clair et le reste de l'interface s'aligne dessus.

## Repères de lecture — à ne pas interpréter cliniquement

Le dashboard est un outil de **visualisation de patientèle**. Il ne calcule aucune
cible individuelle et n'émet aucune recommandation.

- **Seuil sodium ≈ 2300 mg/j** (ligne de référence de l'onglet « Apports vs cible ») :
  c'est un **repère de population générale** (OMS), affiché comme simple point de
  comparaison lisible sur un graphique agrégé. Ce **n'est pas** une cible personnalisée
  par pathologie : les recommandations réelles sont plus basses et variables selon le
  contexte (souvent < 2000 mg/j en cas d'hypertension ou d'insuffisance rénale), et
  dépendent du traitement et du suivi médical. Un lecteur non averti ne doit pas lire
  « au-dessus de 2300 = anormal » au niveau d'un patient.
- **Référence protéique 0,8 g/kg/j** : apport de référence adulte (OMS/EFSA), même
  statut — repère populationnel, pas une prescription (les besoins montent notamment
  chez le sujet âgé ou dénutri).
- **Drapeau « Sodium élevé (cardio-rénal) »** : il se déclenche au-delà de 3500 mg/j
  pour les patients hypertendus ou insuffisants rénaux. C'est un **signal de tri
  interne** pour prioriser la revue de dossiers, pas un seuil de décision clinique.

## Déploiement

Application publiée sur **Streamlit Community Cloud** (`app.py` comme point d'entrée).
Aucun secret n'est requis : les données sont synthétiques, statiques et versionnées
dans le dépôt. Voir `DECISIONS.md` § Étape 6 pour les choix de configuration.

## Scripts générateurs de notebooks

Les notebooks du dossier `notebooks/` sont des artefacts générés, pas des sources. Chaque
`_build_0X_*.py` définit la liste ordonnée des cellules d'un notebook, l'exécute de bout
en bout et écrit le `.ipynb` correspondant. Pour modifier un notebook, on édite le script
puis on le relance :

```
python _build_01_eda.py        # régénère notebooks/01_eda.ipynb
python _build_02_cleaning.py    # régénère notebooks/02_cleaning.ipynb + data/patients_nutrition_clean.csv
python _build_03_features.py    # régénère notebooks/03_features.ipynb + data/patients_nutrition_features.csv
```

Cela garantit un notebook reproductible dont les sorties correspondent toujours au code
affiché.

## Dépendances

- Dashboard (`requirements.txt`) : `streamlit`, `plotly`, `pandas`.
- Notebooks : `pandas`, `numpy`, `scipy`, `matplotlib`, `seaborn`, `nbformat`, `nbclient`, `ipykernel`.

## Avancement

- [x] Étape 1 — EDA
- [x] Étape 2 — Nettoyage
- [x] Étape 3 — Feature engineering
- [x] Étape 4 — Conception du dashboard
- [x] Étape 5 — Construction Streamlit
- [ ] Étape 6 — Déploiement
- [ ] Étape 7 — Documentation finale
