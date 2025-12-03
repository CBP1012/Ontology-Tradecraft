"""
SHACL Validator

Validates RDF graphs against SHACL shape constraints.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from rdflib import Graph


@dataclass
class SHACLViolation:
    """A single SHACL violation."""
    focus_node: str
    result_path: Optional[str]
    message: str
    source_constraint: str
    severity: str = "Violation"


@dataclass
class SHACLValidationResult:
    """Result of SHACL validation."""
    conforms: bool
    violations: list[SHACLViolation]
    results_graph: Optional[Graph] = None


class SHACLValidator:
    """
    Validates RDF data against SHACL shapes.
    """
    
    def __init__(self):
        """Initialize the validator."""
        self.shapes_graph = Graph()
        self._check_dependencies()
    
    def _check_dependencies(self):
        """Check that pySHACL is available."""
        try:
            import pyshacl
            self._pyshacl = pyshacl
        except ImportError:
            raise ImportError(
                "pyshacl is required for SHACL validation. "
                "Install with: pip install pyshacl"
            )
    
    def load_shapes(self, shapes_path: str | Path) -> None:
        """
        Load SHACL shapes from a file.
        
        Args:
            shapes_path: Path to shapes file (Turtle format)
        """
        shapes_path = Path(shapes_path)
        
        if not shapes_path.exists():
            raise FileNotFoundError(f"Shapes file not found: {shapes_path}")
        
        self.shapes_graph.parse(str(shapes_path), format="turtle")
    
    def load_shapes_from_string(self, shapes_ttl: str) -> None:
        """
        Load SHACL shapes from a Turtle string.
        
        Args:
            shapes_ttl: SHACL shapes in Turtle format
        """
        self.shapes_graph.parse(data=shapes_ttl, format="turtle")
    
    def validate(self, data_graph: Graph) -> SHACLValidationResult:
        """
        Validate a data graph against loaded shapes.
        
        Args:
            data_graph: The RDF graph to validate
            
        Returns:
            SHACLValidationResult
        """
        if len(self.shapes_graph) == 0:
            return SHACLValidationResult(conforms=True, violations=[])
        
        conforms, results_graph, results_text = self._pyshacl.validate(
            data_graph,
            shacl_graph=self.shapes_graph,
            inference="none",
            abort_on_first=False,
        )
        
        violations = self._extract_violations(results_graph)
        
        return SHACLValidationResult(
            conforms=conforms,
            violations=violations,
            results_graph=results_graph,
        )
    
    def _extract_violations(self, results_graph: Graph) -> list[SHACLViolation]:
        """Extract violation details from results graph."""
        from rdflib.namespace import SH
        from rdflib import RDF
        
        violations = []
        
        # Find all validation results
        for result in results_graph.subjects(RDF.type, SH.ValidationResult):
            focus_node = None
            result_path = None
            message = ""
            source_constraint = ""
            severity = "Violation"
            
            for pred, obj in results_graph.predicate_objects(result):
                if pred == SH.focusNode:
                    focus_node = str(obj)
                elif pred == SH.resultPath:
                    result_path = str(obj)
                elif pred == SH.resultMessage:
                    message = str(obj)
                elif pred == SH.sourceConstraintComponent:
                    source_constraint = str(obj)
                elif pred == SH.resultSeverity:
                    severity = str(obj).split("#")[-1]
            
            if focus_node:
                violations.append(SHACLViolation(
                    focus_node=focus_node,
                    result_path=result_path,
                    message=message,
                    source_constraint=source_constraint,
                    severity=severity,
                ))
        
        return violations


# Default SHACL shapes for mapping validation
DEFAULT_MAPPING_SHAPES = """
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix sssom: <https://w3id.org/sssom/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .

# Shape for mapping metadata
sssom:MappingShape a sh:NodeShape ;
    sh:targetSubjectsOf owl:equivalentClass, skos:exactMatch, skos:closeMatch,
                        skos:broadMatch, skos:narrowMatch, skos:relatedMatch ;
    sh:message "Subject of mapping must be a valid IRI" ;
    sh:nodeKind sh:IRI .

# Ensure mapping objects are also IRIs
sssom:MappingObjectShape a sh:NodeShape ;
    sh:targetObjectsOf owl:equivalentClass, skos:exactMatch, skos:closeMatch,
                       skos:broadMatch, skos:narrowMatch, skos:relatedMatch ;
    sh:message "Object of mapping must be a valid IRI" ;
    sh:nodeKind sh:IRI .
"""


def validate_mappings(
    mapping_graph: Graph,
    shapes_path: Optional[str | Path] = None,
    use_defaults: bool = True,
) -> SHACLValidationResult:
    """
    Convenience function to validate mappings.
    
    Args:
        mapping_graph: Graph containing mappings
        shapes_path: Optional path to additional shapes
        use_defaults: Whether to include default mapping shapes
        
    Returns:
        SHACLValidationResult
    """
    validator = SHACLValidator()
    
    if use_defaults:
        validator.load_shapes_from_string(DEFAULT_MAPPING_SHAPES)
    
    if shapes_path:
        validator.load_shapes(shapes_path)
    
    return validator.validate(mapping_graph)
