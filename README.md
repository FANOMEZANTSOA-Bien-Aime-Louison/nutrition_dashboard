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
imputées / scores incomplets » (activé par défaut). Les graphiques sont rendus en
thème clair et ne suivent pas le mode sombre de Streamlit.

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
