"""
Candidate Mapping Generator

Uses LLMs to generate candidate mappings between ontologies.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional

from rdflib import Graph

from src.llm.client import LLMClient, create_llm_client
from src.llm.prompts import (
    SYSTEM_PROMPT,
    CANDIDATE_GENERATION_PROMPT,
    format_prompt,
)
from src.llm.parsers import (
    CandidateMapping,
    CandidateGenerationResponse,
    parse_candidate_response,
)
from src.ontology.extractor import ConceptExtractor, OntologyConcept


@dataclass
class MappingCandidate:
    """A candidate mapping with metadata."""
    source_iri: str
    source_label: str
    target_iri: str
    target_label: str
    predicate: str
    confidence: float
    justification: str


class CandidateGenerator:
    """
    Generates candidate mappings using LLM assistance.
    """
    
    # Valid mapping predicates
    VALID_PREDICATES = {
        "owl:equivalentClass",
        "skos:exactMatch",
        "skos:closeMatch",
        "skos:broadMatch",
        "skos:narrowMatch",
        "skos:relatedMatch",
    }
    
    def __init__(
        self,
        llm_client: Optional[LLMClient] = None,
        config_path: str = "configs/llm_config.yaml",
    ):
        """
        Initialize the candidate generator.
        
        Args:
            llm_client: Optional pre-configured LLM client
            config_path: Path to LLM configuration file
        """
        self.llm = llm_client or create_llm_client(config_path)
    
    async def generate_candidates(
        self,
        source_graph: Graph,
        target_graph: Graph,
        min_confidence: float = 0.5,
        batch_size: int = 10,
    ) -> list[MappingCandidate]:
        """
        Generate mapping candidates for all concepts in source ontology.
        
        Args:
            source_graph: Source ontology graph
            target_graph: Target ontology graph
            min_confidence: Minimum confidence threshold
            batch_size: Number of concepts to process in parallel
            
        Returns:
            List of mapping candidates
        """
        # Extract concepts from both ontologies
        source_extractor = ConceptExtractor(source_graph)
        target_extractor = ConceptExtractor(target_graph)
        
        source_concepts = source_extractor.extract_all_concepts()
        target_vocabulary = target_extractor.get_concept_vocabulary(max_concepts=500)
        
        # Process in batches
        all_candidates = []
        
        for i in range(0, len(source_concepts), batch_size):
            batch = source_concepts[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [
                self._generate_for_concept(concept, target_vocabulary)
                for concept in batch
            ]
            
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for concept, result in zip(batch, batch_results):
                if isinstance(result, Exception):
                    print(f"Error processing {concept.iri}: {result}")
                    continue
                
                for candidate in result:
                    if candidate.confidence >= min_confidence:
                        all_candidates.append(candidate)
        
        return all_candidates
    
    async def _generate_for_concept(
        self,
        source_concept: OntologyConcept,
        target_vocabulary: str,
    ) -> list[MappingCandidate]:
        """
        Generate mapping candidates for a single source concept.
        
        Args:
            source_concept: The source concept to map
            target_vocabulary: Formatted target ontology vocabulary
            
        Returns:
            List of candidate mappings
        """
        # Build the prompt
        prompt = format_prompt(
            CANDIDATE_GENERATION_PROMPT,
            source_iri=source_concept.iri,
            source_label=source_concept.primary_label,
            source_definition=source_concept.definition or "No definition available",
            source_synonyms=", ".join(source_concept.synonyms) if source_concept.synonyms else "None",
            source_parents=", ".join(source_concept.parents) if source_concept.parents else "None",
            target_concepts=target_vocabulary,
        )
        
        # Call LLM
        response = await self.llm.complete_with_system(
            system=SYSTEM_PROMPT,
            user=prompt,
        )
        
        # Parse response
        parsed = parse_candidate_response(response.content)
        
        # Convert to MappingCandidate objects
        candidates = []
        for mapping in parsed.mappings:
            if mapping.predicate not in self.VALID_PREDICATES:
                continue
            
            # Extract target label from vocabulary (simplified)
            target_label = self._extract_label_from_iri(mapping.target_iri)
            
            candidates.append(MappingCandidate(
                source_iri=source_concept.iri,
                source_label=source_concept.primary_label,
                target_iri=mapping.target_iri,
                target_label=target_label,
                predicate=mapping.predicate,
                confidence=mapping.confidence,
                justification=mapping.justification,
            ))
        
        return candidates
    
    def _extract_label_from_iri(self, iri: str) -> str:
        """Extract a readable label from an IRI."""
        if "#" in iri:
            return iri.split("#")[-1]
        return iri.split("/")[-1]
    
    async def generate_single(
        self,
        source_concept: OntologyConcept,
        target_graph: Graph,
    ) -> list[MappingCandidate]:
        """
        Generate candidates for a single concept.
        
        Args:
            source_concept: Source concept to map
            target_graph: Target ontology graph
            
        Returns:
            List of candidate mappings
        """
        target_extractor = ConceptExtractor(target_graph)
        target_vocabulary = target_extractor.get_concept_vocabulary(max_concepts=500)
        
        return await self._generate_for_concept(source_concept, target_vocabulary)


def generate_candidates_sync(
    source_graph: Graph,
    target_graph: Graph,
    **kwargs,
) -> list[MappingCandidate]:
    """
    Synchronous wrapper for candidate generation.
    
    Args:
        source_graph: Source ontology graph
        target_graph: Target ontology graph
        **kwargs: Additional arguments for generate_candidates
        
    Returns:
        List of mapping candidates
    """
    generator = CandidateGenerator()
    return asyncio.run(
        generator.generate_candidates(source_graph, target_graph, **kwargs)
    )
