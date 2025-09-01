"""Citation extraction and parsing utilities."""

import re
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Tuple
from urllib.parse import urlparse, urljoin
from dataclasses import dataclass
import httpx
from bs4 import BeautifulSoup, Comment

from ..core.config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class ParsedCitation:
    """Structured citation data."""
    url: str
    title: str
    snippet: str
    domain: str
    content_type: str
    word_count: int
    schema_markup: Dict[str, Any]
    meta_tags: Dict[str, str]
    headers: List[str]
    links_count: int
    images_count: int
    authority_signals: Dict[str, Any]
    freshness_signals: Dict[str, Any]
    content_features: Dict[str, Any]


class CitationParser:
    """Parses and analyzes content from cited URLs."""
    
    def __init__(self):
        self.settings = get_settings()
        self.timeout = 30.0
        self.max_content_length = 1000000  # 1MB max
        
    async def parse_citation_content(self, url: str) -> Optional[ParsedCitation]:
        """
        Parse content from a cited URL to extract detailed information.
        
        Args:
            url: URL to parse
            
        Returns:
            ParsedCitation object or None if parsing fails
        """
        try:
            async with httpx.AsyncClient(
                timeout=self.timeout,
                follow_redirects=True,
                limits=httpx.Limits(max_connections=10)
            ) as client:
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (compatible; AISearchIntelligence/1.0; +https://example.com/bot)',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Accept-Encoding': 'gzip, deflate',
                    'DNT': '1',
                    'Connection': 'keep-alive',
                }
                
                response = await client.get(url, headers=headers)
                
                if response.status_code != 200:
                    logger.warning(f"Failed to fetch {url}: HTTP {response.status_code}")
                    return None
                
                content_type = response.headers.get('content-type', '').lower()
                if 'text/html' not in content_type:
                    logger.warning(f"Skipping non-HTML content: {url}")
                    return None
                
                content = response.text
                if len(content) > self.max_content_length:
                    content = content[:self.max_content_length]
                
                return await self._parse_html_content(url, content)
                
        except Exception as e:
            logger.error(f"Error parsing citation {url}: {str(e)}")
            return None
    
    async def _parse_html_content(self, url: str, html_content: str) -> ParsedCitation:
        """Parse HTML content and extract structured data."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()
        
        # Remove comments
        for comment in soup.find_all(string=lambda text: isinstance(text, Comment)):
            comment.extract()
        
        # Extract basic information
        domain = self._extract_domain(url)
        title = self._extract_title(soup)
        snippet = self._extract_snippet(soup)
        
        # Content analysis
        text_content = soup.get_text()
        word_count = len(text_content.split())
        
        # Extract structured data
        schema_markup = self._extract_schema_markup(soup)
        meta_tags = self._extract_meta_tags(soup)
        headers = self._extract_headers(soup)
        
        # Count elements
        links_count = len(soup.find_all('a', href=True))
        images_count = len(soup.find_all('img'))
        
        # Analyze authority signals
        authority_signals = self._analyze_authority_signals(soup, url)
        
        # Analyze freshness signals
        freshness_signals = self._analyze_freshness_signals(soup, meta_tags)
        
        # Extract content features
        content_features = self._extract_content_features(soup, text_content)
        
        # Determine content type
        content_type = self._determine_content_type(soup, meta_tags, url)
        
        return ParsedCitation(
            url=url,
            title=title,
            snippet=snippet,
            domain=domain,
            content_type=content_type,
            word_count=word_count,
            schema_markup=schema_markup,
            meta_tags=meta_tags,
            headers=headers,
            links_count=links_count,
            images_count=images_count,
            authority_signals=authority_signals,
            freshness_signals=freshness_signals,
            content_features=content_features
        )
    
    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            return urlparse(url).netloc.lower()
        except Exception:
            return ""
    
    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        # Try different title sources in order of preference
        title_sources = [
            soup.find('meta', property='og:title'),
            soup.find('meta', name='twitter:title'),
            soup.find('title'),
            soup.find('h1')
        ]
        
        for source in title_sources:
            if source:
                if source.name == 'meta':
                    title = source.get('content', '').strip()
                else:
                    title = source.get_text().strip()
                
                if title:
                    return title[:200]  # Limit title length
        
        return ""
    
    def _extract_snippet(self, soup: BeautifulSoup) -> str:
        """Extract page description/snippet."""
        # Try different description sources
        description_sources = [
            soup.find('meta', name='description'),
            soup.find('meta', property='og:description'),
            soup.find('meta', name='twitter:description')
        ]
        
        for source in description_sources:
            if source:
                description = source.get('content', '').strip()
                if description:
                    return description[:300]  # Limit snippet length
        
        # Fallback to first paragraph
        first_p = soup.find('p')
        if first_p:
            return first_p.get_text().strip()[:300]
        
        return ""
    
    def _extract_schema_markup(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """Extract JSON-LD and microdata schema markup."""
        schema_data = {}
        
        # Extract JSON-LD
        json_ld_scripts = soup.find_all('script', type='application/ld+json')
        json_ld_data = []
        
        for script in json_ld_scripts:
            try:
                import json
                data = json.loads(script.string)
                json_ld_data.append(data)
            except (json.JSONDecodeError, AttributeError):
                continue
        
        if json_ld_data:
            schema_data['json_ld'] = json_ld_data
        
        # Extract microdata
        microdata_items = soup.find_all(attrs={"itemscope": True})
        if microdata_items:
            microdata = []
            for item in microdata_items:
                item_type = item.get('itemtype', '')
                properties = {}
                
                for prop in item.find_all(attrs={"itemprop": True}):
                    prop_name = prop.get('itemprop')
                    prop_value = prop.get('content') or prop.get_text().strip()
                    properties[prop_name] = prop_value
                
                microdata.append({
                    'type': item_type,
                    'properties': properties
                })
            
            schema_data['microdata'] = microdata
        
        return schema_data
    
    def _extract_meta_tags(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract important meta tags."""
        meta_tags = {}
        
        # Standard meta tags
        standard_tags = [
            'description', 'keywords', 'author', 'robots', 'viewport',
            'generator', 'copyright', 'language', 'rating'
        ]
        
        for tag_name in standard_tags:
            tag = soup.find('meta', name=tag_name)
            if tag:
                meta_tags[tag_name] = tag.get('content', '')
        
        # Open Graph tags
        og_tags = soup.find_all('meta', property=lambda x: x and x.startswith('og:'))
        for tag in og_tags:
            prop = tag.get('property', '')
            content = tag.get('content', '')
            if prop and content:
                meta_tags[prop] = content
        
        # Twitter tags
        twitter_tags = soup.find_all('meta', name=lambda x: x and x.startswith('twitter:'))
        for tag in twitter_tags:
            name = tag.get('name', '')
            content = tag.get('content', '')
            if name and content:
                meta_tags[name] = content
        
        return meta_tags
    
    def _extract_headers(self, soup: BeautifulSoup) -> List[str]:
        """Extract page headers (H1-H6)."""
        headers = []
        
        for i in range(1, 7):
            header_tags = soup.find_all(f'h{i}')
            for tag in header_tags:
                header_text = tag.get_text().strip()
                if header_text:
                    headers.append(f"H{i}: {header_text}")
        
        return headers
    
    def _analyze_authority_signals(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Analyze signals that indicate content authority."""
        signals = {}
        
        # Check for author information
        author_selectors = [
            '[rel="author"]',
            '.author',
            '.byline',
            '[itemprop="author"]'
        ]
        
        author_info = []
        for selector in author_selectors:
            elements = soup.select(selector)
            for elem in elements:
                author_text = elem.get_text().strip()
                if author_text and len(author_text) < 100:
                    author_info.append(author_text)
        
        signals['authors'] = list(set(author_info))
        
        # Check for publication info
        publication_selectors = [
            '[itemprop="publisher"]',
            '.publication',
            '.site-name',
            '[property="og:site_name"]'
        ]
        
        publication_info = []
        for selector in publication_selectors:
            elements = soup.select(selector)
            for elem in elements:
                if elem.name == 'meta':
                    pub_text = elem.get('content', '').strip()
                else:
                    pub_text = elem.get_text().strip()
                if pub_text and len(pub_text) < 100:
                    publication_info.append(pub_text)
        
        signals['publishers'] = list(set(publication_info))
        
        # Check for external links (indicating research)
        external_links = []
        domain = self._extract_domain(url)
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if href.startswith('http') and domain not in href:
                external_links.append(self._extract_domain(href))
        
        signals['external_domains_count'] = len(set(external_links))
        signals['total_external_links'] = len(external_links)
        
        # Check for citations/references
        citation_indicators = [
            'references', 'citations', 'sources', 'bibliography'
        ]
        
        has_citations = any(
            indicator in soup.get_text().lower()
            for indicator in citation_indicators
        )
        signals['has_citations'] = has_citations
        
        return signals
    
    def _analyze_freshness_signals(self, soup: BeautifulSoup, meta_tags: Dict[str, str]) -> Dict[str, Any]:
        """Analyze signals that indicate content freshness."""
        signals = {}
        
        # Extract dates from meta tags
        date_fields = [
            'article:published_time',
            'article:modified_time',
            'og:updated_time',
            'date',
            'pubdate',
            'last-modified'
        ]
        
        extracted_dates = {}
        for field in date_fields:
            if field in meta_tags:
                extracted_dates[field] = meta_tags[field]
        
        signals['meta_dates'] = extracted_dates
        
        # Look for date patterns in content
        date_patterns = [
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
            r'\b\d{4}[/-]\d{1,2}[/-]\d{1,2}\b'
        ]
        
        text_content = soup.get_text()
        found_dates = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, text_content, re.IGNORECASE)
            found_dates.extend(matches)
        
        signals['content_dates'] = found_dates[:10]  # Limit to first 10 dates
        
        # Check for update indicators
        update_indicators = [
            'updated', 'last modified', 'revised', 'edited'
        ]
        
        has_update_info = any(
            indicator in text_content.lower()
            for indicator in update_indicators
        )
        signals['has_update_indicators'] = has_update_info
        
        return signals
    
    def _extract_content_features(self, soup: BeautifulSoup, text_content: str) -> Dict[str, Any]:
        """Extract features that describe the content structure and type."""
        features = {}
        
        # Content structure
        features['paragraph_count'] = len(soup.find_all('p'))
        features['list_count'] = len(soup.find_all(['ul', 'ol']))
        features['table_count'] = len(soup.find_all('table'))
        features['image_count'] = len(soup.find_all('img'))
        features['video_count'] = len(soup.find_all(['video', 'iframe']))
        
        # Content characteristics
        sentences = text_content.split('.')
        features['sentence_count'] = len([s for s in sentences if s.strip()])
        features['avg_sentence_length'] = sum(len(s.split()) for s in sentences if s.strip()) / max(1, len(sentences))
        
        # Question content (useful for FAQ detection)
        question_words = ['what', 'how', 'why', 'when', 'where', 'who', 'which']
        question_count = sum(
            text_content.lower().count(f'{word} ') + text_content.count('?')
            for word in question_words
        )
        features['question_indicators'] = question_count
        
        # Technical content indicators
        technical_indicators = ['API', 'code', 'function', 'method', 'class', 'variable']
        technical_score = sum(
            text_content.count(indicator) for indicator in technical_indicators
        )
        features['technical_content_score'] = technical_score
        
        # List content (tutorials, guides)
        list_indicators = ['step', 'first', 'second', 'third', 'next', 'then', 'finally']
        list_score = sum(
            text_content.lower().count(indicator) for indicator in list_indicators
        )
        features['list_content_score'] = list_score
        
        return features
    
    def _determine_content_type(self, soup: BeautifulSoup, meta_tags: Dict[str, str], url: str) -> str:
        """Determine the type of content based on various signals."""
        
        # Check URL patterns
        url_lower = url.lower()
        if any(pattern in url_lower for pattern in ['/blog/', '/article/', '/post/']):
            return 'blog_post'
        elif any(pattern in url_lower for pattern in ['/tool/', '/calculator/', '/generator/']):
            return 'tool'
        elif any(pattern in url_lower for pattern in ['/guide/', '/tutorial/', '/how-to/']):
            return 'guide'
        elif any(pattern in url_lower for pattern in ['/faq/', '/help/', '/support/']):
            return 'faq'
        
        # Check meta tags
        if 'og:type' in meta_tags:
            og_type = meta_tags['og:type'].lower()
            if og_type == 'article':
                return 'article'
            elif og_type in ['product', 'product.group']:
                return 'product_page'
        
        # Check schema markup
        schema_data = self._extract_schema_markup(soup)
        if 'json_ld' in schema_data:
            for schema in schema_data['json_ld']:
                schema_type = schema.get('@type', '').lower()
                if schema_type in ['article', 'blogposting', 'newsarticle']:
                    return 'article'
                elif schema_type in ['product', 'offer']:
                    return 'product_page'
                elif schema_type == 'faqpage':
                    return 'faq'
                elif schema_type in ['howto', 'recipe']:
                    return 'guide'
        
        # Fallback to content analysis
        text_content = soup.get_text().lower()
        
        if text_content.count('?') > 5:  # Many questions
            return 'faq'
        elif any(word in text_content for word in ['step 1', 'step 2', 'first,', 'second,']):
            return 'guide'
        elif len(soup.find_all('form')) > 0:
            return 'tool'
        elif any(word in text_content for word in ['buy', 'price', '$', 'purchase', 'cart']):
            return 'product_page'
        
        return 'article'  # Default fallback


class CitationNormalizer:
    """Normalizes citation data from different sources."""
    
    @staticmethod
    def normalize_citation(citation_data: Dict[str, Any], source_engine: str) -> Dict[str, Any]:
        """
        Normalize citation data to a standard format.
        
        Args:
            citation_data: Raw citation data from an engine
            source_engine: Engine that provided the citation
            
        Returns:
            Normalized citation dictionary
        """
        normalized = {
            'engine': source_engine,
            'url': citation_data.get('url', ''),
            'title': citation_data.get('title', ''),
            'snippet': citation_data.get('snippet', ''),
            'position': citation_data.get('position', 0),
            'citation_type': citation_data.get('citation_type', 'unknown'),
            'source_domain': citation_data.get('source_domain', ''),
            'prominence_score': citation_data.get('prominence_score', 0.0),
            'metadata': citation_data.get('metadata', {}),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Clean and validate data
        normalized['url'] = CitationNormalizer._clean_url(normalized['url'])
        normalized['title'] = CitationNormalizer._clean_text(normalized['title'], max_length=200)
        normalized['snippet'] = CitationNormalizer._clean_text(normalized['snippet'], max_length=500)
        normalized['prominence_score'] = max(0.0, min(1.0, normalized['prominence_score']))
        
        return normalized
    
    @staticmethod
    def _clean_url(url: str) -> str:
        """Clean and validate URL."""
        if not url:
            return ''
        
        # Remove tracking parameters
        tracking_params = [
            'utm_source', 'utm_medium', 'utm_campaign', 'utm_term', 'utm_content',
            'fbclid', 'gclid', 'ref', 'source'
        ]
        
        try:
            from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            
            # Remove tracking parameters
            clean_params = {k: v for k, v in query_params.items() if k not in tracking_params}
            clean_query = urlencode(clean_params, doseq=True)
            
            clean_url = urlunparse((
                parsed.scheme, parsed.netloc, parsed.path,
                parsed.params, clean_query, parsed.fragment
            ))
            
            return clean_url
            
        except Exception:
            return url
    
    @staticmethod
    def _clean_text(text: str, max_length: int = 500) -> str:
        """Clean and truncate text content."""
        if not text:
            return ''
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        # Truncate if necessary
        if len(text) > max_length:
            text = text[:max_length].rsplit(' ', 1)[0] + '...'
        
        return text