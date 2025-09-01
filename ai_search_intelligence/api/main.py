"""Main FastAPI application with analytics dashboard endpoints."""

from fastapi import FastAPI, HTTPException, Depends, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..core.config import get_settings
from .analytics import AnalyticsDashboard
from .reporting import ReportGenerator


settings = get_settings()

app = FastAPI(
    title=settings.api.title,
    description=settings.api.description,
    version=settings.api.version
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
dashboard = AnalyticsDashboard()
report_generator = ReportGenerator()


@app.get("/")
async def root():
    """Root endpoint with system information."""
    return {
        "name": "AI Search Intelligence API",
        "version": settings.api.version,
        "status": "running",
        "endpoints": {
            "dashboard": "/dashboard",
            "api_docs": "/docs",
            "analytics": "/api/v1/analytics/",
            "reports": "/api/v1/reports/"
        }
    }


@app.get("/dashboard", response_class=HTMLResponse)
async def get_dashboard():
    """Serve the analytics dashboard HTML."""
    return await dashboard.generate_dashboard_html()


@app.get("/api/v1/analytics/overview")
async def get_analytics_overview(
    time_range: str = Query("7d", description="Time range: 1d, 7d, 30d, 90d")
):
    """Get overall analytics overview."""
    try:
        overview = await dashboard.get_overview_data(time_range)
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/citations/trends")
async def get_citation_trends(
    time_range: str = Query("30d"),
    engine: Optional[str] = Query(None, description="Filter by engine"),
    granularity: str = Query("daily", description="daily, weekly, monthly")
):
    """Get citation trends over time."""
    try:
        trends = await dashboard.get_citation_trends(time_range, engine, granularity)
        return trends
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/domains/performance")
async def get_domain_performance(
    time_range: str = Query("30d"),
    limit: int = Query(20, description="Number of domains to return")
):
    """Get domain performance analytics."""
    try:
        performance = await dashboard.get_domain_performance(time_range, limit)
        return performance
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/engines/comparison")
async def get_engine_comparison(
    time_range: str = Query("30d")
):
    """Compare performance across search engines."""
    try:
        comparison = await dashboard.get_engine_comparison(time_range)
        return comparison
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/content-types")
async def get_content_type_analysis(
    time_range: str = Query("30d")
):
    """Analyze citation performance by content type."""
    try:
        analysis = await dashboard.get_content_type_analysis(time_range)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/gaps/summary")
async def get_gaps_summary():
    """Get summary of identified content gaps."""
    try:
        summary = await dashboard.get_gaps_summary()
        return summary
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/analytics/competitors")
async def get_competitor_analysis(
    time_range: str = Query("30d"),
    competitor_domains: Optional[List[str]] = Query(None)
):
    """Get competitor analysis."""
    try:
        analysis = await dashboard.get_competitor_analysis(time_range, competitor_domains)
        return analysis
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/reports/generate")
async def generate_report(
    report_type: str = Query(..., description="weekly, monthly, quarterly"),
    format: str = Query("json", description="json, pdf, html"),
    email_recipients: Optional[List[str]] = Query(None)
):
    """Generate and optionally send reports."""
    try:
        report = await report_generator.generate_report(report_type, format, email_recipients)
        return report
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": settings.api.version
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.api.host,
        port=settings.api.port,
        reload=settings.api.reload
    )