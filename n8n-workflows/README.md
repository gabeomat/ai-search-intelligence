# n8n Automation Workflows for AI Search Intelligence

This directory contains pre-configured n8n workflow templates for automating the AI Search Intelligence system.

## Available Workflows

### 1. Daily Citation Collection (`daily-citation-collection.json`)
- **Purpose**: Automated daily collection of citations from Google (SerpAPI) and Perplexity
- **Trigger**: Cron schedule (runs at 9 AM daily)
- **Features**:
  - Fetches active queries from database
  - Collects citations from multiple engines
  - Stores results in PostgreSQL
  - Sends alerts on failures
  - Rate limiting compliance

### 2. Weekly Intelligence Report (`weekly-intelligence-report.json`)
- **Purpose**: Generate and distribute weekly citation intelligence reports
- **Trigger**: Weekly schedule (Mondays at 8 AM)
- **Features**:
  - Analyzes citation patterns
  - Identifies content gaps
  - Generates competitor insights
  - Sends reports via email/Slack
  - Creates dashboard data

### 3. Real-time Citation Monitor (`realtime-citation-monitor.json`)
- **Purpose**: Monitor for significant citation changes and opportunities
- **Trigger**: Webhook-based (triggered by API events)
- **Features**:
  - Detects new competitor citations
  - Alerts on ranking changes
  - Identifies trending topics
  - Sends immediate notifications

### 4. Content Opportunity Alerts (`content-opportunity-alerts.json`)
- **Purpose**: Automated content opportunity identification and alerting
- **Trigger**: Daily schedule (2 PM daily)
- **Features**:
  - Runs gap analysis
  - Scores opportunities
  - Creates action items
  - Assigns priorities
  - Notifies content team

### 5. Competitor Tracking (`competitor-tracking.json`)
- **Purpose**: Advanced competitor citation monitoring and analysis
- **Trigger**: Twice daily (6 AM and 6 PM)
- **Features**:
  - Tracks competitor performance
  - Identifies competitor strategies
  - Monitors new competitor content
  - Generates competitive intelligence

## Installation Instructions

1. **Import Workflows**:
   - Open n8n interface
   - Go to Workflows → Import from File
   - Select desired workflow JSON file
   - Configure credentials and parameters

2. **Configure Credentials**:
   - Add SerpAPI credentials
   - Add Perplexity API credentials
   - Configure database connections
   - Set up notification channels (Slack, email)

3. **Environment Variables**:
   ```
   AI_SEARCH_API_BASE_URL=http://localhost:8000
   AI_SEARCH_API_KEY=your_api_key
   DATABASE_URL=postgresql://user:password@localhost:5432/ai_search_intelligence
   SLACK_WEBHOOK_URL=your_slack_webhook
   ```

4. **Test Workflows**:
   - Use manual execution for testing
   - Verify database connections
   - Check notification delivery
   - Validate data processing

## Workflow Dependencies

- **PostgreSQL Database**: All workflows require database access
- **AI Search Intelligence API**: Custom API endpoints for data processing
- **External APIs**: SerpAPI, Perplexity API
- **Notification Services**: Slack, email, webhooks

## Customization Guide

### Adding New Search Engines
1. Duplicate existing engine node
2. Update API configuration
3. Modify data parsing logic
4. Add to citation storage workflow

### Custom Notification Channels
1. Add new notification node
2. Configure channel credentials
3. Customize message formatting
4. Add conditional logic for priorities

### Advanced Scheduling
1. Modify cron expressions
2. Add timezone considerations
3. Implement business hours logic
4. Add holiday scheduling exceptions

## Monitoring and Maintenance

### Health Checks
- Each workflow includes health check nodes
- Failed executions trigger alerts
- Performance metrics collection
- Error logging and debugging

### Performance Optimization
- Batch processing for large datasets
- Rate limiting for external APIs
- Database connection pooling
- Memory usage monitoring

### Data Quality
- Validation rules for collected data
- Duplicate detection and handling
- Data consistency checks
- Error correction workflows