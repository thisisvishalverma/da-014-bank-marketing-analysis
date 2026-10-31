# DA-014: Bank Marketing Campaign Analysis

An interactive Streamlit dashboard and Jupyter notebook for exploring the UCI Bank Marketing campaign dataset. This repository contains the dashboard, analysis notebook, bundled CSV, project presentation, and final report.

## Project structure

```text
.
├── data/
│   ├── bank-additional-full.csv
│   ├── download_dataset.py
│   ├── SOURCE.md
│   └── __init__.py
├── notebooks/
│   └── bank_marketing_analysis.ipynb
├── outputs/
│   ├── Bank_Marketing_Campaign_Analysis.pptx
│   ├── Bank_Marketing_Campaign_Analysis_Project_Report.docx
│   ├── Bank_Marketing_Campaign_Analysis_Project_Report.pdf
│   ├── Faculty_Demo_Guide.md
│   └── Invertis_University_Logo_High_Resolution.png
├── main.py
├── README.md
└── requirements.txt
```

## Run the dashboard

Use Python 3.10 or newer. From the repository folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run main.py
```

The dashboard and its analysis functions are in `main.py`. It reads `data/bank-additional-full.csv`. If the CSV is missing, restore it from the official UCI archive with:

```powershell
python data/download_dataset.py
```

## Run the notebook

Open `notebooks/bank_marketing_analysis.ipynb` in Jupyter or Google Colab and run all cells. In Colab, upload `bank-additional-full.csv` into the runtime first (or upload and extract the project ZIP). The notebook searches the runtime root and a `data/` folder and includes its own analysis functions.

## Dataset and calculations

The dataset is **Bank Marketing (`bank-additional-full.csv`)** from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/222/bank+marketing), DOI `10.24432/C5K306`, licensed CC BY 4.0. Source and citation details are in [`data/SOURCE.md`](data/SOURCE.md).

The target is `y`: `yes` means a client subscribed to a term deposit. Response rate is calculated as records with `y = yes` divided by all records with a valid `y` in the selected group. Each row is a campaign contact record; there is no unique customer identifier in this dataset. The source data contains 41,188 records and 4,640 `yes` outcomes (11.27% overall). The dashboard and notebook calculate these values from the data.

Cleaning trims text, treats `?` as missing, preserves `unknown` as an explicit category, parses numeric columns, and excludes only records without a valid yes/no target. The descriptive comparisons do not establish causation. `duration` is only known after contact and should not be used for pre-call targeting.

## Dashboard features

- Overall and filtered record counts, successful responses, response rate, and average campaign contacts.
- Filters for available categorical and numeric columns.
- Response-rate comparisons by customer segment, contact frequency, channel, month, and weekday.
- Filtered record preview, cleaning summary, and data-driven findings.

See [`outputs/Faculty_Demo_Guide.md`](outputs/Faculty_Demo_Guide.md) for a short faculty walkthrough.

## Project deliverables

- [`outputs/Bank_Marketing_Campaign_Analysis_Project_Report.pdf`](outputs/Bank_Marketing_Campaign_Analysis_Project_Report.pdf) — final report.
- [`outputs/Bank_Marketing_Campaign_Analysis_Project_Report.docx`](outputs/Bank_Marketing_Campaign_Analysis_Project_Report.docx) — editable report.
- [`outputs/Bank_Marketing_Campaign_Analysis.pptx`](outputs/Bank_Marketing_Campaign_Analysis.pptx) — project presentation.

The existing hosted dashboard is [available here](https://bank-marketing-da-014-u3pnizm4t9g6wk8tpelvfg.streamlit.app/). It remains connected to the previously configured repository. This repository is not connected to a new Streamlit deployment; pushing these files does not change the current deployment.