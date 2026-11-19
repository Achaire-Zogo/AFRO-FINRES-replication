# AFRO-FINRES replication package

Replication material for *Measuring the Operational Resilience of FinTech Ecosystems in Sub-Saharan Africa: The AFRO-FINRES Framework and Evidence from Cameroon and the CEMAC Region*.

## Requirements
Python 3.10+, packages in `requirements.txt` (`pip install -r requirements.txt`). LaTeX (pdflatex + bibtex) to rebuild the manuscript.

## Run order (from this folder)
1. `cd data && python3 ../code/01_fetch_wb.py && cd ..` – downloads WDI, WGI and Global Findex data from the World Bank API into `data/wb_raw.csv` (optional; the raw file is included).
2. `python3 code/02_build_index.py` – builds indicators, dimension scores, the composite index, robustness analysis (PCA, Cronbach's alpha, LODO, 5000 Monte Carlo draws) and external validation. Outputs: `data/afro_finres_scores.csv`, `data/afro_finres_indicators_raw.csv`, `data/validation.csv`, `data/results_summary.json`.
3. `python3 code/03_figures_scenarios.py` – figures 2–5 (`figures/`) and stress-test results.
4. `cd manuscript && latexmk -pdf main.tex` – manuscript PDF.

## Data
- `data/gci2024_pillars.csv`: ITU GCI 2024 pillar scores transcribed from the country profiles (`source_page` = PDF page of `data/gci2024.pdf`).
- `data/pdb_ix.json`, `data/pdb_fac.json`: PeeringDB snapshots (active IXPs and facilities), November 2026.
- `data/wb_raw.csv`: World Bank API extract (sources 2, 3, 28).
- `refs/verified.json`: DOI metadata resolved via doi.org for every DOI-referenced source.

All sources are public. The scenario parameters in `code/03_figures_scenarios.py` are illustrative assumptions.
