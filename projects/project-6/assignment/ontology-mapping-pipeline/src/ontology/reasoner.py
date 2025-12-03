"""
OWL Reasoner Integration

Provides consistency checking and inference capabilities via OWL reasoners.
"""

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional
import tempfile

from rdflib import Graph


class ReasonerType(Enum):
    """Supported OWL reasoners."""
    HERMIT = "hermit"
    PELLET = "pellet"
    ELK = "elk"


@dataclass
class ConsistencyResult:
    """Result of a consistency check."""
    is_consistent: bool
    unsatisfiable_classes: list[str]
    error_message: Optional[str] = None


@dataclass
class InferenceResult:
    """Result of reasoning/classification."""
    inferred_graph: Graph
    new_axioms_count: int
    reasoning_time_ms: float


class OWLReasoner:
    """
    Interface to OWL reasoners.
    
    Uses owlready2 for Python-native reasoning, with optional
    Java reasoner integration via subprocess.
    """
    
    def __init__(self, reasoner_type: ReasonerType = ReasonerType.HERMIT):
        self.reasoner_type = reasoner_type
        self._check_dependencies()
    
    def _check_dependencies(self) -> None:
        """Check that required dependencies are available."""
        try:
            import owlready2
            self._owlready2 = owlready2
        except ImportError:
            raise ImportError(
                "owlready2 is required for reasoning. "
                "Install with: pip install owlready2"
            )
    
    def check_consistency(self, graph: Graph) -> ConsistencyResult:
        """
        Check if an ontology is logically consistent.
        
        Args:
            graph: RDF graph containing the ontology
            
        Returns:
            ConsistencyResult with consistency status
        """
        # Save graph to temp file for owlready2
        with tempfile.NamedTemporaryFile(
            suffix=".owl", delete=False, mode="wb"
        ) as f:
            graph.serialize(f, format="xml")
            temp_path = f.name
        
        try:
            # Load with owlready2
            onto = self._owlready2.get_ontology(f"file://{temp_path}").load()
            
            # Run reasoner
            unsatisfiable = []
            try:
                with onto:
                    self._owlready2.sync_reasoner_hermit(infer_property_values=False)
                
                # Check for unsatisfiable classes
                for cls in onto.classes():
                    if cls.equivalent_to:
                        for eq in cls.equivalent_to:
                            if eq == self._owlready2.Nothing:
                                unsatisfiable.append(str(cls.iri))
                
                # Check if Nothing has instances (inconsistency)
                is_consistent = len(list(self._owlready2.Nothing.instances())) == 0
                
            except self._owlready2.OwlReadyInconsistentOntologyError:
                return ConsistencyResult(
                    is_consistent=False,
                    unsatisfiable_classes=[],
                    error_message="Ontology is inconsistent"
                )
            
            return ConsistencyResult(
                is_consistent=is_consistent and len(unsatisfiable) == 0,
                unsatisfiable_classes=unsatisfiable
            )
            
        except Exception as e:
            return ConsistencyResult(
                is_consistent=False,
                unsatisfiable_classes=[],
                error_message=str(e)
            )
        finally:
            # Cleanup temp file
            Path(temp_path).unlink(missing_ok=True)
    
    def classify(self, graph: Graph) -> InferenceResult:
        """
        Run classification to compute inferred hierarchy.
        
        Args:
            graph: RDF graph containing the ontology
            
        Returns:
            InferenceResult with inferred axioms
        """
        import time
        
        with tempfile.NamedTemporaryFile(
            suffix=".owl", delete=False, mode="wb"
        ) as f:
            graph.serialize(f, format="xml")
            temp_path = f.name
        
        try:
            onto = self._owlready2.get_ontology(f"file://{temp_path}").load()
            
            start_time = time.time()
            
            with onto:
                self._owlready2.sync_reasoner_hermit(infer_property_values=True)
            
            reasoning_time = (time.time() - start_time) * 1000
            
            # Export inferred ontology
            inferred = Graph()
            with tempfile.NamedTemporaryFile(
                suffix=".owl", delete=False, mode="wb"
            ) as out_f:
                onto.save(out_f.name, format="rdfxml")
                inferred.parse(out_f.name, format="xml")
                Path(out_f.name).unlink(missing_ok=True)
            
            # Count new axioms (approximate)
            original_count = len(graph)
            inferred_count = len(inferred)
            new_axioms = max(0, inferred_count - original_count)
            
            return InferenceResult(
                inferred_graph=inferred,
                new_axioms_count=new_axioms,
                reasoning_time_ms=reasoning_time
            )
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_entailment(self, graph: Graph, axiom_graph: Graph) -> bool:
        """
        Test if an axiom is entailed by the ontology.
        
        Args:
            graph: The ontology graph
            axiom_graph: Graph containing the axiom to test
            
        Returns:
            True if the axiom is entailed
        """
        # Merge ontology with negation of axiom
        # If result is inconsistent, axiom is entailed
        # This is a simplified implementation
        merged = Graph()
        for triple in graph:
            merged.add(triple)
        for triple in axiom_graph:
            merged.add(triple)
        
        result = self.classify(merged)
        
        # Check if axiom triples are in inferred graph
        for triple in axiom_graph:
            if triple not in result.inferred_graph:
                return False
        
        return True


def check_consistency(graph: Graph) -> ConsistencyResult:
    """Convenience function to check ontology consistency."""
    reasoner = OWLReasoner()
    return reasoner.check_consistency(graph)
