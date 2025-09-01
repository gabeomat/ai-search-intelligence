"""Content gap identification and opportunity analysis."""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict, Counter
from dataclasses import dataclass, asdict
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.cluster import KMeans
import re

from ..core.config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class ContentGap:
    """Represents an identified content gap."""
    gap_id: str
    query_text: str
    gap_type: str  # no_citations, weak_citations, competitor_dominated, trending_topic
    opportunity_score: float  # 0.0 to 1.0
    suggested_content_type: str
    suggested_topics: List[str]
    competing_domains: List[str]
    search_volume_estimate: int
    difficulty_score: float  # 0.0 to 1.0 (higher = more difficult)
    priority: str  # low, medium, high
    reasoning: str
    related_queries: List[str]
    content_angle_suggestions: List[str]
    estimated_effort: str  # low, medium, high
    potential_impact: str  # low, medium, high


@dataclass
class TopicCluster:
    """Represents a cluster of related topics/queries."""
    cluster_id: str
    representative_query: str
    related_queries: List[str]
    total_citations: int
    avg_citation_strength: float
    dominant_domains: List[str]
    content_types: List[str]
    gap_opportunities: List[str]


class ContentGapAnalyzer:
    """Identifies content gaps and opportunities across AI search engines."""
    
    def __init__(self):
        self.settings = get_settings()
        self.min_opportunity_score = 0.3
        self.high_opportunity_threshold = 0.7
        
    def identify_content_gaps(
        self,
        citations: List[Dict[str, Any]],
        tracked_queries: List[str],
        competitor_domains: List[str] = None
    ) -> List[ContentGap]:
        """
        Identify content gaps based on citation analysis.
        
        Args:
            citations: List of citation dictionaries
            tracked_queries: List of queries being tracked
            competitor_domains: List of competitor domains to consider
            
        Returns:
            List of identified content gaps
        """
        if not citations or not tracked_queries:
            return []
        
        gaps = []
        df = pd.DataFrame(citations)
        
        # Analyze different types of gaps
        no_citation_gaps = self._find_no_citation_gaps(df, tracked_queries)
        gaps.extend(no_citation_gaps)
        
        weak_citation_gaps = self._find_weak_citation_gaps(df)
        gaps.extend(weak_citation_gaps)
        
        competitor_dominated_gaps = self._find_competitor_dominated_gaps(df, competitor_domains or [])
        gaps.extend(competitor_dominated_gaps)
        
        topic_cluster_gaps = self._find_topic_cluster_gaps(df, tracked_queries)
        gaps.extend(topic_cluster_gaps)
        
        question_variation_gaps = self._find_question_variation_gaps(df, tracked_queries)
        gaps.extend(question_variation_gaps)
        
        # Score and prioritize gaps
        scored_gaps = self._score_and_prioritize_gaps(gaps, df)
        
        logger.info(f"Identified {len(scored_gaps)} content gaps")
        return scored_gaps
    
    def _find_no_citation_gaps(self, df: pd.DataFrame, tracked_queries: List[str]) -> List[ContentGap]:
        """Find queries with no or very few citations."""
        gaps = []
        
        if 'query' not in df.columns:
            return gaps
        
        query_citation_counts = df['query'].value_counts()
        
        for query in tracked_queries:
            citation_count = query_citation_counts.get(query, 0)
            
            if citation_count == 0:
                gap = ContentGap(
                    gap_id=f"no_citations_{hash(query)}",
                    query_text=query,
                    gap_type="no_citations",
                    opportunity_score=0.8,  # High opportunity for queries with no competition
                    suggested_content_type=self._suggest_content_type_for_query(query),
                    suggested_topics=self._extract_topics_from_query(query),
                    competing_domains=[],
                    search_volume_estimate=self._estimate_search_volume(query),
                    difficulty_score=0.2,  # Low difficulty when no one is competing
                    priority="high",
                    reasoning=f"No citations found for '{query}' - clear opportunity for original content",
                    related_queries=self._find_related_queries(query, tracked_queries),
                    content_angle_suggestions=self._suggest_content_angles(query),
                    estimated_effort=self._estimate_content_effort(query),
                    potential_impact="high"
                )
                gaps.append(gap)
            
            elif citation_count <= 2:  # Very weak competition
                competing_domains = df[df['query'] == query]['source_domain'].unique().tolist() if 'source_domain' in df.columns else []
                
                gap = ContentGap(
                    gap_id=f"weak_citations_{hash(query)}",
                    query_text=query,
                    gap_type="weak_citations",
                    opportunity_score=0.7,
                    suggested_content_type=self._suggest_content_type_for_query(query),
                    suggested_topics=self._extract_topics_from_query(query),
                    competing_domains=competing_domains,
                    search_volume_estimate=self._estimate_search_volume(query),
                    difficulty_score=0.3,
                    priority="high",
                    reasoning=f"Only {citation_count} citations for '{query}' - opportunity to dominate",
                    related_queries=self._find_related_queries(query, tracked_queries),
                    content_angle_suggestions=self._suggest_content_angles(query),
                    estimated_effort=self._estimate_content_effort(query),
                    potential_impact="high"
                )
                gaps.append(gap)
        
        return gaps
    
    def _find_weak_citation_gaps(self, df: pd.DataFrame) -> List[ContentGap]:
        """Find queries with weak citation quality or low prominence scores."""
        gaps = []
        
        if 'prominence_score' not in df.columns or 'query' not in df.columns:
            return gaps
        
        # Group by query and calculate average prominence
        query_prominence = df.groupby('query')['prominence_score'].agg(['mean', 'count', 'std']).reset_index()
        
        # Find queries with low average prominence
        weak_queries = query_prominence[
            (query_prominence['mean'] < 0.5) & 
            (query_prominence['count'] >= 2)  # At least some citations exist
        ]
        
        for _, row in weak_queries.iterrows():
            query = row['query']
            competing_domains = df[df['query'] == query]['source_domain'].unique().tolist() if 'source_domain' in df.columns else []
            
            gap = ContentGap(
                gap_id=f"low_prominence_{hash(query)}",
                query_text=query,
                gap_type="weak_citations",
                opportunity_score=0.6 + (0.5 - row['mean']),  # Higher opportunity for lower prominence
                suggested_content_type=self._suggest_content_type_for_query(query),
                suggested_topics=self._extract_topics_from_query(query),
                competing_domains=competing_domains,
                search_volume_estimate=self._estimate_search_volume(query),
                difficulty_score=0.4 + (row['mean'] * 0.4),  # Higher difficulty for higher existing prominence
                priority="medium",
                reasoning=f"Low average prominence ({row['mean']:.2f}) for '{query}' - opportunity to create higher-quality content",
                related_queries=[],
                content_angle_suggestions=self._suggest_content_angles(query, improve_existing=True),
                estimated_effort=self._estimate_content_effort(query),
                potential_impact="medium"
            )
            gaps.append(gap)
        
        return gaps
    
    def _find_competitor_dominated_gaps(self, df: pd.DataFrame, competitor_domains: List[str]) -> List[ContentGap]:
        """Find queries dominated by competitor domains."""
        gaps = []
        
        if not competitor_domains or 'source_domain' not in df.columns or 'query' not in df.columns:
            return gaps
        
        competitor_domains_lower = [d.lower() for d in competitor_domains]
        
        # Find queries where competitors have high citation share
        for query in df['query'].unique():
            query_citations = df[df['query'] == query]
            total_citations = len(query_citations)
            
            if total_citations < 3:  # Skip queries with very few citations
                continue
            
            competitor_citations = query_citations[
                query_citations['source_domain'].isin(competitor_domains_lower)
            ]
            competitor_share = len(competitor_citations) / total_citations
            
            if competitor_share >= 0.6:  # Competitors dominate
                competing_domains = query_citations['source_domain'].unique().tolist()
                
                # Calculate average competitor prominence
                avg_competitor_prominence = competitor_citations['prominence_score'].mean() if 'prominence_score' in df.columns else 0.5
                
                gap = ContentGap(
                    gap_id=f"competitor_dominated_{hash(query)}",
                    query_text=query,
                    gap_type="competitor_dominated",
                    opportunity_score=0.5 - (competitor_share * 0.2),  # Lower opportunity when heavily dominated
                    suggested_content_type=self._suggest_content_type_for_query(query),
                    suggested_topics=self._extract_topics_from_query(query),
                    competing_domains=competing_domains,
                    search_volume_estimate=self._estimate_search_volume(query),
                    difficulty_score=0.6 + (competitor_share * 0.3),  # Higher difficulty when competitors dominate
                    priority="low" if competitor_share > 0.8 else "medium",
                    reasoning=f"Competitors control {competitor_share:.1%} of citations for '{query}' - challenging but potential for disruption",
                    related_queries=self._find_related_queries(query, df['query'].unique().tolist()),
                    content_angle_suggestions=self._suggest_content_angles(query, differentiate=True),
                    estimated_effort="high",
                    potential_impact="high" if competitor_share < 0.8 else "medium"
                )
                gaps.append(gap)
        
        return gaps
    
    def _find_topic_cluster_gaps(self, df: pd.DataFrame, tracked_queries: List[str]) -> List[ContentGap]:
        """Find gaps in topic clusters - topics with uneven coverage."""
        gaps = []
        
        if len(tracked_queries) < 10:  # Need sufficient queries for clustering
            return gaps
        
        try:
            # Cluster queries by topic similarity
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 2))
            query_vectors = vectorizer.fit_transform(tracked_queries)
            
            # Use reasonable number of clusters
            n_clusters = min(5, len(tracked_queries) // 4)
            if n_clusters < 2:
                return gaps
            
            kmeans = KMeans(n_clusters=n_clusters, random_state=42)
            clusters = kmeans.fit_predict(query_vectors)
            
            # Analyze each cluster
            for cluster_id in range(n_clusters):
                cluster_queries = [q for i, q in enumerate(tracked_queries) if clusters[i] == cluster_id]
                
                if len(cluster_queries) < 2:
                    continue
                
                # Analyze citation coverage within cluster
                cluster_citation_counts = []
                for query in cluster_queries:
                    if 'query' in df.columns:
                        count = len(df[df['query'] == query])
                        cluster_citation_counts.append((query, count))
                
                if not cluster_citation_counts:
                    continue
                
                # Find queries with significantly lower citation counts
                avg_citations = np.mean([count for _, count in cluster_citation_counts])
                
                for query, count in cluster_citation_counts:
                    if count < avg_citations * 0.5 and count < 3:  # Significantly under-represented
                        gap = ContentGap(
                            gap_id=f"topic_cluster_gap_{cluster_id}_{hash(query)}",
                            query_text=query,
                            gap_type="topic_cluster_gap",
                            opportunity_score=0.6,
                            suggested_content_type=self._suggest_content_type_for_query(query),
                            suggested_topics=self._extract_topics_from_query(query),
                            competing_domains=[],
                            search_volume_estimate=self._estimate_search_volume(query),
                            difficulty_score=0.4,
                            priority="medium",
                            reasoning=f"Under-represented in topic cluster - other similar queries have {avg_citations:.1f} avg citations",
                            related_queries=[q for q in cluster_queries if q != query][:3],
                            content_angle_suggestions=self._suggest_content_angles(query, cluster_context=cluster_queries),
                            estimated_effort="medium",
                            potential_impact="medium"
                        )
                        gaps.append(gap)
        
        except Exception as e:
            logger.error(f"Error in topic cluster analysis: {str(e)}")
        
        return gaps
    
    def _find_question_variation_gaps(self, df: pd.DataFrame, tracked_queries: List[str]) -> List[ContentGap]:
        """Find gaps in question variations (different ways of asking the same thing)."""
        gaps = []
        
        # Group queries by topic/intent
        question_patterns = {
            'what_is': r'\bwhat\s+is\b',
            'how_to': r'\bhow\s+to\b|\bhow\s+do\b|\bhow\s+can\b',
            'why': r'\bwhy\b',
            'when': r'\bwhen\b',
            'where': r'\bwhere\b',
            'which': r'\bwhich\b',
            'best': r'\bbest\b',
            'vs_comparison': r'\bvs\b|\bversus\b'
        }
        
        # Extract core topics from queries
        topic_variations = defaultdict(lambda: defaultdict(list))
        
        for query in tracked_queries:
            query_lower = query.lower()
            
            # Identify question type
            question_type = 'general'
            for qtype, pattern in question_patterns.items():
                if re.search(pattern, query_lower):
                    question_type = qtype
                    break
            
            # Extract main topic (simplified approach)
            words = query_lower.split()
            # Remove common question words
            content_words = [w for w in words if w not in {'what', 'is', 'how', 'to', 'do', 'can', 'why', 'when', 'where', 'which', 'the', 'a', 'an'}]
            
            if content_words:
                # Use first few content words as topic identifier
                topic = ' '.join(content_words[:3])
                topic_variations[topic][question_type].append(query)
        
        # Find topics with missing question variations
        for topic, variations in topic_variations.items():
            if len(variations) == 1:  # Only one way of asking about this topic
                existing_type = list(variations.keys())[0]
                existing_queries = variations[existing_type]
                
                # Get citation counts for existing queries
                total_citations = 0
                if 'query' in df.columns:
                    for query in existing_queries:
                        total_citations += len(df[df['query'] == query])
                
                # Suggest missing question types
                missing_types = set(question_patterns.keys()) - set(variations.keys())
                
                for missing_type in missing_types:
                    if missing_type in ['what_is', 'how_to', 'best']:  # Focus on high-value question types
                        suggested_query = self._generate_question_variation(topic, missing_type)
                        
                        if suggested_query:
                            gap = ContentGap(
                                gap_id=f"question_variation_{missing_type}_{hash(topic)}",
                                query_text=suggested_query,
                                gap_type="question_variation",
                                opportunity_score=0.5 + (min(total_citations, 10) * 0.03),  # Higher opportunity if related queries have citations
                                suggested_content_type=self._map_question_type_to_content(missing_type),
                                suggested_topics=[topic.replace(' ', '_')],
                                competing_domains=[],
                                search_volume_estimate=max(100, total_citations * 50),  # Estimate based on related queries
                                difficulty_score=0.3,
                                priority="medium",
                                reasoning=f"Missing '{missing_type}' variation for topic '{topic}' - related queries show interest",
                                related_queries=existing_queries[:3],
                                content_angle_suggestions=self._suggest_content_angles_for_question_type(missing_type, topic),
                                estimated_effort="medium",
                                potential_impact="medium"
                            )
                            gaps.append(gap)
        
        return gaps
    
    def _score_and_prioritize_gaps(self, gaps: List[ContentGap], df: pd.DataFrame) -> List[ContentGap]:
        """Score and prioritize identified gaps."""
        if not gaps:
            return gaps
        
        # Adjust scores based on additional factors
        for gap in gaps:
            # Boost score for high-value question types
            if any(word in gap.query_text.lower() for word in ['how to', 'best', 'guide', 'tutorial']):
                gap.opportunity_score = min(1.0, gap.opportunity_score + 0.1)
            
            # Boost score for commercial intent
            if any(word in gap.query_text.lower() for word in ['buy', 'price', 'cost', 'review', 'comparison']):
                gap.opportunity_score = min(1.0, gap.opportunity_score + 0.15)
                gap.potential_impact = "high"
            
            # Adjust priority based on final score
            if gap.opportunity_score >= 0.8:
                gap.priority = "high"
            elif gap.opportunity_score >= 0.5:
                gap.priority = "medium"
            else:
                gap.priority = "low"
        
        # Sort by opportunity score
        gaps.sort(key=lambda x: x.opportunity_score, reverse=True)
        
        return gaps
    
    def _suggest_content_type_for_query(self, query: str) -> str:
        """Suggest appropriate content type based on query."""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ['how to', 'how do', 'tutorial', 'guide', 'step']):
            return 'tutorial_guide'
        elif any(word in query_lower for word in ['what is', 'definition', 'meaning']):
            return 'explainer_article'
        elif any(word in query_lower for word in ['best', 'top', 'review', 'comparison', 'vs']):
            return 'comparison_review'
        elif any(word in query_lower for word in ['tool', 'calculator', 'generator']):
            return 'interactive_tool'
        elif '?' in query or any(word in query_lower for word in ['why', 'when', 'where']):
            return 'faq_article'
        else:
            return 'comprehensive_article'
    
    def _extract_topics_from_query(self, query: str) -> List[str]:
        """Extract main topics from a query."""
        # Simple topic extraction
        stop_words = {'what', 'is', 'how', 'to', 'do', 'can', 'why', 'when', 'where', 'which', 'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'by', 'for', 'with', 'about'}
        
        words = query.lower().replace('?', '').split()
        topics = [word for word in words if len(word) > 2 and word not in stop_words]
        
        # Return unique topics, limited to 5
        return list(dict.fromkeys(topics))[:5]
    
    def _estimate_search_volume(self, query: str) -> int:
        """Estimate search volume based on query characteristics."""
        # Simplified heuristic based on query type and length
        base_volume = 1000
        
        query_lower = query.lower()
        
        # Adjust based on query type
        if any(word in query_lower for word in ['how to', 'tutorial']):
            base_volume *= 2
        elif any(word in query_lower for word in ['best', 'top', 'review']):
            base_volume *= 1.5
        elif len(query.split()) > 6:  # Very specific queries
            base_volume *= 0.3
        elif len(query.split()) <= 2:  # Very broad queries
            base_volume *= 3
        
        return int(base_volume)
    
    def _find_related_queries(self, query: str, all_queries: List[str]) -> List[str]:
        """Find queries related to the given query."""
        if len(all_queries) < 2:
            return []
        
        try:
            vectorizer = TfidfVectorizer(stop_words='english', ngram_range=(1, 2))
            all_vectors = vectorizer.fit_transform(all_queries + [query])
            
            query_vector = all_vectors[-1]
            other_vectors = all_vectors[:-1]
            
            similarities = cosine_similarity(query_vector, other_vectors)[0]
            
            # Get indices of most similar queries
            similar_indices = np.argsort(similarities)[::-1][:5]
            
            related = []
            for idx in similar_indices:
                if similarities[idx] > 0.3:  # Minimum similarity threshold
                    related.append(all_queries[idx])
            
            return related
            
        except Exception:
            # Fallback to simple word overlap
            query_words = set(query.lower().split())
            related = []
            
            for other_query in all_queries:
                if other_query == query:
                    continue
                
                other_words = set(other_query.lower().split())
                overlap = len(query_words & other_words)
                
                if overlap >= 2:  # At least 2 words in common
                    related.append(other_query)
                    if len(related) >= 5:
                        break
            
            return related
    
    def _suggest_content_angles(self, query: str, improve_existing: bool = False, differentiate: bool = False, cluster_context: List[str] = None) -> List[str]:
        """Suggest content angles for addressing the query."""
        angles = []
        query_lower = query.lower()
        
        # Base angles
        if 'how' in query_lower:
            angles.extend([
                "Step-by-step tutorial with screenshots",
                "Video walkthrough with examples",
                "Common mistakes to avoid guide"
            ])
        elif 'what' in query_lower:
            angles.extend([
                "Comprehensive definition with examples",
                "Visual infographic explanation",
                "Comparison with similar concepts"
            ])
        elif 'best' in query_lower:
            angles.extend([
                "Data-driven comparison with pros/cons",
                "User review aggregation",
                "Expert recommendations with reasoning"
            ])
        
        # Modification based on context
        if improve_existing:
            angles.extend([
                "More detailed analysis than existing content",
                "Recent data and updated information",
                "Original research or case studies"
            ])
        
        if differentiate:
            angles.extend([
                "Unique perspective or contrarian viewpoint",
                "Personal experience or case study approach",
                "Interactive elements or tools"
            ])
        
        if cluster_context:
            angles.append("Comprehensive resource covering related topics")
        
        return angles[:5]  # Limit to 5 suggestions
    
    def _estimate_content_effort(self, query: str) -> str:
        """Estimate the effort required to create content for the query."""
        query_lower = query.lower()
        
        # Technical or complex topics
        if any(word in query_lower for word in ['api', 'code', 'programming', 'technical', 'advanced', 'enterprise']):
            return "high"
        
        # Comparison or research-heavy topics
        elif any(word in query_lower for word in ['best', 'comparison', 'review', 'vs', 'analysis']):
            return "high"
        
        # How-to guides
        elif any(word in query_lower for word in ['how to', 'tutorial', 'guide', 'step']):
            return "medium"
        
        # Simple definitions or FAQs
        elif any(word in query_lower for word in ['what is', 'definition', 'meaning']):
            return "low"
        
        else:
            return "medium"
    
    def _generate_question_variation(self, topic: str, question_type: str) -> str:
        """Generate a question variation for a topic."""
        templates = {
            'what_is': f"What is {topic}?",
            'how_to': f"How to {topic}",
            'best': f"Best {topic}",
            'why': f"Why {topic}",
            'when': f"When {topic}",
            'where': f"Where {topic}",
            'which': f"Which {topic}",
            'vs_comparison': f"{topic} vs alternatives"
        }
        
        return templates.get(question_type, f"{topic}")
    
    def _map_question_type_to_content(self, question_type: str) -> str:
        """Map question type to appropriate content type."""
        mapping = {
            'what_is': 'explainer_article',
            'how_to': 'tutorial_guide',
            'best': 'comparison_review',
            'why': 'analytical_article',
            'when': 'timing_guide',
            'where': 'directory_article',
            'which': 'selection_guide',
            'vs_comparison': 'comparison_article'
        }
        
        return mapping.get(question_type, 'comprehensive_article')
    
    def _suggest_content_angles_for_question_type(self, question_type: str, topic: str) -> List[str]:
        """Suggest content angles specific to question type."""
        angles_map = {
            'what_is': [
                f"Complete beginner's guide to {topic}",
                f"Visual explanation of {topic} with examples",
                f"{topic} explained in simple terms"
            ],
            'how_to': [
                f"Step-by-step {topic} tutorial",
                f"{topic} for beginners",
                f"Advanced {topic} techniques"
            ],
            'best': [
                f"Top-rated {topic} options",
                f"{topic} comparison with pros and cons",
                f"Expert recommendations for {topic}"
            ]
        }
        
        return angles_map.get(question_type, [f"Comprehensive guide to {topic}"])
    
    def generate_gap_report(self, gaps: List[ContentGap]) -> Dict[str, Any]:
        """Generate a comprehensive report of identified content gaps."""
        if not gaps:
            return {'total_gaps': 0, 'summary': 'No content gaps identified'}
        
        # Categorize gaps
        gap_by_type = defaultdict(list)
        gap_by_priority = defaultdict(list)
        
        for gap in gaps:
            gap_by_type[gap.gap_type].append(gap)
            gap_by_priority[gap.priority].append(gap)
        
        # Calculate statistics
        avg_opportunity_score = np.mean([gap.opportunity_score for gap in gaps])
        high_opportunity_gaps = [gap for gap in gaps if gap.opportunity_score >= 0.7]
        
        # Content type recommendations
        suggested_types = Counter([gap.suggested_content_type for gap in gaps])
        
        # Effort distribution
        effort_distribution = Counter([gap.estimated_effort for gap in gaps])
        
        report = {
            'total_gaps': len(gaps),
            'gap_types': {gap_type: len(gaps) for gap_type, gaps in gap_by_type.items()},
            'priority_distribution': {priority: len(gaps) for priority, gaps in gap_by_priority.items()},
            'average_opportunity_score': round(avg_opportunity_score, 2),
            'high_opportunity_gaps': len(high_opportunity_gaps),
            'suggested_content_types': dict(suggested_types.most_common()),
            'effort_distribution': dict(effort_distribution),
            'top_opportunities': [
                {
                    'query': gap.query_text,
                    'opportunity_score': gap.opportunity_score,
                    'gap_type': gap.gap_type,
                    'priority': gap.priority,
                    'suggested_content_type': gap.suggested_content_type,
                    'reasoning': gap.reasoning
                }
                for gap in gaps[:10]  # Top 10
            ],
            'quick_wins': [
                {
                    'query': gap.query_text,
                    'opportunity_score': gap.opportunity_score,
                    'estimated_effort': gap.estimated_effort
                }
                for gap in gaps if gap.estimated_effort == 'low' and gap.opportunity_score >= 0.6
            ][:5],
            'summary': f"Identified {len(gaps)} content gaps with {len(high_opportunity_gaps)} high-opportunity targets"
        }
        
        return report