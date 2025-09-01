"""Analytics dashboard backend for AI Search Intelligence."""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
import json
from collections import defaultdict
import pandas as pd
import numpy as np

from ..core.config import get_settings


logger = logging.getLogger(__name__)


class AnalyticsDashboard:
    """Backend for analytics dashboard with real-time insights."""
    
    def __init__(self):
        self.settings = get_settings()
        
    async def generate_dashboard_html(self) -> str:
        """Generate the complete dashboard HTML with embedded JavaScript."""
        
        html_template = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>AI Search Intelligence Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script src="https://cdn.jsdelivr.net/npm/date-fns@2.29.3/index.min.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body { font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; background: #f8fafc; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; }
        .header h1 { font-size: 2.5rem; margin-bottom: 0.5rem; }
        .header p { opacity: 0.9; font-size: 1.1rem; }
        .container { max-width: 1400px; margin: 0 auto; padding: 2rem; }
        .metrics-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1.5rem; margin-bottom: 2rem; }
        .metric-card { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); border-left: 4px solid #667eea; }
        .metric-value { font-size: 2.5rem; font-weight: 700; color: #1a202c; }
        .metric-label { color: #718096; font-size: 0.9rem; margin-top: 0.5rem; }
        .metric-change { font-size: 0.8rem; margin-top: 0.5rem; }
        .positive { color: #38a169; }
        .negative { color: #e53e3e; }
        .charts-grid { display: grid; grid-template-columns: 2fr 1fr; gap: 2rem; margin-bottom: 2rem; }
        .chart-container { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .chart-container h3 { margin-bottom: 1rem; color: #2d3748; }
        .full-width { grid-column: 1 / -1; }
        .opportunities-section { background: white; padding: 1.5rem; border-radius: 12px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin-bottom: 2rem; }
        .opportunity-item { padding: 1rem; border-left: 3px solid #ed8936; margin-bottom: 1rem; background: #fffaf0; border-radius: 0 6px 6px 0; }
        .opportunity-score { font-weight: 700; color: #c05621; }
        .loading { text-align: center; padding: 2rem; color: #718096; }
        .refresh-btn { background: #667eea; color: white; border: none; padding: 0.75rem 1.5rem; border-radius: 6px; cursor: pointer; margin-bottom: 1rem; }
        .refresh-btn:hover { background: #5a67d8; }
        .status-indicator { display: inline-block; width: 8px; height: 8px; border-radius: 50%; margin-right: 8px; }
        .status-active { background: #38a169; }
        .status-warning { background: #ed8936; }
        .status-error { background: #e53e3e; }
        .tab-container { margin-bottom: 2rem; }
        .tab-buttons { display: flex; background: white; border-radius: 8px; overflow: hidden; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
        .tab-button { flex: 1; padding: 1rem; border: none; background: white; cursor: pointer; transition: all 0.3s; }
        .tab-button.active { background: #667eea; color: white; }
        .tab-content { display: none; }
        .tab-content.active { display: block; }
    </style>
</head>
<body>
    <div class="header">
        <div class="container">
            <h1>🔍 AI Search Intelligence</h1>
            <p>Real-time citation tracking and content intelligence across AI search engines</p>
            <div style="margin-top: 1rem;">
                <span class="status-indicator status-active"></span>
                <span style="margin-right: 2rem;">System Active</span>
                <span id="last-updated">Last updated: Loading...</span>
            </div>
        </div>
    </div>

    <div class="container">
        <button class="refresh-btn" onclick="refreshDashboard()">🔄 Refresh Data</button>
        
        <!-- Key Metrics -->
        <div class="metrics-grid" id="metrics-grid">
            <div class="loading">Loading metrics...</div>
        </div>

        <!-- Tab Container -->
        <div class="tab-container">
            <div class="tab-buttons">
                <button class="tab-button active" onclick="showTab('overview')">Overview</button>
                <button class="tab-button" onclick="showTab('trends')">Trends</button>
                <button class="tab-button" onclick="showTab('opportunities')">Opportunities</button>
                <button class="tab-button" onclick="showTab('competitors')">Competitors</button>
            </div>
            
            <!-- Overview Tab -->
            <div id="overview" class="tab-content active">
                <div class="charts-grid">
                    <div class="chart-container">
                        <h3>📈 Citation Trends (30 Days)</h3>
                        <canvas id="trendsChart" width="400" height="200"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>🔍 Engine Distribution</h3>
                        <canvas id="engineChart" width="300" height="200"></canvas>
                    </div>
                </div>
                
                <div class="charts-grid">
                    <div class="chart-container">
                        <h3>🏆 Top Performing Domains</h3>
                        <canvas id="domainsChart" width="400" height="250"></canvas>
                    </div>
                    <div class="chart-container">
                        <h3>📋 Content Types Performance</h3>
                        <canvas id="contentTypesChart" width="300" height="250"></canvas>
                    </div>
                </div>
            </div>
            
            <!-- Trends Tab -->
            <div id="trends" class="tab-content">
                <div class="chart-container full-width">
                    <h3>📊 Detailed Citation Trends</h3>
                    <div style="margin-bottom: 1rem;">
                        <select id="trendsTimeRange" onchange="updateTrends()" style="padding: 0.5rem; border-radius: 4px; border: 1px solid #e2e8f0;">
                            <option value="7d">Last 7 Days</option>
                            <option value="30d" selected>Last 30 Days</option>
                            <option value="90d">Last 90 Days</option>
                        </select>
                        <select id="trendsGranularity" onchange="updateTrends()" style="padding: 0.5rem; border-radius: 4px; border: 1px solid #e2e8f0; margin-left: 1rem;">
                            <option value="daily" selected>Daily</option>
                            <option value="weekly">Weekly</option>
                        </select>
                    </div>
                    <canvas id="detailedTrendsChart" width="800" height="400"></canvas>
                </div>
            </div>
            
            <!-- Opportunities Tab -->
            <div id="opportunities" class="tab-content">
                <div class="opportunities-section">
                    <h3>🎯 High-Priority Content Opportunities</h3>
                    <div id="opportunities-list">
                        <div class="loading">Loading opportunities...</div>
                    </div>
                </div>
            </div>
            
            <!-- Competitors Tab -->
            <div id="competitors" class="tab-content">
                <div class="chart-container full-width">
                    <h3>⚔️ Competitive Analysis</h3>
                    <canvas id="competitorChart" width="800" height="400"></canvas>
                </div>
            </div>
        </div>
    </div>

    <script>
        let charts = {};
        
        // Tab functionality
        function showTab(tabName) {
            document.querySelectorAll('.tab-content').forEach(tab => tab.classList.remove('active'));
            document.querySelectorAll('.tab-button').forEach(btn => btn.classList.remove('active'));
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // Load tab-specific data
            if (tabName === 'trends') updateTrends();
            if (tabName === 'opportunities') loadOpportunities();
            if (tabName === 'competitors') loadCompetitors();
        }

        // Main dashboard refresh
        async function refreshDashboard() {
            try {
                await Promise.all([
                    loadMetrics(),
                    loadOverviewCharts()
                ]);
                document.getElementById('last-updated').textContent = 
                    `Last updated: ${new Date().toLocaleString()}`;
            } catch (error) {
                console.error('Error refreshing dashboard:', error);
            }
        }

        // Load key metrics
        async function loadMetrics() {
            try {
                const response = await fetch('/api/v1/analytics/overview?time_range=7d');
                const data = await response.json();
                
                const metricsGrid = document.getElementById('metrics-grid');
                metricsGrid.innerHTML = `
                    <div class="metric-card">
                        <div class="metric-value">${data.total_citations?.toLocaleString() || '0'}</div>
                        <div class="metric-label">Total Citations (7d)</div>
                        <div class="metric-change ${data.citations_change >= 0 ? 'positive' : 'negative'}">
                            ${data.citations_change >= 0 ? '+' : ''}${((data.citations_change || 0) * 100).toFixed(1)}% vs last week
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.unique_domains || '0'}</div>
                        <div class="metric-label">Unique Domains Cited</div>
                        <div class="metric-change ${data.domains_change >= 0 ? 'positive' : 'negative'}">
                            ${data.domains_change >= 0 ? '+' : ''}${data.domains_change || 0} new domains
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${(data.avg_prominence_score || 0).toFixed(2)}</div>
                        <div class="metric-label">Avg Prominence Score</div>
                        <div class="metric-change ${data.prominence_change >= 0 ? 'positive' : 'negative'}">
                            ${data.prominence_change >= 0 ? '+' : ''}${((data.prominence_change || 0) * 100).toFixed(1)}% change
                        </div>
                    </div>
                    <div class="metric-card">
                        <div class="metric-value">${data.content_opportunities || '0'}</div>
                        <div class="metric-label">Content Opportunities</div>
                        <div class="metric-change positive">
                            ${data.high_priority_opportunities || '0'} high priority
                        </div>
                    </div>
                `;
            } catch (error) {
                console.error('Error loading metrics:', error);
            }
        }

        // Load overview charts
        async function loadOverviewCharts() {
            try {
                const [trendsData, engineData, domainsData, contentTypesData] = await Promise.all([
                    fetch('/api/v1/analytics/citations/trends?time_range=30d').then(r => r.json()),
                    fetch('/api/v1/analytics/engines/comparison').then(r => r.json()),
                    fetch('/api/v1/analytics/domains/performance?limit=10').then(r => r.json()),
                    fetch('/api/v1/analytics/content-types').then(r => r.json())
                ]);

                // Trends Chart
                if (charts.trends) charts.trends.destroy();
                const trendsCtx = document.getElementById('trendsChart').getContext('2d');
                charts.trends = new Chart(trendsCtx, {
                    type: 'line',
                    data: {
                        labels: trendsData.dates || [],
                        datasets: [{
                            label: 'Citations',
                            data: trendsData.citations || [],
                            borderColor: '#667eea',
                            backgroundColor: 'rgba(102, 126, 234, 0.1)',
                            fill: true,
                            tension: 0.4
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });

                // Engine Distribution Chart
                if (charts.engine) charts.engine.destroy();
                const engineCtx = document.getElementById('engineChart').getContext('2d');
                charts.engine = new Chart(engineCtx, {
                    type: 'doughnut',
                    data: {
                        labels: Object.keys(engineData.distribution || {}),
                        datasets: [{
                            data: Object.values(engineData.distribution || {}),
                            backgroundColor: ['#667eea', '#f093fb', '#ffeaa7', '#fd79a8']
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: {
                            legend: { position: 'bottom' }
                        }
                    }
                });

                // Domains Chart
                if (charts.domains) charts.domains.destroy();
                const domainsCtx = document.getElementById('domainsChart').getContext('2d');
                charts.domains = new Chart(domainsCtx, {
                    type: 'bar',
                    data: {
                        labels: (domainsData.domains || []).map(d => d.domain),
                        datasets: [{
                            label: 'Citations',
                            data: (domainsData.domains || []).map(d => d.citation_count),
                            backgroundColor: '#667eea'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true },
                            x: { ticks: { maxRotation: 45 } }
                        }
                    }
                });

                // Content Types Chart
                if (charts.contentTypes) charts.contentTypes.destroy();
                const contentTypesCtx = document.getElementById('contentTypesChart').getContext('2d');
                charts.contentTypes = new Chart(contentTypesCtx, {
                    type: 'bar',
                    data: {
                        labels: Object.keys(contentTypesData.types || {}),
                        datasets: [{
                            label: 'Average Prominence',
                            data: Object.values(contentTypesData.types || {}).map(t => t.avg_prominence),
                            backgroundColor: '#f093fb'
                        }]
                    },
                    options: {
                        responsive: true,
                        plugins: { legend: { display: false } },
                        scales: {
                            y: { beginAtZero: true, max: 1 }
                        }
                    }
                });

            } catch (error) {
                console.error('Error loading overview charts:', error);
            }
        }

        // Load opportunities
        async function loadOpportunities() {
            try {
                const response = await fetch('/api/v1/analytics/gaps/summary');
                const data = await response.json();
                
                const opportunitiesList = document.getElementById('opportunities-list');
                if (data.gaps && data.gaps.length > 0) {
                    opportunitiesList.innerHTML = data.gaps.map(gap => `
                        <div class="opportunity-item">
                            <div style="display: flex; justify-content: between; align-items: start;">
                                <div style="flex: 1;">
                                    <h4>${gap.query_text}</h4>
                                    <p style="color: #718096; margin: 0.5rem 0;">${gap.reasoning}</p>
                                    <div style="font-size: 0.9rem;">
                                        <span style="background: #edf2f7; padding: 0.25rem 0.5rem; border-radius: 4px; margin-right: 0.5rem;">
                                            ${gap.suggested_content_type}
                                        </span>
                                        <span style="background: #f0fff4; color: #38a169; padding: 0.25rem 0.5rem; border-radius: 4px;">
                                            ${gap.priority} priority
                                        </span>
                                    </div>
                                </div>
                                <div class="opportunity-score">
                                    ${(gap.opportunity_score * 100).toFixed(0)}%
                                </div>
                            </div>
                        </div>
                    `).join('');
                } else {
                    opportunitiesList.innerHTML = '<p>No high-priority opportunities identified.</p>';
                }
            } catch (error) {
                console.error('Error loading opportunities:', error);
            }
        }

        // Update trends with filters
        async function updateTrends() {
            const timeRange = document.getElementById('trendsTimeRange').value;
            const granularity = document.getElementById('trendsGranularity').value;
            
            try {
                const response = await fetch(`/api/v1/analytics/citations/trends?time_range=${timeRange}&granularity=${granularity}`);
                const data = await response.json();
                
                if (charts.detailedTrends) charts.detailedTrends.destroy();
                const ctx = document.getElementById('detailedTrendsChart').getContext('2d');
                charts.detailedTrends = new Chart(ctx, {
                    type: 'line',
                    data: {
                        labels: data.dates || [],
                        datasets: (data.engines || []).map((engine, index) => ({
                            label: engine.name,
                            data: engine.data,
                            borderColor: ['#667eea', '#f093fb', '#ffeaa7', '#fd79a8'][index],
                            backgroundColor: ['#667eea', '#f093fb', '#ffeaa7', '#fd79a8'][index] + '20',
                            fill: false,
                            tension: 0.4
                        }))
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true }
                        }
                    }
                });
            } catch (error) {
                console.error('Error updating trends:', error);
            }
        }

        // Load competitors
        async function loadCompetitors() {
            try {
                const response = await fetch('/api/v1/analytics/competitors');
                const data = await response.json();
                
                if (charts.competitor) charts.competitor.destroy();
                const ctx = document.getElementById('competitorChart').getContext('2d');
                charts.competitor = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: (data.competitors || []).map(c => c.domain),
                        datasets: [{
                            label: 'Citation Share (%)',
                            data: (data.competitors || []).map(c => c.citation_share * 100),
                            backgroundColor: '#fd79a8'
                        }]
                    },
                    options: {
                        responsive: true,
                        scales: {
                            y: { beginAtZero: true, max: 100 }
                        }
                    }
                });
            } catch (error) {
                console.error('Error loading competitors:', error);
            }
        }

        // Initialize dashboard
        document.addEventListener('DOMContentLoaded', function() {
            refreshDashboard();
            
            // Auto-refresh every 5 minutes
            setInterval(refreshDashboard, 5 * 60 * 1000);
        });
    </script>
</body>
</html>
        """
        
        return html_template
    
    async def get_overview_data(self, time_range: str = "7d") -> Dict[str, Any]:
        """Get overview data for dashboard metrics."""
        # This would typically query your database
        # For now, returning mock data structure
        return {
            "total_citations": 1247,
            "citations_change": 0.15,  # 15% increase
            "unique_domains": 89,
            "domains_change": 7,  # 7 new domains
            "avg_prominence_score": 0.72,
            "prominence_change": 0.08,  # 8% increase
            "content_opportunities": 23,
            "high_priority_opportunities": 8,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    async def get_citation_trends(self, time_range: str, engine: Optional[str], granularity: str) -> Dict[str, Any]:
        """Get citation trends data."""
        # Mock trends data
        days = int(time_range.replace('d', ''))
        dates = [(datetime.now() - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(days, 0, -1)]
        
        if engine:
            return {
                "dates": dates,
                "citations": [np.random.randint(10, 50) for _ in dates],
                "engine": engine
            }
        else:
            return {
                "dates": dates,
                "engines": [
                    {
                        "name": "Google",
                        "data": [np.random.randint(20, 60) for _ in dates]
                    },
                    {
                        "name": "Perplexity", 
                        "data": [np.random.randint(15, 45) for _ in dates]
                    }
                ]
            }
    
    async def get_domain_performance(self, time_range: str, limit: int) -> Dict[str, Any]:
        """Get domain performance data."""
        # Mock domain data
        domains = [
            {"domain": "example.com", "citation_count": 45, "avg_prominence": 0.78},
            {"domain": "site.com", "citation_count": 38, "avg_prominence": 0.65},
            {"domain": "blog.net", "citation_count": 32, "avg_prominence": 0.71},
            {"domain": "news.org", "citation_count": 28, "avg_prominence": 0.69},
            {"domain": "tech.io", "citation_count": 25, "avg_prominence": 0.73}
        ]
        
        return {
            "domains": domains[:limit],
            "time_range": time_range
        }
    
    async def get_engine_comparison(self, time_range: str) -> Dict[str, Any]:
        """Get engine comparison data."""
        return {
            "distribution": {
                "Google": 65,
                "Perplexity": 28,
                "ChatGPT": 7
            },
            "performance": {
                "Google": {"avg_prominence": 0.68, "total_citations": 812},
                "Perplexity": {"avg_prominence": 0.74, "total_citations": 349},
                "ChatGPT": {"avg_prominence": 0.71, "total_citations": 86}
            }
        }
    
    async def get_content_type_analysis(self, time_range: str) -> Dict[str, Any]:
        """Get content type analysis."""
        return {
            "types": {
                "ai_overview": {"avg_prominence": 0.85, "count": 234},
                "featured_snippet": {"avg_prominence": 0.92, "count": 156},
                "organic": {"avg_prominence": 0.45, "count": 567},
                "people_also_ask": {"avg_prominence": 0.58, "count": 123}
            }
        }
    
    async def get_gaps_summary(self) -> Dict[str, Any]:
        """Get content gaps summary."""
        # Mock gaps data
        gaps = [
            {
                "query_text": "How to optimize AI search visibility",
                "opportunity_score": 0.92,
                "gap_type": "no_citations",
                "suggested_content_type": "comprehensive_guide",
                "priority": "high",
                "reasoning": "High search volume query with no current citations - clear opportunity for thought leadership content"
            },
            {
                "query_text": "Best practices for AI-powered content",
                "opportunity_score": 0.87,
                "gap_type": "weak_citations",
                "suggested_content_type": "expert_roundup",
                "priority": "high", 
                "reasoning": "Existing citations are low quality - opportunity to create authoritative resource"
            }
        ]
        
        return {
            "gaps": gaps,
            "total_opportunities": len(gaps),
            "high_priority_count": len([g for g in gaps if g["priority"] == "high"])
        }
    
    async def get_competitor_analysis(self, time_range: str, competitor_domains: Optional[List[str]]) -> Dict[str, Any]:
        """Get competitor analysis data."""
        competitors = [
            {"domain": "competitor1.com", "citation_share": 0.18, "trend": "increasing"},
            {"domain": "competitor2.com", "citation_share": 0.14, "trend": "stable"},
            {"domain": "competitor3.com", "citation_share": 0.11, "trend": "decreasing"}
        ]
        
        return {
            "competitors": competitors,
            "market_share_analysis": {
                "our_share": 0.23,
                "competitor_share": 0.43,
                "other_share": 0.34
            }
        }