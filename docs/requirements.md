# Requirements: Canada Macro Pipeline

## 1. Business problem
Economic indicators (interest rates, inflation, exchange rates, bond yields, wages)
are published separately, in different formats and at different frequencies.
An analyst who wants a single up-to-date view has to collect and reconcile them
by hand, which is slow and error-prone.

## 2. Goal
Automatically collect a small set of Canadian macro indicators, check their
quality, store them in a single queryable database, and make them available
through SQL and a dashboard.

## 3. Stakeholders (personas, assumed for this project)
| Persona | Need |
|---|---|
| Policy / market analyst | A quick, trustworthy snapshot of current conditions |
| Business analyst | Trends over time to support reporting |
| Data owner (me) | A pipeline that is cheap, repeatable and safe (no secrets in code) |

## 4. User stories and acceptance criteria
| ID | User story | Acceptance criteria | Delivered by |
|---|---|---|---|
| US-1 | As an analyst, I want the latest value of every indicator so I can get a snapshot. | One row per indicator with its latest date and value. | Q1 |
| US-2 | As an analyst, I want averages, ranges and patterns of daily indicators (monthly, by weekday, by quarter). | Results grouped by period. | Q2, Q3, Q4 |
| US-3 | As an analyst, I want year-over-year inflation so I can see the trend. | % change in CPI versus the same month a year earlier. | Q6 |
| US-4 | As a data consumer, I want to trust the data, so bad or stale data is flagged. | Python checks before loading; SQL freshness flag on stored data. | `src/checks.py`, Q8 |
| US-5 | As an analyst, I want all indicators side by side and on a dashboard. | One row per month with every indicator; chart per indicator. | Q7, Piece 11 (planned) |
| US-6 | As the data owner, I want to refresh everything with one command. | One script runs fetch, clean, check, load. | Piece 13 (planned) |
| US-7 | As an analyst, I want to know when the policy rate changed and by how much. | List of change dates with old rate, new rate and difference. | Q5 |

## 5. Non-functional requirements
- Cost: runs on Azure SQL free tier.
- Security: credentials live in `.env`, never in code or GitHub.
- Repeatability: re-running the load does not create duplicates.

## 6. Scope
**In scope:** 5 Bank of Canada indicators (policy rate, USD/CAD, Total CPI,
10-year bond yield, average hourly earnings).
**Out of scope (future work):** unemployment rate and housing price index
(need a Statistics Canada source).

## 7. Assumptions and risks
- Source API series may change or be discontinued (one candidate series,
  `EPS_UNEMPLOYMENT`, was rejected because it was annual and ended in 2018).
- Free-tier database auto-pauses, so the first connection after idle can fail
  and needs a retry.
- Indicators have different frequencies and units, so they are not plotted on one shared axis.
- The first month of data is a partial month, so its averages rest on only a few days.