# ESG Portfolio CO<sub>2</sub> Emissions Data Pipeline

A small ETL pipeline that ingests emissions data, runs QA/QC, computes ESG KPIs, and serves them through a dashboard. Built as a scoped demo of ESG data pipeline used in risk reporting functions (ingestion → validation → KPI computation → reporting).

## Data

[Our World in Data CO2 & GHG dataset](https://github.com/owid/co2-data) (public, no auth required). Ten countries (Norway, Sweden, Denmark, Germany, UK, US, China, India, Brazil, Netherlands) are used as a stand-in for the companies a bank might hold in its lending/investment portfolio — public corporate-level emissions data isn't freely available, so country-level data plays the same structural role.

## Architecture

```
Raw CSV -> Ingest -> QA/QC -> KPI calculation -> Plotly-Dash dashboard
```

- `src/ingest.py` — downloads (if needed) and loads raw data, filters to the tracked portfolio and year range
- `src/qc_checks.py` — schema, completeness, range, and year-over-year consistency checks; rejects go to a separate table with a reason code, not silently dropped
- `src/kpi.py` — computes portfolio KPIs from QA-passed data
- `src/run_local.py` — runs the full pipeline end-to-end against local files
- `pipeline_exec.ipynb` — interactive notebook that runs the same pipeline step by step, for inspecting each stage's output while developing
- `dashboard/app.py` — Plotly-Dash dashboard over the KPI outputs
- `tests/test_qc_checks.py` — unit tests for the QA/QC rules

## KPIs

| KPI | Description |
|---|---|
| Total CO2 by entity | Latest-year emissions, ranked — portfolio exposure snapshot |
| Emissions intensity (CO2 / GDP) | Proxy for transition risk per unit of economic output |
| YoY % change | Year-over-year emissions trend per entity |
| Portfolio total CO₂ | Aggregate CO₂ across the whole tracked portfolio, over time |
| Data completeness score | Share of non-null fields per entity — flags entities with weaker disclosure |

## QA/QC checks

- **Schema check** — required fields (`country`, `year`, `co2`, `total_ghg`) present
- **Range check** — no physically implausible values (e.g. negative emissions)
- **Consistency check** — year-over-year change beyond a 50% threshold is flagged for review rather than auto-accepted (likely a reporting break, not a real shift)
- **Completeness score** — computed and surfaced as a KPI in its own right

## Running locally

```bash
pip install -r requirements.txt
python src/run_local.py       # runs ingest -> qc -> kpi against local files
python dashboard/app.py       # serves dashboard at http://127.0.0.1:8050
pytest tests/                 # runs QA/QC unit tests
```

## Future improvements

- Cloud deployment (e.g. AWS Lambda + S3) for scheduled, serverless runs instead of local execution
- Add **dbt** models for the transformation layer, for lineage and testable SQL
- Add data drift monitoring (flag when completeness or YoY-flag rates shift over time, not just per-run)

## Viewing the dashboard
After running the pipeline at least once (so the KPI files exist), start the dashboard:
bash
```python dashboard/app.py```
Then open http://127.0.0.1:8050 in your browser.
