"""
Pipeline Validator

Orchestrates end-to-end validation of ontology mappings.
"""

from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Optional

from rdflib import Graph

from src.ontology.reasoner import OWLReasoner, ConsistencyResult
from src.shacl.validator import SHACLValidator, SHACLValidationResult
from src.sparql.error_detector import ErrorDetector, SPARQLError


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class ValidationIssue:
    """A single validation issue."""
    severity: ValidationSeverity
    category: str
    message: str
    affected_mappings: list[str] = field(default_factory=list)


@dataclass
class ValidationReport:
    """Complete validation report."""
    is_valid: bool
    consistency_result: Optional[ConsistencyResult] = None
    shacl_result: Optional[SHACLValidationResult] = None
    sparql_errors: list[SPARQLError] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.ERROR)
    
    @property
    def warning_count(self) -> int:
        return sum(1 for i in self.issues if i.severity == ValidationSeverity.WARNING)
    
    def to_dict(self) -> dict:
        """Convert report to dictionary."""
        return {
            "is_valid": self.is_valid,
            "error_count": self.error_count,
            "warning_count": self.warning_count,
            "consistency": {
                "is_consistent": self.consistency_result.is_consistent if self.consistency_result else None,
                "unsatisfiable_classes": self.consistency_result.unsatisfiable_classes if self.consistency_result else [],
            } if self.consistency_result else None,
            "shacl": {
                "conforms": self.shacl_result.conforms if self.shacl_result else None,
                "violation_count": len(self.shacl_result.violations) if self.shacl_result else 0,
            } if self.shacl_result else None,
            "sparql_errors": [
                {"name": e.query_name, "severity": e.severity, "count": len(e.results)}
                for e in self.sparql_errors
            ],
            "issues": [
                {
                    "severity": i.severity.value,
                    "category": i.category,
                    "message": i.message,
                }
                for i in self.issues
            ],
        }


class PipelineValidator:
    """
    Validates mappings through multiple quality checks.
    """
    
    def __init__(
        self,
        run_reasoner: bool = True,
        run_shacl: bool = True,
        run_sparql: bool = True,
        shacl_shapes_dir: Optional[str] = None,
        fail_on_inconsistency: bool = True,
        fail_on_shacl_violation: bool = False,
        max_violations_allowed: int = 10,
    ):
        """
        Initialize the validator.
        
        Args:
            run_reasoner: Whether to run OWL consistency checking
            run_shacl: Whether to run SHACL validation
            run_sparql: Whether to run SPARQL QC queries
            shacl_shapes_dir: Directory containing SHACL shapes
            fail_on_inconsistency: Fail validation if ontology is inconsistent
            fail_on_shacl_violation: Fail validation on SHACL violations
            max_violations_allowed: Maximum SPARQL errors before failure
        """
        self.run_reasoner = run_reasoner
        self.run_shacl = run_shacl
        self.run_sparql = run_sparql
        self.shacl_shapes_dir = shacl_shapes_dir
        self.fail_on_inconsistency = fail_on_inconsistency
        self.fail_on_shacl_violation = fail_on_shacl_violation
        self.max_violations_allowed = max_violations_allowed
    
    def validate(
        self,
        source_graph: Graph,
        target_graph: Graph,
        mapping_graph: Graph,
    ) -> ValidationReport:
        """
        Run all validation checks on mappings.
        
        Args:
            source_graph: Source ontology
            target_graph: Target ontology
            mapping_graph: Graph containing mapping axioms
            
        Returns:
            ValidationReport with all results
        """
        issues = []
        is_valid = True
        
        # Merge graphs for consistency checking
        merged = Graph()
        for g in [source_graph, target_graph, mapping_graph]:
            for triple in g:
                merged.add(triple)
        
        # OWL Consistency
        consistency_result = None
        if self.run_reasoner:
            reasoner = OWLReasoner()
            consistency_result = reasoner.check_consistency(merged)
            
            if not consistency_result.is_consistent:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="consistency",
                    message="Ontology with mappings is inconsistent",
                    affected_mappings=consistency_result.unsatisfiable_classes,
                ))
                if self.fail_on_inconsistency:
                    is_valid = False
            
            if consistency_result.unsatisfiable_classes:
                issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    category="consistency",
                    message=f"Found {len(consistency_result.unsatisfiable_classes)} unsatisfiable classes",
                    affected_mappings=consistency_result.unsatisfiable_classes,
                ))
        
        # SHACL Validation
        shacl_result = None
        if self.run_shacl and self.shacl_shapes_dir:
            validator = SHACLValidator()
            shapes_path = Path(self.shacl_shapes_dir)
            
            if shapes_path.exists():
                # Load all shape files
                for shape_file in shapes_path.glob("*.ttl"):
                    validator.load_shapes(shape_file)
                
                shacl_result = validator.validate(mapping_graph)
                
                if not shacl_result.conforms:
                    for violation in shacl_result.violations:
                        issues.append(ValidationIssue(
                            severity=ValidationSeverity.WARNING,
                            category="shacl",
                            message=violation.message,
                            affected_mappings=[violation.focus_node],
                        ))
                    
                    if self.fail_on_shacl_violation:
                        is_valid = False
        
        # SPARQL QC
        sparql_errors = []
        if self.run_sparql:
            detector = ErrorDetector()
            sparql_errors = detector.run_all_checks(mapping_graph)
            
            error_violations = sum(
                len(e.results) for e in sparql_errors if e.severity == "error"
            )
            
            if error_violations > self.max_violations_allowed:
                is_valid = False
            
            for error in sparql_errors:
                severity = (
                    ValidationSeverity.ERROR if error.severity == "error"
                    else ValidationSeverity.WARNING if error.severity == "warning"
                    else ValidationSeverity.INFO
                )
                
                if error.results:
                    issues.append(ValidationIssue(
                        severity=severity,
                        category="sparql_qc",
                        message=f"{error.query_name}: {error.description} ({len(error.results)} occurrences)",
                    ))
        
        return ValidationReport(
            is_valid=is_valid,
            consistency_result=consistency_result,
            shacl_result=shacl_result,
            sparql_errors=sparql_errors,
            issues=issues,
        )
    
    def validate_from_files(
        self,
        source_path: str | Path,
        target_path: str | Path,
        mapping_path: str | Path,
    ) -> ValidationReport:
        """
        Validate mappings from file paths.
        
        Args:
            source_path: Path to source ontology
            target_path: Path to target ontology
            mapping_path: Path to mapping file
            
        Returns:
            ValidationReport
        """
        from src.ontology.loader import load_ontology
        
        source_graph = load_ontology(source_path)
        target_graph = load_ontology(target_path)
        mapping_graph = load_ontology(mapping_path)
        
        return self.validate(source_graph, target_graph, mapping_graph)
