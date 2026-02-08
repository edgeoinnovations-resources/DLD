import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

st.set_page_config(
    page_title="DLD Land Requests Dashboard",
    page_icon="🏗️",
    layout="wide",
)

st.title("Dubai Land Department — Map Requests Dashboard")


@st.cache_data
def load_data():
    df = pd.read_csv("Map_Requests.csv", dtype=str)
    df["request_date"] = pd.to_datetime(df["request_date"], format="%m/%d/%Y %H:%M:%S", errors="coerce")
    df["year"] = df["request_date"].dt.year
    df["month"] = df["request_date"].dt.to_period("M").astype(str)
    df["no_of_siteplans"] = pd.to_numeric(df["no_of_siteplans"], errors="coerce")
    return df


df = load_data()

# ── Sidebar filters ──────────────────────────────────────────────────────────
st.sidebar.header("Filters")

year_min, year_max = int(df["year"].min()), int(df["year"].max())
year_range = st.sidebar.slider("Year range", year_min, year_max, (year_min, year_max))

all_procedures = sorted(df["procedure_name_en"].dropna().unique())
selected_procedures = st.sidebar.multiselect("Procedure", all_procedures, default=[])

all_property_types = sorted(df["property_type_en"].dropna().unique())
selected_property_types = st.sidebar.multiselect("Property type", all_property_types, default=[])

all_sources = sorted(df["request_source_en"].dropna().unique())
selected_sources = st.sidebar.multiselect("Request source", all_sources, default=[])

all_apps = sorted(df["sub_service_application_en"].dropna().unique())
selected_apps = st.sidebar.multiselect("Application", all_apps, default=[])

# Apply filters
mask = df["year"].between(year_range[0], year_range[1])
if selected_procedures:
    mask &= df["procedure_name_en"].isin(selected_procedures)
if selected_property_types:
    mask &= df["property_type_en"].isin(selected_property_types)
if selected_sources:
    mask &= df["request_source_en"].isin(selected_sources)
if selected_apps:
    mask &= df["sub_service_application_en"].isin(selected_apps)

filtered = df[mask]

# ── KPI row ──────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total requests", f"{len(filtered):,}")
k2.metric("Unique procedures", filtered["procedure_name_en"].nunique())
k3.metric("Total site-plans", f"{int(filtered['no_of_siteplans'].sum()):,}")
k4.metric("Date range", f"{year_range[0]}–{year_range[1]}")

st.divider()

# ── Row 1: Requests over time + by property type ────────────────────────────
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Requests over time")
    time_agg = st.radio("Aggregate by", ["Year", "Month"], horizontal=True, key="time_agg")
    if time_agg == "Year":
        ts = filtered.groupby("year").size().reset_index(name="count")
        fig = px.bar(ts, x="year", y="count", labels={"year": "Year", "count": "Requests"})
    else:
        ts = filtered.groupby("month").size().reset_index(name="count")
        fig = px.line(ts, x="month", y="count", labels={"month": "Month", "count": "Requests"})
        fig.update_xaxes(tickangle=-45, dtick=6)
    fig.update_layout(margin=dict(t=10, b=40))
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("By property type")
    pt = filtered["property_type_en"].value_counts().reset_index()
    pt.columns = ["type", "count"]
    fig2 = px.pie(pt, names="type", values="count", hole=0.4)
    fig2.update_layout(margin=dict(t=10, b=10))
    st.plotly_chart(fig2, use_container_width=True)

# ── Row 2: Top procedures + request sources ─────────────────────────────────
col3, col4 = st.columns(2)

with col3:
    st.subheader("Top 15 procedures")
    top_proc = filtered["procedure_name_en"].value_counts().head(15).reset_index()
    top_proc.columns = ["procedure", "count"]
    fig3 = px.bar(top_proc, x="count", y="procedure", orientation="h",
                  labels={"procedure": "", "count": "Requests"})
    fig3.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=10, l=10))
    st.plotly_chart(fig3, use_container_width=True)

with col4:
    st.subheader("Request sources")
    src = filtered["request_source_en"].value_counts().reset_index()
    src.columns = ["source", "count"]
    fig4 = px.bar(src, x="count", y="source", orientation="h",
                  labels={"source": "", "count": "Requests"})
    fig4.update_layout(yaxis=dict(autorange="reversed"), margin=dict(t=10, l=10))
    st.plotly_chart(fig4, use_container_width=True)

# ── Row 3: Procedure × Property heatmap ─────────────────────────────────────
st.subheader("Procedure vs Property type (top 15 procedures)")
top15 = filtered["procedure_name_en"].value_counts().head(15).index
heat = filtered[filtered["procedure_name_en"].isin(top15)]
cross = pd.crosstab(heat["procedure_name_en"], heat["property_type_en"])
fig5 = px.imshow(
    cross,
    labels=dict(x="Property type", y="Procedure", color="Count"),
    aspect="auto",
    color_continuous_scale="Blues",
)
fig5.update_layout(margin=dict(t=10, b=10))
st.plotly_chart(fig5, use_container_width=True)

# ── Row 4: Yearly trend by property type ────────────────────────────────────
st.subheader("Yearly trend by property type")
yr_pt = filtered.groupby(["year", "property_type_en"]).size().reset_index(name="count")
fig6 = px.area(yr_pt, x="year", y="count", color="property_type_en",
               labels={"year": "Year", "count": "Requests", "property_type_en": "Property type"})
fig6.update_layout(margin=dict(t=10, b=10))
st.plotly_chart(fig6, use_container_width=True)

# ── Row 5: Application breakdown ────────────────────────────────────────────
st.subheader("Application channel breakdown over time")
yr_app = filtered.groupby(["year", "sub_service_application_en"]).size().reset_index(name="count")
fig7 = px.bar(yr_app, x="year", y="count", color="sub_service_application_en",
              labels={"year": "Year", "count": "Requests", "sub_service_application_en": "Application"})
fig7.update_layout(margin=dict(t=10, b=10))
st.plotly_chart(fig7, use_container_width=True)

# ── Raw data explorer ────────────────────────────────────────────────────────
with st.expander("Browse filtered data"):
    st.dataframe(filtered.head(1000), use_container_width=True)

st.caption(f"Showing {len(filtered):,} of {len(df):,} total records.")
