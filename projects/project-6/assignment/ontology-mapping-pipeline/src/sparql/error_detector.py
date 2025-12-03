"""
SPARQL QC Error Detector

Runs SPARQL queries to detect mapping quality issues.
"""

from dataclasses import dataclass
from typing import Any

from rdflib import Graph


@dataclass
class SPARQLError:
    """A detected error from SPARQL QC."""
    query_name: str
    description: str
    severity: str  # error, warning, info
    results: list[dict[str, Any]]


# Library of QC queries
QC_QUERIES = {
    "circular_mappings": {
        "description": "Detect circular equivalence mappings",
        "severity": "error",
        "sparql": """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?a ?b WHERE {
                {
                    ?a owl:equivalentClass ?b .
                    ?b owl:equivalentClass ?a .
                } UNION {
                    ?a skos:exactMatch ?b .
                    ?b skos:exactMatch ?a .
                }
                FILTER(?a != ?b)
                FILTER(STR(?a) < STR(?b))  # Avoid duplicates
            }
        """,
    },
    
    "reflexive_mappings": {
        "description": "Detect mappings from a concept to itself",
        "severity": "warning",
        "sparql": """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?a ?predicate WHERE {
                VALUES ?predicate { 
                    owl:equivalentClass 
                    skos:exactMatch 
                    skos:closeMatch 
                    skos:broadMatch 
                    skos:narrowMatch 
                    skos:relatedMatch 
                }
                ?a ?predicate ?a .
            }
        """,
    },
    
    "conflicting_predicates": {
        "description": "Detect concepts with conflicting mapping predicates",
        "severity": "warning",
        "sparql": """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?a ?b ?pred1 ?pred2 WHERE {
                ?a ?pred1 ?b .
                ?a ?pred2 ?b .
                FILTER(?pred1 != ?pred2)
                FILTER(?pred1 IN (owl:equivalentClass, skos:exactMatch, skos:closeMatch))
                FILTER(?pred2 IN (skos:broadMatch, skos:narrowMatch, skos:relatedMatch))
            }
        """,
    },
    
    "broad_narrow_conflict": {
        "description": "Detect conflicting broad/narrow mappings",
        "severity": "error",
        "sparql": """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?a ?b WHERE {
                ?a skos:broadMatch ?b .
                ?a skos:narrowMatch ?b .
            }
        """,
    },
    
    "deprecated_targets": {
        "description": "Detect mappings to deprecated concepts",
        "severity": "warning",
        "sparql": """
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?source ?target WHERE {
                VALUES ?pred { 
                    owl:equivalentClass 
                    skos:exactMatch 
                    skos:closeMatch 
                    skos:broadMatch 
                    skos:narrowMatch 
                }
                ?source ?pred ?target .
                ?target owl:deprecated true .
            }
        """,
    },
    
    "missing_inverse_broad": {
        "description": "Check broadMatch without corresponding narrowMatch",
        "severity": "info",
        "sparql": """
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?a ?b WHERE {
                ?a skos:broadMatch ?b .
                FILTER NOT EXISTS {
                    ?b skos:narrowMatch ?a .
                }
            }
        """,
    },
}


class ErrorDetector:
    """
    Detects mapping errors using SPARQL queries.
    """
    
    def __init__(self, custom_queries: dict = None):
        """
        Initialize the error detector.
        
        Args:
            custom_queries: Additional custom QC queries
        """
        self.queries = dict(QC_QUERIES)
        if custom_queries:
            self.queries.update(custom_queries)
    
    def run_query(
        self,
        graph: Graph,
        query_name: str,
    ) -> SPARQLError:
        """
        Run a single QC query.
        
        Args:
            graph: The graph to query
            query_name: Name of the query to run
            
        Returns:
            SPARQLError with results
        """
        if query_name not in self.queries:
            raise ValueError(f"Unknown query: {query_name}")
        
        query_def = self.queries[query_name]
        
        results = []
        for row in graph.query(query_def["sparql"]):
            result = {}
            for i, var in enumerate(row):
                result[f"var{i}"] = str(var) if var else None
            results.append(result)
        
        return SPARQLError(
            query_name=query_name,
            description=query_def["description"],
            severity=query_def["severity"],
            results=results,
        )
    
    def run_all_checks(self, graph: Graph) -> list[SPARQLError]:
        """
        Run all QC queries.
        
        Args:
            graph: The graph to check
            
        Returns:
            List of SPARQLError objects
        """
        errors = []
        
        for query_name in self.queries:
            try:
                error = self.run_query(graph, query_name)
                if error.results:  # Only include if there are results
                    errors.append(error)
            except Exception as e:
                print(f"Warning: Query {query_name} failed: {e}")
        
        # Sort by severity
        severity_order = {"error": 0, "warning": 1, "info": 2}
        errors.sort(key=lambda e: severity_order.get(e.severity, 3))
        
        return errors
    
    def run_checks_by_severity(
        self,
        graph: Graph,
        min_severity: str = "warning",
    ) -> list[SPARQLError]:
        """
        Run QC queries filtered by minimum severity.
        
        Args:
            graph: The graph to check
            min_severity: Minimum severity level (error, warning, info)
            
        Returns:
            Filtered list of SPARQLError objects
        """
        severity_levels = {"error": 0, "warning": 1, "info": 2}
        min_level = severity_levels.get(min_severity, 2)
        
        all_errors = self.run_all_checks(graph)
        
        return [
            e for e in all_errors
            if severity_levels.get(e.severity, 2) <= min_level
        ]


def run_qc_checks(graph: Graph) -> list[SPARQLError]:
    """Convenience function to run all QC checks."""
    detector = ErrorDetector()
    return detector.run_all_checks(graph)
