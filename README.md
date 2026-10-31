# DA-014: Bank Marketing Campaign Analysis

An interactive Streamlit dashboard and Jupyter notebook for exploring the UCI Bank Marketing campaign dataset. This repository contains the working dashboard, analysis notebook, bundled CSV, and the final project presentation and report.

## Project structure

```text
.
├── data/
│   ├── bank-additional-full.csv
│   └── SOURCE.md
├── notebooks/
│   └── bank_marketing_analysis.ipynb
├── outputs/
│   ├── Bank_Marketing_Campaign_Analysis.pptx
│   ├── Bank_Marketing_Campaign_Analysis_Project_Report.docx
│   ├── Bank_Marketing_Campaign_Analysis_Project_Report.pdf
│   └── Invertis_University_Logo_High_Resolution.png
├── scripts/
│   └── download_dataset.py
├── analysis.py
├── app.py
├── main.py
├── PROTOTYPE_DEMO.md
├── README.md
└── requirements.txt
```

## Run the dashboard

Use Python 3.10 or newer. From the repository folder:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run app.py
```

`app.py` is kept as Streamlit Cloud's usual entry point; `main.py` contains the dashboard. The app and analysis module expect the dataset at `data/bank-additional-full.csv`.

## Run the notebook

Open `notebooks/bank_marketing_analysis.ipynb` in Jupyter or Google Colab and run all cells. In Colab, upload `bank-additional-full.csv` into the runtime first (or upload the project ZIP and extract it). The notebook searches the runtime root and a `data/` folder, and includes its analysis functions so it does not require a separate `analysis.py` upload.

## Dataset and calculations

The dataset is **Bank Marketing (`bank-additional-full.csv`)** from the [UCI Machine Learning Repository](https://archive.ics.uci.edu/dataset/222/bank+marketing), DOI `10.24432/C5K306`, licensed CC BY 4.0. Source and citation details are in [`data/SOURCE.md`](data/SOURCE.md).

The target is `y`: `yes` means a client subscribed to a term deposit. Response rate is calculated as the number of valid records with `y = yes` divided by all records with a valid `y` in the selected group. Each dataset row is a campaign contact record; there is no unique customer identifier in this file. The bundled source data contains 41,188 records and 4,640 `yes` outcomes (11.27% overall). The dashboard and notebook calculate the values from the data.

The analysis trims text, treats `?` as missing, preserves `unknown` as an explicit category, parses numeric columns, and excludes only records without a valid yes/no target. The descriptive comparisons do not establish causation. `duration` is only known after contact and should not be treated as a pre-call targeting feature.

## Dashboard features

- Overall and filtered record counts, successful responses, response rate, and average campaign contacts.
- Filters for available categorical and numeric columns.
- Response-rate comparisons by customer segment, contact frequency, channel, month, and weekday.
- Filtered record preview, cleaning summary, and data-driven findings.

See [`PROTOTYPE_DEMO.md`](PROTOTYPE_DEMO.md) for a short faculty walkthrough.

## Project deliverables

- [`outputs/Bank_Marketing_Campaign_Analysis_Project_Report.pdf`](outputs/Bank_Marketing_Campaign_Analysis_Project_Report.pdf) — final report.
- [`outputs/Bank_Marketing_Campaign_Analysis_Project_Report.docx`](outputs/Bank_Marketing_Campaign_Analysis_Project_Report.docx) — editable report.
- [`outputs/Bank_Marketing_Campaign_Analysis.pptx`](outputs/Bank_Marketing_Campaign_Analysis.pptx) — project presentation.

The current hosted dashboard is [available here](https://bank-marketing-da-014-u3pnizm4t9g6wk8tpelvfg.streamlit.app/). That deployment remains connected to the previously configured repository; creating or updating this source repository does not change its deployment settings.

