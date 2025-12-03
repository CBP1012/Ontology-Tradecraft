"""
Ontology Loader Module

Handles loading OWL/RDF ontologies from various formats.
"""

from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from rdflib import Graph, Namespace, URIRef
from rdflib.namespace import OWL, RDF, RDFS, SKOS


# Common ontology namespaces
OBO = Namespace("http://purl.obolibrary.org/obo/")
IAO = Namespace("http://purl.obolibrary.org/obo/IAO_")
OBOINOWL = Namespace("http://www.geneontology.org/formats/oboInOwl#")


class OntologyLoader:
    """Loads and manages ontology graphs."""
    
    SUPPORTED_FORMATS = {
        ".owl": "xml",
        ".rdf": "xml",
        ".xml": "xml",
        ".ttl": "turtle",
        ".n3": "n3",
        ".nt": "nt",
        ".nq": "nquads",
        ".jsonld": "json-ld",
    }
    
    def __init__(self):
        self.graphs: dict[str, Graph] = {}
    
    def load(
        self, 
        path: str | Path, 
        name: Optional[str] = None,
        format: Optional[str] = None
    ) -> Graph:
        """
        Load an ontology from a file.
        
        Args:
            path: Path to the ontology file
            name: Optional name to store the graph under
            format: Optional format override
            
        Returns:
            Loaded RDF graph
        """
        path = Path(path)
        
        if not path.exists():
            raise FileNotFoundError(f"Ontology file not found: {path}")
        
        # Determine format from extension if not provided
        if format is None:
            suffix = path.suffix.lower()
            format = self.SUPPORTED_FORMATS.get(suffix)
            if format is None:
                raise ValueError(f"Unsupported file format: {suffix}")
        
        # Load the graph
        graph = Graph()
        graph.parse(str(path), format=format)
        
        # Bind common prefixes
        self._bind_prefixes(graph)
        
        # Store if name provided
        if name:
            self.graphs[name] = graph
        
        return graph
    
    def load_from_url(
        self, 
        url: str, 
        name: Optional[str] = None,
        format: Optional[str] = None
    ) -> Graph:
        """
        Load an ontology from a URL.
        
        Args:
            url: URL of the ontology
            name: Optional name to store the graph under
            format: Optional format override
            
        Returns:
            Loaded RDF graph
        """
        graph = Graph()
        
        # Try to infer format from URL
        if format is None:
            parsed = urlparse(url)
            suffix = Path(parsed.path).suffix.lower()
            format = self.SUPPORTED_FORMATS.get(suffix, "xml")
        
        graph.parse(url, format=format)
        self._bind_prefixes(graph)
        
        if name:
            self.graphs[name] = graph
        
        return graph
    
    def merge(self, graphs: list[Graph]) -> Graph:
        """
        Merge multiple graphs into one.
        
        Args:
            graphs: List of graphs to merge
            
        Returns:
            Merged graph
        """
        merged = Graph()
        
        for graph in graphs:
            for triple in graph:
                merged.add(triple)
            
            # Copy namespace bindings
            for prefix, namespace in graph.namespaces():
                merged.bind(prefix, namespace, replace=False)
        
        return merged
    
    def get_graph(self, name: str) -> Graph:
        """Get a previously loaded graph by name."""
        if name not in self.graphs:
            raise KeyError(f"No graph loaded with name: {name}")
        return self.graphs[name]
    
    def _bind_prefixes(self, graph: Graph) -> None:
        """Bind common ontology prefixes."""
        graph.bind("owl", OWL)
        graph.bind("rdf", RDF)
        graph.bind("rdfs", RDFS)
        graph.bind("skos", SKOS)
        graph.bind("obo", OBO)
        graph.bind("oboInOwl", OBOINOWL)


def load_ontology(path: str | Path, format: Optional[str] = None) -> Graph:
    """
    Convenience function to load an ontology.
    
    Args:
        path: Path to ontology file
        format: Optional format override
        
    Returns:
        Loaded RDF graph
    """
    loader = OntologyLoader()
    return loader.load(path, format=format)
