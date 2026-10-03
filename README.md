# NovaMart Customer Support

An e-commerce support demo with a Streamlit chat UI, FastAPI agent backend,
SQLite seed data, and a public dataset library.

## Run locally

Install Python 3.11 or newer, then from this directory:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python seed_db.py
```

In separate terminals, start the API and UI:

```powershell
python agent_engine.py
```

```powershell
streamlit run app_ui.py
```

Open <http://localhost:8501>. The API documentation is at
<http://localhost:8000/docs>.

## Public reference library and privacy

Public policy and product-specification documents are included under
`datasets/public`. Public operational CSV/JSON files containing customer
contact details, addresses, or chat records, as well as the local SQLite
database, are intentionally excluded from this repository. The app shows
these datasets as not bundled unless their source files are supplied locally.
Hidden evaluation data is not included.

When present locally, the importer stores source data in separate `public_*`
tables without replacing the support demo's own database tables.
