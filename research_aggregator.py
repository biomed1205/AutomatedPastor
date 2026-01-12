"""Enhanced research aggregator for multi-provider research.

Provides parallel research capabilities across multiple AI providers,
with result aggregation, deduplication, and caching.
"""
import json
import hashlib
import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Dict, List, Optional, Any
from collections import defaultdict

from providers.registry import ProviderRegistry
from providers.base import ProviderResult


class ResearchAggregator:
    """Aggregator for executing research across multiple AI providers.

    Supports parallel execution, result aggregation, semantic deduplication,
    and caching of research results.
    """

    def __init__(
        self,
        registry: ProviderRegistry,
        timeout: int = 300,
        max_workers: int = 5,
        use_cache: bool = True
    ):
        """Initialize the research aggregator.

        Args:
            registry: ProviderRegistry instance for accessing AI providers.
            timeout: Timeout in seconds for each provider call (default: 300).
            max_workers: Maximum parallel workers for execution (default: 5).
            use_cache: Whether to cache research results (default: True).
        """
        self.registry = registry
        self.timeout = timeout
        self.max_workers = max_workers
        self.use_cache = use_cache
        self._cache: Dict[str, Any] = {}

    def _get_cache_key(self, topic: str, provider_id: str, research_type: str = "") -> str:
        """Generate a cache key for a research request.

        Args:
            topic: Research topic.
            provider_id: Provider identifier.
            research_type: Type of research (optional).

        Returns:
            String cache key.
        """
        key_data = f"{topic}:{provider_id}:{research_type}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def research_with_provider(
        self,
        topic: str,
        provider_id: str,
        research_type: str = "general",
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute research with a single provider.

        Args:
            topic: The research topic or question.
            provider_id: ID of the provider to use.
            research_type: Type of research (e.g., 'biblical_context', 'illustrations').
            context: Optional additional context for the research.

        Returns:
            Dictionary with research results.
        """
        # Check cache first
        if self.use_cache:
            cache_key = self._get_cache_key(topic, provider_id, research_type)
            if cache_key in self._cache:
                return self._cache[cache_key]

        # Get the provider
        provider = self.registry.get_provider(provider_id)
        if not provider:
            return {
                'provider_id': provider_id,
                'output': '',
                'success': False,
                'error': f'Provider not found: {provider_id}'
            }

        # Build the research prompt
        prompt = build_research_prompt(topic, context, research_type)

        # Execute the research
        try:
            result = provider.run(prompt)

            output = {
                'provider_id': provider_id,
                'output': result.output,
                'success': result.success,
                'model_id': result.model_id,
                'duration': result.duration,
                'tokens_used': result.tokens_used
            }

            if not result.success and result.error:
                output['error'] = result.error

            # Cache successful results
            if self.use_cache and result.success:
                cache_key = self._get_cache_key(topic, provider_id, research_type)
                self._cache[cache_key] = output

            return output

        except Exception as e:
            return {
                'provider_id': provider_id,
                'output': '',
                'success': False,
                'error': str(e)
            }

    def research_with_providers(
        self,
        topic: str,
        provider_ids: List[str],
        research_type: str = "general",
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute research with multiple providers in parallel.

        Args:
            topic: The research topic or question.
            provider_ids: List of provider IDs to query.
            research_type: Type of research.
            context: Optional additional context.

        Returns:
            Dictionary with aggregated results.
        """
        results = []

        with ThreadPoolExecutor(max_workers=min(len(provider_ids), self.max_workers)) as executor:
            futures = {
                executor.submit(
                    self.research_with_provider,
                    topic,
                    provider_id,
                    research_type,
                    context
                ): provider_id
                for provider_id in provider_ids
            }

            for future in as_completed(futures, timeout=self.timeout):
                provider_id = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    results.append({
                        'provider_id': provider_id,
                        'output': '',
                        'success': False,
                        'error': str(e)
                    })

        return aggregate_research_results(results)

    def research_all_providers(
        self,
        topic: str,
        research_type: str = "general",
        context: Optional[Dict] = None
    ) -> Dict[str, Any]:
        """Execute research with all enabled providers.

        Args:
            topic: The research topic or question.
            research_type: Type of research.
            context: Optional additional context.

        Returns:
            Dictionary with aggregated results.
        """
        enabled_providers = self.registry.get_enabled_providers()
        if not enabled_providers:
            return {
                'results': [],
                'provider_sources': {},
                'errors': [{'error': 'No enabled providers found'}]
            }

        provider_ids = [p.provider_id for p in enabled_providers]
        return self.research_with_providers(topic, provider_ids, research_type, context)


def build_research_prompt(
    topic: str,
    context: Optional[Dict] = None,
    research_type: str = "general"
) -> str:
    """Build a research prompt for AI providers.

    Args:
        topic: The research topic or question.
        context: Optional additional context.
        research_type: Type of research to guide the prompt.

    Returns:
        Formatted prompt string.
    """
    # Base prompt structure
    prompt_parts = []

    # Add research type specific instructions
    if research_type == "biblical_context":
        prompt_parts.append(
            "You are a biblical scholar providing research for sermon preparation. "
            "Focus on historical context, original language insights, and scholarly interpretation. "
            "Provide detailed analysis with citations where appropriate."
        )
    elif research_type == "illustrations":
        prompt_parts.append(
            "You are helping find contemporary illustrations for a sermon. "
            "Provide relevant stories, examples, and analogies that illuminate the topic. "
            "Avoid personal anecdotes and focus on universal, relatable illustrations."
        )
    elif research_type == "theological":
        prompt_parts.append(
            "You are a theological researcher with expertise in Wesleyan/Methodist theology. "
            "Provide theological insights and perspectives on the topic, "
            "emphasizing grace, prevenient grace, and the Wesleyan Quadrilateral approach."
        )
    elif research_type == "commentary":
        prompt_parts.append(
            "You are providing commentary research for sermon preparation. "
            "Summarize key insights from major commentators and scholars on the topic."
        )
    else:
        prompt_parts.append(
            "You are a research assistant helping with sermon preparation. "
            "Provide thorough, well-organized research on the following topic."
        )

    # Add the main topic
    prompt_parts.append(f"\nResearch Topic: {topic}")

    # Add context if provided
    if context:
        prompt_parts.append("\nAdditional Context:")
        for key, value in context.items():
            prompt_parts.append(f"- {key}: {value}")

    # Add output format instructions
    prompt_parts.append(
        "\n\nProvide your research findings in a clear, organized format. "
        "Include key insights, supporting evidence, and practical applications for preaching."
    )

    return "\n".join(prompt_parts)


def aggregate_research_results(results: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Aggregate research results from multiple providers.

    Args:
        results: List of result dictionaries from providers.

    Returns:
        Aggregated results with provider sources tracked.
    """
    aggregated = {
        'results': results,
        'provider_sources': {},
        'errors': [],
        'successful_count': 0,
        'failed_count': 0
    }

    combined_insights = []

    for result in results:
        provider_id = result.get('provider_id', 'unknown')

        if result.get('success'):
            aggregated['successful_count'] += 1
            aggregated['provider_sources'][provider_id] = result.get('output', '')

            # Parse output into insights
            if result.get('output'):
                combined_insights.append({
                    'content': result['output'],
                    'provider': provider_id
                })
        else:
            aggregated['failed_count'] += 1
            aggregated['errors'].append({
                'provider_id': provider_id,
                'error': result.get('error', 'Unknown error')
            })

    # Combine insights
    aggregated['insights'] = combined_insights
    aggregated['combined'] = "\n\n---\n\n".join(
        f"[{i['provider']}]\n{i['content']}"
        for i in combined_insights
    )

    return aggregated


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate semantic similarity between two texts.

    Uses a simple word overlap approach for efficiency.
    More sophisticated approaches (embeddings) could be used for better accuracy.

    Args:
        text1: First text string.
        text2: Second text string.

    Returns:
        Similarity score between 0.0 and 1.0.
    """
    if not text1 or not text2:
        return 0.0

    # Normalize texts
    def normalize(text: str) -> set:
        # Convert to lowercase and extract words
        words = re.findall(r'\b\w+\b', text.lower())
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'of', 'at', 'by', 'for', 'with', 'about', 'against',
            'between', 'into', 'through', 'during', 'before', 'after',
            'above', 'below', 'to', 'from', 'up', 'down', 'in', 'out',
            'on', 'off', 'over', 'under', 'again', 'further', 'then',
            'once', 'here', 'there', 'when', 'where', 'why', 'how',
            'all', 'each', 'few', 'more', 'most', 'other', 'some',
            'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
            'than', 'too', 'very', 'just', 'and', 'but', 'if', 'or',
            'because', 'as', 'until', 'while', 'this', 'that', 'these',
            'those', 'it', 'its'
        }
        return set(w for w in words if w not in stop_words and len(w) > 2)

    words1 = normalize(text1)
    words2 = normalize(text2)

    if not words1 or not words2:
        return 0.0

    # Calculate Jaccard similarity
    intersection = len(words1 & words2)
    union = len(words1 | words2)

    if union == 0:
        return 0.0

    return intersection / union


def deduplicate_findings(findings: List[Dict[str, Any]], threshold: float = 0.5) -> Dict[str, Any]:
    """Deduplicate similar findings from multiple providers.

    Groups similar findings together and identifies consensus.

    Args:
        findings: List of finding dictionaries with 'content' and 'provider' keys.
        threshold: Similarity threshold for grouping (default: 0.5).

    Returns:
        Dictionary with grouped and unique findings.
    """
    if not findings:
        return {'groups': [], 'unique': [], 'consensus': []}

    # Group similar findings
    groups: List[List[Dict]] = []
    used = set()

    for i, finding1 in enumerate(findings):
        if i in used:
            continue

        group = [finding1]
        used.add(i)

        for j, finding2 in enumerate(findings):
            if j in used or j <= i:
                continue

            similarity = calculate_similarity(
                finding1.get('content', ''),
                finding2.get('content', '')
            )

            if similarity >= threshold:
                group.append(finding2)
                used.add(j)

        groups.append(group)

    # Classify groups
    unique = []
    consensus = []

    for group in groups:
        providers = set(f.get('provider', 'unknown') for f in group)
        group_data = {
            'findings': group,
            'providers': list(providers),
            'agreement_count': len(group),
            'representative': group[0].get('content', '')
        }

        if len(providers) >= 2:
            # Multiple providers agree - this is consensus
            consensus.append(group_data)
        else:
            # Unique insight from one provider
            unique.append(group_data)

    return {
        'groups': groups,
        'unique': unique,
        'consensus': consensus
    }


def store_research_for_sermon(
    conn,
    sermon_id: int,
    research_data: Dict[str, Any]
) -> bool:
    """Store research results for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.
        research_data: Research data to store.

    Returns:
        True if successful, False otherwise.
    """
    try:
        cursor = conn.cursor()
        research_json = json.dumps(research_data)

        cursor.execute(
            "UPDATE sermons SET research_data = ? WHERE id = ?",
            (research_json, sermon_id)
        )
        conn.commit()
        return True

    except Exception as e:
        return False


def get_research_for_sermon(conn, sermon_id: int) -> Optional[Dict[str, Any]]:
    """Retrieve stored research results for a sermon.

    Args:
        conn: Database connection.
        sermon_id: ID of the sermon.

    Returns:
        Research data dictionary or None if not found.
    """
    try:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT research_data FROM sermons WHERE id = ?",
            (sermon_id,)
        )
        row = cursor.fetchone()

        if row and row['research_data']:
            return json.loads(row['research_data'])

        return None

    except Exception as e:
        return None
