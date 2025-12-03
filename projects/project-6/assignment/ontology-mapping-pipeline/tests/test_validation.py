"""
Tests for the validation module.
"""

import sys
from pathlib import Path

# Ensure project root is in path for tests
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pytest
from rdflib import Graph, Namespace, URIRef, Literal
from rdflib.namespace import RDF, RDFS, OWL, SKOS

from src.validation.pipeline_validator import (
    PipelineValidator,
    ValidationReport,
    ValidationSeverity,
)
from src.sparql.error_detector import ErrorDetector, run_qc_checks
from src.shacl.validator import SHACLValidator, validate_mappings


class TestPipelineValidator:
    """Tests for PipelineValidator class."""
    
    def test_create_validator(self):
        """Test creating a validator with default settings."""
        validator = PipelineValidator()
        
        assert validator.run_reasoner is True
        assert validator.run_shacl is True
        assert validator.run_sparql is True
    
    def test_create_validator_custom_settings(self):
        """Test creating a validator with custom settings."""
        validator = PipelineValidator(
            run_reasoner=False,
            run_shacl=False,
            fail_on_inconsistency=False,
        )
        
        assert validator.run_reasoner is False
        assert validator.fail_on_inconsistency is False


class TestErrorDetector:
    """Tests for SPARQL QC error detection."""
    
    def test_detector_has_queries(self):
        """Test that detector has default queries."""
        detector = ErrorDetector()
        
        assert "circular_mappings" in detector.queries
        assert "reflexive_mappings" in detector.queries
        assert "conflicting_predicates" in detector.queries
    
    def test_detect_circular_mappings(self):
        """Test detection of circular mappings."""
        g = Graph()
        EX = Namespace("http://example.org/")
        g.bind("ex", EX)
        
        # Add circular mapping
        g.add((EX.A, OWL.equivalentClass, EX.B))
        g.add((EX.B, OWL.equivalentClass, EX.A))
        
        detector = ErrorDetector()
        error = detector.run_query(g, "circular_mappings")
        
        assert error.severity == "error"
        assert len(error.results) > 0
    
    def test_detect_reflexive_mappings(self):
        """Test detection of reflexive mappings."""
        g = Graph()
        EX = Namespace("http://example.org/")
        g.bind("ex", EX)
        
        # Add reflexive mapping
        g.add((EX.A, SKOS.exactMatch, EX.A))
        
        detector = ErrorDetector()
        error = detector.run_query(g, "reflexive_mappings")
        
        assert error.severity == "warning"
        assert len(error.results) > 0
    
    def test_no_errors_clean_graph(self):
        """Test that clean graph has no errors."""
        g = Graph()
        EX = Namespace("http://example.org/")
        TGT = Namespace("http://target.org/")
        g.bind("ex", EX)
        g.bind("tgt", TGT)
        
        # Add clean mappings
        g.add((EX.A, SKOS.exactMatch, TGT.B))
        g.add((EX.C, SKOS.closeMatch, TGT.D))
        
        detector = ErrorDetector()
        errors = detector.run_all_checks(g)
        
        # Should have no results for these simple mappings
        error_count = sum(len(e.results) for e in errors if e.severity == "error")
        assert error_count == 0


class TestSHACLValidator:
    """Tests for SHACL validation."""
    
    def test_validate_clean_mappings(self, sample_mapping_graph):
        """Test SHACL validation on clean mappings."""
        result = validate_mappings(sample_mapping_graph, use_defaults=True)
        
        # Default shapes should pass for valid IRIs
        assert result.conforms is True
    
    def test_load_shapes_from_string(self):
        """Test loading SHACL shapes from string."""
        validator = SHACLValidator()
        
        shapes = """
        @prefix sh: <http://www.w3.org/ns/shacl#> .
        @prefix ex: <http://example.org/> .
        
        ex:TestShape a sh:NodeShape ;
            sh:targetClass ex:Thing ;
            sh:property [
                sh:path ex:name ;
                sh:minCount 1 ;
            ] .
        """
        
        validator.load_shapes_from_string(shapes)
        
        # Shapes should be loaded
        assert len(validator.shapes_graph) > 0


class TestValidationReport:
    """Tests for ValidationReport."""
    
    def test_create_report(self):
        """Test creating a validation report."""
        report = ValidationReport(
            is_valid=True,
            consistency_result=None,
            shacl_result=None,
            sparql_errors=[],
            issues=[],
        )
        
        assert report.is_valid is True
        assert report.error_count == 0
        assert report.warning_count == 0
    
    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        report = ValidationReport(
            is_valid=True,
            issues=[],
        )
        
        result = report.to_dict()
        
        assert "is_valid" in result
        assert "error_count" in result
        assert result["is_valid"] is True

        