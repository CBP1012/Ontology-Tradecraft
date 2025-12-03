"""
Mapping Plausibility Scorer

Scores candidate mappings using multiple signals including LLM confidence.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from src.llm.client import LLMClient, create_llm_client
from src.llm.prompts import SYSTEM_PROMPT, SCORING_PROMPT, format_prompt
from src.llm.parsers import ScoringResponse, parse_scoring_response
from src.mapping.candidate_generator import MappingCandidate


@dataclass
class ScoredMapping:
    """A mapping with detailed scoring."""
    candidate: MappingCandidate
    lexical_score: float
    semantic_score: float
    structural_score: float
    llm_score: float
    combined_score: float
    recommended_predicate: Optional[str]
    reasoning: str


class MappingScorer:
    """
    Scores mapping candidates using multiple signals.
    """
    
    DEFAULT_WEIGHTS = {
        "lexical": 0.2,
        "semantic": 0.3,
        "structural": 0.2,
        "llm": 0.3,
    }
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        weights: Optional[dict[str, float]] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize the scorer.
        
        Args:
            llm_client: Optional LLM client
            weights: Custom scoring weights
            embedding_model: Model for semantic similarity
        """
        self.llm = llm_client or create_llm_client()
        self.weights = weights or self.DEFAULT_WEIGHTS
        self.embedding_model = embedding_model
        self._embedder = None
    
    def _get_embedder(self):
        """Lazy load the sentence transformer."""
        if self._embedder is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedder = SentenceTransformer(self.embedding_model)
            except ImportError:
                print("Warning: sentence-transformers not available")
                return None
        return self._embedder
    
    async def score_candidates(
        self,
        candidates: list[MappingCandidate],
        source_definitions: dict[str, str],
        target_definitions: dict[str, str],
    ) -> list[ScoredMapping]:
        """
        Score a list of mapping candidates.
        
        Args:
            candidates: List of candidates to score
            source_definitions: Dict of source IRI -> definition
            target_definitions: Dict of target IRI -> definition
            
        Returns:
            List of scored mappings
        """
        tasks = [
            self._score_candidate(c, source_definitions, target_definitions)
            for c in candidates
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        scored = []
        for candidate, result in zip(candidates, results):
            if isinstance(result, Exception):
                print(f"Error scoring {candidate.source_iri}: {result}")
                continue
            scored.append(result)
        
        # Sort by combined score
        scored.sort(key=lambda x: x.combined_score, reverse=True)
        
        return scored
    
    async def _score_candidate(
        self,
        candidate: MappingCandidate,
        source_definitions: dict[str, str],
        target_definitions: dict[str, str],
    ) -> ScoredMapping:
        """Score a single candidate."""
        source_def = source_definitions.get(candidate.source_iri, "")
        target_def = target_definitions.get(candidate.target_iri, "")
        
        # Calculate lexical similarity
        lexical_score = self._lexical_similarity(
            candidate.source_label, candidate.target_label
        )
        
        # Calculate semantic similarity using embeddings
        semantic_score = await self._semantic_similarity(source_def, target_def)
        
        # Get LLM-based scoring
        llm_response = await self._llm_score(candidate, source_def, target_def)
        
        # Use LLM's structural and overall assessment
        structural_score = llm_response.scores.structural
        llm_score = llm_response.overall_score
        
        # Calculate combined score
        combined_score = (
            self.weights["lexical"] * lexical_score +
            self.weights["semantic"] * semantic_score +
            self.weights["structural"] * structural_score +
            self.weights["llm"] * llm_score
        )
        
        return ScoredMapping(
            candidate=candidate,
            lexical_score=lexical_score,
            semantic_score=semantic_score,
            structural_score=structural_score,
            llm_score=llm_score,
            combined_score=combined_score,
            recommended_predicate=llm_response.recommended_predicate,
            reasoning=llm_response.reasoning,
        )
    
    def _lexical_similarity(self, label1: str, label2: str) -> float:
        """Calculate lexical similarity between labels."""
        # Simple token overlap for now
        tokens1 = set(label1.lower().split())
        tokens2 = set(label2.lower().split())
        
        if not tokens1 or not tokens2:
            return 0.0
        
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        
        return len(intersection) / len(union) if union else 0.0
    
    async def _semantic_similarity(self, text1: str, text2: str) -> float:
        """Calculate semantic similarity using embeddings."""
        if not text1 or not text2:
            return 0.0
        
        embedder = self._get_embedder()
        if embedder is None:
            return 0.5  # Default if embedder not available
        
        try:
            import numpy as np
            
            # Run embedding in thread pool to not block
            loop = asyncio.get_event_loop()
            embeddings = await loop.run_in_executor(
                None,
                lambda: embedder.encode([text1, text2])
            )
            
            # Cosine similarity
            emb1, emb2 = embeddings
            similarity = np.dot(emb1, emb2) / (
                np.linalg.norm(emb1) * np.linalg.norm(emb2)
            )
            
            return float(max(0.0, similarity))
        except Exception:
            return 0.5
    
    async def _llm_score(
        self,
        candidate: MappingCandidate,
        source_def: str,
        target_def: str,
    ) -> ScoringResponse:
        """Get LLM-based scoring."""
        prompt = format_prompt(
            SCORING_PROMPT,
            source_label=candidate.source_label,
            source_iri=candidate.source_iri,
            source_definition=source_def or "No definition",
            target_label=candidate.target_label,
            target_iri=candidate.target_iri,
            target_definition=target_def or "No definition",
            predicate=candidate.predicate,
        )
        
        response = await self.llm.complete_with_system(
            system=SYSTEM_PROMPT,
            user=prompt,
        )
        
        return parse_scoring_response(response.content)


def score_mappings_sync(
    candidates: list[MappingCandidate],
    source_definitions: dict[str, str],
    target_definitions: dict[str, str],
) -> list[ScoredMapping]:
    """Synchronous wrapper for scoring."""
    scorer = MappingScorer()
    return asyncio.run(
        scorer.score_candidates(candidates, source_definitions, target_definitions)
    )
