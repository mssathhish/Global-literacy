import streamlit as st
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Page Config ──
st.set_page_config(page_title="Global Literacy Analytics", page_icon="📚", layout="wide")

# ── Database Connection ──
@st.cache_resource
def get_conn():
    return sqlite3.connect(r"D:\AIML\Global_project\literacy_data.db", check_same_thread=False)

conn = get_conn()

def run_query(sql, params=()):
    return pd.read_sql_query(sql, conn, params=params)

# ── Sidebar ──
st.sidebar.title("📚 Navigation")
page = st.sidebar.radio("Go to", [
    "🌍 Global Overview",
    "🔎 SQL Query Runner",
    "🗺️ Country Profile"
])
st.sidebar.markdown("---")
st.sidebar.caption("Global Literacy & Education Trends")

# ══════════════════════════════════════════════
# PAGE 1 — GLOBAL OVERVIEW (EDA Visualizations)
# ══════════════════════════════════════════════
if page == "🌍 Global Overview":
    st.title("🌍 Global Literacy & Education Overview")
    st.caption("Insights powered by SQL + Plotly")

    # Year filter
    years = run_query("SELECT DISTINCT year FROM literacy_rates ORDER BY year")["year"].tolist()
    sel_year = st.select_slider("Select Year", options=years, value=max(years))

    st.markdown("---")

    # KPI cards
    k1, k2, k3, k4 = st.columns(4)
    avg_lit = run_query("SELECT ROUND(AVG(adult_literacy_rate),2) v FROM literacy_rates WHERE year=?", (sel_year,))["v"].iloc[0]
    avg_gdp = run_query("SELECT ROUND(AVG(gdp_per_capita),2) v FROM gdp_schooling WHERE year=?", (sel_year,))["v"].iloc[0]
    avg_sch = run_query("SELECT ROUND(AVG(avg_years_schooling),2) v FROM gdp_schooling WHERE year=?", (sel_year,))["v"].iloc[0]
    n_countries = run_query("SELECT COUNT(DISTINCT country) v FROM literacy_rates WHERE year=?", (sel_year,))["v"].iloc[0]

    k1.metric("📖 Avg Adult Literacy", f"{avg_lit}%" if avg_lit else "N/A")
    k2.metric("💰 Avg GDP per Capita", f"${avg_gdp:,.0f}" if avg_gdp else "N/A")
    k3.metric("🏫 Avg Schooling Years", f"{avg_sch} yrs" if avg_sch else "N/A")
    k4.metric("🌐 Countries Covered", n_countries)

    st.markdown("---")
    col1, col2 = st.columns(2)

    # Top 10 & Bottom 10 literacy
    with col1:
        st.subheader(f"🏆 Top 10 Literacy Countries ({sel_year})")
        top10 = run_query("""
            SELECT country, ROUND(adult_literacy_rate,2) AS literacy
            FROM literacy_rates WHERE year=? AND adult_literacy_rate IS NOT NULL
            ORDER BY adult_literacy_rate DESC LIMIT 10
        """, (sel_year,))
        if not top10.empty:
            fig = px.bar(top10, x="literacy", y="country", orientation="h",
                         color="literacy", color_continuous_scale="Greens",
                         labels={"literacy":"Literacy Rate (%)"})
            fig.update_layout(height=380, yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader(f"⚠️ Bottom 10 Literacy Countries ({sel_year})")
        bot10 = run_query("""
            SELECT country, ROUND(adult_literacy_rate,2) AS literacy
            FROM literacy_rates WHERE year=? AND adult_literacy_rate IS NOT NULL
            ORDER BY adult_literacy_rate ASC LIMIT 10
        """, (sel_year,))
        if not bot10.empty:
            fig2 = px.bar(bot10, x="literacy", y="country", orientation="h",
                          color="literacy", color_continuous_scale="Reds_r",
                          labels={"literacy":"Literacy Rate (%)"})
            fig2.update_layout(height=380, yaxis=dict(autorange="reversed"), showlegend=False)
            st.plotly_chart(fig2, use_container_width=True)

    st.markdown("---")

    # Global literacy trend
    st.subheader("📈 Global Average Literacy Trend Over Time")
    trend = run_query("""
        SELECT year, ROUND(AVG(adult_literacy_rate),2) AS avg_literacy
        FROM literacy_rates WHERE adult_literacy_rate IS NOT NULL
        GROUP BY year ORDER BY year
    """)
    fig3 = px.line(trend, x="year", y="avg_literacy", markers=True,
                   labels={"avg_literacy":"Avg Literacy (%)", "year":"Year"},
                   color_discrete_sequence=["royalblue"])
    fig3.update_layout(height=350)
    st.plotly_chart(fig3, use_container_width=True)

    st.markdown("---")

    # GDP vs Literacy scatter
    st.subheader(f"💹 GDP per Capita vs Adult Literacy ({sel_year})")
    scatter_df = run_query("""
        SELECT l.country, ROUND(l.adult_literacy_rate,2) AS literacy,
               ROUND(g.gdp_per_capita,2) AS gdp
        FROM literacy_rates l
        JOIN gdp_schooling g ON l.country=g.country AND l.year=g.year
        WHERE l.year=? AND l.adult_literacy_rate IS NOT NULL AND g.gdp_per_capita IS NOT NULL
    """, (sel_year,))
    if not scatter_df.empty:
        fig4 = px.scatter(scatter_df, x="gdp", y="literacy", hover_name="country",
                          log_x=True, trendline="ols",
                          labels={"gdp":"GDP per Capita (log)", "literacy":"Adult Literacy (%)"},
                          color_discrete_sequence=["teal"])
        fig4.update_layout(height=400)
        st.plotly_chart(fig4, use_container_width=True)

# ══════════════════════════════════════════════
# PAGE 2 — SQL QUERY RUNNER
# ══════════════════════════════════════════════
elif page == "🔎 SQL Query Runner":
    st.title("🔎 SQL Query Runner")
    st.caption("Predefined analytical SQL queries")

    QUERIES = {
        "Q1: Top 5 Countries — Highest Adult Literacy (2020)": """
            SELECT country, ROUND(adult_literacy_rate,2) AS adult_literacy_rate
            FROM literacy_rates WHERE year=2020 AND adult_literacy_rate IS NOT NULL
            ORDER BY adult_literacy_rate DESC LIMIT 5""",

        "Q2: Countries Where Female Youth Literacy < 80%": """
            SELECT country, year, ROUND(youth_literacy_female,2) AS youth_literacy_female
            FROM literacy_rates WHERE youth_literacy_female < 80
            ORDER BY youth_literacy_female ASC LIMIT 15""",

        "Q3: Average Adult Literacy by Region": """
            SELECT SUBSTR(code,1,1) AS region_prefix,
                   COUNT(DISTINCT country) AS countries,
                   ROUND(AVG(adult_literacy_rate),2) AS avg_literacy
            FROM literacy_rates WHERE adult_literacy_rate IS NOT NULL
            GROUP BY region_prefix ORDER BY avg_literacy DESC""",

        "Q4: Countries With Illiteracy > 20% in 2000": """
            SELECT country, year, ROUND(illiteracy_pct,2) AS illiteracy_pct
            FROM illiteracy_population WHERE year=2000 AND illiteracy_pct > 20
            ORDER BY illiteracy_pct DESC LIMIT 15""",

        "Q5: Illiteracy Trend for India (2000-2020)": """
            SELECT year, ROUND(illiteracy_pct,2) AS illiteracy_pct
            FROM illiteracy_population WHERE country='India' AND year BETWEEN 2000 AND 2020
            ORDER BY year""",

        "Q6: Top 10 Countries by Illiterate Population (Latest Year)": """
            SELECT country, year, illiterate_total
            FROM illiteracy_population
            WHERE year=(SELECT MAX(year) FROM illiteracy_population)
              AND illiterate_total IS NOT NULL
            ORDER BY illiterate_total DESC LIMIT 10""",

        "Q7: High Schooling but Low GDP Countries": """
            SELECT country, year,
                   ROUND(avg_years_schooling,2) AS avg_years_schooling,
                   ROUND(gdp_per_capita,2) AS gdp_per_capita
            FROM gdp_schooling WHERE avg_years_schooling > 7 AND gdp_per_capita < 5000
            ORDER BY avg_years_schooling DESC LIMIT 15""",

        "Q8: Countries Ranked by GDP per Schooling Year (2020)": """
            SELECT country, ROUND(gdp_per_capita,2) AS gdp,
                   ROUND(avg_years_schooling,2) AS schooling,
                   ROUND(gdp_per_schooling_year,2) AS gdp_per_schooling_yr,
                   RANK() OVER (ORDER BY gdp_per_schooling_year DESC) AS rank
            FROM gdp_schooling WHERE year=2020 AND gdp_per_schooling_year IS NOT NULL
            LIMIT 15""",

        "Q9: Global Average Schooling Years Per Year": """
            SELECT year, ROUND(AVG(avg_years_schooling),2) AS global_avg_schooling
            FROM gdp_schooling WHERE avg_years_schooling IS NOT NULL
            GROUP BY year ORDER BY year""",

        "Q10: High GDP but Low Schooling Countries (2020)": """
            SELECT country, ROUND(gdp_per_capita,2) AS gdp,
                   ROUND(avg_years_schooling,2) AS schooling
            FROM gdp_schooling WHERE year=2020 AND avg_years_schooling < 6
            ORDER BY gdp_per_capita DESC LIMIT 10""",

        "Q11: High Illiteracy Despite 10+ Years Schooling": """
            SELECT i.country, i.year, i.illiterate_total,
                   ROUND(g.avg_years_schooling,2) AS avg_years_schooling
            FROM illiteracy_population i
            JOIN gdp_schooling g ON i.country=g.country AND i.year=g.year
            WHERE g.avg_years_schooling > 10 AND i.illiterate_total > 1000000
            ORDER BY i.illiterate_total DESC LIMIT 10""",

        "Q12: Literacy vs GDP — India (Last 20 Years)": """
            SELECT l.country, l.year,
                   ROUND(l.adult_literacy_rate,2) AS literacy,
                   ROUND(g.gdp_per_capita,2) AS gdp
            FROM literacy_rates l
            JOIN gdp_schooling g ON l.country=g.country AND l.year=g.year
            WHERE l.country='India' AND l.year >= 2000
            ORDER BY l.year""",

        "Q13: Youth Literacy Gender Gap — High GDP Countries (2020)": """
            SELECT l.country,
                   ROUND(l.youth_literacy_male,2) AS youth_male,
                   ROUND(l.youth_literacy_female,2) AS youth_female,
                   ROUND(l.literacy_gender_gap,2) AS gender_gap,
                   ROUND(g.gdp_per_capita,2) AS gdp
            FROM literacy_rates l
            JOIN gdp_schooling g ON l.country=g.country AND l.year=g.year
            WHERE g.year=2020 AND g.gdp_per_capita > 30000
              AND l.youth_literacy_male IS NOT NULL
            ORDER BY ABS(l.literacy_gender_gap) DESC LIMIT 15""",
    }

    selected = st.selectbox("⭐ Select a Query", list(QUERIES.keys()))
    with st.expander("🧾 View SQL"):
        st.code(QUERIES[selected], language="sql")

    if st.button("▶ Run Query"):
        try:
            result = run_query(QUERIES[selected])
            st.success(f"✅ {len(result)} rows returned")
            st.dataframe(result, use_container_width=True)

            # Auto chart for time-series
            if "year" in result.columns and len(result) > 2:
                num_cols = result.select_dtypes("number").columns.tolist()
                num_cols = [c for c in num_cols if c != "year"]
                if num_cols:
                    fig = px.line(result, x="year", y=num_cols, markers=True, title=selected)
                    st.plotly_chart(fig, use_container_width=True)
            elif len(result) > 1:
                num_cols = result.select_dtypes("number").columns.tolist()
                if num_cols and "country" in result.columns:
                    fig = px.bar(result, x="country", y=num_cols[0], title=selected,
                                 color=num_cols[0], color_continuous_scale="Blues")
                    fig.update_layout(xaxis_tickangle=-45)
                    st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.error(f"❌ Query failed: {e}")

    st.caption("⚡ Queries run directly on the SQLite database")

# ══════════════════════════════════════════════
# PAGE 3 — COUNTRY PROFILE
# ══════════════════════════════════════════════
elif page == "🗺️ Country Profile":
    st.title("🗺️ Country Profile")
    st.caption("View all literacy, GDP & schooling indicators for a country over time")

    countries = run_query("SELECT DISTINCT country FROM literacy_rates ORDER BY country")["country"].tolist()
    sel_country = st.selectbox("Select a Country", countries, index=countries.index("India") if "India" in countries else 0)

    st.markdown("---")

    # Fetch all data for selected country
    lit_df = run_query("""
        SELECT year, adult_literacy_rate, youth_literacy_male, youth_literacy_female,
               literacy_gender_gap, youth_literacy_avg, literacy_growth_rate
        FROM literacy_rates WHERE country=? ORDER BY year
    """, (sel_country,))

    gdp_df = run_query("""
        SELECT year, gdp_per_capita, avg_years_schooling, gdp_per_schooling_year
        FROM gdp_schooling WHERE country=? ORDER BY year
    """, (sel_country,))

    illit_df = run_query("""
        SELECT year, illiterate_total, illiteracy_pct
        FROM illiteracy_population WHERE country=? ORDER BY year
    """, (sel_country,))

    # KPIs
    if not lit_df.empty:
        latest = lit_df.iloc[-1]
        k1, k2, k3 = st.columns(3)
        k1.metric("📖 Latest Adult Literacy", f"{latest['adult_literacy_rate']:.1f}%" if pd.notna(latest['adult_literacy_rate']) else "N/A")
        k2.metric("👦 Youth Male Literacy",   f"{latest['youth_literacy_male']:.1f}%" if pd.notna(latest['youth_literacy_male']) else "N/A")
        k3.metric("👧 Youth Female Literacy", f"{latest['youth_literacy_female']:.1f}%" if pd.notna(latest['youth_literacy_female']) else "N/A")

    st.markdown("---")

    # Adult Literacy Trend
    if not lit_df.empty and lit_df['adult_literacy_rate'].notna().any():
        st.subheader(f"📈 Adult Literacy Rate — {sel_country}")
        fig1 = px.line(lit_df, x="year", y="adult_literacy_rate", markers=True,
                       color_discrete_sequence=["royalblue"],
                       labels={"adult_literacy_rate":"Literacy (%)"})
        fig1.update_layout(height=320)
        st.plotly_chart(fig1, use_container_width=True)

    col1, col2 = st.columns(2)

    # GDP Trend
    with col1:
        if not gdp_df.empty and gdp_df['gdp_per_capita'].notna().any():
            st.subheader("💰 GDP per Capita")
            fig2 = px.line(gdp_df, x="year", y="gdp_per_capita", markers=True,
                           color_discrete_sequence=["darkorange"],
                           labels={"gdp_per_capita":"GDP ($)"})
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)

    # Schooling Trend
    with col2:
        if not gdp_df.empty and gdp_df['avg_years_schooling'].notna().any():
            st.subheader("🏫 Avg Years of Schooling")
            fig3 = px.line(gdp_df, x="year", y="avg_years_schooling", markers=True,
                           color_discrete_sequence=["mediumseagreen"],
                           labels={"avg_years_schooling":"Years"})
            fig3.update_layout(height=300)
            st.plotly_chart(fig3, use_container_width=True)

    # Gender Gap
    if not lit_df.empty and 'literacy_gender_gap' in lit_df.columns and lit_df['literacy_gender_gap'].notna().any():
        st.subheader("⚖️ Youth Literacy Gender Gap (Male - Female)")
        fig4 = px.bar(lit_df.dropna(subset=['literacy_gender_gap']),
                      x="year", y="literacy_gender_gap",
                      color="literacy_gender_gap",
                      color_continuous_scale="RdBu_r",
                      labels={"literacy_gender_gap":"Gender Gap (%)"})
        fig4.update_layout(height=300)
        st.plotly_chart(fig4, use_container_width=True)

    # Illiteracy trend
    if not illit_df.empty and illit_df['illiteracy_pct'].notna().any():
        st.subheader("📉 Illiteracy % Over Time")
        fig5 = px.area(illit_df, x="year", y="illiteracy_pct",
                       color_discrete_sequence=["tomato"],
                       labels={"illiteracy_pct":"Illiteracy (%)"})
        fig5.update_layout(height=300)
        st.plotly_chart(fig5, use_container_width=True)

    # Raw data table
    st.markdown("---")
    st.subheader("📋 Raw Data Table")
    tab1, tab2, tab3 = st.tabs(["Literacy Rates", "GDP & Schooling", "Illiteracy Population"])
    with tab1: st.dataframe(lit_df,   use_container_width=True)
    with tab2: st.dataframe(gdp_df,   use_container_width=True)
    with tab3: st.dataframe(illit_df, use_container_width=True)
