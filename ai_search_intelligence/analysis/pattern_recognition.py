"""Citation pattern recognition and analysis algorithms."""

import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.decomposition import PCA

from ..core.config import get_settings


logger = logging.getLogger(__name__)


@dataclass
class CitationPattern:
    """Represents a discovered citation pattern."""
    pattern_id: str
    pattern_type: str
    description: str
    frequency: int
    strength: float
    examples: List[Dict[str, Any]]
    characteristics: Dict[str, Any]
    engines: List[str]
    domains: List[str]
    content_types: List[str]
    time_range: Tuple[datetime, datetime]


@dataclass
class CompetitorPattern:
    """Represents competitor citation patterns."""
    competitor_domain: str
    citation_frequency: float
    preferred_content_types: List[str]
    strong_topics: List[str]
    citation_timing_patterns: Dict[str, float]
    average_position: float
    engines_dominance: Dict[str, float]


class CitationPatternAnalyzer:
    """Analyzes citation patterns across engines and content types."""
    
    def __init__(self):
        self.settings = get_settings()
        self.min_pattern_frequency = 3
        self.min_pattern_strength = 0.6
        
    def analyze_citation_patterns(self, citations: List[Dict[str, Any]]) -> List[CitationPattern]:
        """
        Analyze citation data to identify patterns.
        
        Args:
            citations: List of citation dictionaries
            
        Returns:
            List of discovered citation patterns
        """
        if not citations:
            return []
        
        patterns = []
        
        # Convert to DataFrame for easier analysis
        df = pd.DataFrame(citations)
        
        # Domain-based patterns
        domain_patterns = self._analyze_domain_patterns(df)
        patterns.extend(domain_patterns)
        
        # Content type patterns
        content_type_patterns = self._analyze_content_type_patterns(df)
        patterns.extend(content_type_patterns)
        
        # Position patterns
        position_patterns = self._analyze_position_patterns(df)
        patterns.extend(position_patterns)
        
        # Temporal patterns
        temporal_patterns = self._analyze_temporal_patterns(df)
        patterns.extend(temporal_patterns)
        
        # Engine-specific patterns
        engine_patterns = self._analyze_engine_patterns(df)
        patterns.extend(engine_patterns)
        
        # Content feature patterns
        feature_patterns = self._analyze_content_feature_patterns(df)
        patterns.extend(feature_patterns)
        
        # Query similarity patterns
        query_patterns = self._analyze_query_similarity_patterns(df)
        patterns.extend(query_patterns)
        
        logger.info(f"Identified {len(patterns)} citation patterns")
        return patterns
    
    def _analyze_domain_patterns(self, df: pd.DataFrame) -> List[CitationPattern]:
        """Analyze patterns based on domain performance."""
        patterns = []
        
        if 'source_domain' not in df.columns:
            return patterns
        
        # Domain frequency analysis
        domain_counts = df['source_domain'].value_counts()
        
        # High-frequency domains
        high_freq_domains = domain_counts[domain_counts >= self.min_pattern_frequency]
        if len(high_freq_domains) > 0:
            pattern = CitationPattern(
                pattern_id=f"high_freq_domains_{datetime.now().strftime('%Y%m%d')}",
                pattern_type="domain_frequency",
                description=f"Domains with high citation frequency (≥{self.min_pattern_frequency} citations)",
                frequency=len(high_freq_domains),
                strength=min(1.0, len(high_freq_domains) / 10),
                examples=[
                    {'domain': domain, 'count': count}
                    for domain, count in high_freq_domains.head(5).items()
                ],
                characteristics={
                    'avg_citations_per_domain': high_freq_domains.mean(),
                    'max_citations': high_freq_domains.max(),
                    'domain_concentration': len(high_freq_domains) / len(domain_counts)
                },
                engines=df['engine'].unique().tolist(),
                domains=high_freq_domains.index.tolist(),
                content_types=df['citation_type'].unique().tolist(),
                time_range=(df['created_at'].min() if 'created_at' in df else datetime.now(),
                          df['created_at'].max() if 'created_at' in df else datetime.now())
            )
            patterns.append(pattern)
        
        # Domain prominence analysis
        if 'prominence_score' in df.columns:
            domain_prominence = df.groupby('source_domain')['prominence_score'].agg(['mean', 'count'])
            high_prominence = domain_prominence[
                (domain_prominence['mean'] >= 0.7) &
                (domain_prominence['count'] >= 2)
            ]
            
            if len(high_prominence) > 0:
                pattern = CitationPattern(
                    pattern_id=f"high_prominence_domains_{datetime.now().strftime('%Y%m%d')}",
                    pattern_type="domain_prominence",
                    description="Domains with consistently high prominence scores",
                    frequency=len(high_prominence),
                    strength=high_prominence['mean'].mean(),
                    examples=[
                        {
                            'domain': domain,
                            'avg_prominence': row['mean'],
                            'citation_count': row['count']
                        }
                        for domain, row in high_prominence.head(5).iterrows()
                    ],
                    characteristics={
                        'avg_prominence': high_prominence['mean'].mean(),
                        'prominence_consistency': high_prominence['mean'].std()
                    },
                    engines=df['engine'].unique().tolist(),
                    domains=high_prominence.index.tolist(),
                    content_types=df['citation_type'].unique().tolist(),
                    time_range=(df['created_at'].min() if 'created_at' in df else datetime.now(),
                              df['created_at'].max() if 'created_at' in df else datetime.now())
                )
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_content_type_patterns(self, df: pd.DataFrame) -> List[CitationPattern]:
        """Analyze patterns based on content types."""
        patterns = []
        
        if 'citation_type' not in df.columns:
            return patterns
        
        # Citation type performance
        type_stats = df.groupby('citation_type').agg({
            'prominence_score': ['mean', 'std', 'count'] if 'prominence_score' in df else lambda x: len(x),
            'position': ['mean', 'std'] if 'position' in df else lambda x: 0
        }).round(3)
        
        # Identify high-performing content types
        if 'prominence_score' in df.columns:
            high_performing_types = type_stats[
                (type_stats[('prominence_score', 'mean')] >= 0.6) &
                (type_stats[('prominence_score', 'count')] >= 3)
            ]
            
            if len(high_performing_types) > 0:
                pattern = CitationPattern(
                    pattern_id=f"high_performing_types_{datetime.now().strftime('%Y%m%d')}",
                    pattern_type="content_type_performance",
                    description="Content types with high average prominence scores",
                    frequency=int(high_performing_types[('prominence_score', 'count')].sum()),
                    strength=high_performing_types[('prominence_score', 'mean')].mean(),
                    examples=[
                        {
                            'content_type': content_type,
                            'avg_prominence': row[('prominence_score', 'mean')],
                            'count': row[('prominence_score', 'count')]
                        }
                        for content_type, row in high_performing_types.iterrows()
                    ],
                    characteristics={
                        'type_distribution': df['citation_type'].value_counts().to_dict(),
                        'avg_prominence_by_type': type_stats[('prominence_score', 'mean')].to_dict() if 'prominence_score' in df else {}
                    },
                    engines=df['engine'].unique().tolist(),
                    domains=df['source_domain'].unique().tolist() if 'source_domain' in df else [],
                    content_types=high_performing_types.index.tolist(),
                    time_range=(df['created_at'].min() if 'created_at' in df else datetime.now(),
                              df['created_at'].max() if 'created_at' in df else datetime.now())
                )
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_position_patterns(self, df: pd.DataFrame) -> List[CitationPattern]:
        """Analyze citation position patterns."""
        patterns = []
        
        if 'position' not in df.columns:
            return patterns
        
        # Top position analysis
        top_positions = df[df['position'] <= 3]
        if len(top_positions) >= self.min_pattern_frequency:
            position_stats = top_positions.groupby(['source_domain', 'citation_type']).agg({
                'position': ['mean', 'count'],
                'prominence_score': 'mean' if 'prominence_score' in df else lambda x: 0
            })
            
            # Find consistently top-performing combinations
            consistent_top = position_stats[position_stats[('position', 'count')] >= 2]
            
            if len(consistent_top) > 0:
                pattern = CitationPattern(
                    pattern_id=f"top_position_pattern_{datetime.now().strftime('%Y%m%d')}",
                    pattern_type="position_consistency",
                    description="Domain-content type combinations consistently ranking in top 3 positions",
                    frequency=int(consistent_top[('position', 'count')].sum()),
                    strength=1.0 - (consistent_top[('position', 'mean')].mean() / 10),  # Lower position = higher strength
                    examples=[
                        {
                            'domain': idx[0],
                            'content_type': idx[1],
                            'avg_position': row[('position', 'mean')],
                            'occurrences': row[('position', 'count')]
                        }
                        for idx, row in consistent_top.head(5).iterrows()
                    ],
                    characteristics={
                        'avg_top_position': top_positions['position'].mean(),
                        'top_position_distribution': top_positions['position'].value_counts().to_dict()
                    },
                    engines=df['engine'].unique().tolist(),
                    domains=df['source_domain'].unique().tolist() if 'source_domain' in df else [],
                    content_types=df['citation_type'].unique().tolist(),
                    time_range=(df['created_at'].min() if 'created_at' in df else datetime.now(),
                              df['created_at'].max() if 'created_at' in df else datetime.now())
                )
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_temporal_patterns(self, df: pd.DataFrame) -> List[CitationPattern]:
        """Analyze temporal citation patterns."""
        patterns = []
        
        if 'created_at' not in df.columns:
            return patterns
        
        # Convert to datetime if needed
        if not pd.api.types.is_datetime64_any_dtype(df['created_at']):
            df['created_at'] = pd.to_datetime(df['created_at'])
        
        # Add time-based features
        df['hour'] = df['created_at'].dt.hour
        df['day_of_week'] = df['created_at'].dt.day_name()
        df['date'] = df['created_at'].dt.date
        
        # Daily citation patterns
        daily_counts = df.groupby('date').size()
        if len(daily_counts) >= 7:  # At least a week of data
            avg_daily = daily_counts.mean()
            high_activity_days = daily_counts[daily_counts > avg_daily * 1.5]
            
            if len(high_activity_days) >= 2:
                pattern = CitationPattern(
                    pattern_id=f"high_activity_days_{datetime.now().strftime('%Y%m%d')}",
                    pattern_type="temporal_spikes",
                    description="Days with significantly higher citation activity",
                    frequency=len(high_activity_days),
                    strength=min(1.0, len(high_activity_days) / len(daily_counts)),
                    examples=[
                        {'date': str(date), 'citation_count': count}
                        for date, count in high_activity_days.head(5).items()
                    ],
                    characteristics={
                        'avg_daily_citations': avg_daily,
                        'peak_daily_citations': daily_counts.max(),
                        'citation_volatility': daily_counts.std() / avg_daily
                    },
                    engines=df['engine'].unique().tolist(),
                    domains=df['source_domain'].unique().tolist() if 'source_domain' in df else [],
                    content_types=df['citation_type'].unique().tolist(),
                    time_range=(df['created_at'].min(), df['created_at'].max())
                )
                patterns.append(pattern)
        
        # Weekly patterns
        weekly_patterns = df.groupby('day_of_week').size()
        if len(weekly_patterns) > 0:
            max_day = weekly_patterns.idxmax()
            min_day = weekly_patterns.idxmin()
            
            if weekly_patterns.max() / weekly_patterns.min() > 1.5:  # Significant variation
                pattern = CitationPattern(
                    pattern_id=f"weekly_pattern_{datetime.now().strftime('%Y%m%d')}",
                    pattern_type="weekly_variation",
                    description=f"Strong weekly pattern: peak on {max_day}, low on {min_day}",
                    frequency=len(df),
                    strength=min(1.0, (weekly_patterns.max() - weekly_patterns.min()) / weekly_patterns.mean()),
                    examples=[
                        {'day': day, 'citation_count': count}
                        for day, count in weekly_patterns.items()
                    ],
                    characteristics={
                        'peak_day': max_day,
                        'low_day': min_day,
                        'weekly_variation_coefficient': weekly_patterns.std() / weekly_patterns.mean()
                    },
                    engines=df['engine'].unique().tolist(),
                    domains=df['source_domain'].unique().tolist() if 'source_domain' in df else [],
                    content_types=df['citation_type'].unique().tolist(),
                    time_range=(df['created_at'].min(), df['created_at'].max())
                )
                patterns.append(pattern)
        
        return patterns
    
    def _analyze_engine_patterns(self, df: pd.DataFrame) -> List[CitationPattern]:
        """Analyze engine-specific citation patterns."""
        patterns = []
        
        if 'engine' not in df.columns:
            return patterns
        
        # Engine performance comparison
        engine_stats = df.groupby('engine').agg({
            'prominence_score': ['mean', 'std', 'count'] if 'prominence_score' in df else lambda x: len(x),
            'position': ['mean', 'std'] if 'position' in df else lambda x: 0,
            'source_domain': lambda x: x.nunique() if 'source_domain' in df else 0
        })
        
        # Find engines with distinct patterns
        if 'prominence_score' in df.columns:
            engine_diversity = df.groupby('engine')['source_domain'].nunique() if 'source_domain' in df else pd.Series()
            
            for engine in df['engine'].unique():
                engine_data = df[df['engine'] == engine]
                
                # Check for engine-specific preferences
                if 'citation_type' in df.columns:
                    type_prefs = engine_data['citation_type'].value_counts()
                    dominant_type = type_prefs.idxmax()
                    
                    if type_prefs.iloc[0] / len(engine_data) > 0.6:  # >60% of one type
                        pattern = CitationPattern(
                            pattern_id=f"engine_preference_{engine}_{datetime.now().strftime('%Y%m%d')}",
                            pattern_type="engine_content_preference",
                            description=f"{engine} shows strong preference for {dominant_type} citations",
                            frequency=type_prefs.iloc[0],
                            strength=type_prefs.iloc[0] / len(engine_data),
                            examples=[
                                {'content_type': ctype, 'count': count}
                                for ctype, count in type_prefs.head(3).items()
                            ],
                            characteristics={
                                'dominant_type': dominant_type,
                                'preference_strength': type_prefs.iloc[0] / len(engine_data),
                                'type_diversity': len(type_prefs)
                            },
                            engines=[engine],
                            domains=engine_data['source_domain'].unique().tolist() if 'source_domain' in df else [],
                            content_types=[dominant_type],
                            time_range=(df['created_at'].min() if 'created_at' in df else datetime.now(),
                                      df['created_at'].max() if 'created_at' in df else datetime.now())
                        )
                        patterns.append(pattern)
        
        return patterns
    
    def _analyze_content_feature_patterns(self, df: pd.DataFrame) -> List[CitationPattern]:
        """Analyze patterns based on content features."""
        patterns = []
        
        # This would require parsed content data
        # For now, we'll analyze based on available metadata
        
        if 'metadata' not in df.columns:
            return patterns
        
        # Analyze metadata patterns
        metadata_features = []
        for _, row in df.iterrows():
            if isinstance(row['metadata'], dict):
                metadata_features.append(row['metadata'])
        
        if not metadata_features:
            return patterns
        
        # Find common metadata patterns
        feature_counts = defaultdict(int)
        for metadata in metadata_features:
            for key, value in metadata.items():
                if isinstance(value, (str, int, float, bool)):
                    feature_counts[f"{key}:{value}"] += 1
        
        # Identify frequent patterns
        frequent_features = {k: v for k, v in feature_counts.items() if v >= self.min_pattern_frequency}
        
        if frequent_features:
            pattern = CitationPattern(
                pattern_id=f"metadata_patterns_{datetime.now().strftime('%Y%m%d')}",
                pattern_type="content_features",
                description="Common content features in cited content",
                frequency=sum(frequent_features.values()),
                strength=len(frequent_features) / max(len(feature_counts), 1),
                examples=[
                    {'feature': feature, 'frequency': freq}
                    for feature, freq in sorted(frequent_features.items(), key=lambda x: x[1], reverse=True)[:10]
                ],
                characteristics={
                    'total_unique_features': len(feature_counts),
                    'frequent_features_count': len(frequent_features)
                },
                engines=df['engine'].unique().tolist(),
                domains=df['source_domain'].unique().tolist() if 'source_domain' in df else [],
                content_types=df['citation_type'].unique().tolist(),
                time_range=(df['created_at'].min() if 'created_at' in df else datetime.now(),
                          df['created_at'].max() if 'created_at' in df else datetime.now())
            )
            patterns.append(pattern)
        
        return patterns
    
    def _analyze_query_similarity_patterns(self, df: pd.DataFrame) -> List[CitationPattern]:
        """Analyze patterns based on query similarities."""
        patterns = []
        
        if 'query' not in df.columns or len(df) < 10:
            return patterns
        
        try:
            # Vectorize queries
            vectorizer = TfidfVectorizer(max_features=100, stop_words='english', ngram_range=(1, 2))
            query_vectors = vectorizer.fit_transform(df['query'].fillna(''))
            
            # Cluster similar queries
            n_clusters = min(5, len(df) // 3)  # Reasonable number of clusters
            if n_clusters >= 2:
                kmeans = KMeans(n_clusters=n_clusters, random_state=42)
                clusters = kmeans.fit_predict(query_vectors)
                
                df['query_cluster'] = clusters
                
                # Analyze each cluster
                for cluster_id in range(n_clusters):
                    cluster_data = df[df['query_cluster'] == cluster_id]
                    
                    if len(cluster_data) >= self.min_pattern_frequency:
                        # Find representative queries
                        sample_queries = cluster_data['query'].head(5).tolist()
                        
                        # Analyze citation patterns within cluster
                        if 'source_domain' in df.columns:
                            common_domains = cluster_data['source_domain'].value_counts().head(3)
                            
                            pattern = CitationPattern(
                                pattern_id=f"query_cluster_{cluster_id}_{datetime.now().strftime('%Y%m%d')}",
                                pattern_type="query_similarity",
                                description=f"Similar queries (cluster {cluster_id}) with common citation patterns",
                                frequency=len(cluster_data),
                                strength=len(cluster_data) / len(df),
                                examples=[
                                    {'query': query, 'citations': len(cluster_data[cluster_data['query'] == query])}
                                    for query in sample_queries
                                ],
                                characteristics={
                                    'cluster_size': len(cluster_data),
                                    'common_domains': common_domains.to_dict(),
                                    'avg_prominence': cluster_data['prominence_score'].mean() if 'prominence_score' in df else 0
                                },
                                engines=cluster_data['engine'].unique().tolist(),
                                domains=common_domains.index.tolist() if len(common_domains) > 0 else [],
                                content_types=cluster_data['citation_type'].unique().tolist(),
                                time_range=(df['created_at'].min() if 'created_at' in df else datetime.now(),
                                          df['created_at'].max() if 'created_at' in df else datetime.now())
                            )
                            patterns.append(pattern)
            
        except Exception as e:
            logger.error(f"Error in query similarity analysis: {str(e)}")
        
        return patterns
    
    def analyze_competitor_patterns(self, citations: List[Dict[str, Any]], competitor_domains: List[str]) -> List[CompetitorPattern]:
        """
        Analyze citation patterns for competitor domains.
        
        Args:
            citations: List of citation dictionaries
            competitor_domains: List of competitor domains to analyze
            
        Returns:
            List of competitor pattern analyses
        """
        if not citations or not competitor_domains:
            return []
        
        df = pd.DataFrame(citations)
        competitor_patterns = []
        
        for domain in competitor_domains:
            if 'source_domain' not in df.columns:
                continue
                
            domain_citations = df[df['source_domain'] == domain.lower()]
            
            if len(domain_citations) == 0:
                continue
            
            # Calculate citation frequency (citations per day)
            if 'created_at' in df.columns:
                date_range = (df['created_at'].max() - df['created_at'].min()).days
                citation_frequency = len(domain_citations) / max(1, date_range)
            else:
                citation_frequency = len(domain_citations)
            
            # Preferred content types
            if 'citation_type' in df.columns:
                content_type_counts = domain_citations['citation_type'].value_counts()
                preferred_types = content_type_counts.head(3).index.tolist()
            else:
                preferred_types = []
            
            # Strong topics (from queries)
            if 'query' in df.columns:
                queries = domain_citations['query'].tolist()
                # Simple topic extraction from queries
                all_words = ' '.join(queries).lower().split()
                word_counts = Counter(all_words)
                common_words = [word for word, count in word_counts.most_common(10) 
                              if len(word) > 3 and word not in {'what', 'how', 'why', 'when', 'where', 'who', 'which'}]
                strong_topics = common_words[:5]
            else:
                strong_topics = []
            
            # Citation timing patterns
            timing_patterns = {}
            if 'created_at' in df.columns:
                domain_citations_with_time = domain_citations.copy()
                domain_citations_with_time['hour'] = pd.to_datetime(domain_citations_with_time['created_at']).dt.hour
                domain_citations_with_time['day_of_week'] = pd.to_datetime(domain_citations_with_time['created_at']).dt.day_name()
                
                hourly_dist = domain_citations_with_time['hour'].value_counts().to_dict()
                daily_dist = domain_citations_with_time['day_of_week'].value_counts().to_dict()
                
                timing_patterns = {
                    'hourly_distribution': hourly_dist,
                    'daily_distribution': daily_dist
                }
            
            # Average position
            avg_position = domain_citations['position'].mean() if 'position' in df.columns else 0
            
            # Engine dominance
            engines_dominance = {}
            if 'engine' in df.columns:
                engine_counts = domain_citations['engine'].value_counts()
                total_citations = len(domain_citations)
                engines_dominance = {
                    engine: count / total_citations
                    for engine, count in engine_counts.items()
                }
            
            competitor_pattern = CompetitorPattern(
                competitor_domain=domain,
                citation_frequency=citation_frequency,
                preferred_content_types=preferred_types,
                strong_topics=strong_topics,
                citation_timing_patterns=timing_patterns,
                average_position=avg_position,
                engines_dominance=engines_dominance
            )
            
            competitor_patterns.append(competitor_pattern)
        
        logger.info(f"Analyzed patterns for {len(competitor_patterns)} competitors")
        return competitor_patterns
    
    def generate_pattern_insights(self, patterns: List[CitationPattern]) -> Dict[str, Any]:
        """
        Generate actionable insights from identified patterns.
        
        Args:
            patterns: List of citation patterns
            
        Returns:
            Dictionary with insights and recommendations
        """
        insights = {
            'total_patterns': len(patterns),
            'pattern_types': Counter([p.pattern_type for p in patterns]),
            'high_strength_patterns': [p for p in patterns if p.strength >= 0.8],
            'recommendations': [],
            'opportunities': [],
            'threats': []
        }
        
        # Generate recommendations based on patterns
        for pattern in patterns:
            if pattern.pattern_type == "domain_frequency" and pattern.strength >= 0.7:
                insights['recommendations'].append({
                    'type': 'content_partnership',
                    'description': f"Consider partnerships or guest content with high-frequency domains: {', '.join(pattern.domains[:3])}",
                    'priority': 'high' if pattern.strength >= 0.8 else 'medium'
                })
            
            elif pattern.pattern_type == "content_type_performance" and pattern.strength >= 0.7:
                best_types = [ex['content_type'] for ex in pattern.examples[:2]]
                insights['opportunities'].append({
                    'type': 'content_optimization',
                    'description': f"Focus on creating {' and '.join(best_types)} content types for better citation potential",
                    'priority': 'high'
                })
            
            elif pattern.pattern_type == "engine_content_preference":
                engine = pattern.engines[0] if pattern.engines else 'unknown'
                content_type = pattern.content_types[0] if pattern.content_types else 'unknown'
                insights['opportunities'].append({
                    'type': 'engine_optimization',
                    'description': f"Optimize content for {engine} by focusing on {content_type} format",
                    'priority': 'medium'
                })
            
            elif pattern.pattern_type == "temporal_spikes" and pattern.strength >= 0.6:
                insights['opportunities'].append({
                    'type': 'timing_optimization',
                    'description': f"Schedule content publication during high-activity periods identified in pattern",
                    'priority': 'medium'
                })
        
        # Identify threats (competitor dominance)
        domain_patterns = [p for p in patterns if p.pattern_type == "domain_frequency"]
        if domain_patterns:
            for pattern in domain_patterns:
                if pattern.strength >= 0.8:
                    insights['threats'].append({
                        'type': 'competitor_dominance',
                        'description': f"High competitor dominance in citation space: {', '.join(pattern.domains[:3])}",
                        'priority': 'high'
                    })
        
        return insights