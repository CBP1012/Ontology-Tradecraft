"""
Pytest Configuration and Fixtures
"""

import sys
from pathlib import Path

# Ensure project root is in path for tests
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from unittest.mock import AsyncMock, MagicMock

from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, SKOS


@pytest.fixture
def sample_source_ontology() -> Graph:
    """Create a sample source ontology for testing."""
    g = Graph()
    
    # Define namespace
    EX = Namespace("http://example.org/source#")
    g.bind("ex", EX)
    
    # Add some classes
    g.add((EX.Animal, RDF.type, OWL.Class))
    g.add((EX.Animal, RDFS.label, Literal("Animal")))
    g.add((EX.Animal, RDFS.comment, Literal("A living organism that feeds on organic matter")))
    
    g.add((EX.Dog, RDF.type, OWL.Class))
    g.add((EX.Dog, RDFS.label, Literal("Dog")))
    g.add((EX.Dog, RDFS.subClassOf, EX.Animal))
    g.add((EX.Dog, RDFS.comment, Literal("A domesticated carnivorous mammal")))
    
    g.add((EX.Cat, RDF.type, OWL.Class))
    g.add((EX.Cat, RDFS.label, Literal("Cat")))
    g.add((EX.Cat, RDFS.subClassOf, EX.Animal))
    
    return g


@pytest.fixture
def sample_target_ontology() -> Graph:
    """Create a sample target ontology for testing."""
    g = Graph()
    
    # Define namespace
    TGT = Namespace("http://example.org/target#")
    g.bind("tgt", TGT)
    
    # Add some classes
    g.add((TGT.Organism, RDF.type, OWL.Class))
    g.add((TGT.Organism, RDFS.label, Literal("Organism")))
    g.add((TGT.Organism, RDFS.comment, Literal("A living entity")))
    
    g.add((TGT.Canine, RDF.type, OWL.Class))
    g.add((TGT.Canine, RDFS.label, Literal("Canine")))
    g.add((TGT.Canine, RDFS.subClassOf, TGT.Organism))
    g.add((TGT.Canine, RDFS.comment, Literal("Member of the dog family")))
    
    g.add((TGT.Feline, RDF.type, OWL.Class))
    g.add((TGT.Feline, RDFS.label, Literal("Feline")))
    g.add((TGT.Feline, RDFS.subClassOf, TGT.Organism))
    
    return g


@pytest.fixture
def sample_mapping_graph() -> Graph:
    """Create a sample mapping graph for testing."""
    g = Graph()
    
    EX = Namespace("http://example.org/source#")
    TGT = Namespace("http://example.org/target#")
    
    g.bind("ex", EX)
    g.bind("tgt", TGT)
    
    # Add some mappings
    g.add((EX.Animal, OWL.equivalentClass, TGT.Organism))
    g.add((EX.Dog, SKOS.exactMatch, TGT.Canine))
    g.add((EX.Cat, SKOS.closeMatch, TGT.Feline))
    
    return g


@pytest.fixture
def mock_llm_client():
    """Create a mock LLM client for testing."""
    mock = AsyncMock()
    
    # Default response for candidate generation
    mock.complete_with_system.return_value = MagicMock(
        content="""
        {
            "mappings": [
                {
                    "target_iri": "http://example.org/target#Canine",
                    "predicate": "skos:exactMatch",
                    "confidence": 0.95,
                    "justification": "Both refer to dogs"
                }
            ],
            "no_match_reason": null
        }
        """
    )
    
    return mock


@pytest.fixture
def temp_ontology_file(tmp_path, sample_source_ontology) -> Path:
    """Create a temporary ontology file."""
    file_path = tmp_path / "source.owl"
    sample_source_ontology.serialize(str(file_path), format="xml")
    return file_path


@pytest.fixture
def temp_output_dir(tmp_path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


# Markers for different test types
def pytest_configure(config):
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
    