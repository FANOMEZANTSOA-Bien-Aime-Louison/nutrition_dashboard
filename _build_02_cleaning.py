"""Generate and execute notebooks/02_cleaning.ipynb from source cells defined here.

The notebook is a build artifact: edit this file, then run `python _build_02_cleaning.py`
to regenerate and re-execute it. Reads data/patients_nutrition.csv, writes
data/patients_nutrition_clean.csv.
"""

from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "notebooks" / "02_cleaning.ipynb"

CELLS = [
    ("markdown", """# Étape 2 — Nettoyage

Entrée : `data/patients_nutrition.csv` (brut, 2500 lignes).
Sortie : `data/patients_nutrition_clean.csv`.

Périmètre : correction de type, traitement des valeurs manquantes colonne par colonne,
requalification des valeurs de saisie impossibles en valeurs manquantes puis imputation,
contrôle des bornes sur les autres colonnes. Aucune ligne n'est supprimée.
"""),

    ("code", """import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)
sns.set_theme(style="whitegrid")

raw = pd.read_csv("../data/patients_nutrition.csv")
df = raw.copy()
raw.shape
"""),

    ("markdown", "## 1. Correction de type"),

    ("code", """df["admission_date"] = pd.to_datetime(df["admission_date"])
df["admission_date"].dtype
"""),

    ("markdown", """## 2. `condition` — 25 valeurs manquantes

Le manque signifie « pathologie inconnue » ; il est distinct de la modalité `Aucune`
(pathologie connue comme absente). Requalification en modalité explicite `Non renseigné`.
"""),

    ("code", """print("Avant :")
print(df["condition"].value_counts(dropna=False))

df["condition"] = df["condition"].fillna("Non renseigné")

print("\\nAprès :")
print(df["condition"].value_counts(dropna=False))
"""),

    ("markdown", """## 3. Valeurs de saisie impossibles → valeurs manquantes

Distinction appliquée :
- **erreur de saisie** = valeur physiquement impossible (négative) ou incompatible avec
  toute alimentation (apport quasi nul) → requalifiée en `NaN`, puis imputée en section 5 ;
- **valeur extrême réelle** = rare mais atteignable → conservée (voir section 4).

Seuils : `daily_protein_g` < 5 g/j ; `daily_sodium_mg` < 100 mg/j.
"""),

    ("code", """protein_bad = df["daily_protein_g"] < 5
sodium_bad = df["daily_sodium_mg"] < 100

print("daily_protein_g < 5 g/j :", int(protein_bad.sum()))
print(raw.loc[protein_bad, ["patient_id", "diet_type", "daily_calories", "daily_protein_g"]])
print("\\ndaily_sodium_mg < 100 mg/j :", int(sodium_bad.sum()))
print(raw.loc[sodium_bad, ["patient_id", "diet_type", "condition", "daily_sodium_mg"]])

df.loc[protein_bad, "daily_protein_g"] = np.nan
df.loc[sodium_bad, "daily_sodium_mg"] = np.nan
"""),

    ("markdown", """## 4. Contrôle de plausibilité des `daily_sodium_mg` élevés

Vérification que les 20 valeurs > 5000 mg/j sont des valeurs réelles et non des erreurs
avant de décider de les garder.
"""),

    ("code", """s = df["daily_sodium_mg"].dropna().sort_values()
print("30 plus hautes valeurs de sodium (mg/j) :")
print(s.tail(30).round().tolist())
print()
print("Pas de rupture nette entre le corps de la distribution et la queue :")
print("p95 =", round(s.quantile(0.95)), " p99 =", round(s.quantile(0.99)), " max =", round(s.max()))

hi = df[df["daily_sodium_mg"] > 5000]
print("\\nRépartition des", len(hi), "valeurs > 5000 mg/j :")
print(hi.groupby("diet_type").size())
print(hi.groupby("condition").size())
"""),

    ("code", """fig, axes = plt.subplots(1, 2, figsize=(13, 3.6))
axes[0].hist(df["daily_sodium_mg"].dropna(), bins=60, color="#2980b9", edgecolor="white")
axes[0].set_title("daily_sodium_mg (échelle linéaire)")
axes[0].axvline(5000, color="#c0392b", ls="--", lw=1)
axes[1].hist(df["daily_sodium_mg"].dropna(), bins=60, color="#2980b9", edgecolor="white")
axes[1].set_yscale("log")
axes[1].set_title("daily_sodium_mg (axe y log)")
axes[1].axvline(5000, color="#c0392b", ls="--", lw=1)
plt.tight_layout()
plt.show()
"""),

    ("markdown", """Queue continue, sans discontinuité (pas de saut compatible avec une erreur d'unité ou
un facteur 10), valeurs consommables avec une alimentation très transformée, réparties
sur tous les régimes et pathologies. **Conservées telles quelles.**
"""),

    ("markdown", """## 5. Imputation des valeurs manquantes numériques

Trois colonnes : `daily_protein_g`, `daily_sodium_mg`, `weight_change_pct`.

Choix de la granularité de la médiane (globale vs par `diet_type`) décidé sur preuve :
test de Kruskal-Wallis des différences entre régimes, et corrélations avec les autres
variables numériques (pour une éventuelle imputation par modèle).
"""),

    ("code", """num_impute = ["daily_protein_g", "daily_sodium_mg", "weight_change_pct"]

by_diet = df.groupby("diet_type")[num_impute].median().round(2)
print("Médianes par diet_type :")
print(by_diet)
print("\\nÉcart max entre régimes :")
print((by_diet.max() - by_diet.min()).round(2))

print("\\nKruskal-Wallis (H0 : même distribution entre régimes) :")
for col in num_impute:
    groups = [g[col].dropna().values for _, g in df.groupby("diet_type")]
    print(f"  {col:20s} p = {stats.kruskal(*groups).pvalue:.2e}")

print("\\nCorrélations avec les autres numériques :")
print(df[num_impute + ["age", "bmi", "daily_calories", "follow_up_weeks"]].corr()
        .loc[num_impute, ["age", "bmi", "daily_calories", "follow_up_weeks"]].round(3))
"""),

    ("markdown", """`daily_protein_g` (p = 0,56) et `daily_sodium_mg` (p = 0,31) : aucune différence entre
régimes → **médiane globale**. `weight_change_pct` (p ≈ 3e-34) : forte différence
(le régime hypocalorique fait perdre plus de poids) → **médiane par `diet_type`**, pour
ne pas effacer cet effet sur les lignes imputées. Corrélations toutes ≈ 0 → imputation
par modèle (KNN, régression) sans intérêt.
"""),

    ("code", """before = df[num_impute].copy()

# médiane globale
for col in ["daily_protein_g", "daily_sodium_mg"]:
    df[col + "_imputed"] = df[col].isna()
    df[col] = df[col].fillna(df[col].median())

# médiane par diet_type
df["weight_change_pct_imputed"] = df["weight_change_pct"].isna()
df["weight_change_pct"] = df.groupby("diet_type")["weight_change_pct"].transform(
    lambda s: s.fillna(s.median())
)

print("Médianes globales :", df["daily_protein_g"].median().round(2),
      "g /", df["daily_sodium_mg"].median().round(0), "mg")
print("\\nMédianes de weight_change_pct par diet_type utilisées pour l'imputation :")
print(before.assign(diet_type=df["diet_type"]).groupby("diet_type")["weight_change_pct"].median().round(2))
print("\\nNombre de valeurs imputées par colonne :")
print(df[[c + "_imputed" for c in num_impute]].sum())
"""),

    ("code", """fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, col in zip(axes, num_impute):
    ax.hist(before[col].dropna(), bins=40, alpha=0.6, label="avant", color="#7f8c8d", edgecolor="white")
    ax.hist(df[col], bins=40, alpha=0.6, label="après imputation", color="#c0392b", edgecolor="white")
    ax.set_title(col)
    ax.legend()
fig.suptitle("Effet de l'imputation par la médiane (pic artificiel à la médiane)", y=1.02)
plt.tight_layout()
plt.show()

std_tbl = pd.DataFrame({
    "std_avant": before.std(),
    "std_apres": df[num_impute].std(),
}).assign(reduction_pct=lambda t: ((1 - t.std_apres / t.std_avant) * 100).round(1))
print(std_tbl)

print("\\nweight_change_pct moyen par diet_type — effet préservé après imputation :")
print(pd.DataFrame({
    "avant": before.assign(d=df["diet_type"]).groupby("d")["weight_change_pct"].mean(),
    "apres": df.groupby("diet_type")["weight_change_pct"].mean(),
}).round(3))
"""),

    ("markdown", """## 6. Contrôle des bornes sur les autres colonnes

Colonnes citées au brief (`age`, `bmi`, `daily_calories`) et les colonnes de mesure
restantes. On cherche des valeurs impossibles, pas des valeurs rares.
"""),

    ("code", """ranges = df[["age", "height_cm", "weight_kg", "bmi", "daily_calories",
             "follow_up_weeks", "nutritionist_visits"]].agg(["min", "max"]).T
ranges["commentaire"] = [
    "18-84 : plage adulte plausible",
    "145-200 : plausible",
    "40-100.3 : plausible",
    "15-36.6 : 15 = maigreur sevère mais réelle, pas d'impossibilité",
    "900-2978 : 900 = régime hypocalorique encadré, plausible",
    "1-25 semaines : plausible",
    "0-10 visites : plausible",
]
ranges
"""),

    ("code", """print("Lignes entièrement dupliquées :", int(df.duplicated().sum()))
print("patient_id dupliqués :", int(df["patient_id"].duplicated().sum()))
print("age non entier / hors [18, 84] :", int(((df["age"] < 18) | (df["age"] > 84)).sum()))
print("bmi <= 0 :", int((df["bmi"] <= 0).sum()), " | daily_calories <= 0 :", int((df["daily_calories"] <= 0).sum()))
"""),

    ("markdown", "## 7. Validation finale"),

    ("code", """print("Valeurs manquantes restantes :")
print(df.isna().sum()[df.isna().sum() > 0] if df.isna().any().any() else "aucune")

print("\\nDimensions :", df.shape, " (lignes conservées :", len(df) == len(raw), ")")
print("\\nColonnes ajoutées :", [c for c in df.columns if c not in raw.columns])
print("\\nTypes :")
print(df.dtypes)
"""),

    ("code", """df.to_csv("../data/patients_nutrition_clean.csv", index=False)
print("Écrit : data/patients_nutrition_clean.csv", df.shape)
"""),

    ("markdown", """## 8. Observations

- **Type** : `admission_date` converti en `datetime64`.
- **`condition`** : 25 manques → modalité `Non renseigné` (distincte de `Aucune`).
  Aucune ligne perdue.
- **Erreurs de saisie requalifiées en `NaN`** : `daily_protein_g` 4 valeurs < 5 g/j
  (dont 1 négative) ; `daily_sodium_mg` 4 valeurs < 100 mg/j (dont 2 négatives).
- **Valeurs extrêmes conservées** : 20 `daily_sodium_mg` > 5000 mg/j (max 6405).
  Queue de distribution continue, pas de signature d'erreur d'unité, valeurs atteignables.
- **Imputation** décidée sur test de Kruskal-Wallis (différences entre régimes) :
  - `daily_protein_g` (104 valeurs, p = 0,56) → médiane globale 65,5 g ;
  - `daily_sodium_mg` (154 valeurs, p = 0,31) → médiane globale 2820 mg ;
  - `weight_change_pct` (225 valeurs, p ≈ 3e-34) → médiane par `diet_type`
    (Hypocalorique −1,92 %, Hyperprotéiné −0,92 %, autres ≈ 0), pour préserver
    l'effet régime → perte de poids.
  Imputation par modèle (KNN, régression) écartée : corrélations avec les autres
  numériques toutes ≈ 0. Colonnes indicatrices `*_imputed` ajoutées ; réduction
  d'écart-type de 1 à 5 %.
- **Autres colonnes** : bornes contrôlées (`age`, `bmi`, `daily_calories`, `height_cm`,
  `weight_kg`, `follow_up_weeks`, `nutritionist_visits`) — aucune valeur impossible,
  aucune correction. Aucun doublon.
- **Sortie** : `data/patients_nutrition_clean.csv`, 2500 lignes × 18 colonnes
  (15 d'origine + 3 indicatrices), 0 valeur manquante.
"""),
]


def build():
    nb = nbformat.v4.new_notebook()
    nb.metadata = {
        "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
        "language_info": {"name": "python"},
    }
    nb.cells = [
        nbformat.v4.new_markdown_cell(src) if kind == "markdown" else nbformat.v4.new_code_cell(src)
        for kind, src in CELLS
    ]
    NotebookClient(nb, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(OUT.parent)}}).execute()
    nbformat.write(nb, OUT)
    print(f"Wrote {OUT}")


if __name__ == "__main__":
    build()
