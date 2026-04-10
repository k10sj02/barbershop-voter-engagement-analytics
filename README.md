# Barbershop Voter Engagement Analytics

**[🔗 Live App](https://sutv-analytics.streamlit.app)** &nbsp;·&nbsp; **[📋 Shape Up The Vote](https://www.shapeupthevote.org)**

---

## Overview

Shape Up The Vote (SUTV) is a non-partisan campaign that activates barbershops and salons as voter engagement hubs in their communities. Barbers and stylists are uniquely positioned for relational organizing — they are trusted community leaders with established relationships with their clients and a natural space for conversation.

In 2024, SUTV ran its most data-intensive campaign to date, shifting from in-person organizing to a fully digital, multi-channel outreach model across 13 swing states.

### 2024 Program Impact

| Metric | Result |
|--------|--------|
| States | 14 |
| Cities | 600 |
| Congressional Districts | 127 |
| Kits Mailed | 14,500 |
| Confirmed Participants | 4,000 |
| Barbers/Stylists Contacted | 113,000 |
| Conversations with Participants | 23,000 |
| Estimated Shop Impressions | 950,000 |
| Estimated Voting Conversations | 200,000 |
| Estimated Voting Commitments | 45,000 |

---

## My Contributions

The work I owned on this project fell into two areas: **lead generation** and **service density analysis**. Both fed directly into how the campaign decided where to focus outreach and which shops to contact first.

### 1. Lead Generation — Zip Code Coverage Analysis

I was tasked with identifying which zip codes across all 13 swing states were under-covered in the scraped dataset — i.e., where we didn't have enough shop data to run effective outreach. This involved:

- Joining scraped shop data to US Census demographic data at the zip code level in BigQuery (via Hex)
- Building a **state-specific density benchmark** for each of the 13 target states, rather than relying on the static national industry average (1:773) which undercounts urban density
- Deriving a normalized **Service Density KPI** (0–1) to measure how well each locality was covered relative to its state benchmark
- Producing a CSV of all under-covered zips across all 13 swing states for the data team and organizers

### 2. Service Density KPI — Methodology

**State benchmark formula:**
```
state_benchmark = state_population / total_licensed_salons_in_state
```

Rather than using the national average, each state gets its own benchmark based on actual licensed salon density. For example, Pennsylvania's benchmark (1:638) is meaningfully denser than the national figure (1:773) — using the national average would make Philadelphia look better-covered than it actually is.

**KPI formula:**
```
people_per_scraped_shop = locality_population / scraped_shop_count
KPI = min(state_benchmark / people_per_scraped_shop, 1.0)
```

| KPI | Status | Meaning |
|-----|--------|---------|
| ≥ 1.0 | ✅ Adequate | Meets or exceeds the state benchmark — ready for outreach |
| 0.5–1.0 | 🟠 Partial | Coverage gap — more scraping needed before outreach |
| < 0.5 | 🔴 Severely Under | Critical gap — data collection must be prioritized |

**Example — Philadelphia zip 19132:**
```
people_per_scraped_shop = 22,000 / 28 = 785.7
KPI = min(638 / 785.7, 1.0) = 0.81  →  🟠 Partial coverage
```

### 3. Zip Code Prioritization

Beyond coverage, I also contributed to flagging which zip codes should be prioritized for outreach based on demographics. This was grounded in the campaign's targeting framework:

```python
high_priority_zip = (pct_black > 0.30) | (pct_nonwhite > 0.50)
```

Secondary signals used: median household income, educational attainment, median age, and organizer recommendations.

### 4. Interactive Streamlit App (this repo)

To make the analysis accessible and reusable, I built this Streamlit app on top of the pipeline. It surfaces three views:

- **State Overview** — salon density across all 13 states vs. the national benchmark, filterable by Wave 1 / Wave 2
- **Service Density KPI Calculator** — live calculator where you can input any city's population and scraped shop count and see the KPI computed in real time with a state-level comparison
- **Zip Code Prioritization** — filterable table of zip codes by state, priority flag, income ceiling, and non-white population floor

The app uses a synthetic dataset that mirrors the real schema (real zip codes and city names, plausible Census-derived demographics) so it runs fully without credentials.

### 5. Portfolio Notebooks

Two Jupyter notebooks document the analytical methodology end-to-end with synthetic data:

- `salonbarbershop_density_portfolio.ipynb` — state benchmark calculations, Service Density KPI derivation, city-level coverage analysis
- `sutv_city_and_zipcode_prioritization_portfolio.ipynb` — zip code enrichment, demographic scoring, priority flagging, output to CSV

---

## Full Data Infrastructure

The following documents the broader data infrastructure I worked within. This was built and owned by the data engineering team; I'm including it here to give full context to the system and because understanding it was essential to doing my own work effectively.

### Data & Tooling Evolution

| Era | Lead Gen | Tooling | Challenges |
|-----|----------|---------|------------|
| **Pre-2024** | Manual (in-person), state license files | Airtable CRM, Spoke (texting) | Bifurcated channels, data spread across Google Drive |
| **2024** | Google Places API, Bing API, state license files, past participants | Airtable + ThruText sync, lead gen scripts, master database, dbt | Cold mail targeting, list pulling |
| **2025+** | Same + self-serve lead gen | Same + self-serve list pulling, dbt-managed pipelines | Scaling organizer capacity |

### Program Flow

```
SOURCE                    RECRUIT                    ONBOARD         ORGANIZE
──────                    ───────                    ───────         ────────
Google/Bing APIs          Targeting +   ──▶ Cold Mail               Confirmation
State License Files  ──▶  Data Quality  ──▶ SMS / Phone  ──▶ Mail   │ Receipt / Display / Convos
Past Participants         (diamond)     ──▶ Instagram        SUTV   │
Other Sources                           ──▶ Website/Inbound  Kit    Asks
                                        ──▶ Referrals               │ 'Make a plan?' / IG post
                                                                     │ Election info / Organizer 1:1s
                                                                     │
                                                                     Deeper Asks
                                                                       Convo guide + tracker
                                                                       Virtual rally / Advisory Council
                                                                       Ask clients to text 5 friends
```

### Master Database Architecture

```
Google SMBs         ─ ─ ─ ─▶ ┐
State License Files ─ ─ ─ ─▶ │                    ┌──▶ Stones Phones ─ ─▶ ┐
Voter Files         ─ ─ ─ ─▶ ├──▶ Master DB ──▶ List Pulls ──▶ Marquadt Mail ─ ─▶ ├──▶ CRM
Geo Data            ─ ─ ─ ─▶ ┘        ▲            └──▶ ThruText    ◀──────────────┘ ▲
                                       └─────────────────────────────────────────────────┘
                                                         (automated feedback loop)

── automated        - - semi-automated (requires data team)
```

### Current State — Full Pipeline

```
                    ┌─────────────────────┐
                    │ Data Cleaning &     │
                    │ Validation (Smarty) │
                    └──────────┬──────────┘
                               │
Google Places ─────────────────▼──────┐
State License Files ───────────────── ├──▶ BigQuery ──▶ dbt ──▶ GDrive ──▶ Stone's Phones ──▶ ┐
         ▲                            │                    │                                    │
    SmartMatch (manual)               │                    ├──▶ GDrive ──▶ Cold Mail      ──▶ ├──▶ Mother DB ──▶ CRM
                                      └──────────────────── │                                    │         │
                                                            └──▶ GDrive ──▶ Cold ThruText  ──▶ ┘         │
                                                                                                          │
                                                                             Hex Reporting ◀──────────────┘
                                                                                                          │
                                             CRM downstream (all manual): ◀───────────────────────────────┘
                                             Airtable Reporting · IG DMs · List Pulls
                                             Phone Follow-Ups · ThruText Follow-Ups · Kit Requests
```

Key architectural decisions:
- **BigQuery → dbt → GDrive** is the transformation and staging layer before each outreach channel
- **Only confirmed participants** are loaded into Airtable CRM — not raw leads
- **Hex Reporting** sits downstream of the Mother DB — reflects the consolidated participant view
- The CRM fans out to **six downstream consumers**, all manual

### dbt Layer

dbt (`sutv-dbt` repo) was the transformation backbone, sitting between raw BigQuery ingestion and the final models consumed by outreach tools and reporting.

**Deduplication models** — the primary use case. Raw leads from Google Places and Bing contained significant duplication. dbt produced clean, deduplicated views as the source of truth for all downstream list pulls. Priority order for resolving dupes:
1. Mobile numbers over landlines
2. Google Places over Bing
3. Records with more complete data (has website, more fields populated)

**Reference models:**

| Model | Description |
|-------|-------------|
| `reference.target_zips` | All US zip codes with priority tier flags (1–4) and boolean targeting fields |
| `reference.us_zips` | All US zip codes with full Census demographic data |
| `reference.zip_cd_crosswalk` | Zip code → congressional district mapping |
| `reference.district_urbanization_2022` | Congressional district urbanization index and political lean (PVI) |

**KTLO backlog:** fix lead dupe edge cases, move ThruText external table generation into dbt, move engagement reporting into dbt, re-implement engagement level definitions.

### Messaging Campaign Analytics Pipeline

```
GetThru / ThruText    AWS S3              Google Cloud                  Hex Dashboard
──────────────────    ──────              ────────────                  ─────────────
Text banking    ──▶   Nightly      ──▶   GCS bucket    ──▶   BQ   ──▶  SUTV Messaging
platform              export (8am)        (9am UTC)           views     Campaign Dashboard
                                          via STS             (PII
                                                              removed)
```

ThruText exported four CSV files nightly to AWS S3 (`caller_activity_details`, `daily_messages`, `daily_surveys`, `opt_outs`). Google Cloud STS transferred these to GCS daily at 9am UTC. Scheduled BigQuery queries ran at 10am UTC producing PII-stripped views with address fields parsed via regex into city/state/zipcode. Hex connected to these views for the live campaign dashboard.

### BigQuery Schema

| Dataset | Key Tables | Description |
|---------|-----------|-------------|
| `lead_generation` | `google_places`, `raw_bing_api` | Raw scraped leads — contains dupes, unique ID is `place_id` / phone |
| `sutv` | `sutv_leads`, `sutv_leads_2` | All leads, deduped with validated address info. `shop_id` is unique |
| `thrutext_validation` | `sutv_leads_validation` | ThruText phone validation — `carrier_type` (mobile/voip/landline) is the key column |
| `address_validation` | `smarty_validation` | Smarty address validation. `delivery_point_barcode` = unique mailable address |
| `past_participants` | `sms_2020`, `sms_2022`, `phone_2020`, `phone_2022` | Past participant records by year and channel |
| `reference` | `target_zips`, `us_zips`, `zip_cd_crosswalk`, `district_urbanization_2022` | Static lookup tables |
| `airtable` | `ALL` | Nightly CRM sync via pyairtable |
| `data_pulls` | `ALL` | All data pulls for Stone's Phones, ThruText, etc. |
| `thrutext_exports` | `messages_view`, `surveys_view` | Cleaned ThruText exports (PII removed, address parsed) |

**Key derived fields:** `shop_id` (phone stripped of non-numerics), `carrier_type`, `population_by_race_nonwhite_percentage`, `high_priority_zip`, `pvi_22`, `urbanindex` / `urban_type`.

### Targeting Framework

**4-tier prioritization:**

| Tier | Criteria | Available Channels |
|------|----------|--------------------|
| **Tier 1** | Blanket area AND priority zip | Cold Mail + SMS + Cold Phone |
| **Tier 2** | Blanket area ONLY | Cold Mail + SMS + Cold Phone |
| **Tier 3** | Priority zip ONLY | Cold Mail + SMS + Cold Phone |
| **Tier 4** | Neither | SMS Only |

**Priority zip:** `>30% Black population OR >50% non-white population`

**Negative criteria (excluded regardless of tier):** out of business · invalid phone AND unmailable address · national franchise (GreatClips, SuperCuts) · wrong vertical

### Channel Conversion Performance

| Channel | Leads | Participants | Conversion | Cost/Participant |
|---------|-------|-------------|------------|----------------|
| SMS (ThruText) | 90,967 | 558 | 0.61% | $10 |
| Phone | 13,900 | 317 | 2.2% | $29 |
| Cold Mail | 13,472 | 3,069 | 22.78% | $88 |

Google/Bing API data converted at far higher rates than state license files (15% vs 0.7%).

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
├── app.py                                                # Streamlit app
├── requirements.txt
├── README.md
├── salonbarbershop_density_portfolio.ipynb               # Density analysis (portfolio)
├── sutv_city_and_zipcode_prioritization_portfolio.ipynb  # Prioritization (portfolio)
└── archive/                                              # Original Hex notebooks
    ├── salonbarbershop_density_by_cityneighborhoodzipcode.ipynb
    └── sutv_city_and_zipcode_prioritization.ipynb
```

> **Note on data:** Portfolio notebooks use a synthetic dataset mirroring the real schema — real zip codes and city names, plausible demographics from Census distributions. The original pipeline connected to live BigQuery tables and Google Cloud Storage. Proprietary shop and participant data is not included.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data Collection | Pline.io, Google Places API (~$0.15/lead), Bing API (free), State License Files |
| Address Validation | Smarty API |
| Contact Enrichment | TargetSmart / SmartMatch (voter file matching), ThruText (phone validation) |
| Transformation & Modeling | **dbt** (`sutv-dbt` repo) — deduplication, reference models, zip targeting |
| Data Warehouse | Google BigQuery |
| Data Storage | Google Cloud Storage, AWS S3, Google Drive |
| Data Transfer | Google Storage Transfer Service (STS) |
| CRM | Airtable + ThruText sync (pyairtable nightly) |
| Analysis & Notebooks | Python (pandas, numpy, dask), SQL, Hex |
| Cold Mail Vendor | Marquadt Mail |
| Phone Recruitment | Stone's Phones |
| Messaging Platform | GetThru / ThruText |
| Dashboard / App | Streamlit, Matplotlib |

---

*Paid for by Progressive Turnout Project and not authorized by any candidate or candidate's committee.*