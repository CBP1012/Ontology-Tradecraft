"""
SPARQL QC Queries Library

A comprehensive collection of SPARQL queries for ontology mapping quality control.
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class QCQuery:
    """Definition of a QC query."""
    name: str
    description: str
    severity: str  # error, warning, info
    category: str  # consistency, completeness, quality, structure
    sparql: str
    fix_suggestion: Optional[str] = None


# Comprehensive QC Query Library
QC_QUERY_LIBRARY = {
    
    # ==================== CONSISTENCY CHECKS ====================
    
    "circular_equivalence": QCQuery(
        name="circular_equivalence",
        description="Detect circular equivalence mappings (A equiv B and B equiv A)",
        severity="error",
        category="consistency",
        sparql="""
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
                FILTER(STR(?a) < STR(?b))
            }
        """,
        fix_suggestion="Remove one direction of the circular mapping",
    ),
    
    "reflexive_mapping": QCQuery(
        name="reflexive_mapping",
        description="Detect mappings from a concept to itself",
        severity="warning",
        category="consistency",
        sparql="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?concept ?predicate WHERE {
                VALUES ?predicate { 
                    owl:equivalentClass 
                    skos:exactMatch skos:closeMatch 
                    skos:broadMatch skos:narrowMatch skos:relatedMatch 
                }
                ?concept ?predicate ?concept .
            }
        """,
        fix_suggestion="Remove reflexive mappings as they are trivially true",
    ),
    
    "conflicting_exact_and_close": QCQuery(
        name="conflicting_exact_and_close",
        description="Detect concepts mapped with both exactMatch and closeMatch to the same target",
        severity="error",
        category="consistency",
        sparql="""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?source ?target WHERE {
                ?source skos:exactMatch ?target .
                ?source skos:closeMatch ?target .
            }
        """,
        fix_suggestion="Choose either exactMatch or closeMatch, not both",
    ),
    
    "conflicting_broad_narrow": QCQuery(
        name="conflicting_broad_narrow",
        description="Detect concepts with both broadMatch and narrowMatch to the same target",
        severity="error",
        category="consistency",
        sparql="""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?source ?target WHERE {
                ?source skos:broadMatch ?target .
                ?source skos:narrowMatch ?target .
            }
        """,
        fix_suggestion="broadMatch and narrowMatch are inverses; use only one",
    ),
    
    "equivalence_with_hierarchical": QCQuery(
        name="equivalence_with_hierarchical",
        description="Detect equivalentClass combined with hierarchical mapping to same target",
        severity="warning",
        category="consistency",
        sparql="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?source ?target ?hierarchicalPred WHERE {
                ?source owl:equivalentClass ?target .
                VALUES ?hierarchicalPred { skos:broadMatch skos:narrowMatch rdfs:subClassOf }
                ?source ?hierarchicalPred ?target .
            }
        """,
        fix_suggestion="Equivalence implies same level; remove hierarchical predicate",
    ),
    
    # ==================== COMPLETENESS CHECKS ====================
    
    "unmapped_classes": QCQuery(
        name="unmapped_classes",
        description="Find classes in source ontology without any mapping",
        severity="info",
        category="completeness",
        sparql="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
            
            SELECT DISTINCT ?class WHERE {
                ?class rdf:type owl:Class .
                FILTER NOT EXISTS {
                    VALUES ?pred { 
                        owl:equivalentClass 
                        skos:exactMatch skos:closeMatch 
                        skos:broadMatch skos:narrowMatch skos:relatedMatch 
                    }
                    ?class ?pred ?target .
                }
                FILTER(!isBlank(?class))
            }
        """,
        fix_suggestion="Review unmapped classes to determine if mappings are needed",
    ),
    
    "missing_inverse_broad_narrow": QCQuery(
        name="missing_inverse_broad_narrow",
        description="Find broadMatch without corresponding narrowMatch on target",
        severity="info",
        category="completeness",
        sparql="""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?source ?target WHERE {
                ?source skos:broadMatch ?target .
                FILTER NOT EXISTS {
                    ?target skos:narrowMatch ?source .
                }
            }
        """,
        fix_suggestion="Consider adding inverse narrowMatch for completeness",
    ),
    
    # ==================== QUALITY CHECKS ====================
    
    "deprecated_mapping_target": QCQuery(
        name="deprecated_mapping_target",
        description="Find mappings to deprecated concepts",
        severity="warning",
        category="quality",
        sparql="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?source ?predicate ?target WHERE {
                VALUES ?predicate { 
                    owl:equivalentClass 
                    skos:exactMatch skos:closeMatch 
                    skos:broadMatch skos:narrowMatch 
                }
                ?source ?predicate ?target .
                ?target owl:deprecated true .
            }
        """,
        fix_suggestion="Update mappings to use non-deprecated replacement concepts",
    ),
    
    "deprecated_mapping_source": QCQuery(
        name="deprecated_mapping_source",
        description="Find mappings from deprecated concepts",
        severity="info",
        category="quality",
        sparql="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?source ?predicate ?target WHERE {
                VALUES ?predicate { 
                    owl:equivalentClass 
                    skos:exactMatch skos:closeMatch 
                }
                ?source ?predicate ?target .
                ?source owl:deprecated true .
            }
        """,
        fix_suggestion="Consider if deprecated source mappings should be removed",
    ),
    
    "multiple_exact_matches": QCQuery(
        name="multiple_exact_matches",
        description="Find concepts with multiple exactMatch mappings",
        severity="warning",
        category="quality",
        sparql="""
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT ?source (COUNT(?target) AS ?matchCount) WHERE {
                ?source skos:exactMatch ?target .
            }
            GROUP BY ?source
            HAVING (COUNT(?target) > 1)
        """,
        fix_suggestion="Review if multiple exact matches are appropriate or if some should be closeMatch",
    ),
    
    "unlabeled_mapping_participant": QCQuery(
        name="unlabeled_mapping_participant",
        description="Find mapping participants without labels",
        severity="info",
        category="quality",
        sparql="""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?concept WHERE {
                {
                    VALUES ?pred { owl:equivalentClass skos:exactMatch skos:closeMatch }
                    { ?concept ?pred ?other } UNION { ?other ?pred ?concept }
                }
                FILTER NOT EXISTS {
                    ?concept rdfs:label ?label .
                }
                FILTER NOT EXISTS {
                    ?concept skos:prefLabel ?label .
                }
                FILTER(!isBlank(?concept))
            }
        """,
        fix_suggestion="Add labels to improve mapping readability",
    ),
    
    # ==================== STRUCTURAL CHECKS ====================
    
    "blank_node_in_mapping": QCQuery(
        name="blank_node_in_mapping",
        description="Find mappings involving blank nodes",
        severity="error",
        category="structure",
        sparql="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?subject ?predicate ?object WHERE {
                VALUES ?predicate { 
                    owl:equivalentClass 
                    skos:exactMatch skos:closeMatch 
                    skos:broadMatch skos:narrowMatch 
                }
                ?subject ?predicate ?object .
                FILTER(isBlank(?subject) || isBlank(?object))
            }
        """,
        fix_suggestion="Mappings should use named IRIs, not blank nodes",
    ),
    
    "literal_in_mapping": QCQuery(
        name="literal_in_mapping",
        description="Find mappings with literal values (invalid)",
        severity="error",
        category="structure",
        sparql="""
            PREFIX owl: <http://www.w3.org/2002/07/owl#>
            PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
            
            SELECT DISTINCT ?subject ?predicate ?object WHERE {
                VALUES ?predicate { 
                    owl:equivalentClass 
                    skos:exactMatch skos:closeMatch 
                    skos:broadMatch skos:narrowMatch 
                }
                ?subject ?predicate ?object .
                FILTER(isLiteral(?object))
            }
        """,
        fix_suggestion="Mapping objects must be IRIs, not literals",
    ),
    
    "cross_ontology_subclass": QCQuery(
        name="cross_ontology_subclass",
        description="Find rdfs:subClassOf used across different ontology namespaces",
        severity="warning",
        category="structure",
        sparql="""
            PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
            
            SELECT DISTINCT ?child ?parent WHERE {
                ?child rdfs:subClassOf ?parent .
                FILTER(!isBlank(?child) && !isBlank(?parent))
                # Check if they have different namespace prefixes
                BIND(REPLACE(STR(?child), "[^/:#]+$", "") AS ?childNS)
                BIND(REPLACE(STR(?parent), "[^/:#]+$", "") AS ?parentNS)
                FILTER(?childNS != ?parentNS)
            }
        """,
        fix_suggestion="Consider using skos:broadMatch instead of rdfs:subClassOf across ontologies",
    ),
    
    # ==================== SSSOM-SPECIFIC CHECKS ====================
    
    "missing_mapping_justification": QCQuery(
        name="missing_mapping_justification",
        description="Find SSSOM mappings without justification",
        severity="info",
        category="quality",
        sparql="""
            PREFIX sssom: <https://w3id.org/sssom/>
            
            SELECT DISTINCT ?mapping WHERE {
                ?mapping a sssom:Mapping .
                FILTER NOT EXISTS {
                    ?mapping sssom:mapping_justification ?justification .
                }
            }
        """,
        fix_suggestion="Add mapping_justification to improve traceability",
    ),
    
    "low_confidence_mappings": QCQuery(
        name="low_confidence_mappings",
        description="Find mappings with confidence below 0.5",
        severity="info",
        category="quality",
        sparql="""
            PREFIX sssom: <https://w3id.org/sssom/>
            PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
            
            SELECT ?mapping ?confidence WHERE {
                ?mapping sssom:confidence ?confidence .
                FILTER(xsd:decimal(?confidence) < 0.5)
            }
        """,
        fix_suggestion="Review low-confidence mappings for accuracy",
    ),
}


def get_query(name: str) -> Optional[QCQuery]:
    """Get a QC query by name."""
    return QC_QUERY_LIBRARY.get(name)


def get_queries_by_category(category: str) -> list[QCQuery]:
    """Get all queries in a category."""
    return [q for q in QC_QUERY_LIBRARY.values() if q.category == category]


def get_queries_by_severity(severity: str) -> list[QCQuery]:
    """Get all queries of a given severity level."""
    return [q for q in QC_QUERY_LIBRARY.values() if q.severity == severity]


def list_all_queries() -> list[str]:
    """List all available query names."""
    return list(QC_QUERY_LIBRARY.keys())


def get_error_queries() -> list[QCQuery]:
    """Get all error-level queries."""
    return get_queries_by_severity("error")


def get_warning_queries() -> list[QCQuery]:
    """Get all warning-level queries."""
    return get_queries_by_severity("warning")


# Export query dictionary for backward compatibility
QUERIES = {name: q.sparql for name, q in QC_QUERY_LIBRARY.items()}
