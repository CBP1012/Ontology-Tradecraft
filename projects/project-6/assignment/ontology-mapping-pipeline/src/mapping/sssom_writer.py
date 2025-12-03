"""
SSSOM Format Writer

Outputs mappings in the Simple Standard for Sharing Ontology Mappings (SSSOM) format.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, TextIO

import yaml

from src.mapping.candidate_generator import MappingCandidate
from src.mapping.scorer import ScoredMapping
from src.mapping.explainer import ExplainedMapping


@dataclass
class SSSOMMetadata:
    """SSSOM file metadata."""
    mapping_set_id: str
    mapping_set_title: str
    mapping_tool: str = "ontology-mapping-pipeline"
    mapping_tool_version: str = "0.1.0"
    creator_id: Optional[str] = None
    license: str = "https://creativecommons.org/publicdomain/zero/1.0/"
    subject_source: Optional[str] = None
    object_source: Optional[str] = None
    mapping_date: Optional[str] = None
    
    def __post_init__(self):
        if self.mapping_date is None:
            self.mapping_date = datetime.now().strftime("%Y-%m-%d")


# Mapping from our predicates to SSSOM predicate IRIs
PREDICATE_MAP = {
    "owl:equivalentClass": "owl:equivalentClass",
    "skos:exactMatch": "skos:exactMatch",
    "skos:closeMatch": "skos:closeMatch",
    "skos:broadMatch": "skos:broadMatch",
    "skos:narrowMatch": "skos:narrowMatch",
    "skos:relatedMatch": "skos:relatedMatch",
}

# SSSOM columns
SSSOM_COLUMNS = [
    "subject_id",
    "subject_label",
    "predicate_id",
    "object_id",
    "object_label",
    "mapping_justification",
    "confidence",
    "comment",
]


class SSSOMWriter:
    """Writes mappings to SSSOM format."""
    
    def __init__(self, metadata: SSSOMMetadata):
        """
        Initialize the writer.
        
        Args:
            metadata: SSSOM file metadata
        """
        self.metadata = metadata
    
    def write(
        self,
        mappings: list[MappingCandidate | ScoredMapping | ExplainedMapping],
        output_path: str | Path,
    ) -> None:
        """
        Write mappings to SSSOM TSV file.
        
        Args:
            mappings: List of mappings to write
            output_path: Output file path
        """
        output_path = Path(output_path)
        
        with open(output_path, "w") as f:
            self._write_header(f)
            self._write_mappings(f, mappings)
    
    def _write_header(self, f: TextIO) -> None:
        """Write SSSOM YAML header."""
        header = {
            "mapping_set_id": self.metadata.mapping_set_id,
            "mapping_set_title": self.metadata.mapping_set_title,
            "mapping_tool": self.metadata.mapping_tool,
            "mapping_tool_version": self.metadata.mapping_tool_version,
            "mapping_date": self.metadata.mapping_date,
            "license": self.metadata.license,
        }
        
        if self.metadata.creator_id:
            header["creator_id"] = [self.metadata.creator_id]
        if self.metadata.subject_source:
            header["subject_source"] = self.metadata.subject_source
        if self.metadata.object_source:
            header["object_source"] = self.metadata.object_source
        
        # Write as YAML with comment prefix
        yaml_str = yaml.dump(header, default_flow_style=False, sort_keys=False)
        for line in yaml_str.strip().split("\n"):
            f.write(f"# {line}\n")
        f.write("\n")
    
    def _write_mappings(
        self,
        f: TextIO,
        mappings: list[MappingCandidate | ScoredMapping | ExplainedMapping],
    ) -> None:
        """Write mapping rows."""
        # Write column headers
        f.write("\t".join(SSSOM_COLUMNS) + "\n")
        
        for mapping in mappings:
            row = self._mapping_to_row(mapping)
            f.write("\t".join(str(v) for v in row) + "\n")
    
    def _mapping_to_row(
        self,
        mapping: MappingCandidate | ScoredMapping | ExplainedMapping,
    ) -> list:
        """Convert a mapping to a TSV row."""
        # Extract the base candidate
        if isinstance(mapping, ScoredMapping):
            candidate = mapping.candidate
            confidence = mapping.combined_score
            comment = mapping.reasoning
        elif isinstance(mapping, ExplainedMapping):
            candidate = mapping.candidate
            confidence = candidate.confidence
            comment = mapping.summary
        else:
            candidate = mapping
            confidence = candidate.confidence
            comment = candidate.justification
        
        # Map predicate to SSSOM format
        predicate = PREDICATE_MAP.get(
            candidate.predicate, candidate.predicate
        )
        
        return [
            candidate.source_iri,
            candidate.source_label,
            predicate,
            candidate.target_iri,
            candidate.target_label,
            "semapv:LexicalMatching",  # Default justification
            round(confidence, 4),
            self._escape_tsv(comment),
        ]
    
    def _escape_tsv(self, text: str) -> str:
        """Escape text for TSV format."""
        if not text:
            return ""
        # Replace tabs and newlines
        return text.replace("\t", " ").replace("\n", " ").strip()


def write_sssom(
    mappings: list[MappingCandidate | ScoredMapping | ExplainedMapping],
    output_path: str | Path,
    title: str = "Generated Mappings",
    mapping_set_id: Optional[str] = None,
    **metadata_kwargs,
) -> None:
    """
    Convenience function to write SSSOM output.
    
    Args:
        mappings: List of mappings
        output_path: Output file path
        title: Mapping set title
        mapping_set_id: Optional ID (generated if not provided)
        **metadata_kwargs: Additional metadata fields
    """
    if mapping_set_id is None:
        mapping_set_id = f"urn:uuid:{datetime.now().strftime('%Y%m%d%H%M%S')}"
    
    metadata = SSSOMMetadata(
        mapping_set_id=mapping_set_id,
        mapping_set_title=title,
        **metadata_kwargs,
    )
    
    writer = SSSOMWriter(metadata)
    writer.write(mappings, output_path)
