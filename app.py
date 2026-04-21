import os
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="Supply Side Dashboard",
    page_icon="🏗️",
    layout="wide")
st.title("🏗️ Supply-Side Analysis")
st.caption("Residential construction indicators")
file_path = "/Users/yizhouzheng/Desktop/residential_panel.parquet"
if not os.path.exists(file_path):
    st.error(f"File not found: {file_path}")
    st.info("First create this file from your notebook using: panel_df.to_parquet('residential_panel.parquet')")
    st.stop()
df = pd.read_parquet(file_path)
df.index = pd.to_datetime(df.index)
st.sidebar.header("Filters")
min_date = df.index.min().date()
max_date = df.index.max().date()
date_range = st.sidebar.date_input(
    "Date range",
    value=(min_date, max_date),
    min_value=min_date,
    max_value=max_date)
if len(date_range) == 2:
    start_date, end_date = date_range
    filtered_df = df.loc[(df.index.date >= start_date) & (df.index.date <= end_date)].copy()
else:
    filtered_df = df.copy()

tab1, tab2, tab3, tab4 = st.tabs(["Data Overview", "Pipeline", "Cost Pressures", "Interest Rates & Market"])

with tab1:
    st.subheader("Data Overview")
    col1, col2, col3, col4 = st.columns(4)
    def latest_value(col):
        if col in filtered_df.columns and filtered_df[col].dropna().shape[0] > 0:
            return filtered_df[col].dropna().iloc[-1]
        return np.nan
    latest_permit = latest_value("PERMIT1")
    latest_starts = latest_value("HOUST1F")
    latest_completion = latest_value("COMPU1USA")
    latest_mortgage = latest_value("MORTGAGE30US")
    col1.metric("Latest Single-Family Permits", f"{latest_permit:,.1f}" if pd.notna(latest_permit) else "NA")
    col2.metric("Latest Single-Family Starts", f"{latest_starts:,.1f}" if pd.notna(latest_starts) else "NA")
    col3.metric("Latest Single-Family Completions", f"{latest_completion:,.1f}" if pd.notna(latest_completion) else "NA")
    col4.metric("Latest Mortgage Rate", f"{latest_mortgage:.2f}%" if pd.notna(latest_mortgage) else "NA")
    st.markdown("### Recent Data")
    st.dataframe(filtered_df.tail(12), width="stretch")

with tab2:
    st.subheader("Residential Construction Pipeline")
    pipeline_cols = [c for c in ["PERMIT1", "HOUST1F", "COMPU1USA"] if c in filtered_df.columns]
    label_map = {
        "PERMIT1": "Single-Family Permits",
        "HOUST1F": "Single-Family Starts",
        "COMPU1USA": "Single-Family Completions"}
    if len(pipeline_cols) > 0:
        plot_df = filtered_df[pipeline_cols].reset_index()
        plot_df = plot_df.rename(columns=label_map)
        friendly_cols = [label_map[c] for c in pipeline_cols]
        fig = px.line(
            plot_df,
            x="date",
            y=friendly_cols,
            title="Permits, Starts, and Completions Over Time")
        fig.update_layout(
            legend_title_text="Series",
            xaxis_title="Date",
            yaxis_title="Units (SAAR)")
        st.plotly_chart(fig, config={"responsive": True})
    else:
        st.warning("Could not find pipeline columns in your dataset.")
    st.markdown("### Interpretation")
    st.write(
        "This chart shows the residential construction pipeline from permits to starts to completions. "
        "Permits act as an early signal, starts reflect construction activity, and completions show finished housing supply.")

with tab3:
    st.subheader("Construction Cost Pressures")
    material_cols = [
        "WPU081",
        "WPU101",
        "lumber_canada_tariff_pct",
        "steel_section232_tariff_pct",
        "signal_tariff_cost_score"]
    label_map = {
        "WPU081": "Lumber Prices",
        "WPU101": "Steel Prices",
        "lumber_canada_tariff_pct": "Lumber Tariff (%)",
        "steel_section232_tariff_pct": "Steel Tariff (%)",
        "signal_tariff_cost_score": "Tariff Cost Pressure Index"}
    material_cols = [c for c in material_cols if c in filtered_df.columns]
    if len(material_cols) > 0:
        plot_df = filtered_df[material_cols].reset_index()
        plot_df = plot_df.rename(columns=label_map)
        friendly_cols = [label_map[c] for c in material_cols]
        fig = px.line(
            plot_df,
            x="date",
            y=friendly_cols,
            title="Material Cost Trends and Tariff Shocks")
        fig.update_layout(legend_title_text="Series")
        st.plotly_chart(fig, config={"responsive": True})
    else:
        st.warning("Material and tariff data not available.")
    st.markdown("### Interpretation")
    st.write(
        "Higher material prices and tariff shocks can raise construction costs, "
        "which may delay or reduce housing starts over time.")

with tab4:
    st.subheader("Interest Rates & Housing Activity")
    if "PERMIT1" in filtered_df.columns and "MORTGAGE30US" in filtered_df.columns:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=filtered_df.index,
            y=filtered_df["PERMIT1"],
            name="Single-Family Permits"))
        fig.add_trace(go.Scatter(
            x=filtered_df.index,
            y=filtered_df["MORTGAGE30US"],
            name="Mortgage Rate",
            yaxis="y2"))
        fig.update_layout(
            title="Mortgage Rates vs Housing Permits",
            xaxis_title="Date",
            yaxis=dict(title="Permits"),
            yaxis2=dict(title="Mortgage Rate (%)", overlaying="y", side="right"),
            legend=dict(orientation="h"))
        st.plotly_chart(fig, config={"responsive": True})
    else:
        st.warning("Need PERMIT1 and MORTGAGE30US columns for this chart.")
    st.markdown("### Correlation Analysis")
    corr_cols = [c for c in [
        "PERMIT1", "HOUST1F", "COMPU1USA",
        "MORTGAGE30US", "WPU081", "WPU101"] if c in filtered_df.columns]
    if len(corr_cols) >= 2:
        corr = filtered_df[corr_cols].corr(numeric_only=True)
        fig_corr = px.imshow(
            corr,
            text_auto=True,
            aspect="auto",
            title="Correlation Matrix")
        st.plotly_chart(fig_corr, config={"responsive": True})
    else:
        st.warning("Not enough variables available for the correlation matrix.")
