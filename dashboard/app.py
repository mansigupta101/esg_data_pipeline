"""
Script to create plotly-Dash dashboard, reading the KPI outputs produced by src/kpi.py.
Run command: python dashboard/app.py, then open http://127.0.0.1:8050

To install plotly dash use: 'pip install dash plotly'

Panels (2x2 grid):
  1. Total CO2 by entity, selectable year (portfolio exposure ranking)
  2. YoY % change over time, by entity, with an all-countries or single-country view
  3. Portfolio-wide total GHG over time (aggregate exposure trend)
  4. Data completeness by entity, colored by a completeness threshold
"""

from pathlib import Path
import pandas as pd
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

BASE = Path(__file__).resolve().parent.parent
KPI_DIR = BASE / "data/processed/kpis"
PROCESSED_DIR = BASE / "data/processed"

FONT_FAMILY = "'Times New Roman', Times, serif"
CO2 = "CO\u2082"  # subscript 2, for all *displayed* text -- column names stay "co2"

clean = pd.read_csv(PROCESSED_DIR / "portfolio_clean.csv")
yoy = pd.read_csv(KPI_DIR / "kpi_yoy_change.csv")
portfolio_ghg = pd.read_csv(KPI_DIR / "kpi_portfolio_ghg_total.csv")
completeness = pd.read_csv(KPI_DIR / "kpi_completeness_by_entity.csv")

YEARS = sorted(clean["year"].unique())
COUNTRIES = sorted(yoy["country"].unique())
COMPLETENESS_THRESHOLD = 0.95

# ---- styling constants -----------------------------------------------------

CARD_STYLE = {
    "border": "1px solid #d8dee4",
    "borderRadius": "8px",
    "padding": "16px 24px 8px 24px",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.06)",
}

GRID_STYLE = {
    "display": "grid",
    "gridTemplateColumns": "1fr 1fr",
    "gap": "24px",
}

CONTROL_ROW_STYLE = {
    "display": "flex",
    "flexDirection": "row",
    "alignItems": "center",
    "justifyContent": "flex-end",
    "gap": "10px",
    "marginBottom": "4px",
}

DROPDOWN_STYLE = {"width": "200px", "fontFamily": FONT_FAMILY}
GRAPH_STYLE = {"height": "420px"}


def apply_layout(fig):
    fig.update_layout(
        font_family=FONT_FAMILY,
        title_font_family=FONT_FAMILY,
        margin=dict(t=50, b=50, l=60, r=30),
    )
    return fig


def make_card(control_row, graph_id_or_figure, is_id=True):
    graph = dcc.Graph(id=graph_id_or_figure, style=GRAPH_STYLE) if is_id \
        else dcc.Graph(figure=graph_id_or_figure, style=GRAPH_STYLE)
    return html.Div([control_row, graph], style=CARD_STYLE)


# ---- static figures (no dropdown) ------------------------------------------

fig_portfolio = apply_layout(px.line(
    portfolio_ghg, x="year", y="portfolio_total_ghg",
    title="Portfolio Total GHG Over Time",
    labels={"portfolio_total_ghg": f"Total GHG (Mt {CO2}eq)"},
))

completeness_sorted = completeness.sort_values("completeness_score").copy()
completeness_sorted["status"] = completeness_sorted["completeness_score"].apply(
    lambda s: "Below threshold" if s < COMPLETENESS_THRESHOLD else "OK"
)
fig_completeness = apply_layout(px.bar(
    completeness_sorted,
    x="country", y="completeness_score", color="status",
    title=f"Data Completeness Score by Entity (threshold: {COMPLETENESS_THRESHOLD:.0%})",
    labels={"completeness_score": "Completeness (0-1)"},
    range_y=[0, 1],
    color_discrete_map={"Below threshold": "#d62728", "OK": "#2ca02c"},
))

# ---- app --------------------------------------------------------------

app = Dash(__name__)
app.title = "ESG Portfolio Emissions Dashboard"

year_control = html.Div([
    html.Label("Year"),
    dcc.Dropdown(
        id="year-dropdown",
        options=[{"label": str(y), "value": y} for y in YEARS],
        value=YEARS[-1],
        clearable=False,
        style=DROPDOWN_STYLE,
    ),
], style=CONTROL_ROW_STYLE)

country_control = html.Div([
    html.Label("Country"),
    dcc.Dropdown(
        id="country-dropdown",
        options=[{"label": "All", "value": "All"}] + [{"label": c, "value": c} for c in COUNTRIES],
        value="All",
        clearable=False,
        style=DROPDOWN_STYLE,
    ),
], style=CONTROL_ROW_STYLE)

app.layout = html.Div([
    html.H1("ESG Portfolio Emissions Dashboard", style={"textAlign": "center"}),
    html.P(
        "Demo pipeline: public country-level emissions data used as a "
        "stand-in for a bank's counterparty/portfolio ESG exposure.",
        style={"textAlign": "center", "fontSize": "18px"},
    ),

    html.Div([
        make_card(year_control, "total-co2-graph", is_id=True),
        make_card(country_control, "yoy-graph", is_id=True),
        make_card(html.Div(), fig_portfolio, is_id=False),
        make_card(html.Div(), fig_completeness, is_id=False),
    ], style=GRID_STYLE),
], style={"fontFamily": FONT_FAMILY, "maxWidth": "1600px", "margin": "0 auto", "padding": "24px"})


@app.callback(
    Output("total-co2-graph", "figure"),
    Input("year-dropdown", "value"),
)
def update_total_co2(selected_year):
    filtered = clean[clean["year"] == selected_year].sort_values("co2", ascending=False)
    fig = px.bar(
        filtered, x="country", y="co2",
        title=f"Total {CO2} by Entity ({selected_year})",
        labels={"co2": f"{CO2} (Mt)", "country": "Entity"},
    )
    return apply_layout(fig)


@app.callback(
    Output("yoy-graph", "figure"),
    Input("country-dropdown", "value"),
)
def update_yoy(selected_country):
    if selected_country == "All":
        fig = px.line(
            yoy, x="year", y="yoy_change_pct", color="country",
            title=f"Year-over-Year {CO2} Change by Entity (%)",
            labels={"yoy_change_pct": "YoY change (%)"},
        )
    else:
        filtered = yoy[yoy["country"] == selected_country]
        fig = px.line(
            filtered, x="year", y="yoy_change_pct",
            title=f"Year-over-Year {CO2} Change \u2014 {selected_country} (%)",
            labels={"yoy_change_pct": "YoY change (%)"},
        )
    fig.update_xaxes(dtick=1, tickangle=-45)
    return apply_layout(fig)


if __name__ == "__main__":
    app.run(debug=True)
