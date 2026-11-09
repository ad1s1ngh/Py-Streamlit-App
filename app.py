import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Page config
st.set_page_config(
    page_title="Motorcycle Performance Dashboard",
    page_icon="🏍️",
    layout="wide"
)

# Set matplotlib style
plt.style.use('seaborn-v0_8-whitegrid' if 'seaborn-v0_8-whitegrid' in plt.style.available else 'default')


# Load and clean dataset
@st.cache_data
def load_data():
    try:
        df = pd.read_csv("all_bikez_curated.csv")
    except FileNotFoundError:
        df = pd.read_csv("all_bikez_raw.csv")

    df.columns = df.columns.str.strip()

    # Extract numerical displacement
    if 'Displacement' in df.columns:
        df['Displacement_cc'] = pd.to_numeric(
            df['Displacement'].astype(str).str.extract(r'([\d\.]+)')[0], errors='coerce'
        )
    elif 'Engine size' in df.columns:
        df['Displacement_cc'] = pd.to_numeric(
            df['Engine size'].astype(str).str.extract(r'([\d\.]+)')[0], errors='coerce'
        )
    else:
        df['Displacement_cc'] = pd.to_numeric(df.select_dtypes(include=['float64', 'int64']).iloc[:, 0], errors='coerce')

    # Extract power
    if 'Power' in df.columns:
        df['Power_hp'] = pd.to_numeric(
            df['Power'].astype(str).str.extract(r'([\d\.]+)')[0], errors='coerce'
        )
    else:
        df['Power_hp'] = None

    # Clean year and brand
    if 'Year' in df.columns:
        df['Year'] = pd.to_numeric(df['Year'], errors='coerce')

    if 'Brand' in df.columns:
        df['Brand_Clean'] = df['Brand']
    elif 'Make' in df.columns:
        df['Brand_Clean'] = df['Make']
    else:
        df['Brand_Clean'] = "Unknown"

    if 'Category' in df.columns:
        df['Category_Clean'] = df['Category']
    elif 'Type' in df.columns:
        df['Category_Clean'] = df['Type']
    else:
        df['Category_Clean'] = "General"

    return df

df_raw = load_data()


# Sidebar controls
st.sidebar.title("Filters")

# Brand filter
available_brands = sorted(df_raw['Brand_Clean'].dropna().unique())
selected_brands = st.sidebar.multiselect(
    "Select Brands:",
    options=available_brands,
    default=available_brands[:5] if len(available_brands) >= 5 else available_brands
)

# Year filter
min_year = int(df_raw['Year'].min()) if df_raw['Year'].notna().any() else 1900
max_year = int(df_raw['Year'].max()) if df_raw['Year'].notna().any() else 2026
selected_years = st.sidebar.slider(
    "Production Year:",
    min_value=min_year,
    max_value=max_year,
    value=(max(min_year, 1990), max_year)
)

# CC filter
min_cc = float(df_raw['Displacement_cc'].min()) if df_raw['Displacement_cc'].notna().any() else 0.0
max_cc = float(df_raw['Displacement_cc'].max()) if df_raw['Displacement_cc'].notna().any() else 2500.0
selected_cc = st.sidebar.slider(
    "Engine Capacity (cc):",
    min_value=0.0,
    max_value=max(max_cc, 1000.0),
    value=(0.0, max(max_cc, 1000.0))
)

# Filter dataset
filtered_df = df_raw.copy()

if selected_brands:
    filtered_df = filtered_df[filtered_df['Brand_Clean'].isin(selected_brands)]

filtered_df = filtered_df[
    (filtered_df['Year'] >= selected_years[0]) &
    (filtered_df['Year'] <= selected_years[1])
]

if 'Displacement_cc' in filtered_df.columns:
    filtered_df = filtered_df[
        (filtered_df['Displacement_cc'] >= selected_cc[0]) &
        (filtered_df['Displacement_cc'] <= selected_cc[1])
    ]


# Dashboard Title & Metrics
st.title("Motorcycle Performance Analytics")

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric("Total Models", f"{len(filtered_df):,}")
with col2:
    avg_cc = filtered_df['Displacement_cc'].mean() if 'Displacement_cc' in filtered_df.columns else 0
    st.metric("Avg Displacement", f"{avg_cc:.1f} cc" if pd.notna(avg_cc) else "N/A")
with col3:
    avg_hp = filtered_df['Power_hp'].mean() if 'Power_hp' in filtered_df.columns and filtered_df['Power_hp'].notna().any() else None
    st.metric("Avg Power", f"{avg_hp:.1f} HP" if avg_hp else "N/A")
with col4:
    st.metric("Brands Selected", f"{filtered_df['Brand_Clean'].nunique()}")

st.markdown("---")

# Tabs layout
tab1, tab2, tab3, tab4 = st.tabs(["Overview", "Comparative Plots", "Trends", "Insights"])


# TAB 1: Dataset Overview
with tab1:
    st.subheader("Filtered Dataset View")
    st.write(f"Showing {len(filtered_df)} entries.")

    with st.expander("Show Data Table", expanded=True):
        st.dataframe(filtered_df, use_container_width=True)

    col_a, col_b = st.columns(2)
    with col_a:
        st.write("**Category Counts**")
        cat_counts = filtered_df['Category_Clean'].value_counts().reset_index()
        cat_counts.columns = ['Category', 'Count']
        st.dataframe(cat_counts, use_container_width=True)

    with col_b:
        st.write("**Summary Stats**")
        st.dataframe(filtered_df.describe().T[['mean', 'std', 'min', '50%', 'max']], use_container_width=True)


# TAB 2: Visualizations with Matplotlib
with tab2:
    st.subheader("Performance Comparisons")
    col_v1, col_v2 = st.columns(2)

    # Bar plot: Top brands by avg displacement
    with col_v1:
        st.write("##### Top Brands by Avg Displacement (cc)")
        brand_cc = filtered_df.groupby('Brand_Clean')['Displacement_cc'].mean().dropna()
        brand_cc = brand_cc.sort_values(ascending=False).head(10)

        fig, ax = plt.subplots(figsize=(6, 4))
        ax.bar(brand_cc.index, brand_cc.values, color='#2b5c8f')
        ax.set_ylabel("Avg Displacement (cc)")
        ax.tick_params(axis='x', rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

    # Scatter plot: Displacement vs Power
    with col_v2:
        st.write("##### Engine Size (cc) vs Power (HP)")
        valid_scatter = filtered_df.dropna(subset=['Displacement_cc', 'Power_hp'])

        if not valid_scatter.empty:
            fig, ax = plt.subplots(figsize=(6, 4))
            ax.scatter(valid_scatter['Displacement_cc'], valid_scatter['Power_hp'], alpha=0.6, color='#d95f02')
            ax.set_xlabel("Displacement (cc)")
            ax.set_ylabel("Power (HP)")
            plt.tight_layout()
            st.pyplot(fig)
        else:
            st.info("Power data not available for scatter plot.")


# TAB 3: Line Chart Trend
with tab3:
    st.subheader("Historical Trends")
    st.write("##### Avg Engine Displacement Over Time")

    year_trend = filtered_df.groupby('Year')['Displacement_cc'].agg(['mean', 'count']).dropna()
    year_trend = year_trend[year_trend['count'] >= 2]

    if not year_trend.empty:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.plot(year_trend.index, year_trend['mean'], marker='o', color='#e41a1c', linewidth=2)
        ax.set_xlabel("Year")
        ax.set_ylabel("Avg Displacement (cc)")
        plt.tight_layout()
        st.pyplot(fig)
    else:
        st.info("Insufficient timeline data available.")


# TAB 4: Summary Insights
with tab4:
    st.subheader("Insights & Recommendations")
    st.markdown("""
    * **Displacement vs Power:** Larger displacement engines show a strong upward trend in total horsepower output.
    * **Market Shift:** Mid-range motorcycles (300cc–650cc) show consistent representation across modern production years.
    * **Inventory Strategy:** Focus mass-market offerings on the 300cc–600cc segment while reserving 1000cc+ models for high-performance enthusiast categories.
    """)
