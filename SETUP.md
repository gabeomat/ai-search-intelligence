# AI Search Intelligence System - Setup Guide

## Quick Start

This comprehensive AI search intelligence system tracks, analyzes, and optimizes content performance across multiple AI-powered search engines including Google AI Overviews, Perplexity, and more.

## Phase 1 Implementation (Ready to Deploy)

### 1. System Requirements

- **Python 3.11+**
- **PostgreSQL 13+** (primary database)
- **Redis 6+** (caching and task queue)
- **InfluxDB 2.0+** (time-series data, optional)
- **n8n** (workflow automation)

### 2. Environment Setup

```bash
# Clone and setup
cd ai-search-intelligence
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt

# Copy and configure environment
cp .env.example .env
# Edit .env with your API keys and database credentials
```

### 3. Required API Keys

Add to your `.env` file:

```env
# Search APIs
SERPAPI_KEY=your_serpapi_key_here
PERPLEXITY_API_KEY=your_perplexity_api_key_here

# Database
DATABASE_URL=postgresql://user:password@localhost:5432/ai_search_intelligence
REDIS_URL=redis://localhost:6379/0

# Notifications
SLACK_WEBHOOK_URL=your_slack_webhook_url
SMTP_FROM_EMAIL=reports@yourcompany.com
```

### 4. Database Setup

```bash
# Initialize database
python -m alembic upgrade head

# Or manually create tables using the models in:
# ai_search_intelligence/database/models.py
```

### 5. Launch the System

```bash
# Start the API server
python -m ai_search_intelligence.api.main

# In another terminal, start the Celery worker
celery -A ai_search_intelligence.workers worker --loglevel=info

# Access dashboard at: http://localhost:8000/dashboard
# API docs at: http://localhost:8000/docs
```

## Core Features Available

### ✅ Multi-Engine Citation Tracking
- **Google SERP**: AI Overviews, Featured Snippets, People Also Ask, Knowledge Panels
- **Perplexity**: Direct answer citations, source attribution, follow-up questions
- **Extensible**: Ready for ChatGPT Search, Claude, Bing Copilot

### ✅ Advanced Analytics
- Citation pattern recognition using ML algorithms
- Content gap identification with opportunity scoring
- Competitive intelligence tracking
- Real-time analytics dashboard

### ✅ Automation Workflows (n8n)
- **Daily Citation Collection**: Automated data gathering
- **Weekly Intelligence Reports**: Comprehensive analysis and insights  
- **Content Opportunity Alerts**: Real-time gap identification
- **Competitive Monitoring**: Track competitor performance

### ✅ Intelligent Reporting
- Weekly, monthly, quarterly reports
- HTML and PDF export formats
- Automated email distribution
- Executive dashboards with visualizations

## Key System Components

### 🔧 Core Engine (`ai_search_intelligence/`)

1. **Citation Collection** (`engines/`)
   - `google_serp.py`: Google SERP data via SerpAPI
   - `perplexity.py`: Perplexity AI citation tracking

2. **Analysis Engine** (`analysis/`)  
   - `pattern_recognition.py`: ML-based citation patterns
   - `gap_identification.py`: Content opportunity detection
   - `citation_parser.py`: Content analysis and extraction

3. **Database Layer** (`database/`)
   - Comprehensive schema for citations, content analysis, competitors
   - Time-series tracking for trend analysis
   - Optimized indexes for fast queries

4. **API & Dashboard** (`api/`)
   - FastAPI server with real-time analytics endpoints
   - Interactive HTML dashboard with Chart.js visualizations
   - Advanced reporting engine with multiple export formats

### 🤖 Automation (`n8n-workflows/`)

Pre-built workflows for:
- **daily-citation-collection.json**: Automated data gathering
- **weekly-intelligence-report.json**: Comprehensive analysis reports
- **content-opportunity-alerts.json**: Real-time opportunity detection

## Usage Examples

### Track New Queries

```python
from ai_search_intelligence.engines.google_serp import GoogleSERPCollector
from ai_search_intelligence.engines.perplexity import PerplexityCollector

# Initialize collectors
google = GoogleSERPCollector()
perplexity = PerplexityCollector()

# Collect citations for a query
google_citations = await google.collect_citations("AI search optimization")
perplexity_citations = await perplexity.collect_citations("AI search optimization")
```

### Analyze Citation Patterns

```python
from ai_search_intelligence.analysis.pattern_recognition import CitationPatternAnalyzer

analyzer = CitationPatternAnalyzer()
patterns = analyzer.analyze_citation_patterns(all_citations)

# Get actionable insights
insights = analyzer.generate_pattern_insights(patterns)
print(f"Found {len(insights['recommendations'])} recommendations")
```

### Identify Content Gaps

```python
from ai_search_intelligence.analysis.gap_identification import ContentGapAnalyzer

gap_analyzer = ContentGapAnalyzer()
gaps = await gap_analyzer.identify_content_gaps(
    citations=citations,
    tracked_queries=your_queries,
    competitor_domains=["competitor.com", "example.com"]
)

# Get high-opportunity gaps
high_value_gaps = [gap for gap in gaps if gap.opportunity_score >= 0.8]
```

## Dashboard Features

### 📊 Real-time Analytics
- **Citation Trends**: Track performance across time periods
- **Engine Comparison**: Compare Google vs Perplexity vs others  
- **Domain Performance**: See which domains dominate citations
- **Content Type Analysis**: Understand what content gets cited

### 🎯 Content Intelligence
- **Gap Opportunities**: Identified content opportunities with scoring
- **Competitive Analysis**: Track competitor citation strategies
- **Pattern Recognition**: Automated insights from citation data
- **Action Items**: Generated recommendations with priorities

### 📈 Advanced Reporting
- **Executive Summaries**: High-level performance metrics
- **Detailed Analysis**: Deep-dive into citation patterns
- **Competitive Intelligence**: Market position and threats
- **Predictive Insights**: Forecasting and trend analysis

## n8n Workflow Setup

1. **Import Workflows**:
   - Open n8n → Workflows → Import from File
   - Import `n8n-workflows/*.json` files

2. **Configure Credentials**:
   - Add SerpAPI credentials
   - Add Perplexity API credentials  
   - Configure database connections
   - Set up Slack/email notifications

3. **Activate Workflows**:
   - Enable daily citation collection
   - Set up weekly report generation
   - Configure opportunity alerts

## Next Steps

### Immediate Actions:
1. **Add Your Queries**: Input the search terms you want to track
2. **Configure Competitors**: Add competitor domains to monitor
3. **Set Up Alerts**: Configure Slack/email notifications
4. **Review Dashboard**: Check real-time analytics

### Phase 2 Enhancements:
- **Additional Engines**: ChatGPT Search, Claude web search, Bing Copilot
- **Advanced ML**: Predictive modeling for citation trends
- **Content Automation**: Auto-generate content based on gaps
- **Enterprise Features**: Multi-tenant support, advanced permissions

## Support & Troubleshooting

### Common Issues:
- **API Rate Limits**: Adjust collection intervals in config
- **Database Connections**: Verify PostgreSQL is running
- **Missing Dependencies**: Run `pip install -r requirements.txt`

### Monitoring:
- Check API health: `GET /api/v1/health`
- View system metrics: Dashboard → Overview tab
- Review logs: Check application logs for errors

## Architecture Overview

The system follows a modular, scalable architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Sources  │────│   Collection    │────│   Processing    │
│   (APIs)        │    │   Layer         │    │   Layer         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Database      │────│   Analysis      │────│   Intelligence  │
│   Layer         │    │   Engine        │    │   Layer         │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Automation    │────│   API Server    │────│   Dashboard     │
│   (n8n)         │    │   (FastAPI)     │    │   (Web UI)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

This system provides everything needed for comprehensive AI search intelligence - from data collection to advanced analytics to automated reporting. The modular design allows for easy expansion and customization based on your specific needs.

## 🚀 Ready to Deploy!

Your AI Search Intelligence System is now ready for deployment. Start with Phase 1 implementation and scale based on your requirements and insights gained from the initial data collection.