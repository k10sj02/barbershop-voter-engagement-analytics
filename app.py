import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mtick

# ── Page config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Shape Up The Vote | Data Explorer",
    page_icon="✂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Styling ────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Mono:wght@400;500&family=DM+Sans:wght@300;400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'DM Sans', sans-serif;
}

/* Background */
.stApp {
    background-color: #0f0f0f;
    color: #f0ece3;
}

/* Sidebar */
[data-testid="stSidebar"] {
    background-color: #1a1a1a;
    border-right: 1px solid #2a2a2a;
}
[data-testid="stSidebar"] * {
    color: #f0ece3 !important;
}

/* Hero header */
.hero {
    padding: 2.5rem 0 1.5rem 0;
    border-bottom: 1px solid #2a2a2a;
    margin-bottom: 2rem;
}
.hero-tag {
    font-family: 'DM Mono', monospace;
    font-size: 0.9rem;
    letter-spacing: 0.18em;
    text-transform: uppercase;
    color: #c8f55a;
    margin-bottom: 0.8rem;
}
.hero-title {
    font-family: 'Syne', sans-serif;
    font-size: 4.5rem;
    font-weight: 800;
    color: #f0ece3;
    line-height: 1.05;
    margin-bottom: 1rem;
}
.hero-title span {
    color: #c8f55a;
}
.hero-sub {
    font-size: 1.45rem;
    color: #bbb;
    font-weight: 300;
    max-width: 620px;
    line-height: 1.6;
}

/* Section headers */
.section-label {
    font-family: 'DM Mono', monospace;
    font-size: 0.8rem;
    letter-spacing: 0.2em;
    text-transform: uppercase;
    color: #c8f55a;
    margin-bottom: 0.4rem;
}
.section-title {
    font-family: 'Syne', sans-serif;
    font-size: 1.8rem;
    font-weight: 700;
    color: #f0ece3;
    margin-bottom: 0.3rem;
}

/* Metric cards */
.metric-card {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    padding: 1.4rem 1.2rem;
    margin-bottom: 0.5rem;
    min-width: 0;
    overflow: hidden;
}
.metric-value {
    font-family: 'Syne', sans-serif;
    font-size: clamp(1.6rem, 2.5vw, 2.8rem);
    font-weight: 800;
    color: #c8f55a;
    line-height: 1;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}
.metric-label {
    font-family: 'DM Mono', monospace;
    font-size: clamp(0.75rem, 1.1vw, 0.80rem);
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #aaa;
    margin-top: 0.5rem;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* KPI gauge */
.kpi-display {
    background: #1a1a1a;
    border: 1px solid #2a2a2a;
    border-radius: 12px;
    padding: 2rem;
    text-align: center;
}
.kpi-number {
    font-family: 'Syne', sans-serif;
    font-size: 4rem;
    font-weight: 800;
    line-height: 1;
}
.kpi-status {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.15em;
    text-transform: uppercase;
    margin-top: 0.5rem;
}

/* Pill badges */
.pill-high {
    background: #2a1a1a;
    color: #ff6b6b;
    border: 1px solid #ff6b6b44;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
}
.pill-standard {
    background: #1a2a1a;
    color: #c8f55a;
    border: 1px solid #c8f55a44;
    padding: 2px 10px;
    border-radius: 20px;
    font-family: 'DM Mono', monospace;
    font-size: 0.7rem;
    letter-spacing: 0.1em;
}

/* Divider */
hr { border-color: #2a2a2a; }

/* Streamlit overrides */
.stSelectbox label, .stSlider label, .stRadio label { 
    color: #888 !important; 
    font-family: 'DM Mono', monospace !important;
    font-size: 0.72rem !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
}
[data-testid="stMetricValue"] {
    font-family: 'Syne', sans-serif !important;
    color: #c8f55a !important;
}
.stDataFrame { border: 1px solid #2a2a2a; border-radius: 8px; }

/* Nav pills in sidebar */
.nav-item {
    font-family: 'DM Mono', monospace;
    font-size: 0.75rem;
    letter-spacing: 0.1em;
    text-transform: uppercase;
}

/* Footnote */
.footnote {
    font-family: 'DM Mono', monospace;
    font-size: 0.65rem;
    color: #444;
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #2a2a2a;
}
</style>
""", unsafe_allow_html=True)

# ── Shared data ────────────────────────────────────────────────────────────────
NATIONAL_BENCHMARK = 343_477_335 / 444_102  # ~773

STATE_STATS = pd.DataFrame([
    ("AZ", "Arizona",        8_875,  7_431_344, "Wave 2"),
    ("GA", "Georgia",       13_656, 11_029_227, "Wave 1"),
    ("NV", "Nevada",         3_422,  3_194_176, "Wave 1"),
    ("MI", "Michigan",      11_492, 10_037_261, "Wave 1"),
    ("NC", "North Carolina",16_200, 10_835_491, "Wave 1"),
    ("PA", "Pennsylvania",  20_322, 12_961_683, "Wave 1"),
    ("WI", "Wisconsin",      8_637,  5_892_539, "Wave 1"),
    ("OH", "Ohio",          15_647, 11_785_935, "Wave 1"),
    ("CO", "Colorado",       6_661,  5_839_926, "Wave 2"),
    ("FL", "Florida",       40_060, 22_244_823, "Wave 2"),
    ("TX", "Texas",         32_578, 30_029_572, "Wave 2"),
    ("VA", "Virginia",       7_630,  8_683_619, "Wave 2"),
    ("NH", "New Hampshire",  1_625,  1_395_231, "Wave 2"),
], columns=["state", "state_name", "total_salons", "population", "wave"])

STATE_STATS["people_per_salon"] = (
    STATE_STATS["population"] / STATE_STATS["total_salons"]
).round(0).astype(int)

ZIP_DATA = pd.DataFrame([
    ("30301","Atlanta","GA",42000,0.72,38000,0.31,31,True),
    ("30303","Atlanta","GA",18000,0.78,34000,0.28,29,True),
    ("30310","Atlanta","GA",25000,0.11,72000,0.55,36,False),
    ("30318","Atlanta","GA",31000,0.59,51000,0.40,33,True),
    ("30324","Atlanta","GA",29000,0.38,63000,0.50,35,True),
    ("30060","Marietta","GA",38000,0.55,49000,0.37,34,True),
    ("30067","Marietta","GA",27000,0.29,68000,0.53,38,False),
    ("19103","Philadelphia","PA",33000,0.42,61000,0.52,32,True),
    ("19121","Philadelphia","PA",28000,0.81,29000,0.21,28,True),
    ("19132","Philadelphia","PA",22000,0.92,25000,0.15,30,True),
    ("19140","Philadelphia","PA",36000,0.88,27000,0.13,29,True),
    ("19143","Philadelphia","PA",41000,0.69,33000,0.24,31,True),
    ("19401","Norristown","PA",19000,0.56,47000,0.34,33,True),
    ("48201","Detroit","MI",15000,0.89,22000,0.18,27,True),
    ("48205","Detroit","MI",24000,0.95,20000,0.12,28,True),
    ("48213","Detroit","MI",27000,0.91,23000,0.14,30,True),
    ("48227","Detroit","MI",31000,0.93,21000,0.11,29,True),
    ("48235","Detroit","MI",26000,0.86,28000,0.19,31,True),
    ("48033","Southfield","MI",34000,0.78,45000,0.38,36,True),
    ("28202","Charlotte","NC",20000,0.51,55000,0.48,30,True),
    ("28206","Charlotte","NC",29000,0.69,37000,0.28,31,True),
    ("28208","Charlotte","NC",33000,0.73,34000,0.24,30,True),
    ("28212","Charlotte","NC",37000,0.62,39000,0.27,32,True),
    ("28217","Charlotte","NC",28000,0.57,41000,0.31,33,True),
    ("43201","Columbus","OH",22000,0.45,42000,0.43,28,True),
    ("43205","Columbus","OH",19000,0.76,30000,0.22,27,True),
    ("43211","Columbus","OH",27000,0.82,27000,0.16,29,True),
    ("43219","Columbus","OH",31000,0.67,34000,0.24,31,True),
    ("85003","Phoenix","AZ",17000,0.59,32000,0.26,29,True),
    ("85006","Phoenix","AZ",28000,0.71,29000,0.18,28,True),
    ("85008","Phoenix","AZ",34000,0.65,34000,0.22,31,True),
    ("85040","Phoenix","AZ",29000,0.48,47000,0.31,33,True),
    ("89101","Las Vegas","NV",26000,0.70,28000,0.17,30,True),
    ("89104","Las Vegas","NV",31000,0.68,31000,0.19,31,True),
    ("89106","Las Vegas","NV",24000,0.73,26000,0.15,29,True),
    ("89121","Las Vegas","NV",38000,0.56,38000,0.25,33,True),
    ("53202","Milwaukee","WI",18000,0.28,57000,0.51,32,False),
    ("53206","Milwaukee","WI",21000,0.95,22000,0.11,28,True),
    ("53209","Milwaukee","WI",27000,0.88,27000,0.14,30,True),
    ("53215","Milwaukee","WI",31000,0.80,31000,0.18,31,True),
    ("33101","Miami","FL",29000,0.82,30000,0.21,30,True),
    ("33125","Miami","FL",37000,0.88,27000,0.15,29,True),
    ("33602","Tampa","FL",22000,0.50,48000,0.40,31,True),
    ("33610","Tampa","FL",34000,0.73,31000,0.19,30,True),
    ("77002","Houston","TX",20000,0.68,38000,0.36,29,True),
    ("77051","Houston","TX",31000,0.92,24000,0.13,28,True),
    ("75201","Dallas","TX",25000,0.54,55000,0.48,30,True),
    ("75216","Dallas","TX",38000,0.89,26000,0.14,29,True),
    ("23220","Richmond","VA",22000,0.62,42000,0.38,28,True),
    ("23224","Richmond","VA",27000,0.77,30000,0.20,30,True),
    ("22201","Arlington","VA",30000,0.39,88000,0.72,33,False),
    ("80204","Denver","CO",25000,0.64,40000,0.34,30,True),
    ("80216","Denver","CO",29000,0.73,34000,0.22,31,True),
    ("80229","Thornton","CO",33000,0.56,52000,0.30,33,True),
    ("03101","Manchester","NH",18000,0.32,48000,0.32,33,False),
    ("03103","Manchester","NH",22000,0.40,44000,0.28,32,False),
], columns=["zipcode","city","state","population","pct_nonwhite",
            "median_hh_income","pct_bachelors","median_age","high_priority"])

LOCALITY_DATA = pd.DataFrame([
    ("Philadelphia","19121","PA",28000,45),
    ("Philadelphia","19132","PA",22000,28),
    ("Philadelphia","19140","PA",36000,52),
    ("Philadelphia","19143","PA",41000,61),
    ("Philadelphia","19103","PA",33000,87),
    ("Atlanta",     "30301","GA",42000,95),
    ("Atlanta",     "30303","GA",18000,30),
    ("Atlanta",     "30310","GA",25000,38),
    ("Atlanta",     "30318","GA",31000,55),
    ("Detroit",     "48201","MI",15000,18),
    ("Detroit",     "48205","MI",24000,22),
    ("Detroit",     "48213","MI",27000,25),
    ("Detroit",     "48227","MI",31000,29),
    ("Charlotte",   "28206","NC",29000,47),
    ("Charlotte",   "28208","NC",33000,55),
    ("Charlotte",   "28212","NC",37000,60),
    ("Columbus",    "43205","OH",19000,21),
    ("Columbus",    "43211","OH",27000,30),
], columns=["city","zip_code","state","population","scraped_shops"])

def calc_kpi(people_per_shop, benchmark):
    if people_per_shop == 0:
        return 0.0
    return min(benchmark / people_per_shop, 1.0)

LOCALITY_DATA = LOCALITY_DATA.merge(
    STATE_STATS[["state","people_per_salon"]].rename(columns={"people_per_salon":"benchmark"}),
    on="state", how="left"
)
LOCALITY_DATA["people_per_shop"] = (LOCALITY_DATA["population"] / LOCALITY_DATA["scraped_shops"]).round(1)
LOCALITY_DATA["kpi"] = LOCALITY_DATA.apply(
    lambda r: calc_kpi(r["people_per_shop"], r["benchmark"]), axis=1
).round(3)
LOCALITY_DATA["coverage"] = LOCALITY_DATA["kpi"].apply(
    lambda k: "Adequate"     if k >= 1.0 else
              "Near"         if k >= 0.8 else
              "Under"        if k >= 0.5 else
              "Severely Under"
)

# ── Matplotlib dark theme ──────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.facecolor":  "#1a1a1a",
    "axes.facecolor":    "#1a1a1a",
    "axes.edgecolor":    "#333333",
    "axes.labelcolor":   "#dddddd",
    "xtick.color":       "#dddddd",
    "ytick.color":       "#dddddd",
    "xtick.labelsize":   14,
    "ytick.labelsize":   14,
    "text.color":        "#f0ece3",
    "grid.color":        "#2a2a2a",
    "grid.linestyle":    "--",
    "font.family":       "DejaVu Sans",
    "font.size":         14,
    "axes.titlesize":    17,
    "axes.titleweight":  "bold",
    "axes.titlepad":     20,
    "axes.labelsize":    14,
    "axes.labelpad":     10,
    "figure.autolayout": True,
})

# ── Sidebar nav ────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("""
    <div style='padding: 1rem 0 1.5rem 0; border-bottom: 1px solid #2a2a2a; margin-bottom: 1.5rem;'>
        <div style='font-family: Syne, sans-serif; font-size: 1.1rem; font-weight: 800; color: #f0ece3;'>✂️ SUTV</div>
        <div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #555; letter-spacing: 0.15em; text-transform: uppercase;'>Shape Up The Vote</div>
    </div>
    """, unsafe_allow_html=True)

    page = st.radio(
        "NAVIGATE",
        ["State Overview", "KPI Calculator", "Zip Prioritization"],
        label_visibility="visible"
    )

    st.markdown("""
    <div style='margin-top: 2rem; padding-top: 1.5rem; border-top: 1px solid #2a2a2a;'>
        <div style='font-family: DM Mono, monospace; font-size: 0.6rem; color: #444; letter-spacing: 0.1em; text-transform: uppercase; line-height: 1.8;'>
            13 Target States<br>
            5,500 Target Shops<br>
            186,805 Est. Shops Total<br><br>
            <span style='color: #c8f55a;'>● Wave 1</span> AZ GA NV MI NC PA WI OH<br>
            <span style='color: #888;'>● Wave 2</span> CO FL TX VA NH
        </div>
    </div>
    """, unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
# PAGE 1 — STATE OVERVIEW
# ══════════════════════════════════════════════════════════════════════════════
if page == "State Overview":

    st.markdown("""
    <div class='hero'>
        <div class='hero-tag'>Shape Up The Vote · 2024</div>
        <div class='hero-title'>State <span>Overview</span></div>
        <div class='hero-sub'>Salon & barbershop density across 13 swing states — measured against the national benchmark.</div>
    </div>
    """, unsafe_allow_html=True)

    # Top metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>186,805</div>
            <div class='metric-label'>Est. Shops in Swing States</div>
        </div>""", unsafe_allow_html=True)
    with col2:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>13</div>
            <div class='metric-label'>Target States</div>
        </div>""", unsafe_allow_html=True)
    with col3:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>5,500</div>
            <div class='metric-label'>Shops to Engage</div>
        </div>""", unsafe_allow_html=True)
    with col4:
        st.markdown("""
        <div class='metric-card'>
            <div class='metric-value'>1:773</div>
            <div class='metric-label'>National Benchmark</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<hr>", unsafe_allow_html=True)

    # Filters
    col_f1, col_f2 = st.columns([1, 3])
    with col_f1:
        wave_filter = st.radio("FILTER BY WAVE", ["All", "Wave 1", "Wave 2"])

    filtered = STATE_STATS if wave_filter == "All" else STATE_STATS[STATE_STATS["wave"] == wave_filter]
    filtered = filtered.sort_values("people_per_salon")

    # Chart
    fig, ax = plt.subplots(figsize=(12, 6))
    colors = ["#c8f55a" if w == "Wave 1" else "#F58518" for w in filtered["wave"]]
    bars = ax.bar(filtered["state"], filtered["people_per_salon"], color=colors, width=0.65, zorder=3)
    ax.axhline(NATIONAL_BENCHMARK, color="#ff6b6b", linestyle="--", linewidth=1.5,
               label=f"National avg  1:{NATIONAL_BENCHMARK:.0f}", zorder=4)
    ax.set_ylabel("People per Salon / Barbershop", fontsize=10)
    ax.set_title("State Salon Density vs. National Average\nlower = more salons per capita", 
                 fontsize=11, pad=12)
    ax.yaxis.grid(True, zorder=0)
    ax.set_axisbelow(True)
    for bar, val in zip(bars, filtered["people_per_salon"]):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 8,
                f"1:{val}", ha="center", va="bottom", fontsize=12, color="#ddd")
    wave1 = mpatches.Patch(color="#c8f55a", label="Wave 1")
    wave2 = mpatches.Patch(color="#F58518", label="Wave 2")
    nat   = mpatches.Patch(color="#ff6b6b", label=f"National avg 1:{NATIONAL_BENCHMARK:.0f}")
    ax.legend(handles=[wave1, wave2, nat], fontsize=12, facecolor="#1a1a1a", edgecolor="#333", labelcolor="#ddd")
    fig.patch.set_facecolor("#1a1a1a")
    plt.tight_layout()
    st.pyplot(fig)
    plt.close()

    st.markdown("<hr>", unsafe_allow_html=True)

    # Table
    st.markdown("<div class='section-label'>Raw Data</div>", unsafe_allow_html=True)
    display_df = filtered[["state","state_name","wave","total_salons","population","people_per_salon"]].copy()
    display_df.columns = ["State","Name","Wave","Total Salons","Population (2023)","People / Salon"]
    display_df["Population (2023)"] = display_df["Population (2023)"].apply(lambda x: f"{x:,}")
    display_df["Total Salons"] = display_df["Total Salons"].apply(lambda x: f"{x:,}")
    display_df["People / Salon"] = display_df["People / Salon"].apply(lambda x: f"1:{x:,}")
    st.dataframe(display_df, use_container_width=True, hide_index=True)

    st.markdown("""
    <div class='footnote'>
        Source: SalonSpaConnection.com Hair Salon Industry Statistics (2023) · US Census Bureau (2023) · 
        National benchmark derived from 444,102 licensed salons across 343M population.
    </div>
    """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 2 — KPI CALCULATOR
# ══════════════════════════════════════════════════════════════════════════════
elif page == "KPI Calculator":

    st.markdown("""
    <div class='hero'>
        <div class='hero-tag'>Shape Up The Vote · Methodology</div>
        <div class='hero-title'>Service Density <span>KPI</span></div>
        <div class='hero-sub'>How well does our scraped dataset cover a given locality? Input a city's stats to find out.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#1a1a1a; border:1px solid #2a2a2a; border-radius:8px; padding:1.2rem 1.5rem; margin-bottom:1.5rem;'>
        <div style='font-family: DM Mono, monospace; font-size: 0.65rem; color: #c8f55a; letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.6rem;'>Formula</div>
        <div style='font-family: DM Mono, monospace; font-size: 0.9rem; color: #f0ece3;'>
            KPI = min( state_benchmark / actual_people_per_shop,  1.0 )
        </div>
        <div style='font-family: DM Sans, sans-serif; font-size: 0.82rem; color: #666; margin-top:0.6rem;'>
            KPI ≥ 1.0 → adequate coverage &nbsp;·&nbsp; KPI < 0.5 → severely under-scraped
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_in, col_out = st.columns([1, 1], gap="large")

    with col_in:
        st.markdown("<div class='section-label'>Inputs</div>", unsafe_allow_html=True)

        state_sel = st.selectbox(
            "STATE",
            STATE_STATS["state"].tolist(),
            format_func=lambda s: f"{s} — {STATE_STATS.loc[STATE_STATS['state']==s,'state_name'].values[0]}"
        )
        city_name = st.text_input("CITY NAME", value="Philadelphia")
        population = st.number_input("POPULATION", min_value=1000, max_value=10_000_000,
                                      value=28000, step=1000)
        scraped_shops = st.number_input("SCRAPED SHOPS IN DATASET", min_value=1, max_value=10000,
                                         value=45, step=5)

        benchmark = int(STATE_STATS.loc[STATE_STATS["state"] == state_sel, "people_per_salon"].values[0])
        total_state_salons = int(STATE_STATS.loc[STATE_STATS["state"] == state_sel, "total_salons"].values[0])

        st.markdown(f"""
        <div style='margin-top:1rem; padding:1rem; background:#111; border-radius:6px; 
                    font-family: DM Mono, monospace; font-size: 0.72rem; color:#555; line-height:2;'>
            State benchmark&nbsp;&nbsp;&nbsp; 1:{benchmark:,} people/salon<br>
            Total state salons&nbsp; {total_state_salons:,}<br>
            National avg&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1:{NATIONAL_BENCHMARK:.0f}
        </div>
        """, unsafe_allow_html=True)

    with col_out:
        st.markdown("<div class='section-label'>Result</div>", unsafe_allow_html=True)

        people_per_shop = population / scraped_shops
        kpi = calc_kpi(people_per_shop, benchmark)
        pct = int(kpi * 100)

        if kpi >= 1.0:
            kpi_color = "#c8f55a"
            status = "✅  Adequate Coverage"
            status_color = "#c8f55a"
            advice = "Dataset meets the state benchmark. Coverage is sufficient for this locality."
        elif kpi >= 0.8:
            kpi_color = "#EECA3B"
            status = "🟡  Near Benchmark"
            status_color = "#EECA3B"
            advice = "Close to benchmark. Minor gaps — consider light additional scraping."
        elif kpi >= 0.5:
            kpi_color = "#F58518"
            status = "🟠  Under-Scraped"
            status_color = "#F58518"
            advice = "Meaningful coverage gap. More scraping needed before outreach."
        else:
            kpi_color = "#E45756"
            status = "🔴  Severely Under-Scraped"
            status_color = "#E45756"
            advice = "Critical gap. Data collection must be prioritized here before launch."

        st.markdown(f"""
        <div class='kpi-display'>
            <div style='font-family: DM Mono, monospace; font-size:0.65rem; color:#555; 
                        letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.8rem;'>
                {city_name}, {state_sel}
            </div>
            <div class='kpi-number' style='color:{kpi_color};'>{kpi:.2f}</div>
            <div class='kpi-status' style='color:{status_color}; margin-top:0.6rem;'>{status}</div>
        </div>
        """, unsafe_allow_html=True)

        # Progress bar
        st.markdown("<div style='height:0.8rem'></div>", unsafe_allow_html=True)
        fig2, ax2 = plt.subplots(figsize=(5, 0.6))
        ax2.barh([0], [min(kpi, 1.0)], color=kpi_color, height=0.5)
        ax2.barh([0], [1.0], color="#2a2a2a", height=0.5)
        ax2.barh([0], [min(kpi, 1.0)], color=kpi_color, height=0.5)
        ax2.set_xlim(0, 1)
        ax2.axis("off")
        fig2.patch.set_facecolor("#1a1a1a")
        plt.tight_layout(pad=0)
        st.pyplot(fig2, use_container_width=True)
        plt.close()

        st.markdown(f"""
        <div style='margin-top:1rem; padding:1rem; background:#111; border-radius:6px;
                    font-family: DM Mono, monospace; font-size: 0.72rem; color:#555; line-height:2;'>
            Population&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {population:,}<br>
            Scraped shops&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; {scraped_shops:,}<br>
            People / shop&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; 1:{people_per_shop:,.0f}<br>
            State benchmark&nbsp;&nbsp; 1:{benchmark:,}<br>
            <span style='color:#888;'>→ {advice}</span>
        </div>
        """, unsafe_allow_html=True)

    # Benchmark comparison chart
    st.markdown("<hr>", unsafe_allow_html=True)
    st.markdown("<div class='section-label'>How does this city compare?</div>", unsafe_allow_html=True)

    compare_data = LOCALITY_DATA[LOCALITY_DATA["state"] == state_sel].copy()
    if len(compare_data) > 0:
        # Add current input as a new row for comparison
        new_row = pd.DataFrame([{
            "city": city_name, "zip_code": "—", "state": state_sel,
            "population": population, "scraped_shops": scraped_shops,
            "benchmark": benchmark,
            "people_per_shop": people_per_shop,
            "kpi": kpi, "coverage": status.split("  ")[-1]
        }])
        compare_data = pd.concat([compare_data, new_row], ignore_index=True).sort_values("kpi")

        fig3, ax3 = plt.subplots(figsize=(9, max(4, len(compare_data) * 0.65)))
        bar_colors = []
        for _, row in compare_data.iterrows():
            if row["city"] == city_name and row["zip_code"] == "—":
                bar_colors.append("#ffffff")
            elif row["kpi"] >= 1.0:
                bar_colors.append("#c8f55a")
            elif row["kpi"] >= 0.8:
                bar_colors.append("#EECA3B")
            elif row["kpi"] >= 0.5:
                bar_colors.append("#F58518")
            else:
                bar_colors.append("#E45756")

        labels = [f"{r['city']} {r['zip_code']}" for _, r in compare_data.iterrows()]
        bars3 = ax3.barh(labels, compare_data["kpi"], color=bar_colors)
        ax3.axvline(1.0, color="#555", linestyle="--", linewidth=1)
        ax3.set_xlim(0, 1.15)
        ax3.set_xlabel("Service Density KPI")
        ax3.set_title(f"{state_sel} — Locality Coverage Comparison\n(white bar = your input)", fontsize=15, fontweight="bold")
        for bar, val in zip(bars3, compare_data["kpi"]):
            ax3.text(bar.get_width() + 0.01, bar.get_y() + bar.get_height()/2,
                     f"{val:.2f}", va="center", fontsize=12, color="#ddd")
        fig3.patch.set_facecolor("#1a1a1a")
        plt.tight_layout()
        st.pyplot(fig3)
        plt.close()
    else:
        st.info("No comparison localities available for this state in the demo dataset.")


# ══════════════════════════════════════════════════════════════════════════════
# PAGE 3 — ZIP PRIORITIZATION
# ══════════════════════════════════════════════════════════════════════════════
elif page == "Zip Prioritization":

    st.markdown("""
    <div class='hero'>
        <div class='hero-tag'>Shape Up The Vote · Targeting</div>
        <div class='hero-title'>Zip Code <span>Prioritization</span></div>
        <div class='hero-sub'>Flag high-priority zip codes based on demographics — communities most likely to benefit from voter engagement.</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div style='background:#1a1a1a; border:1px solid #2a2a2a; border-radius:8px; 
                padding:1.2rem 1.5rem; margin-bottom:1.5rem;'>
        <div style='font-family: DM Mono, monospace; font-size: 0.65rem; color: #c8f55a; 
                    letter-spacing:0.15em; text-transform:uppercase; margin-bottom:0.5rem;'>Hypothesis</div>
        <div style='font-family: DM Sans, sans-serif; font-size: 0.9rem; color: #aaa; font-style:italic;'>
            "Young people, as well as people with less education and lower incomes, will be less likely 
            to cast a ballot in any given election."
        </div>
        <div style='font-family: DM Mono, monospace; font-size: 0.65rem; color: #444; margin-top:0.5rem;'>
            Source: Elections Canada — Correlates of Voter Turnout
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Filters row
    col_f1, col_f2, col_f3, col_f4 = st.columns(4)
    with col_f1:
        states_available = sorted(ZIP_DATA["state"].unique())
        sel_states = st.multiselect("STATE", states_available, default=["GA","PA","MI"])
    with col_f2:
        priority_filter = st.radio("PRIORITY", ["All", "High Priority Only", "Standard Only"])
    with col_f3:
        income_max = st.slider("MAX MEDIAN INCOME ($)", 20000, 100000, 100000, step=5000,
                                format="$%d")
    with col_f4:
        nonwhite_min = st.slider("MIN % NON-WHITE", 0, 100, 0, step=5, format="%d%%")

    # Apply filters
    df = ZIP_DATA.copy()
    if sel_states:
        df = df[df["state"].isin(sel_states)]
    if priority_filter == "High Priority Only":
        df = df[df["high_priority"] == True]
    elif priority_filter == "Standard Only":
        df = df[df["high_priority"] == False]
    df = df[df["median_hh_income"] <= income_max]
    df = df[df["pct_nonwhite"] >= nonwhite_min / 100]

    # Summary bar
    total = len(df)
    high = df["high_priority"].sum()
    st.markdown(f"""
    <div style='display:flex; gap:1rem; margin: 1rem 0; flex-wrap:wrap;'>
        <div style='font-family:DM Mono,monospace; font-size:0.75rem; color:#f0ece3;'>
            <span style='color:#c8f55a; font-size:1.2rem; font-family:Syne,sans-serif; font-weight:800;'>{total}</span>
            &nbsp;zip codes matched
        </div>
        <div style='font-family:DM Mono,monospace; font-size:0.75rem; color:#f0ece3;'>
            <span style='color:#ff6b6b; font-size:1.2rem; font-family:Syne,sans-serif; font-weight:800;'>{high}</span>
            &nbsp;high-priority
        </div>
        <div style='font-family:DM Mono,monospace; font-size:0.75rem; color:#f0ece3;'>
            <span style='color:#c8f55a; font-size:1.2rem; font-family:Syne,sans-serif; font-weight:800;'>{total - high}</span>
            &nbsp;standard
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Chart — priority breakdown by state
    if len(df) > 0:
        pivot = df.groupby(["state","high_priority"]).size().unstack(fill_value=0).reset_index()
        if True not in pivot.columns:
            pivot[True] = 0
        if False not in pivot.columns:
            pivot[False] = 0
        pivot = pivot.sort_values(True, ascending=False)

        fig4, ax4 = plt.subplots(figsize=(10, 5))
        x = range(len(pivot))
        ax4.bar(x, pivot[True], color="#E45756", label="High Priority", zorder=3)
        ax4.bar(x, pivot[False], bottom=pivot[True], color="#4C78A8", label="Standard", zorder=3)
        ax4.set_xticks(list(x))
        ax4.set_xticklabels(pivot["state"])
        ax4.set_ylabel("Number of Zip Codes")
        ax4.set_title("Priority Breakdown by State", fontsize=11)
        ax4.yaxis.grid(True, zorder=0)
        ax4.legend(facecolor="#1a1a1a", edgecolor="#333", fontsize=12, labelcolor="#ddd")
        fig4.patch.set_facecolor("#1a1a1a")
        plt.tight_layout()
        st.pyplot(fig4)
        plt.close()

    st.markdown("<hr>", unsafe_allow_html=True)

    # Data table
    st.markdown("<div class='section-label'>Zip Code Detail</div>", unsafe_allow_html=True)

    display = df[["zipcode","city","state","population","pct_nonwhite",
                  "median_hh_income","median_age","high_priority"]].copy()
    display.columns = ["ZIP","City","State","Population","% Non-White",
                       "Median HH Income","Median Age","High Priority"]
    display["Population"]       = display["Population"].apply(lambda x: f"{x:,}")
    display["% Non-White"]      = display["% Non-White"].apply(lambda x: f"{x*100:.0f}%")
    display["Median HH Income"] = display["Median HH Income"].apply(lambda x: f"${x:,}")
    display["High Priority"]    = display["High Priority"].apply(lambda x: "✅ Yes" if x else "No")

    st.dataframe(display, use_container_width=True, hide_index=True)

    st.markdown("""
    <div class='footnote'>
        High-priority threshold: >33% non-white population. 
        Synthetic data — real zip codes, plausible demographics drawn from Census distributions.
        Original pipeline used US Census API + Hex for enrichment.
    </div>
    """, unsafe_allow_html=True)