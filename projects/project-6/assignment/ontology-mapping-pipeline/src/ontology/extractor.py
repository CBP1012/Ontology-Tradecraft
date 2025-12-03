"""
Ontology Concept Extractor

Extracts concepts, labels, definitions, and relationships from ontologies.
"""

from dataclasses import dataclass, field
from typing import Iterator, Optional

from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS


# OBO-specific namespaces
OBO = Namespace("http://purl.obolibrary.org/obo/")
IAO_DEFINITION = URIRef("http://purl.obolibrary.org/obo/IAO_0000115")
OBOINOWL = Namespace("http://www.geneontology.org/formats/oboInOwl#")


@dataclass
class OntologyConcept:
    """Represents a concept extracted from an ontology."""
    
    iri: str
    labels: list[str] = field(default_factory=list)
    definition: Optional[str] = None
    synonyms: list[str] = field(default_factory=list)
    parents: list[str] = field(default_factory=list)
    children: list[str] = field(default_factory=list)
    related: list[tuple[str, str]] = field(default_factory=list)
    deprecated: bool = False
    
    @property
    def primary_label(self) -> str:
        """Get the primary label (first label or local name from IRI)."""
        if self.labels:
            return self.labels[0]
        # Extract local name from IRI
        if "#" in self.iri:
            return self.iri.split("#")[-1]
        return self.iri.split("/")[-1]
    
    @property
    def all_labels(self) -> list[str]:
        """Get all labels including synonyms."""
        return self.labels + self.synonyms
    
    def to_context_string(self) -> str:
        """Generate a context string for LLM prompts."""
        parts = [f"IRI: {self.iri}"]
        
        if self.labels:
            parts.append(f"Labels: {', '.join(self.labels)}")
        
        if self.definition:
            parts.append(f"Definition: {self.definition}")
        
        if self.synonyms:
            parts.append(f"Synonyms: {', '.join(self.synonyms)}")
        
        if self.parents:
            parts.append(f"Parents: {', '.join(self.parents)}")
        
        return "\n".join(parts)


class ConceptExtractor:
    """Extracts concepts from an ontology graph."""
    
    # Properties to check for labels
    LABEL_PROPERTIES = [
        RDFS.label,
        SKOS.prefLabel,
        URIRef("http://www.w3.org/2004/02/skos/core#prefLabel"),
    ]
    
    # Properties to check for definitions
    DEFINITION_PROPERTIES = [
        RDFS.comment,
        SKOS.definition,
        IAO_DEFINITION,
        URIRef("http://purl.org/dc/terms/description"),
    ]
    
    # Properties to check for synonyms
    SYNONYM_PROPERTIES = [
        SKOS.altLabel,
        OBOINOWL.hasExactSynonym,
        OBOINOWL.hasRelatedSynonym,
        OBOINOWL.hasBroadSynonym,
        OBOINOWL.hasNarrowSynonym,
    ]
    
    def __init__(self, graph: Graph):
        self.graph = graph
    
    def extract_all_concepts(
        self, 
        include_deprecated: bool = False
    ) -> list[OntologyConcept]:
        """
        Extract all class concepts from the ontology.
        
        Args:
            include_deprecated: Whether to include deprecated concepts
            
        Returns:
            List of extracted concepts
        """
        concepts = []
        
        # Find all classes
        classes = set()
        for class_type in [OWL.Class, RDFS.Class]:
            for subj in self.graph.subjects(RDF.type, class_type):
                if isinstance(subj, URIRef):
                    classes.add(subj)
        
        # Also include subjects of rdfs:subClassOf
        for subj in self.graph.subjects(RDFS.subClassOf, None):
            if isinstance(subj, URIRef):
                classes.add(subj)
        
        for class_iri in classes:
            concept = self.extract_concept(class_iri)
            
            if concept.deprecated and not include_deprecated:
                continue
            
            concepts.append(concept)
        
        return concepts
    
    def extract_concept(self, iri: str | URIRef) -> OntologyConcept:
        """
        Extract a single concept by IRI.
        
        Args:
            iri: The IRI of the concept
            
        Returns:
            Extracted concept
        """
        if isinstance(iri, str):
            iri = URIRef(iri)
        
        concept = OntologyConcept(iri=str(iri))
        
        # Extract labels
        for prop in self.LABEL_PROPERTIES:
            for obj in self.graph.objects(iri, prop):
                if isinstance(obj, Literal):
                    label = str(obj)
                    if label not in concept.labels:
                        concept.labels.append(label)
        
        # Extract definition (take first found)
        for prop in self.DEFINITION_PROPERTIES:
            for obj in self.graph.objects(iri, prop):
                if isinstance(obj, Literal):
                    concept.definition = str(obj)
                    break
            if concept.definition:
                break
        
        # Extract synonyms
        for prop in self.SYNONYM_PROPERTIES:
            for obj in self.graph.objects(iri, prop):
                if isinstance(obj, Literal):
                    syn = str(obj)
                    if syn not in concept.synonyms:
                        concept.synonyms.append(syn)
        
        # Extract parents (direct superclasses)
        for obj in self.graph.objects(iri, RDFS.subClassOf):
            if isinstance(obj, URIRef):
                parent_label = self._get_label(obj)
                concept.parents.append(parent_label)
        
        # Extract children (direct subclasses)
        for subj in self.graph.subjects(RDFS.subClassOf, iri):
            if isinstance(subj, URIRef):
                child_label = self._get_label(subj)
                concept.children.append(child_label)
        
        # Check if deprecated
        deprecated_pred = OWL.deprecated
        for obj in self.graph.objects(iri, deprecated_pred):
            if isinstance(obj, Literal) and obj.toPython() == True:
                concept.deprecated = True
                break
        
        return concept
    
    def _get_label(self, iri: URIRef) -> str:
        """Get the best label for an IRI."""
        for prop in self.LABEL_PROPERTIES:
            for obj in self.graph.objects(iri, prop):
                if isinstance(obj, Literal):
                    return str(obj)
        
        # Fallback to local name
        iri_str = str(iri)
        if "#" in iri_str:
            return iri_str.split("#")[-1]
        return iri_str.split("/")[-1]
    
    def get_concept_vocabulary(
        self, 
        max_concepts: Optional[int] = None
    ) -> str:
        """
        Get a formatted vocabulary string for LLM prompts.
        
        Args:
            max_concepts: Maximum number of concepts to include
            
        Returns:
            Formatted vocabulary string
        """
        concepts = self.extract_all_concepts()
        
        if max_concepts:
            concepts = concepts[:max_concepts]
        
        lines = []
        for concept in concepts:
            label = concept.primary_label
            defn = concept.definition or "No definition"
            defn = defn[:200] + "..." if len(defn) > 200 else defn
            lines.append(f"- {label} ({concept.iri}): {defn}")
        
        return "\n".join(lines)


def extract_concepts(graph: Graph) -> list[OntologyConcept]:
    """Convenience function to extract concepts from a graph."""
    extractor = ConceptExtractor(graph)
    return extractor.extract_all_concepts()
