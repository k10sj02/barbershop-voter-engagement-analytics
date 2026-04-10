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

## Data & Tooling Evolution

| Era | Lead Gen | Tooling | Challenges |
|-----|----------|---------|------------|
| **Pre-2024** | Manual (in-person), state license files | Airtable CRM, Spoke (texting) | Bifurcated channels, data spread across Google Drive |
| **2024** | Google Places API, Bing API, state license files, past participants | Airtable + ThruText sync, lead gen scripts, master database, dbt | Cold mail targeting, list pulling |
| **2025+** | Same + self-serve lead gen | Same + self-serve list pulling, dbt-managed pipelines | Scaling organizer capacity |

---

## Program Flow

The full participant journey moved through four stages:

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

Key design decisions:
- The **targeting diamond** routes leads by data quality, not just demographics — contact type determines channel
- **Inbound channels** (Instagram, website, referrals) bypass the targeting funnel entirely
- The organize phase follows a structured **escalation ladder**: Confirmation → Asks → Deeper Asks

---

## Data Architecture

### Master Database — Source Inputs

```
Google SMBs         ─ ─ ─ ─▶ ┐
State License Files ─ ─ ─ ─▶ │                    ┌──▶ Stones Phones ─ ─▶ ┐
Voter Files         ─ ─ ─ ─▶ ├──▶ Master DB ──▶ List Pulls ──▶ Marquadt Mail ─ ─▶ ├──▶ CRM
Geo Data            ─ ─ ─ ─▶ ┘        ▲            └──▶ ThruText    ◀──────────────┘ ▲
                                       └─────────────────────────────────────────────────┘
                                                         (automated feedback loop)

── automated        - - semi-automated (requires data team)
```

- Four source inputs — Google SMBs, State License Files, Voter Files, Geo Data — feed the Master DB via semi-automated processes
- **Smarty** validated mailable addresses, writing results to `address_validation.smarty_validation`
- **SmartMatch** had a bidirectional manual relationship specifically with State License Files for voter file matching (restricted access due to cost)
- The **CRM → ThruText** sync and **ThruText → CRM** feedback loop were the only fully automated connections

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
- **BigQuery → dbt → GDrive** is the transformation and staging layer before each outreach channel — three separate GDrive exports, one per channel
- **Only confirmed participants** (text/phone signups and cold mail confirmations) are loaded into Airtable CRM — not raw leads
- **Hex Reporting** sits downstream of the Mother DB — reporting reflects the consolidated participant view, not raw lead data
- The CRM fans out to **six downstream consumers**, all manual

---

## dbt Layer

dbt (`sutv-dbt` repo) was the transformation backbone of the pipeline, sitting between raw BigQuery ingestion and the final models consumed by outreach tools and reporting.

### What dbt managed

**Deduplication models** — the primary use case. Raw lead data from Google Places and Bing contained significant duplication. dbt models produced clean, deduplicated views as the source of truth for all downstream list pulls:

```sql
-- Simplified example of deduplication logic in dbt
-- Full model used window functions to resolve dupes by shop_id (phone number stripped of chars)

with deduped_leads as (
    select *
    from {{ ref('sutv_leads') }}
    qualify row_number() over (
        partition by shop_id
        order by
            case when carrier_type = 'mobile' then 1
                 when carrier_type = 'voip'   then 2
                 else 3 end,                          -- prefer textable numbers
            case when source = 'google' then 1
                 when source = 'bing'   then 2
                 else 3 end,                          -- prefer Google over Bing
            has_website desc                          -- prefer more complete records
    ) = 1
)
select * from deduped_leads
```

**Reference models** — static lookup tables used across the pipeline:

| Model | Description |
|-------|-------------|
| `reference.target_zips` | All US zip codes with priority tier flags (1–4) and boolean targeting fields |
| `reference.us_zips` | All US zip codes with full Census demographic data |
| `reference.zip_cd_crosswalk` | Zip code → congressional district mapping ([source](https://github.com/OpenSourceActivismTech/us-zipcodes-congress/blob/master/zccd_hud.csv)) |
| `reference.district_urbanization_2022` | Congressional district urbanization index and political lean (PVI) |

**ThruText integration models** — after message/survey data landed in BigQuery from the S3 → GCS → BQ pipeline, dbt models were planned to manage the external table generation and sync logic (partially implemented; noted as KTLO work).

### dbt workflow

```bash
# Set up locally
cd sutv-dbt
# Follow setup instructions to configure BigQuery connection

# Run all models
dbt run

# Run specific model
dbt run --select deduped_leads

# Test
dbt test
```

### Known issues & planned improvements (KTLO backlog)

- Fix dbt pipeline to eliminate lead duplicates in edge cases
- Move ThruText external table generation into dbt
- Move engagement reporting changes into dbt
- Re-implement engagement levels to match updated definitions

---

## BigQuery Schema

The data warehouse was organized into purpose-specific datasets:

| Dataset | Key Tables | Description |
|---------|-----------|-------------|
| `lead_generation` | `google_places`, `raw_bing_api` | Raw scraped leads — contains dupes, unique ID is `place_id` / phone |
| `sutv` | `sutv_leads`, `sutv_leads_2` | All leads, deduped with validated address info. `shop_id` is unique |
| `thrutext_validation` | `sutv_leads_validation`, `sutv_leads_validation_2` | ThruText phone validation results — `carrier_type` (mobile/voip/landline) is the key column |
| `address_validation` | `smarty_validation` | Smarty address validation. `delivery_point_barcode` is a unique mailable address |
| `past_participants` | `sms_2020`, `sms_2022`, `phone_2020`, `phone_2022` | Past participant records by year and channel |
| `reference` | `target_zips`, `us_zips`, `zip_cd_crosswalk`, `district_urbanization_2022` | Static lookup tables used across the pipeline |
| `airtable` | `ALL` | Nightly sync of Airtable CRM data via pyairtable |
| `data_pulls` | `ALL` | All data pulls used for delivering lists to Stone's Phones, ThruText, etc. |
| `thrutext_exports` | `messages`, `surveys`, `messages_view`, `surveys_view` | Raw ThruText exports + cleaned views (PII removed, address parsed) |

**Key derived fields:**
- `shop_id` — phone number stripped of non-numeric characters: `regexp_replace(phone, r'\D+', '')`
- `carrier_type` — mobile / voip / landline (from ThruText validation; determines SMS eligibility)
- `population_by_race_nonwhite_percentage` — derived from Census race columns
- `high_priority_zip` — boolean flag based on demographic thresholds
- `pvi_22` — Cook Political Report Partisan Voting Index for the shop's congressional district
- `urbanindex` / `urban_type` — urbanization score and classification (e.g. "Dense Suburban")

---

## Data Pipeline (Technical Detail)

### Pipeline 1: Shop Data Collection & Prioritization

**Step 1 — Data Collection**

Two primary API sources, each with different cost/quality tradeoffs:

| Source | Cost | Quality | Limit | Notes |
|--------|------|---------|-------|-------|
| Google Places | ~$0.15/lead | Highest | None | Zip-based search, writes to `lead_generation.google_places_2` |
| Bing API | Free | High | 20 results/call | Geo-based search around lat/lon point; staged in GCS before BQ ingestion via dask |

Bing data was written to GCS (`shape-up-the-vote/raw/bing_api_{datetime}`) before being read into BigQuery. State license files and past participant CRM records were also incorporated as separate ingestion workflows.

**Step 2 — Cleaning & Enrichment**

- Phone numbers normalized: `regexp_replace(phone, r'\D+', '') as shop_id`
- Zip codes standardized to 5 digits: `left(zip_code, 5)`
- Addresses validated via **Smarty API** → `address_validation.smarty_validation`
- Each record joined to Census demographic data at zip code level
- Phone numbers validated via **ThruText** for carrier type (mobile / voip / landline)
- `shop_id` used as the deduplication key throughout

**Step 3 — dbt Transformation**

`dbt run` executed against the `sutv-dbt` repo to produce deduplicated models. Deduplication priority order:
1. Mobile numbers over landlines
2. Google Places over Bing
3. Records with more complete data (has website, has address)

**Step 4 — Targeting & Tier Assignment**

Every shop was assigned a priority tier based on two independent criteria:

| Tier | Criteria | Available Channels |
|------|----------|--------------------|
| **Tier 1** | Blanket area AND priority zip | Cold Mail + SMS + Cold Phone |
| **Tier 2** | Blanket area ONLY | Cold Mail + SMS + Cold Phone |
| **Tier 3** | Priority zip ONLY | Cold Mail + SMS + Cold Phone |
| **Tier 4** | Neither blanket nor priority zip | SMS Only |

**Priority zip definition:** `>30% Black population OR >50% non-white population`

**Blanket areas** (guaranteed presence regardless of zip demographics):

| State | Cities |
|-------|--------|
| GA | Atlanta, Augusta, Columbus, Savannah + 12 rural counties (Wilkes, Warren, Spalding, Screven, Bulloch, Evans, Glynn, Ware, Lowndes, Decatur, Baldwin, Hancock) |
| MI | Detroit, Muskegon, Flint, Saginaw, Grand Rapids (East) |
| NC | Charlotte, Raleigh, Fayetteville, Greensboro |
| PA | Philadelphia, Pittsburgh, Chester, Harrisburg, Reading, Coatesville, Aliquippa, McKeesport, Steelton, York |

**Negative criteria** — excluded regardless of tier:
- Out of business
- Invalid phone AND unmailable address
- National franchise (GreatClips, SuperCuts, etc.)
- Wrong vertical (e.g. "John Barber's Homeowner Loans")

**Data quality deduplication rules** (for duplicate mailable addresses):
1. Textable numbers over landlines
2. Google Places over Bing
3. More complete records (has website, more fields populated)

**Step 5 — Channel Assignment & Output**

Leads with a phone → direct data pull to ThruText or Stone's Phones  
Leads without a phone → SmartMatch voter file matching to find a number  
Final lists exported to Google Drive per channel; `high_priority_zips.csv` exported to GCS

---

### Pipeline 2: Messaging Campaign Analytics

**Step 1 — GetThru / ThruText Export**
Nightly exports of four CSV files to AWS S3 at 8am UTC: `caller_activity_details`, `daily_messages`, `daily_surveys`, `opt_outs`.

**Step 2 — S3 to GCS via Storage Transfer Service**
Google Cloud STS ran a daily batch transfer at 9am UTC. Scheduled through December 31, 2024.

**Step 3 — BigQuery Ingestion & PII Removal**
Scheduled queries ran daily at 10am UTC, producing `messages_view` and `surveys_view` — PII stripped, address parsed into city/state/zipcode:

```sql
REGEXP_EXTRACT(address, r'([A-Za-z\.]{3}[A-Za-z\.]*),*\s+(?:[A-Za-z]{2})') AS city,
UPPER(REGEXP_EXTRACT(address, r'\s+([A-Za-z]{2})(?:,?\s*\d+(?:[-\s]\d+)?)?\s*$')) AS state,
REGEXP_EXTRACT(address, r'\s+(?:[A-Za-z]{2},?\s*)(\d{5})(?:[-\s]\d+)*\s*$') AS zipcode
```

**Step 4 — Hex Dashboard**
Connected to BigQuery views for the SUTV Messaging Campaign Dashboard — tracking texts sent, response rates, conversations, and survey respondents by state, refreshing daily.

---

## Methodology

### 1. State-Level Salon Density Benchmark

Rather than using the static US industry benchmark of 1 salon per 1,500–2,000 people (which undercounts urban density), this project derives a **state-specific benchmark** for each target state.

```
state_benchmark = state_population / total_licensed_salons_in_state
```

**Example — Pennsylvania:**
```
state_benchmark = 12,961,683 / 20,322 = 1:638
```
PA's benchmark (1:638) is denser than the national average (1:773). Using the national average would undercount expected coverage and produce misleading KPI scores at the city level.

### 2. Service Density KPI

```
people_per_scraped_shop = locality_population / scraped_shop_count
KPI = min(state_benchmark / people_per_scraped_shop, 1.0)
```

| KPI | Status | Meaning |
|-----|--------|---------|
| ≥ 1.0 | ✅ Adequate | Meets or exceeds the state benchmark — ready for outreach |
| 0.5–1.0 | 🟠 Partial | Coverage gap — more scraping needed before outreach |
| < 0.5 | 🔴 Severely Under | Critical gap — data collection must be prioritized |

### 3. Zip Code Prioritization

```python
# Primary flag — matches campaign targeting definition
high_priority_zip = (pct_black > 0.30) | (pct_nonwhite > 0.50)
```

Secondary signals: median household income, educational attainment, median age, organizer recommendations.

### 4. Channel Conversion Performance

| Channel | Leads | Participants | Conversion | Cost/Participant |
|---------|-------|-------------|------------|----------------|
| SMS (ThruText) | 90,967 | 558 | 0.61% | $10 |
| Phone | 13,900 | 317 | 2.2% | $29 |
| Cold Mail | 13,472 | 3,069 | 22.78% | $88 |

Google/Bing API data converted at far higher rates than state license files (15% vs 0.7%), validating the investment in API-based lead generation.

---

## Interactive App

**State Overview** — Salon density across 13 states vs. national benchmark, filterable by Wave 1 / Wave 2.

**Service Density KPI Calculator** — Live calculator: input any city, population, and scraped shop count to compute the KPI with color-coded result and state comparison.

**Zip Code Prioritization** — Filterable table by state, priority flag, income ceiling, and non-white population floor.

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