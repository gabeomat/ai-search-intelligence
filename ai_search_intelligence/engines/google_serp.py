"""Google SERP data collection via SerpAPI."""

import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
import httpx
from serpapi import GoogleSearch

from ..core.config import get_settings
from ..database.models import Citation


logger = logging.getLogger(__name__)


class GoogleSERPCollector:
    """Collects Google SERP data including AI Overviews, featured snippets, and other SERP features."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.api_keys.serpapi_key
        self.rate_limit = self.settings.rate_limit.serpapi_rate_limit
        
    async def collect_citations(self, query: str, location: str = "United States") -> List[Dict[str, Any]]:
        """
        Collect citations from Google SERP for a given query.
        
        Args:
            query: Search query to analyze
            location: Geographic location for search
            
        Returns:
            List of citation data dictionaries
        """
        try:
            # Configure search parameters
            search_params = {
                "q": query,
                "api_key": self.api_key,
                "location": location,
                "hl": "en",
                "gl": "us",
                "device": "desktop",
                "safe": "off",
                "no_cache": True
            }
            
            # Execute search
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            citations = []
            
            # Extract AI Overview citations
            ai_overview_citations = self._extract_ai_overview_citations(results, query)
            citations.extend(ai_overview_citations)
            
            # Extract Featured Snippet citations
            featured_snippet_citations = self._extract_featured_snippet_citations(results, query)
            citations.extend(featured_snippet_citations)
            
            # Extract People Also Ask citations
            paa_citations = self._extract_people_also_ask_citations(results, query)
            citations.extend(paa_citations)
            
            # Extract Knowledge Panel citations
            knowledge_panel_citations = self._extract_knowledge_panel_citations(results, query)
            citations.extend(knowledge_panel_citations)
            
            # Extract organic results that might be cited
            organic_citations = self._extract_organic_citations(results, query)
            citations.extend(organic_citations)
            
            logger.info(f"Collected {len(citations)} citations for query: {query}")
            return citations
            
        except Exception as e:
            logger.error(f"Error collecting citations for query '{query}': {str(e)}")
            return []
    
    def _extract_ai_overview_citations(self, results: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Extract citations from AI Overview section."""
        citations = []
        
        if "ai_overview" not in results:
            return citations
            
        ai_overview = results["ai_overview"]
        
        # Main AI overview content
        if "sources" in ai_overview:
            for idx, source in enumerate(ai_overview["sources"]):
                citation = {
                    "engine": "google",
                    "query": query,
                    "url": source.get("link", ""),
                    "title": source.get("title", ""),
                    "snippet": source.get("snippet", ""),
                    "position": idx + 1,
                    "citation_type": "ai_overview",
                    "source_domain": self._extract_domain(source.get("link", "")),
                    "prominence_score": self._calculate_ai_overview_prominence(idx, len(ai_overview["sources"])),
                    "metadata": {
                        "ai_overview_text": ai_overview.get("text", ""),
                        "source_index": idx,
                        "total_sources": len(ai_overview["sources"])
                    }
                }
                citations.append(citation)
        
        return citations
    
    def _extract_featured_snippet_citations(self, results: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Extract citations from featured snippets."""
        citations = []
        
        if "answer_box" in results:
            answer_box = results["answer_box"]
            citation = {
                "engine": "google",
                "query": query,
                "url": answer_box.get("link", ""),
                "title": answer_box.get("title", ""),
                "snippet": answer_box.get("snippet", ""),
                "position": 0,  # Featured snippets are position 0
                "citation_type": "featured_snippet",
                "source_domain": self._extract_domain(answer_box.get("link", "")),
                "prominence_score": 1.0,  # Featured snippets have maximum prominence
                "metadata": {
                    "snippet_type": answer_box.get("type", ""),
                    "displayed_link": answer_box.get("displayed_link", "")
                }
            }
            citations.append(citation)
            
        return citations
    
    def _extract_people_also_ask_citations(self, results: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Extract citations from People Also Ask section."""
        citations = []
        
        if "related_questions" in results:
            for idx, question in enumerate(results["related_questions"]):
                if "snippet" in question:
                    snippet_data = question["snippet"]
                    citation = {
                        "engine": "google",
                        "query": query,
                        "url": snippet_data.get("link", ""),
                        "title": snippet_data.get("title", ""),
                        "snippet": snippet_data.get("snippet", ""),
                        "position": idx + 1,
                        "citation_type": "people_also_ask",
                        "source_domain": self._extract_domain(snippet_data.get("link", "")),
                        "prominence_score": self._calculate_paa_prominence(idx),
                        "metadata": {
                            "question": question.get("question", ""),
                            "paa_index": idx
                        }
                    }
                    citations.append(citation)
        
        return citations
    
    def _extract_knowledge_panel_citations(self, results: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Extract citations from Knowledge Panel."""
        citations = []
        
        if "knowledge_graph" in results:
            kg = results["knowledge_graph"]
            
            # Main knowledge graph source
            if "source" in kg:
                source = kg["source"]
                citation = {
                    "engine": "google",
                    "query": query,
                    "url": source.get("link", ""),
                    "title": kg.get("title", ""),
                    "snippet": kg.get("description", ""),
                    "position": 1,
                    "citation_type": "knowledge_panel",
                    "source_domain": self._extract_domain(source.get("link", "")),
                    "prominence_score": 0.9,  # High prominence for knowledge panels
                    "metadata": {
                        "kg_type": kg.get("type", ""),
                        "source_name": source.get("name", "")
                    }
                }
                citations.append(citation)
                
            # Additional knowledge graph sources
            if "sources" in kg:
                for idx, source in enumerate(kg["sources"]):
                    citation = {
                        "engine": "google",
                        "query": query,
                        "url": source.get("link", ""),
                        "title": source.get("name", ""),
                        "snippet": "",
                        "position": idx + 2,
                        "citation_type": "knowledge_panel_source",
                        "source_domain": self._extract_domain(source.get("link", "")),
                        "prominence_score": 0.7 - (idx * 0.1),  # Decreasing prominence
                        "metadata": {
                            "source_type": "additional_kg_source",
                            "source_index": idx
                        }
                    }
                    citations.append(citation)
        
        return citations
    
    def _extract_organic_citations(self, results: Dict[str, Any], query: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Extract citations from organic search results."""
        citations = []
        
        if "organic_results" in results:
            for idx, result in enumerate(results["organic_results"][:max_results]):
                citation = {
                    "engine": "google",
                    "query": query,
                    "url": result.get("link", ""),
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "position": result.get("position", idx + 1),
                    "citation_type": "organic",
                    "source_domain": self._extract_domain(result.get("link", "")),
                    "prominence_score": self._calculate_organic_prominence(result.get("position", idx + 1)),
                    "metadata": {
                        "displayed_link": result.get("displayed_link", ""),
                        "cached_page_link": result.get("cached_page_link", ""),
                        "rich_snippet": result.get("rich_snippet", {})
                    }
                }
                citations.append(citation)
        
        return citations
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ""
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""
    
    def _calculate_ai_overview_prominence(self, position: int, total_sources: int) -> float:
        """Calculate prominence score for AI Overview citations."""
        if total_sources == 0:
            return 0.0
        # First source gets highest score, decreases logarithmically
        base_score = 0.9
        position_penalty = (position - 1) * 0.1
        return max(0.1, base_score - position_penalty)
    
    def _calculate_paa_prominence(self, position: int) -> float:
        """Calculate prominence score for People Also Ask citations."""
        # PAA prominence decreases with position
        base_score = 0.6
        position_penalty = position * 0.05
        return max(0.1, base_score - position_penalty)
    
    def _calculate_organic_prominence(self, position: int) -> float:
        """Calculate prominence score for organic results."""
        if position <= 3:
            return 0.5 - ((position - 1) * 0.1)
        elif position <= 10:
            return 0.3 - ((position - 4) * 0.02)
        else:
            return 0.1
    
    async def analyze_serp_features(self, query: str) -> Dict[str, Any]:
        """
        Analyze SERP features present for a given query.
        
        Args:
            query: Search query to analyze
            
        Returns:
            Dictionary with SERP features analysis
        """
        try:
            search_params = {
                "q": query,
                "api_key": self.api_key,
                "location": "United States",
                "hl": "en",
                "gl": "us",
                "device": "desktop"
            }
            
            search = GoogleSearch(search_params)
            results = search.get_dict()
            
            features = {
                "has_ai_overview": "ai_overview" in results,
                "has_featured_snippet": "answer_box" in results,
                "has_people_also_ask": "related_questions" in results and len(results["related_questions"]) > 0,
                "has_knowledge_panel": "knowledge_graph" in results,
                "has_images": "images_results" in results,
                "has_videos": "video_results" in results,
                "has_news": "news_results" in results,
                "has_shopping": "shopping_results" in results,
                "organic_results_count": len(results.get("organic_results", [])),
                "total_results": results.get("search_information", {}).get("total_results", 0),
                "search_time": results.get("search_information", {}).get("time_taken_displayed", 0),
                "query": query,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Detailed feature analysis
            if features["has_ai_overview"]:
                ai_overview = results["ai_overview"]
                features["ai_overview_sources_count"] = len(ai_overview.get("sources", []))
                features["ai_overview_has_text"] = bool(ai_overview.get("text"))
            
            if features["has_people_also_ask"]:
                features["paa_questions_count"] = len(results["related_questions"])
            
            if features["has_knowledge_panel"]:
                kg = results["knowledge_graph"]
                features["knowledge_panel_type"] = kg.get("type", "")
                features["knowledge_panel_has_images"] = "images" in kg
            
            return features
            
        except Exception as e:
            logger.error(f"Error analyzing SERP features for query '{query}': {str(e)}")
            return {}
    
    async def get_competitor_citations(self, query: str, competitor_domains: List[str]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Get citations for competitor domains for a specific query.
        
        Args:
            query: Search query
            competitor_domains: List of competitor domains to track
            
        Returns:
            Dictionary mapping domains to their citations
        """
        citations = await self.collect_citations(query)
        competitor_citations = {}
        
        for domain in competitor_domains:
            domain_citations = [
                citation for citation in citations
                if citation["source_domain"] == domain.lower()
            ]
            competitor_citations[domain] = domain_citations
        
        return competitor_citations