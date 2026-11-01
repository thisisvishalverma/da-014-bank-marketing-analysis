# DA-014: Bank Marketing Campaign Analysis

An interactive Streamlit dashboard and Jupyter/Colab notebook for exploring the UCI Bank Marketing campaign dataset.

## Project structure

```text
.
├── prototype/
│   └── README.md                 # Live dashboard link
├── data/
│   ├── __init__.py
│   ├── Google_Sheets_Dataset_Link.md
│   ├── bank-additional-full.csv
│   ├── download_dataset.py
│   └── SOURCE.md
├── notebooks/
│   └── bank_marketing_analysis.ipynb
├── outputs/
│   ├── Bank_Marketing_Campaign_Analysis_Project_Report.pdf
│   └── Report_Google_Doc_Link.md
├── main.py
├── README.md
├── requirements.txt
├── .gitattributes
└── .gitignore
```

## Run the dashboard locally

Use Python 3.10 or newer. From the project folder in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
streamlit run main.py
```

The dashboard reads `data/bank-additional-full.csv`. The dataset download helper and source attribution are in `data/`.

## Run the notebook

Open `notebooks/bank_marketing_analysis.ipynb` in Jupyter or Google Colab and run the cells. The supplied CSV can be uploaded to the Colab session root or placed in a `data/` folder. The notebook contains the charts and analysis outputs from the updated Colab file.

## Dataset and calculations

The project uses the UCI **Bank Marketing** dataset (`bank-additional-full.csv`), documented in [`data/SOURCE.md`](data/SOURCE.md). A shared Google Sheets copy is linked in [`data/Google_Sheets_Dataset_Link.md`](data/Google_Sheets_Dataset_Link.md). The target is `y`: `yes` indicates that a client subscribed to a term deposit. Response rate is successful `yes` responses divided by records with a valid yes/no target in the selected group.

The bundled dataset contains 41,188 records and 4,640 `yes` outcomes, an overall response rate of 11.27%. Dashboard and notebook calculations are based on the data. Segment comparisons are descriptive and do not establish causation.

## Dashboard and report

- Live dashboard: [Open the Bank Marketing prototype](https://bank-marketing-da-014-u3pnizm4t9g6wk8tpelvfg.streamlit.app/). A separate [prototype link file](prototype/README.md) is included.
- Final PDF report: [`outputs/Bank_Marketing_Campaign_Analysis_Project_Report.pdf`](outputs/Bank_Marketing_Campaign_Analysis_Project_Report.pdf).
- Editable Google Docs report: [`outputs/Report_Google_Doc_Link.md`](outputs/Report_Google_Doc_Link.md).

To demonstrate the dashboard, open the prototype link, try the sidebar filters, and show how the KPIs and charts recalculate for the selected records.

