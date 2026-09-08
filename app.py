"""Tableau de bord Streamlit — patientèle nutrition/santé.

Lit data/patients_nutrition_features.csv et expose six vues filtrables.
Lancer avec : streamlit run app.py
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

DATA_PATH = Path(__file__).parent / "data" / "patients_nutrition_features.csv"

PALETTE = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
INK = "#0b0b0b"
INK_MUTED = "#898781"
GRID = "#e1e0d9"
BASELINE = "#c3c2b7"
SURFACE = "#fcfcfb"

DIET_ORDER = ["Standard", "Hypocalorique", "Diabétique", "Hyperprotéiné", "Sans sel"]
CONDITION_ORDER = [
    "Aucune", "Diabète type 2", "Hypertension", "Obésité", "Insuffisance rénale", "Non renseigné",
]
BMI_ORDER = ["Insuffisance pondérale", "Corpulence normale", "Surpoids", "Obésité"]
AGE_ORDER = ["18-34", "35-49", "50-64", "65-74", "75-84"]

FLAG_LABELS = {
    "flag_underweight_or_obese": "IMC hors norme",
    "flag_protein_low": "Apport protéique bas",
    "flag_sodium_high_cardiorenal": "Sodium élevé (cardio-rénal)",
    "flag_weight_change_marked": "Variation de poids marquée",
}

SODIUM_TARGET_MG = 2300
PROTEIN_TARGET_G_PER_KG = 0.8
MIN_GROUP_N = 30


@st.cache_data
def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH, parse_dates=["admission_date"])
    df["age_band"] = pd.cut(
        df["age"],
        bins=[18, 35, 50, 65, 75, 200],
        right=False,
        labels=AGE_ORDER,
    )
    df["admission_month"] = df["admission_date"].dt.to_period("M").astype(str)
    return df


def style_fig(fig: go.Figure, height: int = 360, left: int = 64, bottom: int = 64) -> go.Figure:
    fig.update_layout(
        height=height,
        margin=dict(l=left, r=48, t=44, b=bottom),
        paper_bgcolor=SURFACE,
        plot_bgcolor=SURFACE,
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color=INK, size=13),
        colorway=PALETTE,
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0, title_text=""),
        bargap=0.5,
    )
    fig.update_xaxes(gridcolor=GRID, zerolinecolor=BASELINE, linecolor=BASELINE, automargin=True)
    fig.update_yaxes(gridcolor=GRID, zerolinecolor=BASELINE, linecolor=BASELINE, automargin=True)
    return fig


def target_line(fig: go.Figure, *, x=None, y=None, text: str) -> None:
    line = dict(line_dash="dash", line_color=INK_MUTED, line_width=1)
    note = dict(text=text, showarrow=False, font=dict(color=INK_MUTED, size=11),
                xanchor="left", yanchor="bottom", bgcolor="rgba(252,252,251,0.75)")
    if x is not None:
        fig.add_vline(x=x, **line)
        fig.add_annotation(x=x, yref="paper", y=1.0, xshift=4, **note)
    else:
        fig.add_hline(y=y, **line)
        fig.add_annotation(xref="paper", x=0.0, y=y, yshift=4, **note)


def style_box(fig: go.Figure) -> None:
    fig.update_traces(fillcolor="rgba(42,120,214,0.12)", line=dict(color=PALETTE[0], width=1.5),
                      width=0.5, selector=dict(type="box"))


def group_labels(df: pd.DataFrame, col: str, order: list[str]) -> tuple[pd.Series, list[str]]:
    counts = df.groupby(col, observed=False).size()
    mapping = {c: f"{c}<br>(n={int(counts.get(c, 0))})" for c in order}
    return df[col].map(mapping), [mapping[c] for c in order]


def low_group_note(df: pd.DataFrame, col: str, order: list[str]) -> None:
    counts = df.groupby(col, observed=False).size()
    low = [c for c in order if 0 < int(counts.get(c, 0)) < MIN_GROUP_N]
    if low:
        st.caption(f"Effectif inférieur à {MIN_GROUP_N} — lecture prudente : {', '.join(low)}.")


# ---------------------------------------------------------------------------
# Vues
# ---------------------------------------------------------------------------

def view_overview(df: pd.DataFrame, exclude_imputed: bool) -> None:
    st.subheader("Vue d'ensemble de la patientèle")

    score_base = df[~df["risk_screen_incomplete"]] if exclude_imputed else df
    off_norm = df["bmi_category"].isin(["Insuffisance pondérale", "Obésité"]).mean()
    share_ge2 = (score_base["risk_screen_score"] >= 2).mean() if len(score_base) else 0.0

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Patients", f"{len(df):,}".replace(",", " "))
    c2.metric("Âge médian", f"{df['age'].median():.0f} ans" if len(df) else "—")
    c3.metric("IMC hors norme", f"{off_norm:.0%}" if len(df) else "—")
    c4.metric(
        f"Score de risque ≥ 2 (n={len(score_base):,})".replace(",", " "),
        f"{share_ge2:.0%}" if len(score_base) else "—",
    )

    for col, order, title in [
        ("bmi_category", BMI_ORDER, "Catégorie d'IMC (seuils OMS)"),
        ("diet_type", DIET_ORDER, "Type de régime"),
        ("condition", CONDITION_ORDER, "Pathologie associée"),
    ]:
        vc = df[col].value_counts().reindex(order).fillna(0).astype(int)
        fig = go.Figure(go.Bar(
            x=vc.values, y=vc.index, orientation="h", marker_color=PALETTE[0],
            hovertemplate="%{y} : %{x} patients<extra></extra>",
        ))
        fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(order)))
        fig.update_layout(title=title)
        st.plotly_chart(style_fig(fig, height=260, left=170), width="stretch")

    with st.expander("Voir les données"):
        st.dataframe(pd.DataFrame({
            "IMC": df["bmi_category"].value_counts().reindex(BMI_ORDER),
            "Régime": df["diet_type"].value_counts().reindex(DIET_ORDER),
            "Pathologie": df["condition"].value_counts().reindex(CONDITION_ORDER),
        }))


def view_risk(df: pd.DataFrame, exclude_imputed: bool) -> None:
    st.subheader("Triage — score de risque et drapeaux")
    st.caption(
        "Score = nombre de signaux d'alerte diététiques cumulés, pour prioriser la revue "
        "de dossiers. Pas un diagnostic ni un score de gravité."
    )

    base = df[~df["risk_screen_incomplete"]] if exclude_imputed else df
    if exclude_imputed:
        st.caption(f"Scores incomplets exclus : {int(df['risk_screen_incomplete'].sum())} patients "
                   "dont une valeur contributive est imputée.")

    dist = df.groupby(["risk_screen_score", "risk_screen_incomplete"], observed=False).size().unstack(fill_value=0)
    dist = dist.reindex(columns=[False, True], fill_value=0)
    fig = go.Figure()
    fig.add_bar(x=dist.index, y=dist[False], name="Complet", marker_color=PALETTE[0])
    fig.add_bar(x=dist.index, y=dist[True], name="Incomplet (valeur imputée)", marker_color=INK_MUTED)
    fig.update_layout(barmode="stack", title="Distribution du score de risque",
                      xaxis_title="nombre de drapeaux", yaxis_title="patients")
    st.plotly_chart(style_fig(fig), width="stretch")

    freq = {FLAG_LABELS[c]: int(base[c].sum()) for c in FLAG_LABELS}
    freq = pd.Series(freq).sort_values()
    fig = go.Figure(go.Bar(
        x=freq.values, y=freq.index, orientation="h", marker_color=PALETTE[0],
        hovertemplate="%{y} : %{x} patients<extra></extra>",
    ))
    fig.update_layout(title=f"Fréquence de chaque drapeau (n={len(base):,})".replace(",", " "))
    st.plotly_chart(style_fig(fig, height=260, left=190), width="stretch")

    st.markdown("**Taux de chaque drapeau par régime**")
    st.caption(
        "Les seuils des drapeaux ne dépendent pas du régime, sauf le sodium via la pathologie "
        "cardio-rénale. Les écarts entre régimes reflètent la composition des groupes."
    )
    rates = []
    for diet in DIET_ORDER:
        sub = base[base["diet_type"] == diet]
        row = {"Régime": f"{diet} (n={len(sub)})"}
        for c, lab in FLAG_LABELS.items():
            row[lab] = sub[c].mean() if len(sub) else 0.0
        rates.append(row)
    rates_df = pd.DataFrame(rates).set_index("Régime")
    fig = go.Figure()
    for i, lab in enumerate(FLAG_LABELS.values()):
        fig.add_bar(y=rates_df.index, x=rates_df[lab] * 100, name=lab,
                    orientation="h", marker_color=PALETTE[i],
                    text=[f"{v:.0f}%" for v in rates_df[lab] * 100],
                    textposition="outside", textfont_size=10)
    fig.update_layout(barmode="group", title="", xaxis_title="% de patients du régime")
    fig.update_yaxes(categoryorder="array", categoryarray=list(reversed(rates_df.index.tolist())))
    st.plotly_chart(style_fig(fig, height=440, left=160), width="stretch")

    with st.expander("Voir les données"):
        st.dataframe((rates_df * 100).round(1))


def view_intake(df: pd.DataFrame, exclude_imputed: bool) -> None:
    st.subheader("Apports observés vs cible thérapeutique, par régime")
    st.caption(
        "Les apports ne se distinguent pas nettement par régime (test EDA) : lire l'écart à la "
        "ligne de cible, pas l'écart entre régimes."
    )

    specs = [
        ("daily_sodium_mg", "daily_sodium_mg_imputed", "Sodium (mg/j)",
         SODIUM_TARGET_MG, f"repère pop. générale ≈ {SODIUM_TARGET_MG} mg"),
        ("protein_per_kg", "protein_per_kg_imputed", "Protéines (g/kg/j)",
         PROTEIN_TARGET_G_PER_KG, f"repère pop. générale {PROTEIN_TARGET_G_PER_KG} g/kg"),
    ]
    for value_col, imputed_col, title, target, target_text in specs:
        data = df if not exclude_imputed else df[~df[imputed_col]]
        if not exclude_imputed:
            st.caption("Valeurs imputées incluses — forme des distributions déformée par l'imputation.")
        labels, ordered = group_labels(data, "diet_type", DIET_ORDER)
        data = data.assign(_grp=labels)
        fig = go.Figure()
        fig.add_box(x=data["_grp"], y=data[value_col], boxpoints=False)
        style_box(fig)
        fig.update_xaxes(categoryorder="array", categoryarray=ordered)
        fig.update_layout(title=title, yaxis_title=title)
        target_line(fig, y=target, text=target_text)
        st.plotly_chart(style_fig(fig, bottom=80), width="stretch")
        low_group_note(data, "diet_type", DIET_ORDER)

    with st.expander("Voir les données"):
        rows = {}
        for value_col, imputed_col, title, _, _ in specs:
            data = df if not exclude_imputed else df[~df[imputed_col]]
            rows[title] = data.groupby("diet_type", observed=False)[value_col].median().reindex(DIET_ORDER).round(2)
        st.dataframe(pd.DataFrame(rows))


def view_weight(df: pd.DataFrame, exclude_imputed: bool) -> None:
    st.subheader("Évolution du poids par type de régime")
    st.caption(
        "Seul croisement que les données portent (différence testée entre régimes). "
        "Valeurs imputées exclues par défaut : l'imputation ayant été stratifiée par régime, "
        "les inclure resserre artificiellement les boîtes."
    )
    data = df if not exclude_imputed else df[~df["weight_change_pct_imputed"]]
    if not exclude_imputed:
        st.caption("Valeurs imputées incluses — écart entre régimes exagéré par l'imputation stratifiée.")
    labels, ordered = group_labels(data, "diet_type", DIET_ORDER)
    data = data.assign(_grp=labels)
    fig = go.Figure()
    fig.add_box(x=data["_grp"], y=data["weight_change_pct"], boxpoints=False)
    style_box(fig)
    fig.update_xaxes(categoryorder="array", categoryarray=ordered)
    fig.update_layout(title="Variation de poids (%)", yaxis_title="variation de poids (%)")
    target_line(fig, y=0, text="poids stable")
    st.plotly_chart(style_fig(fig, bottom=80), width="stretch")
    low_group_note(data, "diet_type", DIET_ORDER)

    with st.expander("Voir les données"):
        st.dataframe(data.groupby("diet_type", observed=False)["weight_change_pct"]
                     .agg(["size", "median", "mean"]).reindex(DIET_ORDER).round(2))


def view_protein(df: pd.DataFrame, exclude_imputed: bool) -> None:
    st.subheader("Adéquation protéique de la patientèle")
    data = df if not exclude_imputed else df[~df["protein_per_kg_imputed"]]
    if not exclude_imputed:
        st.caption("Valeurs imputées incluses — distribution déformée par l'imputation.")

    fig = go.Figure(go.Histogram(x=data["protein_per_kg"], marker_color=PALETTE[0], nbinsx=40))
    fig.update_layout(title=f"protein_per_kg (n={len(data):,})".replace(",", " "),
                      xaxis_title="g de protéines / kg de poids", yaxis_title="patients")
    target_line(fig, x=PROTEIN_TARGET_G_PER_KG, text=f"repère pop. générale {PROTEIN_TARGET_G_PER_KG} g/kg")
    st.plotly_chart(style_fig(fig), width="stretch")

    st.markdown("**Taux de patients sous 0,8 g/kg par tranche d'âge**")
    st.caption("Ordre naturel des tranches d'âge, non trié par le taux.")
    below = data.assign(_below=data["protein_per_kg"] < PROTEIN_TARGET_G_PER_KG)
    grp = below.groupby("age_band", observed=False)["_below"]
    rate = grp.mean()
    n = grp.size()
    labels = [f"{b}<br>(n={int(n.get(b, 0))})" for b in AGE_ORDER]
    fig = go.Figure(go.Bar(
        x=labels, y=[rate.get(b, 0.0) * 100 for b in AGE_ORDER], marker_color=PALETTE[0],
        hovertemplate="%{x} : %{y:.1f} %<extra></extra>",
    ))
    fig.update_layout(title="", yaxis_title="% sous 0,8 g/kg")
    st.plotly_chart(style_fig(fig, height=300, bottom=72), width="stretch")

    with st.expander("Voir les données"):
        st.dataframe(pd.DataFrame({
            "n": [int(n.get(b, 0)) for b in AGE_ORDER],
            "% sous 0,8 g/kg": [round(rate.get(b, 0.0) * 100, 1) for b in AGE_ORDER],
        }, index=AGE_ORDER))


def view_admissions(df: pd.DataFrame, exclude_imputed: bool) -> None:
    st.subheader("Flux d'admissions dans le temps")
    st.caption("Flux stable sur la période (≈ 139/mois ± 10 %, pas de tendance significative).")
    monthly = df["admission_month"].value_counts().sort_index()
    fig = go.Figure(go.Bar(
        x=monthly.index, y=monthly.values, marker_color=PALETTE[0],
        hovertemplate="%{x} : %{y} admissions<extra></extra>",
    ))
    fig.update_layout(title="Admissions par mois", yaxis_title="admissions")
    fig.update_xaxes(tickangle=-45)
    st.plotly_chart(style_fig(fig, bottom=80), width="stretch")

    with st.expander("Voir les données"):
        st.dataframe(monthly.rename("admissions").to_frame())


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

def main() -> None:
    st.set_page_config(page_title="Dashboard nutrition/santé", layout="wide")
    st.title("Dashboard nutrition/santé — patientèle")
    st.caption("Données synthétiques. Outil de visualisation, sans recommandation clinique automatisée.")

    df = load_data()

    st.sidebar.header("Filtres")
    diet_sel = st.sidebar.multiselect("Régime", DIET_ORDER, default=DIET_ORDER)
    cond_sel = st.sidebar.multiselect("Pathologie", CONDITION_ORDER, default=CONDITION_ORDER)
    bmi_sel = st.sidebar.multiselect("Catégorie d'IMC", BMI_ORDER, default=BMI_ORDER)
    age_sel = st.sidebar.multiselect("Tranche d'âge", AGE_ORDER, default=AGE_ORDER)
    exclude_imputed = st.sidebar.toggle(
        "Exclure les valeurs imputées / scores incomplets", value=True,
    )

    diet_sel = diet_sel or DIET_ORDER
    cond_sel = cond_sel or CONDITION_ORDER
    bmi_sel = bmi_sel or BMI_ORDER
    age_sel = age_sel or AGE_ORDER

    mask = (
        df["diet_type"].isin(diet_sel)
        & df["condition"].isin(cond_sel)
        & df["bmi_category"].isin(bmi_sel)
        & df["age_band"].isin(age_sel)
    )
    df_f = df[mask]

    st.sidebar.markdown(f"**{len(df_f):,}**".replace(",", " ") + f" / {len(df)} patients")
    if len(df_f) == 0:
        st.warning("Aucun patient ne correspond aux filtres.")
        return
    if len(df_f) < 50:
        st.warning(f"Sélection réduite ({len(df_f)} patients) — lecture prudente des distributions.")

    tabs = st.tabs([
        "Vue d'ensemble", "Triage risque", "Apports vs cible",
        "Évolution du poids", "Adéquation protéique", "Admissions",
    ])
    with tabs[0]:
        view_overview(df_f, exclude_imputed)
    with tabs[1]:
        view_risk(df_f, exclude_imputed)
    with tabs[2]:
        view_intake(df_f, exclude_imputed)
    with tabs[3]:
        view_weight(df_f, exclude_imputed)
    with tabs[4]:
        view_protein(df_f, exclude_imputed)
    with tabs[5]:
        view_admissions(df_f, exclude_imputed)


if __name__ == "__main__":
    main()
