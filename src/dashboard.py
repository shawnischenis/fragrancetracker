import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

# ===== Load your data =====
# Example CSV format:
# fragrance,brand,size_ml,condition,price_usd,source,date
# Bleu de Chanel EDP,Chanel,100,New,115,Reddit,2025-09-01
@st.cache_data
def load_data():
    df = pd.read_csv("fragrance_data.csv")
    return df

df = load_data()

# ===== Sidebar Filters =====
st.sidebar.header("Filters")

# Let user pick fragrance
fragrance_list = sorted(df["fragrance"].unique())
selected_fragrance = st.sidebar.selectbox("Choose a fragrance:", fragrance_list)

# Optional: condition filter
condition = st.sidebar.multiselect(
    "Condition:", options=df["condition"].unique(), default=df["condition"].unique()
)

# ===== Filtered Dataset =====
filtered_df = df[(df["fragrance"] == selected_fragrance) & (df["condition"].isin(condition))]

st.title("📊 Fragrance Deal Dashboard")
st.subheader(f"{selected_fragrance}")

if filtered_df.empty:
    st.warning("No data available for this selection.")
else:
    # ===== Stats =====
    mean_price = filtered_df["price_usd"].mean()
    stdev_price = filtered_df["price_usd"].std()
    min_price = filtered_df["price_usd"].min()
    max_price = filtered_df["price_usd"].max()
    threshold = mean_price - stdev_price

    st.markdown(f"""
    **Summary Statistics:**
    - Mean price: ${mean_price:.2f}  
    - Std Dev: ${stdev_price:.2f}  
    - Min price: ${min_price:.2f}  
    - Max price: ${max_price:.2f}  
    - 🔔 Deal threshold: **${threshold:.2f} or lower**
    """)

    # ===== Histogram =====
    fig = px.histogram(
        filtered_df,
        x="price_usd",
        nbins=20,
        title=f"Price Distribution for {selected_fragrance}",
        labels={"price_usd": "Price (USD)"},
    )
    fig.add_vline(x=threshold, line_dash="dash", line_color="red", annotation_text="Deal threshold")
    st.plotly_chart(fig, use_container_width=True)

    # ===== User Alerts =====
    st.markdown("### Set an Alert")
    alert = st.checkbox("Notify me when a new deal appears below the threshold")
    if alert:
        st.success(f"✅ Alert set for {selected_fragrance}! (to be wired to Discord/email)")
