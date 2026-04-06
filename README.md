# Barbershop Voter Engagement Analytics

> Turning barbershop chairs into ballot boxes. End-to-end data pipeline and interactive explorer built for Shape Up The Vote's 2024 national voter engagement campaign across 13 swing states.

**[🔗 Live App](https://sutv-analytics.streamlit.app)** &nbsp;·&nbsp; **[📋 Shape Up The Vote](https://www.shapeupthevote.org)**

---

## Overview

Shape Up The Vote (SUTV) is a non-partisan campaign that activates barbershops and salons as voter engagement hubs in their communities. In 2024, the program launched across 13 swing states with a goal of engaging 5,500 participating shops.

This project covers the full data lifecycle: collecting shop data via web scraping, cleaning and enriching it with Census demographics, prioritizing the highest-impact zip codes and cities for outreach, and surfacing insights through an interactive Streamlit dashboard.

**Target States:** AZ, GA, NV, MI, NC, PA, WI, OH, CO, FL, TX, VA, NH  
**Est. Shops in Swing States:** 186,805  
**Target Shops to Engage:** 5,500

---

## Data Pipeline

The project involved two parallel pipelines — one for shop data collection and prioritization, and one for messaging campaign analytics.

### Pipeline 1: Shop Data Collection & Prioritization

```
Google / Bing API          Hex (Python + SQL)         Google Cloud Storage
─────────────────          ──────────────────         ────────────────────
Pline.io scraper    ──▶    Clean & deduplicate  ──▶   high_priority_zips.csv
(shop listings)            Enrich w/ Census API
                           Score & rank shops
                           by density KPI
```

**Step 1 — Data Collection**  
Shop listings (name, address, phone number) were scraped from Google Places and Bing using the Pline.io Chrome extension across all 13 target states. Raw data was stored in Google Drive.

**Step 2 — Cleaning & Enrichment**  
In Hex, the raw data was deduplicated using `osm_id` as a unique key, phone numbers were normalized using regex (`regexp_replace(PhoneNumber, r'\D', '')`), and zip codes were standardized to 5 digits. Each record was then joined to US Census API data to enrich with population, race, income, education, and age demographics at the zip code level.

**Step 3 — Analysis & Prioritization**  
SQL queries in BigQuery joined enriched shop records to zip code demographics. Python (pandas) in Hex was used to score and rank localities. Final output — a prioritized list of zip codes and shops — was exported to Google Cloud Storage as `high_priority_zips.csv`.

---

### Pipeline 2: Messaging Campaign Analytics (SUTV Dashboard)

```
GetThru / ThruText    AWS S3           Google Cloud              Hex Dashboard
──────────────────    ──────           ────────────              ─────────────
Text banking    ──▶   Nightly   ──▶   GCS bucket   ──▶   BQ  ──▶  SUTV Messaging
platform              export           (9am UTC)          views     Campaign Dashboard
                      (8am UTC)        via STS            (PII
                                                          removed)
```

**Step 1 — GetThru / ThruText Export**  
ThruText (a peer-to-peer text banking platform) supported nightly exports to AWS S3 but not directly to Google Cloud. GetThru support was engaged to configure automated nightly exports, delivering four CSV files to S3 daily at 8am UTC: `caller_activity_details`, `daily_messages`, `daily_surveys`, and `opt_outs`.

**Step 2 — S3 to GCS via Storage Transfer Service**  
Since the rest of the analytics infrastructure lived in GCP, Google Cloud's Storage Transfer Service (STS) was configured to run a daily batch transfer from S3 to a GCS bucket (`thrutext-exports`) at 9am UTC. The GCS bucket mirrors the S3 structure exactly.

**Step 3 — BigQuery Ingestion & PII Removal**  
External tables in BigQuery (`messages`, `surveys`) read directly from GCS using auto-detected schemas. Scheduled queries ran daily at 10am UTC to produce cleaned views (`messages_view`, `surveys_view`) that: stripped all personally identifiable information (names, contact details), and used regex to parse the `address` column into separate `city`, `state`, and `zipcode` fields:

```sql
REGEXP_EXTRACT(address, r'([A-Za-z\.]{3}[A-Za-z\.]*),*\s+(?:[A-Za-z]{2})') AS city,
UPPER(REGEXP_EXTRACT(address, r'\s+([A-Za-z]{2})(?:,?\s*\d+(?:[-\s]\d+)?)?\s*$')) AS state,
REGEXP_EXTRACT(address, r'\s+(?:[A-Za-z]{2},?\s*)(\d{5})(?:[-\s]\d+)*\s*$') AS zipcode
```

**Step 4 — Hex Dashboard**  
Hex connected directly to the BigQuery views to power the SUTV Messaging Campaign Dashboard, tracking sent texts, response rates, conversations, and survey respondents by state — refreshing daily in sync with the scheduled queries.

---

## Methodology

### 1. State-Level Salon Density Benchmark

Rather than relying on the static US industry benchmark of 1 salon per 1,500–2,000 people (which undercounts urban density), this project derives a **state-specific benchmark** for each of the 13 target states.

**Formula:**
```
state_benchmark = state_population / total_licensed_salons_in_state
```

Source: [SalonSpaConnection.com Hair Salon Industry Statistics (2023)](https://salonspaconnection.com/beauty-hair-salon-industry-statistics-in-2023/) for state totals; US Census Bureau for population.

**Example — Pennsylvania:**
```
state_benchmark = 12,961,683 / 20,322 = 1:638
```
PA's benchmark of 1:638 is denser than the national average (1:773), meaning Pennsylvania has more salons per capita than the country as a whole. Using the national average here would undercount expected coverage.

**Why state-specific?**  
Each state has different market saturation, licensing rates, and urban/rural mix. A single national figure obscures these differences and produces misleading coverage assessments at the city level.

---

### 2. Service Density KPI

For each locality (city or zip code), a normalized **Service Density KPI** between 0 and 1 measures how well the scraped dataset covers the expected number of shops relative to the state benchmark.

**Formula:**
```
people_per_scraped_shop = locality_population / scraped_shop_count
KPI = min(state_benchmark / people_per_scraped_shop, 1.0)
```

**Interpretation:**

| KPI Range | Status | Meaning |
|-----------|--------|---------|
| ≥ 1.0 | ✅ Adequate | Meets or exceeds the state benchmark — coverage is sufficient |
| 0.8–1.0 | 🟡 Near | Minor gap — light additional scraping recommended |
| 0.5–0.8 | 🟠 Under-scraped | Meaningful coverage gap — more scraping needed before outreach |
| < 0.5 | 🔴 Severely Under | Critical gap — data collection must be prioritized here |

**Example — Philadelphia zip 19132:**
```
people_per_scraped_shop = 22,000 / 28 = 785.7
KPI = min(638 / 785.7, 1.0) = 0.81  →  🟡 Near benchmark
```

---

### 3. Zip Code Prioritization

Zip codes were flagged as **high-priority** based on the hypothesis that communities of color and lower-income areas are historically underserved in voter engagement:

> *"Young people, as well as people with less education and lower incomes, will be less likely to cast a ballot in any given election."*  
> — [Elections Canada, Correlates of Voter Turnout](https://www.elections.ca/content.aspx?section=res&dir=rec/part/tud&document=correlates&lang=e)

**Primary flag — Non-white population threshold:**
```python
high_priority_zip = population_by_race_nonwhite_percentage > 0.33
```

Zip codes where more than 33% of residents identify as non-white were flagged as high-priority, reflecting communities that are disproportionately underrepresented in voter registration and turnout data.

**Supporting signals considered:**
- Median household income (lower income → lower historical turnout)
- Educational attainment (lower bachelor's degree rates → lower turnout)
- Median age (younger populations → lower turnout)

**Data source:** US Census API, accessed via Hex, enriched at the zip code level.

---

## Interactive App

The Streamlit app surfaces these analyses interactively across three pages:

**State Overview** — Bar chart of all 13 states benchmarked against the national average (1:773), filterable by Wave 1 / Wave 2 launch states, with a full data table.

**Service Density KPI Calculator** — Live calculator: input any city, state, population, and scraped shop count to compute the KPI in real time, with a color-coded gauge and comparison against other localities in the same state.

**Zip Code Prioritization** — Filterable table of zip codes by state, priority flag, median household income ceiling, and non-white population floor, with a stacked priority breakdown chart by state.

---

## Running Locally

```bash
git clone https://github.com/k10sj02/barbershop-voter-engagement-analytics.git
cd barbershop-voter-engagement-analytics

uv venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
uv pip install -r requirements.txt
streamlit run app.py
```

---

## Repo Structure

```
.
├── app.py                                          # Streamlit app
├── requirements.txt                                # Python dependencies
├── README.md
├── salonbarbershop_density_portfolio.ipynb         # Density analysis (portfolio version)
├── sutv_city_and_zipcode_prioritization_portfolio.ipynb  # Prioritization (portfolio version)
├── archive/                                        # Original Hex notebooks (read-only)
│   ├── salonbarbershop_density_by_cityneighborhoodzipcode.ipynb
│   └── sutv_city_and_zipcode_prioritization.ipynb
└── presentation/                                   # Supporting documentation
```

> **Note on data:** The portfolio notebooks use a synthetic dataset that mirrors the real schema — real zip codes and city names, with plausible demographic values drawn from Census distributions. The original pipeline connected to live BigQuery tables (`sutv.*`) and Google Cloud Storage. Proprietary shop data is not included.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data Collection | Pline.io, Google Places API, Bing API |
| Data Storage | Google Cloud Storage, AWS S3 |
| Data Transfer | Google Storage Transfer Service (STS) |
| Data Warehouse | Google BigQuery |
| Analysis & Notebooks | Python (pandas, numpy), SQL, Hex |
| Dashboard / App | Streamlit, Matplotlib |
| Messaging Platform | GetThru / ThruText |

---

*Paid for by Progressive Turnout Project and not authorized by any candidate or candidate's committee.*