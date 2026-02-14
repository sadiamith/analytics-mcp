# Analytics MCP Server

**A unified Google Analytics + Search Console interface built for an autonomous AI agent that drives SEO growth for local businesses — without human intervention.**

---

## What This Is

This is the data backbone of an internal AI system I built that autonomously monitors, diagnoses, and improves search performance for local businesses. The agent connects to real Google Analytics and Search Console accounts, interprets the data, identifies opportunities, and takes action — all on its own.

This MCP (Model Context Protocol) server is what gives the agent its eyes. It exposes 18 structured tools across both Google APIs through a single, clean interface that the AI reasons over in real time.

## What the Agent Does

- **Detects ranking drops** before clients notice and traces them to root causes — crawl errors, canonical mismatches, indexing blocks
- **Identifies high-impression, low-CTR queries** sitting on page 2 and recommends content optimizations to push them over the edge
- **Compares performance across time periods** to measure the impact of changes and surface emerging trends
- **Audits technical SEO at scale** — batch URL inspection, sitemap health checks, indexing coverage analysis
- **Generates actionable reports** from raw API data, translating numbers into plain-language recommendations for business owners

## Architecture

```
analytics-mcp/
├── analytics_mcp/
│   ├── server.py              # FastMCP instance — 18 tools, single entry point
│   ├── auth.py                # Scoped service-account auth (GA read-only, GSC read+write)
│   ├── errors.py              # Retry with exponential backoff, structured error handling
│   ├── _clients.py            # Async GA clients + thread-safe GSC execution pool
│   └── tools/
│       ├── _helpers.py        # Universal response envelope, proto conversion, validation
│       ├── ga/                # 7 tools — reports, realtime, account admin, custom metrics
│       └── gsc/               # 11 tools — search analytics, URL inspection, sitemaps
└── tests/                     # 31 tests — registration, contracts, error handling
```

### Key Engineering Decisions

- **Uniform response contract** — every tool returns `{ok, data, error, meta}`, making it trivial for the AI agent to parse results and handle failures gracefully
- **Scoped credentials** — GA gets `analytics.readonly`, GSC gets `webmasters`, cached separately via `lru_cache`. Principle of least privilege
- **Thread-safe concurrency** — GA uses native async protobuf clients; GSC sync calls run in a bounded `ThreadPoolExecutor(4)` with 30-second timeouts and fresh service instances per call to avoid shared-state bugs
- **Automatic retry** — transient failures (429, 500, 502, 503) retry up to 3x with jittered exponential backoff. The agent doesn't break because Google had a bad moment
- **Consolidated tool surface** — reduced GSC from 19 overlapping tools down to 11 focused ones. Fewer tools = less confusion for the AI, better tool selection, more reliable outputs

## Tools

| Tool | What It Does |
|------|-------------|
| `ga_get_account_summaries` | List all accessible GA accounts and properties |
| `ga_get_property_details` | Deep dive on a single property's configuration |
| `ga_list_google_ads_links` | Surface Ads integrations for a property |
| `ga_list_property_annotations` | Pull date annotations (campaign launches, releases) |
| `ga_get_custom_dimensions_and_metrics` | Retrieve custom-defined dimensions and metrics |
| `ga_run_report` | Full reporting — dimensions, metrics, filters, ordering, pagination |
| `ga_run_realtime_report` | Live active-user data |
| `gsc_list_properties` | All Search Console properties with permission levels |
| `gsc_get_property_details` | Verification and ownership details |
| `gsc_search_analytics` | The workhorse — query performance data with filters and sorting |
| `gsc_compare_search_periods` | Side-by-side period comparison with computed deltas |
| `gsc_search_overview` | High-level totals + daily trend for quick health checks |
| `gsc_inspect_url` | Full URL inspection — indexing, crawl status, rich results |
| `gsc_batch_inspect_urls` | Inspect up to 10 URLs with categorized issue summary |
| `gsc_list_sitemaps` | All sitemaps with status and URL counts |
| `gsc_get_sitemap_details` | Detailed breakdown for a single sitemap |
| `gsc_submit_sitemap` | Submit or resubmit a sitemap |
| `gsc_delete_sitemap` | Remove a sitemap from GSC |

## Stack

- **Python 3.11+**
- **MCP SDK** (FastMCP) — tool registration and stdio transport
- **google-analytics-data / google-analytics-admin** — async protobuf clients for GA4
- **google-api-python-client** — REST client for Search Console
- **pytest + pytest-asyncio** — 31 tests covering registration, response contracts, error paths

## Quick Start

```bash
# Install
pip install -e ".[dev]"

# Set your service account path
export GOOGLE_SERVICE_ACCOUNT_PATH=/path/to/service-account.json

# Run the server
analytics-mcp

# Run tests
pytest tests/ -v
```

## Why I Built This

Local businesses don't have SEO teams. They don't have time to check Search Console dashboards or interpret crawl reports. I wanted to build something that just handles it — an AI agent that watches their search presence, catches problems early, and surfaces opportunities they'd never find on their own.

This MCP server is one piece of that system. It turns two complex Google APIs into a clean, structured interface that an AI can reason over reliably. The agent does the thinking. This server gives it the data.

---

*Built by Sadi Mustafa*
