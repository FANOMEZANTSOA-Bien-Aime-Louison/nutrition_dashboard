"""Generate and execute notebooks/01_eda.ipynb from source cells defined here.

The notebook is a build artifact: edit this file, then run `python _build_01_eda.py`
to regenerate and re-execute it.
"""

from pathlib import Path

import nbformat
from nbclient import NotebookClient

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "notebooks" / "01_eda.ipynb"

CELLS = [
    ("markdown", """# Étape 1 — Analyse exploratoire (EDA)

Dataset : `data/patients_nutrition.csv` — suivi nutritionnel de patients (données synthétiques).

Objectif de l'étape : décrire la structure des données, les distributions, le taux de
valeurs manquantes par colonne, et vérifier la cohérence interne (`bmi` fourni vs IMC
recalculé) afin de cadrer le nettoyage de l'étape 2.
"""),

    ("code", """import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 140)
sns.set_theme(style="whitegrid")

df = pd.read_csv("../data/patients_nutrition.csv")
df.shape
"""),

    ("markdown", "## 1. Structure et intégrité"),

    ("code", "df.head()"),

    ("code", "df.dtypes"),

    ("code", """print("Lignes, colonnes :", df.shape)
print("patient_id uniques :", df["patient_id"].nunique(), "/", len(df))
print("patient_id dupliqués :", int(df["patient_id"].duplicated().sum()))
print("Lignes entièrement dupliquées :", int(df.duplicated().sum()))
"""),

    ("code", "df.describe(include=\"all\").T"),

    ("markdown", """## 2. Valeurs manquantes par colonne

`condition = \"Aucune\"` est une modalité valide (absence de pathologie), pas un null :
les deux sont comptés séparément ci-dessous.
"""),

    ("code", """missing = pd.DataFrame({
    "n_null": df.isna().sum(),
    "pct_null": (df.isna().mean() * 100).round(2),
})
missing = missing.sort_values("pct_null", ascending=False)
missing
"""),

    ("code", """cols_with_null = missing[missing["n_null"] > 0].index.tolist()

fig, ax = plt.subplots(figsize=(7, 3.5))
ax.barh(cols_with_null, missing.loc[cols_with_null, "pct_null"], color="#c0392b")
ax.invert_yaxis()
ax.set_xlabel("% de valeurs manquantes")
ax.set_title("Valeurs manquantes par colonne")
for i, c in enumerate(cols_with_null):
    ax.text(missing.loc[c, "pct_null"] + 0.1, i, f'{missing.loc[c, "pct_null"]:.1f}%', va="center")
plt.tight_layout()
plt.show()
"""),

    ("code", """rows_any_null = df.isna().any(axis=1).sum()
rows_multi_null = (df.isna().sum(axis=1) >= 2).sum()
print(f"Lignes avec >=1 valeur manquante : {rows_any_null} ({rows_any_null / len(df):.1%})")
print(f"Lignes avec >=2 valeurs manquantes : {rows_multi_null}")
print()
print("condition : 'Aucune' vs réellement manquante")
print(df["condition"].value_counts(dropna=False))
print()
print("diet_type des lignes où condition est manquante :")
print(df.loc[df["condition"].isna(), "diet_type"].value_counts())
"""),

    ("markdown", "## 3. Distributions des variables numériques"),

    ("code", """num_cols = [
    "age", "height_cm", "weight_kg", "bmi",
    "daily_calories", "daily_protein_g", "daily_sodium_mg",
    "follow_up_weeks", "weight_change_pct", "nutritionist_visits",
]
df[num_cols].describe(percentiles=[0.01, 0.25, 0.5, 0.75, 0.99]).T
"""),

    ("code", """fig, axes = plt.subplots(4, 3, figsize=(14, 14))
for ax, col in zip(axes.ravel(), num_cols):
    ax.hist(df[col].dropna(), bins=40, color="#2980b9", edgecolor="white")
    ax.set_title(col)
for ax in axes.ravel()[len(num_cols):]:
    ax.set_visible(False)
fig.suptitle("Distributions des variables numériques", y=1.01, fontsize=14)
plt.tight_layout()
plt.show()
"""),

    ("markdown", "## 4. Distributions des variables catégorielles"),

    ("code", """cat_cols = ["gender", "diet_type", "condition"]

fig, axes = plt.subplots(1, 3, figsize=(15, 4))
for ax, col in zip(axes, cat_cols):
    vc = df[col].astype("string").fillna("(manquant)").value_counts()
    ax.bar(vc.index.tolist(), vc.values, color="#16a085")
    ax.set_title(col)
    ax.tick_params(axis="x", rotation=30)
plt.tight_layout()
plt.show()

for col in cat_cols:
    print(f"--- {col} ---")
    print(df[col].value_counts(dropna=False))
    print()
"""),

    ("markdown", "## 5. Couverture temporelle (`admission_date`)"),

    ("code", """adm = pd.to_datetime(df["admission_date"])
print("Min :", adm.min().date(), " Max :", adm.max().date(), " Étendue :", (adm.max() - adm.min()).days, "jours")
print("Dates dans le futur (> 2026-09-07) :", int((adm > pd.Timestamp("2026-09-07")).sum()))

by_month = adm.dt.to_period("M").value_counts().sort_index()
fig, ax = plt.subplots(figsize=(12, 3.5))
ax.bar(by_month.index.astype(str), by_month.values, color="#8e44ad")
ax.set_title("Admissions par mois")
ax.tick_params(axis="x", rotation=90)
plt.tight_layout()
plt.show()
"""),

    ("markdown", """## 6. Cohérence `bmi` fourni vs IMC recalculé

IMC recalculé = `weight_kg / (height_cm / 100) ** 2`. La colonne `bmi` est fournie avec
une décimale : un écart absolu <= 0,05 correspond à la tolérance d'arrondi. Au-delà, il
faudrait suspecter une incohérence interne à traiter au nettoyage.
"""),

    ("code", """bmi_calc = df["weight_kg"] / (df["height_cm"] / 100) ** 2
diff = (df["bmi"] - bmi_calc).abs()
comparable = df["bmi"].notna() & df["height_cm"].notna() & df["weight_kg"].notna()

print("Lignes comparables :", int(comparable.sum()), "/", len(df))
print(diff[comparable].describe())
print()
for thr in (0.05, 0.1, 0.5, 1.0, 2.0):
    print(f"  |écart| > {thr:>4} : {int((diff[comparable] > thr).sum())}")
"""),

    ("code", """fig, ax = plt.subplots(figsize=(7, 3.5))
ax.hist(diff[comparable], bins=50, color="#d35400", edgecolor="white")
ax.set_xlabel("|bmi fourni - IMC recalculé|")
ax.set_title("Écart absolu bmi vs IMC recalculé")
plt.tight_layout()
plt.show()

df.assign(bmi_calc=bmi_calc.round(2), ecart=(df["bmi"] - bmi_calc).round(3)) \
  .loc[comparable, ["patient_id", "height_cm", "weight_kg", "bmi", "bmi_calc", "ecart"]] \
  .reindex(diff[comparable].sort_values(ascending=False).index) \
  .head(10)
"""),

    ("markdown", """## 7. Valeurs hors plage plausible

Repérage (sans correction ici — la correction relève de l'étape 2) des valeurs
physiologiquement impossibles ou extrêmes.
"""),

    ("code", """checks = {
    "age < 18": (df["age"] < 18).sum(),
    "age > 90": (df["age"] > 90).sum(),
    "bmi < 15": (df["bmi"] < 15).sum(),
    "bmi > 40": (df["bmi"] > 40).sum(),
    "daily_calories < 800": (df["daily_calories"] < 800).sum(),
    "daily_calories > 3500": (df["daily_calories"] > 3500).sum(),
    "daily_protein_g <= 0": (df["daily_protein_g"] <= 0).sum(),
    "daily_protein_g < 5": (df["daily_protein_g"] < 5).sum(),
    "daily_sodium_mg < 0": (df["daily_sodium_mg"] < 0).sum(),
    "daily_sodium_mg < 100": (df["daily_sodium_mg"] < 100).sum(),
    "daily_sodium_mg > 5000": (df["daily_sodium_mg"] > 5000).sum(),
}
pd.Series(checks, name="n_lignes").to_frame()
"""),

    ("code", """print("Protéines <= 5 g/j :")
print(df.loc[df["daily_protein_g"] < 5, ["patient_id", "diet_type", "daily_calories", "daily_protein_g"]])
print()
print("Sodium < 100 mg/j :")
print(df.loc[df["daily_sodium_mg"] < 100, ["patient_id", "diet_type", "condition", "daily_sodium_mg"]])
"""),

    ("markdown", "## 8. Corrélations entre variables numériques"),

    ("code", """corr = df[num_cols].corr()
fig, ax = plt.subplots(figsize=(9, 7))
sns.heatmap(corr, annot=True, fmt=".2f", cmap="RdBu_r", center=0, vmin=-1, vmax=1, ax=ax)
ax.set_title("Matrice de corrélation (Pearson)")
plt.tight_layout()
plt.show()
"""),

    ("markdown", """## 9. Observations

- **Structure** : 2500 lignes, 15 colonnes, `patient_id` unique, aucune ligne dupliquée.
- **Valeurs manquantes** : 4 colonnes concernées — `weight_change_pct` (9 %),
  `daily_sodium_mg` (6 %), `daily_protein_g` (4 %), `condition` (1 %, 25 lignes,
  distinctes de la modalité `Aucune`). ~19 % des lignes ont au moins un null, mais les
  manques se recouvrent peu (33 lignes avec ≥ 2 nulls).
- **Distributions** : `age` bornée 18–84, `follow_up_weeks` 1–25, `bmi` centré ~24
  (15–36,6). Apports globalement plausibles ; `daily_sodium_mg` fortement étalé à droite.
- **Catégorielles** : genre ~équilibré ; `diet_type` dominé par `Standard` (35 %) ;
  `condition` : 39 % `Aucune`, puis Diabète type 2, Hypertension, Obésité, Insuffisance rénale.
- **Temporel** : admissions du 2025-01-01 au 2026-06-29 (≈ 18 mois), aucune date future.
- **Cohérence IMC** : écart absolu `bmi` vs IMC recalculé ≤ 0,05 sur les 2500 lignes
  (la seule « au-delà » est à 0,05000000000000071 — bruit de calcul flottant sur un
  0,05 exact). La colonne `bmi` est cohérente avec `height_cm`/`weight_kg` : pas de
  problème de qualité de ce côté, elle peut servir de contrôle croisé au nettoyage.
- **Valeurs aberrantes** : 1 protéine négative + 3 valeurs < 5 g/j ; 2 sodiums négatifs
  + 2 valeurs < 100 mg/j ; 20 sodiums > 5000 mg/j (queue haute, plausibilité limite).
  À traiter à l'étape 2.
- **Corrélations** : quasi nulles entre toutes les paires, en particulier
  `weight_change_pct` avec `follow_up_weeks`, `daily_calories`, `bmi`, `age`. Les
  variables d'évolution se comportent comme du bruit non relié aux profils.
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
