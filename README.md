# ZeroCAC

<p align="center">
  <img src="docs/images/zerocac-banner.svg" alt="ZeroCAC Banner" width="100%">
</p>

<p align="center">
  <strong>The Autonomous AI Marketing Agent that scales products to $0 Customer Acquisition Cost.</strong><br>
  Replace expensive Meta and Google ad spend with permanent, compounding organic distribution.
</p>

<p align="center">
  <a href="https://github.com/PatelDeepB/zerocac/stargazers"><img src="https://img.shields.io/github/stars/PatelDeepB/zerocac?style=for-the-badge&color=10b981" alt="Stars"></a>
  <a href="https://github.com/PatelDeepB/zerocac/blob/main/LICENSE"><img src="https://img.shields.io/badge/License-Apache_2.0-blue.svg?style=for-the-badge" alt="License"></a>
  <a href="https://python.org"><img src="https://img.shields.io/badge/Python-3.11%20%7C%203.12-6366f1.svg?style=for-the-badge" alt="Python"></a>
  <a href="#supported-frontier-models"><img src="https://img.shields.io/badge/Frontier_Models-OpenAI_GPT--6_|_Gemini_4_|_Claude_5.5_|_Nemotron-06b6d4.svg?style=for-the-badge" alt="AI Models"></a>
  <a href="#zero-ad-spend-guarantee"><img src="https://img.shields.io/badge/Ad_Spend-$0_Guaranteed-f59e0b.svg?style=for-the-badge" alt="Zero Ad Spend"></a>
</p>

---

## The Hard Truth About Paid Ads in 2026

If you are paying Google or Meta to acquire users in 2026, you are on a financial treadmill:
1. **Skyrocketing CAC:** Cost-per-click (CPC) on search and social rises every quarter. Early-stage margins get wiped out before reaching Product-Market Fit.
2. **Rented Attention:** The exact millisecond you turn off your ad spend, your traffic and pipeline drop to absolute zero.
3. **Ad Blindness & Cynicism:** Buyers scroll past sponsored banners, use ad-blockers, and distrust sponsored recommendations.
4. **The AI Search Revolution:** Tech buyers no longer click sponsored Google links; they ask ChatGPT, Perplexity, Gemini, and Claude for product recommendations.

**ZeroCAC fixes this.** Give ZeroCAC your landing page URL and your choice of AI API keys (OpenAI, Gemini, Claude, NVIDIA, DeepSeek). It analyzes your product positioning, dissects competitor weaknesses, and deploys 4 compounding organic distribution engines that drive high-intent customers for **$0 in ad spend**.

---

## Comparison: ZeroCAC vs Traditional Channels

| Feature | Meta Ads | Google Ads | Marketing Agency | ZeroCAC (Organic AI) |
| :--- | :--- | :--- | :--- | :--- |
| **Monthly Ad Spend** | $2,000 - $20,000+ | $3,000 - $50,000+ | $5,000 - $10,000 fee | **$0 (Zero Ad Spend)** |
| **Residual Asset Equity** | Zero (Dies when stopped) | Zero (Dies when stopped) | Minimal | **Permanent Compounding** |
| **User Trust Level** | Low (Sponsored Tag) | Low (Ad label) | Variable | **High (Peer Value-First)** |
| **Answer Engine Ready** | No (Ignored by LLMs) | No (Ignored by LLMs) | Rarely | **Native (Perplexity / SearchGPT)** |
| **Average Conversion** | 0.8% - 2.1% | 1.5% - 3.2% | 1.0% - 2.5% | **15% - 30% Intent Sniping** |
| **Setup & Launch Time** | 3 - 5 days | 3 - 7 days | 2 - 4 weeks | **60 Seconds** |

---

## The 4 Organic Growth Engines

### 1. 🎯 The Intent Sniper (Contextual Community Infiltration)
* Monitors live conversations across Reddit (`r/SaaS`, `r/webdev`, `r/entrepreneur`), Hacker News (`Ask HN`), and X.
* Pinpoints buyers actively agonizing over the exact problem your product solves.
* Drafts practitioner-to-practitioner answers: 80% genuine, technical value solving their immediate issue, 20% natural contextual recommendation of your product.
* Yields 15% to 30% conversion rates because buyers perceive expert guidance rather than an intrusive ad.

### 2. 🔍 Answer Engine Optimization (AEO & GEO)
* Tech-savvy buyers ask Perplexity, ChatGPT Search, and Claude: *"What is the best alternative to [Competitor]?"*
* ZeroCAC generates programmatic, data-dense comparison pages (`alternative-to-x.md`) and valid JSON-LD FAQ schemas.
* Structures your product footprint so generative answer engines cite your product as the canonical recommendation.

### 3. ⚡ Viral Narrative & Multi-Modal Content Engine
* Generates 5-tweet build-in-public threads with counter-intuitive data and retention hooks.
* Produces 5-slide LinkedIn document carousels breaking down industry bottlenecks.
* Scripts 60-second short-form videos for TikTok, YouTube Shorts, and Instagram Reels with concrete `[Visual]` and `[Audio]` cues.

### 4. 🚀 100+ Free Directory Multiplier
* Curated database of 30+ high-authority launch directories and registries (Product Hunt, BetaList, AlternativeTo, SaaSHub, Toolify, Futurepedia, LaunchingNext).
* Formats tailored submission packages adhering strictly to character constraints (tagline <= 60 chars, short description <= 140 chars, comprehensive overview, maker comment, tags).

---

## Supported Frontier Models (2026 Matrix)

ZeroCAC features a multi-provider router with dynamic fallback failover:

| Provider | Supported Models | Optimal Role in ZeroCAC |
| :--- | :--- | :--- |
| **OpenAI** | `gpt-6-astra`, `gpt-6.1-luna`, `gpt-oss-120b` | Strategic positioning, competitive teardowns, and high-conversion hooks |
| **Google** | `gemini-4-argon`, `gemini-3.8-flash` | Multimodal UI extraction, high-throughput web crawling synthesis |
| **Anthropic** | `claude-opus-5-5`, `claude-sonnet-5-5` | Authoritative comparison guides and human-sounding community responses |
| **NVIDIA** | `nemotron-3-ultra`, `nemotron-3.5-super-vl` | Heavyweight open-weight reasoning via NVIDIA NIM microservices |
| **DeepSeek** | `deepseek-v4.1-flash`, `deepseek-r1` | High-speed lead parsing and competitor vulnerability analysis |

---

## Quickstart in 60 Seconds

### Option 1: Web Control Dashboard (Recommended)

```bash
# Clone the repository
git clone https://github.com/PatelDeepB/zerocac.git
cd zerocac

# Install dependencies
pip install -e ".[dev]"

# Configure your chosen AI keys
cp .env.example .env

# Launch the interactive web dashboard
zerocac serve
# Open http://localhost:8000 in your browser
```

### Option 2: Command Line Interface (CLI)

```bash
# Analyze any product landing page
zerocac analyze https://yourproduct.com

# Deploy the Intent Sniper for Reddit & Hacker News
zerocac snipe https://yourproduct.com --count 3

# Generate Answer Engine comparison pages (SearchGPT / Perplexity)
zerocac aeo https://yourproduct.com

# Generate X build-in-public threads & 60s video scripts
zerocac viral https://yourproduct.com

# Output 30+ directory submission packages
zerocac directories https://yourproduct.com

# Run the complete autonomous pipeline and export to disk
zerocac run https://yourproduct.com --out dist_campaign
```

### Option 3: Docker Compose

```bash
docker compose up -d
# Dashboard running at http://localhost:8000
```

---

## Architecture

```
[Target Product URL / Pitch]
            │
            ▼
┌────────────────────────────────────────┐
│ 1. Web Scraper & DOM Extractor         │
│    (Title, Meta, Headers, CTAs, Price) │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ 2. Product Intelligence Analyzer       │
│    (UVP, ICP Personas, Competitor Gaps)│
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────────────────────┐
│ 3. The 4 Autonomous Organic Engines                    │
│   ├── Engine A: Intent Sniper (Reddit / HN / X)        │
│   ├── Engine B: AEO & GEO Comparisons (SearchGPT)      │
│   ├── Engine C: Viral Narrative & Video Scripts        │
│   └── Engine D: 100+ Free Directory Multiplier         │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│ 4. Human-in-the-Loop Review Dashboard  │
│    (One-Click Copy, Export & Staging)  │
└────────────────────────────────────────┘
```

---

## Project Structure

```
zerocac/
├── docs/
│   └── images/zerocac-banner.svg   # Vector preview asset
├── zerocac/
│   ├── ai/                          # Multi-LLM fallback router (OpenAI, Gemini, Claude, NVIDIA, DeepSeek)
│   ├── crawler/                     # Web scraper and DOM feature extractor
│   ├── analyzer/                    # Positioning and ICP synthesis engine
│   ├── engines/                     # Intent Sniper, AEO, Viral Narrative, Directory Multiplier
│   ├── web/                         # FastAPI application and responsive dark-theme dashboard
│   ├── cli.py                       # Typer-powered terminal CLI
│   └── config.py                    # Pydantic v2 settings manager
└── tests/                           # 31 unit and integration tests (100% pass rate)
```

---

## Community & Contributing

We welcome contributions from developers, growth marketers, and open-source advocates.
* **Code of Conduct:** Please review our [Code of Conduct](CODE_OF_CONDUCT.md).
* **Contributing Guide:** See [CONTRIBUTING.md](CONTRIBUTING.md) for branch naming and PR standards.
* **Security Policy:** See [SECURITY.md](SECURITY.md) for vulnerability reporting.

---

## License

ZeroCAC is released under the **Apache-2.0 License**. See [LICENSE](LICENSE) for details.
