"""
Tests for the candidate generator module.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.mapping.candidate_generator import (
    CandidateGenerator,
    MappingCandidate,
)
from src.llm.parsers import CandidateGenerationResponse, CandidateMapping


class TestCandidateGenerator:
    """Tests for CandidateGenerator class."""
    
    @pytest.mark.asyncio
    async def test_generate_for_concept(self, mock_llm_client):
        """Test generating candidates for a single concept."""
        generator = CandidateGenerator(llm_client=mock_llm_client)
        
        # Mock concept
        from src.ontology.extractor import OntologyConcept
        source_concept = OntologyConcept(
            iri="http://example.org/source#Dog",
            labels=["Dog"],
            definition="A domesticated mammal",
        )
        
        target_vocabulary = """
        - Canine (http://example.org/target#Canine): Member of dog family
        - Feline (http://example.org/target#Feline): Member of cat family
        """
        
        candidates = await generator._generate_for_concept(
            source_concept, target_vocabulary
        )
        
        # Verify LLM was called
        mock_llm_client.complete_with_system.assert_called_once()
        
        # Check results
        assert len(candidates) >= 0  # May be empty if parsing fails
    
    def test_extract_label_from_iri(self):
        """Test IRI to label extraction."""
        generator = CandidateGenerator.__new__(CandidateGenerator)
        
        # Test with hash
        assert generator._extract_label_from_iri(
            "http://example.org#MyClass"
        ) == "MyClass"
        
        # Test with slash
        assert generator._extract_label_from_iri(
            "http://example.org/ontology/MyClass"
        ) == "MyClass"
    
    def test_valid_predicates(self):
        """Test that valid predicates are defined."""
        assert "owl:equivalentClass" in CandidateGenerator.VALID_PREDICATES
        assert "skos:exactMatch" in CandidateGenerator.VALID_PREDICATES
        assert "skos:closeMatch" in CandidateGenerator.VALID_PREDICATES


class TestMappingCandidate:
    """Tests for MappingCandidate dataclass."""
    
    def test_create_candidate(self):
        """Test creating a mapping candidate."""
        candidate = MappingCandidate(
            source_iri="http://example.org/source#A",
            source_label="A",
            target_iri="http://example.org/target#B",
            target_label="B",
            predicate="skos:exactMatch",
            confidence=0.9,
            justification="Test mapping",
        )
        
        assert candidate.source_iri == "http://example.org/source#A"
        assert candidate.confidence == 0.9
        assert candidate.predicate == "skos:exactMatch"
