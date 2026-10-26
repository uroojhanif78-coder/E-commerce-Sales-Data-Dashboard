from __future__ import annotations

from io import BytesIO
from pathlib import Path
import calendar

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


st.set_page_config(page_title="E-commerce Store Insights", page_icon="🛍️", layout="wide")

COLORS = ["#5B67F1", "#23B5A5", "#F5A623", "#E66B8A", "#8673D5", "#4F9BD9"]
MONTHS = list(calendar.month_name)[1:]

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Manrope:wght@500;600;700;800&display=swap');
:root { --ink:#182235; --muted:#738096; --line:#e9edf3; --paper:#f5f7fb; }
.stApp { background:var(--paper); color:var(--ink); font-family:'DM Sans',sans-serif; }
header[data-testid="stHeader"] { background:transparent; }
.block-container { padding-top:1.5rem; max-width:1500px; }
h1,h2,h3 { font-family:'Manrope',sans-serif; letter-spacing:-.04em; color:var(--ink); }
.hero { padding:25px 30px; border-radius:20px; background:linear-gradient(115deg,#182444 0%,#304678 56%,#526be8 100%); color:white; margin:0 0 20px; }
.hero h1 { color:white; font-size:2.05rem; margin:0 0 5px; }
.hero p { color:#d5def4; margin:0; font-size:.98rem; }
.eyebrow { text-transform:uppercase; letter-spacing:.14em; font-size:.72rem; font-weight:700; color:#9fb2ff; margin-bottom:9px; }
div[data-testid="stMetric"] { background:#fff; border:1px solid var(--line); border-radius:15px; padding:16px 18px; box-shadow:0 3px 12px rgba(30,45,75,.035); }
div[data-testid="stMetricLabel"] { color:var(--muted); font-weight:600; }
div[data-testid="stMetricValue"] { color:var(--ink); font-family:'Manrope',sans-serif; }
div[data-testid="stTabs"] button { font-weight:700; }
.insight { background:#fff; border:1px solid var(--line); border-left:4px solid #5B67F1; border-radius:12px; padding:14px 16px; margin:8px 0; color:#334055; }
.note { color:var(--muted); font-size:.88rem; }
.stPlotlyChart { background:#fff; border:1px solid var(--line); border-radius:15px; padding:8px; }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def read_csv(file_bytes: bytes) -> pd.DataFrame:
    return pd.read_csv(BytesIO(file_bytes))


def money(value: float) -> str:
    return f"${value:,.0f}"


def style_fig(fig, height=360):
    fig.update_layout(
        height=height, paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="white",
        font=dict(family="DM Sans, sans-serif", color="#354158", size=12),
        margin=dict(l=14, r=14, t=48, b=12), title=dict(font=dict(size=16, color="#182235")),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    fig.update_xaxes(showgrid=True, gridcolor="#edf0f5", zeroline=False)
    fig.update_yaxes(showgrid=False, zeroline=False)
    return fig


NOTEBOOK_MONTH = pd.DataFrame({
    "Month": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "Revenue": [2271989.21,2556542.09,1965211.31,1883991.70,2539650.55,2704548.43,2100090.77,2046098.80,2053765.68,2640283.17,2265159.35,2096213.46],
})
NOTEBOOK_CATEGORY = pd.DataFrame({
    "Category": ["Home Decor", "Groceries", "Beauty Products", "Electronics", "Fashion", "Books"],
    "Revenue": [5021519.17,4789067.90,4699065.69,4640928.26,4256189.07,3716774.43],
    "Profit": [1010554.50,1012596.35,919309.22,929368.70,879845.52,743058.37],
    "Orders": [172,159,168,178,167,156],
})
NOTEBOOK_REGION = pd.DataFrame({"Region": ["North", "East", "West", "South"], "Average order revenue": [28549.553792,27573.445040,26503.651586,25738.950273]})

st.markdown('<div class="hero"><div class="eyebrow">Commerce intelligence · 1,000 notebook records</div><h1>E-commerce Store Insights</h1><p>Explore sales, profit, customer ratings and advertising performance across your store.</p></div>', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("## Dashboard controls")
    st.caption("Add the source CSV to enable live, row-level analysis.")
    upload = st.file_uploader("Upload ecommerce_sales_data.csv", type=["csv"])
    st.markdown("---")
    st.markdown("**Expected columns**")
    st.caption("Year, Month, Category, Region, Units_Sold, Revenue, Profit, Customer_Rating, Ad_Spend")

df = None
load_error = None
if upload:
    try:
        df = read_csv(upload.getvalue())
        required = {"Year", "Month", "Category", "Region", "Units_Sold", "Revenue", "Profit", "Customer_Rating", "Ad_Spend"}
        missing = required - set(df.columns)
        if missing:
            load_error = "Missing required columns: " + ", ".join(sorted(missing))
            df = None
    except Exception as exc:
        load_error = f"Could not read CSV: {exc}"
if load_error:
    st.error(load_error)

if df is None:
    st.info("Showing the saved, verified notebook summaries. Upload the original CSV in the sidebar for interactive date, region, category and metric filters.")
    month_data, category_data, region_data = NOTEBOOK_MONTH.copy(), NOTEBOOK_CATEGORY.copy(), NOTEBOOK_REGION.copy()
    records, rev_total, profit_total = 1000, category_data.Revenue.sum(), category_data.Profit.sum()
    tab_labels = ["Overview", "Products & regions", "Monthly trends", "Data notes"]
    row_data = None
else:
    data = df.copy()
    data["Month"] = data["Month"].astype(str).str.strip().str.capitalize()
    data["MonthNum"] = data["Month"].apply(lambda x: MONTHS.index(x) + 1 if x in MONTHS else 0)
    data["Date"] = pd.to_datetime(data["Year"].astype(str) + "-" + data["MonthNum"].astype(str) + "-01", errors="coerce")
    data = data.dropna(subset=["Date"])
    if data.empty:
        st.error("No rows have a recognizable Month and Year.")
        st.stop()
    with st.sidebar:
        years = sorted(data.Year.dropna().unique())
        selected_years = st.multiselect("Year", years, default=years)
        categories = sorted(data.Category.dropna().unique())
        selected_categories = st.multiselect("Category", categories, default=categories)
        regions = sorted(data.Region.dropna().unique())
        selected_regions = st.multiselect("Region", regions, default=regions)
        metric = st.selectbox("Trend metric", ["Revenue", "Profit", "Units_Sold", "Ad_Spend", "Customer_Rating"])
        percentile_trim = st.checkbox("Exclude top 1% revenue outliers from distribution", value=False)
    data = data[data.Year.isin(selected_years) & data.Category.isin(selected_categories) & data.Region.isin(selected_regions)]
    row_data = data
    records = len(data)
    rev_total, profit_total = data.Revenue.sum(), data.Profit.sum()
    month_data = data.groupby(["MonthNum", "Month"], as_index=False).agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Units_Sold=("Units_Sold", "sum"), Ad_Spend=("Ad_Spend", "sum"), Customer_Rating=("Customer_Rating", "mean")).sort_values("MonthNum")
    category_data = data.groupby("Category", as_index=False).agg(Revenue=("Revenue", "sum"), Profit=("Profit", "sum"), Orders=("Category", "size"), Units_Sold=("Units_Sold", "sum"), Customer_Rating=("Customer_Rating", "mean"), Ad_Spend=("Ad_Spend", "sum"))
    region_data = data.groupby("Region", as_index=False).agg(**{"Average order revenue": ("Revenue", "mean"), "Revenue": ("Revenue", "sum"), "Profit": ("Profit", "sum"), "Orders": ("Region", "size")}).sort_values("Average order revenue", ascending=False)
    tab_labels = ["Overview", "Products & regions", "Monthly trends", "Data explorer"]

col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("Revenue", money(rev_total))
with col2: st.metric("Profit", money(profit_total), f"{profit_total/rev_total:.1%} margin" if rev_total else None)
with col3: st.metric("Transactions", f"{records:,}")
with col4: st.metric("Avg. order revenue", money(rev_total / records) if records else "$0")
with col5:
    if row_data is not None and records:
        st.metric("Avg. customer rating", f"{row_data.Customer_Rating.mean():.2f} / 5")
    else:
        st.metric("Revenue / units correlation", "0.67", "positive relationship")

tabs = st.tabs(tab_labels)

with tabs[0]:
    left, right = st.columns([1.35, 1])
    with left:
        st.subheader("Revenue by month")
        ycol = metric if row_data is not None else "Revenue"
        title = f"Monthly {ycol.replace('_', ' ').lower()}"
        fig = px.bar(month_data, x="Month", y=ycol, title=title, color_discrete_sequence=[COLORS[0]], text_auto=".2s")
        fig.update_traces(hovertemplate="%{x}<br>%{y:,.2f}<extra></extra>")
        st.plotly_chart(style_fig(fig, 390), use_container_width=True)
    with right:
        st.subheader("Category performance")
        sort_col = "Revenue"
        cdata = category_data.sort_values(sort_col)
        fig = px.bar(cdata, x=sort_col, y="Category", orientation="h", title="Revenue by category", color=sort_col, color_continuous_scale=["#b9c2ff", COLORS[0]], text_auto=".2s")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig, 390), use_container_width=True)
    st.subheader("At a glance")
    best_month = month_data.loc[month_data.Revenue.idxmax()]
    best_cat = category_data.loc[category_data.Profit.idxmax()]
    st.markdown(f'<div class="insight"><b>Top revenue month:</b> {best_month.Month} at {money(best_month.Revenue)}.</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="insight"><b>Profit leader:</b> {best_cat.Category} generated {money(best_cat.Profit)} in profit.</div>', unsafe_allow_html=True)
    if row_data is not None:
        corr = row_data[["Revenue", "Units_Sold", "Profit", "Customer_Rating", "Ad_Spend"]].corr(numeric_only=True)
        if corr.loc["Revenue", "Profit"] > .5:
            st.markdown(f'<div class="insight"><b>Revenue and profit move together:</b> correlation {corr.loc["Revenue", "Profit"]:.2f} in the current selection. Correlation does not establish cause.</div>', unsafe_allow_html=True)

with tabs[1]:
    lcol, rcol = st.columns(2)
    with lcol:
        st.subheader("Category scorecard")
        metric_options = [x for x in ["Revenue", "Profit", "Orders", "Units_Sold", "Customer_Rating", "Ad_Spend"] if x in category_data]
        score_metric = st.selectbox("Compare categories by", metric_options, key="category_metric")
        fig = px.bar(category_data.sort_values(score_metric), x=score_metric, y="Category", orientation="h", color=score_metric, color_continuous_scale=["#b9c2ff", COLORS[1]], title=f"{score_metric.replace('_', ' ')} by category", text_auto=".2s")
        fig.update_layout(coloraxis_showscale=False)
        st.plotly_chart(style_fig(fig), use_container_width=True)
    with rcol:
        st.subheader("Regional performance")
        if row_data is None:
            reg_plot = region_data.sort_values("Average order revenue")
            fig = px.bar(reg_plot, x="Average order revenue", y="Region", orientation="h", title="Average order revenue by region", color_discrete_sequence=[COLORS[2]], text_auto=".2s")
        else:
            reg_plot = region_data.sort_values("Revenue")
            fig = px.bar(reg_plot, x="Revenue", y="Region", orientation="h", title="Revenue by region", color="Profit", color_continuous_scale="Tealgrn", text_auto=".2s")
        st.plotly_chart(style_fig(fig), use_container_width=True)
    st.subheader("Revenue and profit mix")
    fig = go.Figure()
    fig.add_bar(name="Revenue", x=category_data.Category, y=category_data.Revenue, marker_color=COLORS[0])
    fig.add_bar(name="Profit", x=category_data.Category, y=category_data.Profit, marker_color=COLORS[1])
    fig.update_layout(barmode="group", title="Revenue vs. profit by category", yaxis_title="Amount ($)")
    st.plotly_chart(style_fig(fig), use_container_width=True)
    st.dataframe(category_data.sort_values("Profit", ascending=False).style.format({"Revenue": "${:,.2f}", "Profit": "${:,.2f}", "Average order revenue": "${:,.2f}"}, na_rep="—"), use_container_width=True, hide_index=True)

with tabs[2]:
    st.subheader("Seasonality and monthly totals")
    m1, m2 = st.columns([1.5, 1])
    with m1:
        fig = px.line(month_data, x="Month", y="Revenue", markers=True, title="Revenue trend", color_discrete_sequence=[COLORS[0]])
        fig.update_traces(line=dict(width=3), marker=dict(size=8))
        st.plotly_chart(style_fig(fig, 380), use_container_width=True)
    with m2:
        fig = px.pie(month_data, values="Revenue", names="Month", hole=.62, title="Share of annual revenue", color_discrete_sequence=COLORS)
        fig.update_traces(textposition="inside", textinfo="percent")
        st.plotly_chart(style_fig(fig, 380), use_container_width=True)
    st.dataframe(month_data.drop(columns=["MonthNum"], errors="ignore").style.format({c: ("${:,.2f}" if c in ["Revenue", "Profit", "Ad_Spend"] else "{:,.2f}") for c in month_data.columns if c not in ["Month", "MonthNum"]}, na_rep="—"), use_container_width=True, hide_index=True)

if row_data is None:
    with tabs[3]:
        st.subheader("Notebook findings")
        st.markdown("""
        <div class="insight"><b>Dataset:</b> 1,000 complete records across six product categories and four regions. The notebook reports no missing values or duplicates.</div>
        <div class="insight"><b>Revenue leader:</b> Home Decor has the highest category revenue ($5.02M) and the most transactions in the saved analysis (172).</div>
        <div class="insight"><b>Profit leader:</b> Groceries tops profit ($1.01M), narrowly ahead of Home Decor ($1.01M); Books is lowest at $743K.</div>
        <div class="insight"><b>Seasonality:</b> June is the strongest month ($2.70M); April is weakest ($1.88M).</div>
        <div class="insight"><b>Regional order value:</b> North is highest ($28.5K average revenue per record); South is lowest ($25.7K).</div>
        <div class="insight"><b>Relationships:</b> Revenue and profit correlate at 0.91; units sold and revenue at 0.67. Ad spend and revenue have a near-zero correlation (0.02) in the notebook.</div>
        """, unsafe_allow_html=True)
        st.markdown("**Important:** The original CSV is not in this project folder. These cards use saved aggregate notebook outputs; category by region, correlation details, and filtered record analysis require uploading the CSV.")
else:
    with tabs[3]:
        st.subheader("Transaction explorer")
        x1, x2 = st.columns(2)
        with x1: x_axis = st.selectbox("Horizontal axis", ["Revenue", "Units_Sold", "Profit", "Ad_Spend", "Customer_Rating"])
        with x2: y_axis = st.selectbox("Vertical axis", ["Profit", "Revenue", "Units_Sold", "Ad_Spend", "Customer_Rating"], index=0)
        fig = px.scatter(row_data, x=x_axis, y=y_axis, color="Category", symbol="Region", hover_data=["Year", "Month", "Revenue", "Profit", "Customer_Rating"], title=f"{y_axis.replace('_',' ')} vs. {x_axis.replace('_',' ')}", opacity=.72, color_discrete_sequence=COLORS)
        st.plotly_chart(style_fig(fig, 440), use_container_width=True)
        numeric_cols = row_data.select_dtypes("number").columns.tolist()
        st.subheader("Correlation matrix")
        corr = row_data[numeric_cols].corr(numeric_only=True)
        heat = px.imshow(corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1, aspect="auto")
        st.plotly_chart(style_fig(heat, 430), use_container_width=True)
        st.subheader("Filtered records")
        st.dataframe(row_data.drop(columns=["MonthNum"], errors="ignore"), use_container_width=True, hide_index=True)
        st.download_button("Download filtered CSV", row_data.drop(columns=["MonthNum"], errors="ignore").to_csv(index=False), "filtered_ecommerce_data.csv", "text/csv")

st.caption("Notebook source: Ecommerce_sales_data_EDA.ipynb · Dashboard summaries reflect the saved notebook outputs. Upload the source CSV for live calculations.")
