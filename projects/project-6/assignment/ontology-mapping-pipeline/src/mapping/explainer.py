"""
Mapping Explanation Generator

Generates human-readable explanations and rationales for ontology mappings.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from src.llm.client import LLMClient, create_llm_client
from src.llm.prompts import SYSTEM_PROMPT, EXPLANATION_PROMPT, format_prompt
from src.llm.parsers import MappingExplanation, parse_explanation_response
from src.mapping.candidate_generator import MappingCandidate


@dataclass
class ExplainedMapping:
    """A mapping with its explanation."""
    candidate: MappingCandidate
    summary: str
    evidence: list[str]
    caveats: list[str]
    alternatives_considered: list[tuple[str, str]]  # (concept, reason_rejected)


class ExplanationGenerator:
    """
    Generates human-readable explanations for mappings.
    """
    
    def __init__(self, llm_client: Optional[LLMClient] = None):
        """
        Initialize the explanation generator.
        
        Args:
            llm_client: Optional LLM client
        """
        self.llm = llm_client or create_llm_client()
    
    async def generate_explanations(
        self,
        candidates: list[MappingCandidate],
        source_context: dict[str, dict],
        target_context: dict[str, dict],
        batch_size: int = 10,
    ) -> list[ExplainedMapping]:
        """
        Generate explanations for multiple mappings.
        
        Args:
            candidates: List of mapping candidates
            source_context: Dict of source IRI -> {definition, parents}
            target_context: Dict of target IRI -> {definition, parents}
            batch_size: Concurrent requests
            
        Returns:
            List of explained mappings
        """
        results = []
        
        for i in range(0, len(candidates), batch_size):
            batch = candidates[i:i + batch_size]
            
            tasks = [
                self._generate_explanation(c, source_context, target_context)
                for c in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for candidate, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    print(f"Error explaining {candidate.source_iri}: {result}")
                    # Provide minimal explanation on error
                    results.append(ExplainedMapping(
                        candidate=candidate,
                        summary=f"Mapping from {candidate.source_label} to {candidate.target_label}",
                        evidence=[candidate.justification],
                        caveats=["Explanation generation failed"],
                        alternatives_considered=[],
                    ))
                else:
                    results.append(result)
        
        return results
    
    async def _generate_explanation(
        self,
        candidate: MappingCandidate,
        source_context: dict[str, dict],
        target_context: dict[str, dict],
    ) -> ExplainedMapping:
        """Generate explanation for a single mapping."""
        source_ctx = source_context.get(candidate.source_iri, {})
        target_ctx = target_context.get(candidate.target_iri, {})
        
        prompt = format_prompt(
            EXPLANATION_PROMPT,
            source_label=candidate.source_label,
            source_iri=candidate.source_iri,
            target_label=candidate.target_label,
            target_iri=candidate.target_iri,
            predicate=candidate.predicate,
            confidence=candidate.confidence,
            source_definition=source_ctx.get("definition", "Not available"),
            source_parents=", ".join(source_ctx.get("parents", [])) or "None",
            target_definition=target_ctx.get("definition", "Not available"),
            target_parents=", ".join(target_ctx.get("parents", [])) or "None",
        )
        
        response = await self.llm.complete_with_system(
            system=SYSTEM_PROMPT,
            user=prompt,
        )
        
        parsed = parse_explanation_response(response.content)
        
        return ExplainedMapping(
            candidate=candidate,
            summary=parsed.summary,
            evidence=parsed.evidence,
            caveats=parsed.caveats,
            alternatives_considered=[
                (alt.concept, alt.reason_rejected)
                for alt in parsed.alternatives_considered
            ],
        )
    
    async def generate_single(
        self,
        candidate: MappingCandidate,
        source_definition: str = "",
        source_parents: list[str] = None,
        target_definition: str = "",
        target_parents: list[str] = None,
    ) -> ExplainedMapping:
        """
        Generate explanation for a single mapping.
        
        Args:
            candidate: The mapping candidate
            source_definition: Source concept definition
            source_parents: Source concept parents
            target_definition: Target concept definition
            target_parents: Target concept parents
            
        Returns:
            Explained mapping
        """
        source_context = {
            candidate.source_iri: {
                "definition": source_definition,
                "parents": source_parents or [],
            }
        }
        target_context = {
            candidate.target_iri: {
                "definition": target_definition,
                "parents": target_parents or [],
            }
        }
        
        return await self._generate_explanation(
            candidate, source_context, target_context
        )


def explain_mapping_sync(
    candidate: MappingCandidate,
    **kwargs,
) -> ExplainedMapping:
    """Synchronous wrapper for single explanation."""
    generator = ExplanationGenerator()
    return asyncio.run(generator.generate_single(candidate, **kwargs))
