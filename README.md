# GeoMeasure API

A REST API that accepts geospatial files (KML and Shapefile ZIP), extracts spatial features, performs CRS-aware measurements, and stores results for retrieval.

Built as part of a backend engineering assignment. Implemented with **FastAPI**, **GeoPandas**, **SQLAlchemy**, and **SQLite**.

> Full documentation, architecture notes, design decisions, and API examples will be added as development progresses.

## Quick Start

```bash
python -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

Visit `http://localhost:8000/docs` for the interactive API documentation.

## Status

🚧 Work in progress — Milestone 1 complete.
