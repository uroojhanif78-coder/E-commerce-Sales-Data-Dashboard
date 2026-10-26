# E-commerce Store Insights dashboard

Interactive Streamlit dashboard built from `Ecommerce_sales_data_EDA.ipynb`.

The notebook's source CSV was not present in the project folder. The dashboard therefore starts with the notebook's saved aggregate findings and accepts the original CSV from the sidebar to enable row-level filters, detailed charts, correlations, and downloads.

## Run

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

Expected CSV columns: `Year`, `Month`, `Category`, `Region`, `Units_Sold`, `Revenue`, `Profit`, `Customer_Rating`, and `Ad_Spend`.
