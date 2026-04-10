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
| **2024** | Google Places API, Bing API, state license files, past participants | Airtable + ThruText sync, lead gen scripts, master database | Cold mail targeting, list pulling |
| **2025+** | Same + self-serve lead gen | Same + self-serve list pulling | Scaling organizer capacity |

---

## Program Flow

The full participant journey moved through four stages:

```
SOURCE                    RECRUIT                    ONBOARD         ORGANIZE
──────                    ───────                    ───────         ────────
Google/Bing APIs  ──▶                                                Confirmation
State License           Targeting +    ──▶  Cold Mail               │  Receipt Y/N?
Past Participants  ──▶  Data Quality   ──▶  SMS / Phone  ──▶  Mail  │  Display Y/N?
Other Sources           (diamond)      ──▶  Instagram         SUTV  │  Convos Y/N?
                                       ──▶  Website/Inbound   Kit   │
                                       ──▶  Referrals               Asks
                                                                │  Ask 'Make a plan?'
                                                                │  Election info
                                                                │  Post on IG
                                                                │  Organizer 1:1s
                                                                │
                                                                Deeper Asks
                                                                   Convo guide + tracker
                                                                   Virtual rally
                                                                   Ask ppl to text 5 friends
                                                                   Advisory Council
```

Key design decisions visible in this flow:
- The **targeting diamond** routes leads by data quality, not just demographics — contact type determines channel
- **Inbound channels** (Instagram, website, referrals) bypass the targeting funnel entirely and feed kit requests directly
- The organize phase is a structured **escalation ladder**: Confirmation → Asks → Deeper Asks, with specific touchpoints at each level

---

## Data Architecture

### Master Database — Source Inputs

Four data sources fed the Master DB, with a clear automated vs. semi-automated split:

```
Google SMBs         ─ ─ ─ ─▶ ┐
State License Files ─ ─ ─ ─▶ │                    ┌──────────────▶ Stones Phones ─ ─ ─▶ ┐
Voter Files         ─ ─ ─ ─▶ ├──▶ Master DB ──▶ List Pulls ──▶ Marquadt Mail  ─ ─ ─▶ ├──▶ CRM
Geo Data            ─ ─ ─ ─▶ ┘        ▲            └──────────────▶ ThruText    ◀────────┘ ▲
                                       └─────────────────────────────────────────────────────┘
                                                    (automated feedback loop)

── automated        - - semi-automated (requires data team)
```

- **Google SMBs, State License Files, Voter Files, Geo Data** all feed the Master DB via semi-automated processes requiring data team involvement
- **SmartMatch** had a bidirectional manual relationship specifically with State License Files — used to validate and enrich license data before ingestion
- **List pulls** were semi-automated, routing to three outreach vendors: Stones Phones (phone recruitment), Marquadt Mail (cold mail), and ThruText (SMS)
- The **CRM → ThruText** sync and the **ThruText → CRM** feedback loop were the only fully automated connections in this architecture

### Current State — Full Pipeline

```
                    ┌──────────────────────┐
                    │  Data Cleaning &     │
                    │  Validation          │
                    └──────────┬───────────┘
                               │ (automated, bidirectional)
Google Places ─────────────────▼──────────┐
State License Files ───────────────────── ├──▶ BigQuery ──▶ GDrive ──▶ Stone's Phones ──▶ ┐
         ▲                                │         │                                       │
         │ (manual, SmartMatch)           │         ├──▶ GDrive ──▶ Cold Mail        ──▶ ├──▶ Mother DB ──▶ CRM
    SmartMatch                            │         │                                       │         │
                                          └─────────┘    └──▶ GDrive ──▶ Cold ThruText ──▶ ┘         │
                                                                                                       │
                                                                              Hex Reporting ◀──────────┘
                                                                                                       │
                                          CRM downstream consumers (all manual): ◀─────────────────────┘
                                          Airtable Reporting · IG DMs · List Pulls
                                          Phone Follow-Ups · ThruText Follow-Ups · Kit Requests
```

Key architectural decisions:
- **BigQuery → GDrive** serves as a staging layer before each outreach channel — three separate GDrive exports, one per channel (phones, cold mail, ThruText)
- **Only confirmed participants** (text/phone signups and cold mail confirmations) are loaded into Airtable CRM — the CRM is not a raw leads store
- **Hex Reporting** sits downstream of the Mother DB, not BigQuery — reporting reflects the consolidated participant view, not raw lead data
- The CRM fans out to **six downstream consumers**, all manual: Airtable Reporting, IG DMs, List Pulls, Phone Follow-Ups, ThruText Follow-Ups, and Kit Requests

---

## Data Pipeline (Technical Detail)

### Pipeline 1: Shop Data Collection & Prioritization

**Step 1 — Data Collection**
Shop listings (name, address, phone number) scraped from Google Places and Bing via the Pline.io Chrome extension across all 13 target states. State license files and past participant CRM records also incorporated. Raw data stored in Google Drive.

**Step 2 — Cleaning & Enrichment**
In Hex, raw data was deduplicated using `osm_id` as a unique key, phone numbers normalized via regex (`regexp_replace(PhoneNumber, r'\D', '')`), and zip codes standardized to 5 digits. Each record joined to US Census API data to enrich with population, race, income, education, and age at the zip code level. Phone numbers cross-referenced with TargetSmart/SmartMatch to validate textability.

**Step 3 — Prioritization & Channel Assignment**
Leads scored and filtered by zip code demographics, then assigned to outreach channels based on contact data quality:

| Data Source | Phone Type | Leads | Primary Channel |
|-------------|-----------|-------|----------------|
| Google / Bing | Textable | 11,186 | SMS |
| Google / Bing | Not Textable | 22,629 | Cold Mail |
| License Files | Textable | 93,398 | SMS |
| License Files | Not Textable | 136,503 | Phone |

**Step 4 — Output**
Prioritized zip code lists exported to Google Cloud Storage as `high_priority_zips.csv`. Final shop lists loaded into Airtable CRM and synced to ThruText for outreach.

---

### Pipeline 2: Messaging Campaign Analytics

**Step 1 — GetThru / ThruText Export**
ThruText supported nightly exports to AWS S3 but not directly to GCP. GetThru support configured automated nightly exports delivering four CSV files to S3 at 8am UTC: `caller_activity_details`, `daily_messages`, `daily_surveys`, `opt_outs`.

**Step 2 — S3 to GCS via Storage Transfer Service**
Google Cloud's Storage Transfer Service (STS) ran a daily batch transfer from S3 to GCS at 9am UTC, mirroring the S3 bucket structure exactly. Scheduled through December 31, 2024.

**Step 3 — BigQuery Ingestion & PII Removal**
External tables in BigQuery read directly from GCS with auto-detected schemas. Scheduled queries ran daily at 10am UTC producing cleaned views (`messages_view`, `surveys_view`) that stripped all PII and parsed the `address` field into city/state/zipcode using regex:

```sql
REGEXP_EXTRACT(address, r'([A-Za-z\.]{3}[A-Za-z\.]*),*\s+(?:[A-Za-z]{2})') AS city,
UPPER(REGEXP_EXTRACT(address, r'\s+([A-Za-z]{2})(?:,?\s*\d+(?:[-\s]\d+)?)?\s*$')) AS state,
REGEXP_EXTRACT(address, r'\s+(?:[A-Za-z]{2},?\s*)(\d{5})(?:[-\s]\d+)*\s*$') AS zipcode
```

**Step 4 — Hex Dashboard**
Hex connected directly to BigQuery views to power the SUTV Messaging Campaign Dashboard — tracking sent texts, response rates, conversations, and survey respondents by state, refreshing daily.

---

## Methodology

### 1. State-Level Salon Density Benchmark

Rather than using the static US industry benchmark of 1 salon per 1,500–2,000 people (which undercounts urban density), this project derives a **state-specific benchmark** for each target state.

**Formula:**
```
state_benchmark = state_population / total_licensed_salons_in_state
```

Source: [SalonSpaConnection.com (2023)](https://salonspaconnection.com/beauty-hair-salon-industry-statistics-in-2023/) for state totals; US Census Bureau for population.

**Example — Pennsylvania:**
```
state_benchmark = 12,961,683 / 20,322 = 1:638
```
PA's benchmark of 1:638 is denser than the national average (1:773). Using the national average would undercount expected coverage in Pennsylvania and produce misleading KPI scores.

---

### 2. Service Density KPI

For each locality (city or zip code), a normalized **Service Density KPI** between 0 and 1 measures how well the scraped dataset covers the expected number of shops relative to the state benchmark.

**Formula:**
```
people_per_scraped_shop = locality_population / scraped_shop_count
KPI = min(state_benchmark / people_per_scraped_shop, 1.0)
```

**Interpretation:**

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

---

### 3. Zip Code Prioritization

Zip codes flagged as **high-priority** based on the hypothesis that communities of color and lower-income areas are historically underserved in voter engagement:

> *"Young people, as well as people with less education and lower incomes, will be less likely to cast a ballot in any given election."*  
> — [Elections Canada, Correlates of Voter Turnout](https://www.elections.ca/content.aspx?section=res&dir=rec/part/tud&document=correlates&lang=e)

**Primary flag:**
```python
high_priority_zip = population_by_race_nonwhite_percentage > 0.33
```

Organizer recommendations were incorporated as a secondary signal alongside the demographic threshold.

**Supporting signals:** median household income, educational attainment, median age.

---

### 4. Channel Conversion Performance

Outreach channel selection was driven by data quality. Cold mail dramatically outperformed digital channels on conversion rate, though at higher cost per participant:

| Channel | Leads | Participants | Conversion | Cost/Participant |
|---------|-------|-------------|------------|----------------|
| SMS (ThruText) | 90,967 | 558 | 0.61% | $10 |
| Phone | 13,900 | 317 | 2.2% | $29 |
| Cold Mail | 13,472 | 3,069 | 22.78% | $88 |

Google/Bing API data converted at far higher rates than state license files (15% vs 0.7%), validating the investment in API-based lead generation over license file matching.

---

## Interactive App

**State Overview** — Bar chart of all 13 states benchmarked against the national average (1:773), filterable by Wave 1 / Wave 2 launch states.

**Service Density KPI Calculator** — Live calculator: input any city, state, population, and scraped shop count to compute the KPI in real time with a color-coded result and comparison against other localities in the same state.

**Zip Code Prioritization** — Filterable table by state, priority flag, median household income ceiling, and non-white population floor.

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
├── requirements.txt                                      # Python dependencies
├── README.md
├── salonbarbershop_density_portfolio.ipynb               # Density analysis (portfolio)
├── sutv_city_and_zipcode_prioritization_portfolio.ipynb  # Prioritization (portfolio)
└── archive/                                              # Original Hex notebooks
    ├── salonbarbershop_density_by_cityneighborhoodzipcode.ipynb
    └── sutv_city_and_zipcode_prioritization.ipynb
```

> **Note on data:** Portfolio notebooks use a synthetic dataset mirroring the real schema — real zip codes and city names, plausible demographics from Census distributions. The original pipeline connected to live BigQuery tables (`sutv.*`) and Google Cloud Storage. Proprietary shop data is not included.

---

## Tech Stack

| Layer | Tools |
|-------|-------|
| Data Collection | Pline.io, Google Places API, Bing API, State License Files |
| Contact Enrichment | TargetSmart / SmartMatch (phone validation), US Census API |
| CRM | Airtable + ThruText sync |
| Cold Mail Vendor | Marquadt Mail |
| Phone Recruitment | Stone's Phones |
| Data Storage | Google Cloud Storage, AWS S3, Google Drive |
| Data Transfer | Google Storage Transfer Service (STS) |
| Data Warehouse | Google BigQuery |
| Analysis & Notebooks | Python (pandas, numpy), SQL, Hex |
| Messaging Platform | GetThru / ThruText |
| Dashboard / App | Streamlit, Matplotlib |

---

*Paid for by Progressive Turnout Project and not authorized by any candidate or candidate's committee.*