"""Perplexity AI citation tracking and analysis."""

import asyncio
import json
import logging
import re
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
import httpx

from ..core.config import get_settings


logger = logging.getLogger(__name__)


class PerplexityCollector:
    """Collects citation data from Perplexity AI responses."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.settings = get_settings()
        self.api_key = api_key or self.settings.api_keys.perplexity_api_key
        self.base_url = "https://api.perplexity.ai"
        self.rate_limit = self.settings.rate_limit.perplexity_rate_limit
        
    async def collect_citations(self, query: str, model: str = "llama-3.1-sonar-huge-128k-online") -> List[Dict[str, Any]]:
        """
        Collect citations from Perplexity AI for a given query.
        
        Args:
            query: Search query to analyze
            model: Perplexity model to use
            
        Returns:
            List of citation data dictionaries
        """
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": model,
                    "messages": [
                        {
                            "role": "system",
                            "content": "Be precise and comprehensive. Always cite your sources."
                        },
                        {
                            "role": "user", 
                            "content": query
                        }
                    ],
                    "max_tokens": 1000,
                    "temperature": 0.2,
                    "top_p": 0.9,
                    "return_citations": True,
                    "search_domain_filter": [],  # No domain restrictions
                    "return_images": False,
                    "return_related_questions": True,
                    "search_recency_filter": "month",  # Recent results
                    "top_k": 0,
                    "stream": False,
                    "presence_penalty": 0,
                    "frequency_penalty": 1
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code != 200:
                    logger.error(f"Perplexity API error {response.status_code}: {response.text}")
                    return []
                
                result = response.json()
                return await self._extract_citations_from_response(result, query)
                
        except Exception as e:
            logger.error(f"Error collecting Perplexity citations for query '{query}': {str(e)}")
            return []
    
    async def _extract_citations_from_response(self, response: Dict[str, Any], query: str) -> List[Dict[str, Any]]:
        """Extract citation data from Perplexity API response."""
        citations = []
        
        try:
            if "choices" not in response or len(response["choices"]) == 0:
                return citations
            
            choice = response["choices"][0]
            message = choice.get("message", {})
            content = message.get("content", "")
            
            # Extract citations from the response
            if "citations" in response:
                for idx, citation_url in enumerate(response["citations"]):
                    citation = await self._create_citation_from_url(citation_url, query, idx, content)
                    if citation:
                        citations.append(citation)
            
            # Parse inline citations from content
            inline_citations = self._parse_inline_citations(content, query)
            citations.extend(inline_citations)
            
            # Extract follow-up questions if available
            if "related_questions" in response:
                for question in response["related_questions"]:
                    related_citations = await self.collect_citations(question)
                    for citation in related_citations:
                        citation["metadata"]["related_question"] = question
                        citation["citation_type"] = "related_question"
                    citations.extend(related_citations)
            
            logger.info(f"Extracted {len(citations)} citations from Perplexity for query: {query}")
            return citations
            
        except Exception as e:
            logger.error(f"Error extracting citations from Perplexity response: {str(e)}")
            return []
    
    async def _create_citation_from_url(self, url: str, query: str, position: int, content: str) -> Optional[Dict[str, Any]]:
        """Create citation dictionary from URL and context."""
        try:
            domain = self._extract_domain(url)
            
            # Try to extract title and snippet from content
            title, snippet = self._extract_title_and_snippet_from_content(url, content)
            
            citation = {
                "engine": "perplexity",
                "query": query,
                "url": url,
                "title": title,
                "snippet": snippet,
                "position": position + 1,
                "citation_type": "direct_answer",
                "source_domain": domain,
                "prominence_score": self._calculate_perplexity_prominence(position, content, url),
                "metadata": {
                    "citation_context": self._extract_citation_context(url, content),
                    "citation_frequency": content.lower().count(domain.lower()),
                    "citation_position_in_text": self._find_citation_positions(url, content)
                }
            }
            
            return citation
            
        except Exception as e:
            logger.error(f"Error creating citation for URL {url}: {str(e)}")
            return None
    
    def _parse_inline_citations(self, content: str, query: str) -> List[Dict[str, Any]]:
        """Parse inline citations from Perplexity content."""
        citations = []
        
        # Look for citation patterns like [1], [2], etc.
        citation_pattern = r'\[(\d+)\]'
        url_pattern = r'https?://[^\s\]]+|www\.[^\s\]]+(?:\.[a-zA-Z]{2,})[^\s\]]*'
        
        # Find all citation numbers
        citation_matches = re.findall(citation_pattern, content)
        url_matches = re.findall(url_pattern, content)
        
        for idx, url in enumerate(url_matches):
            if not url.startswith('http'):
                url = 'https://' + url
                
            domain = self._extract_domain(url)
            title, snippet = self._extract_title_and_snippet_from_content(url, content)
            
            citation = {
                "engine": "perplexity",
                "query": query,
                "url": url,
                "title": title,
                "snippet": snippet,
                "position": idx + 1,
                "citation_type": "inline_citation",
                "source_domain": domain,
                "prominence_score": self._calculate_inline_prominence(url, content),
                "metadata": {
                    "citation_number": citation_matches[idx] if idx < len(citation_matches) else str(idx + 1),
                    "inline_context": self._extract_citation_context(url, content)
                }
            }
            citations.append(citation)
        
        return citations
    
    def _extract_title_and_snippet_from_content(self, url: str, content: str) -> Tuple[str, str]:
        """Extract title and snippet for a URL from the content context."""
        domain = self._extract_domain(url)
        
        # Look for sentences mentioning the domain
        sentences = content.split('.')
        relevant_sentences = []
        
        for sentence in sentences:
            if domain.lower() in sentence.lower() or url in sentence:
                relevant_sentences.append(sentence.strip())
        
        if relevant_sentences:
            snippet = '. '.join(relevant_sentences[:2])  # Take first 2 relevant sentences
            # Try to infer title from context
            title = f"Content from {domain}"
            return title, snippet
        
        return f"Source: {domain}", ""
    
    def _extract_citation_context(self, url: str, content: str, context_window: int = 100) -> str:
        """Extract context around where a URL is cited."""
        url_pos = content.find(url)
        if url_pos == -1:
            # Try with domain
            domain = self._extract_domain(url)
            url_pos = content.lower().find(domain.lower())
        
        if url_pos == -1:
            return ""
        
        start = max(0, url_pos - context_window)
        end = min(len(content), url_pos + len(url) + context_window)
        
        return content[start:end]
    
    def _find_citation_positions(self, url: str, content: str) -> List[int]:
        """Find all positions where a URL or its domain is mentioned."""
        positions = []
        domain = self._extract_domain(url)
        
        # Find URL positions
        start = 0
        while True:
            pos = content.find(url, start)
            if pos == -1:
                break
            positions.append(pos)
            start = pos + 1
        
        # Find domain positions
        start = 0
        while True:
            pos = content.lower().find(domain.lower(), start)
            if pos == -1:
                break
            if pos not in positions:  # Avoid duplicates
                positions.append(pos)
            start = pos + 1
        
        return sorted(positions)
    
    def _calculate_perplexity_prominence(self, position: int, content: str, url: str) -> float:
        """Calculate prominence score for Perplexity citations."""
        base_score = 0.8 - (position * 0.1)  # Decreases with position
        
        # Boost if cited multiple times
        domain = self._extract_domain(url)
        mention_count = content.lower().count(domain.lower())
        mention_boost = min(0.2, mention_count * 0.05)
        
        # Boost if cited early in the response
        first_mention = content.lower().find(domain.lower())
        if first_mention != -1:
            early_mention_boost = max(0, 0.1 - (first_mention / len(content)) * 0.1)
        else:
            early_mention_boost = 0
        
        return max(0.1, min(1.0, base_score + mention_boost + early_mention_boost))
    
    def _calculate_inline_prominence(self, url: str, content: str) -> float:
        """Calculate prominence score for inline citations."""
        domain = self._extract_domain(url)
        
        # Base score for inline citations
        base_score = 0.6
        
        # Boost based on how often it's mentioned
        mention_count = len(self._find_citation_positions(url, content))
        mention_boost = min(0.3, mention_count * 0.1)
        
        return max(0.1, min(1.0, base_score + mention_boost))
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        if not url:
            return ""
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'https://' + url
            return urlparse(url).netloc.lower()
        except Exception:
            return ""
    
    async def get_follow_up_questions(self, query: str) -> List[str]:
        """Get related questions from Perplexity for a given query."""
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                }
                
                payload = {
                    "model": "llama-3.1-sonar-huge-128k-online",
                    "messages": [
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    "return_related_questions": True,
                    "max_tokens": 100  # Short response, we just want questions
                }
                
                response = await client.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=payload
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return result.get("related_questions", [])
                else:
                    logger.error(f"Error getting follow-up questions: {response.status_code}")
                    return []
                    
        except Exception as e:
            logger.error(f"Error getting follow-up questions for '{query}': {str(e)}")
            return []
    
    async def analyze_citation_patterns(self, query: str) -> Dict[str, Any]:
        """
        Analyze citation patterns in Perplexity responses.
        
        Args:
            query: Search query to analyze
            
        Returns:
            Dictionary with citation pattern analysis
        """
        citations = await self.collect_citations(query)
        
        if not citations:
            return {}
        
        # Analyze domains
        domains = [c["source_domain"] for c in citations if c["source_domain"]]
        domain_counts = {}
        for domain in domains:
            domain_counts[domain] = domain_counts.get(domain, 0) + 1
        
        # Analyze citation types
        citation_types = [c["citation_type"] for c in citations]
        type_counts = {}
        for ctype in citation_types:
            type_counts[ctype] = type_counts.get(ctype, 0) + 1
        
        # Calculate average prominence
        avg_prominence = sum(c["prominence_score"] for c in citations) / len(citations)
        
        analysis = {
            "total_citations": len(citations),
            "unique_domains": len(set(domains)),
            "domain_distribution": domain_counts,
            "citation_types": type_counts,
            "average_prominence": avg_prominence,
            "top_domains": sorted(domain_counts.items(), key=lambda x: x[1], reverse=True)[:5],
            "query": query,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        return analysis