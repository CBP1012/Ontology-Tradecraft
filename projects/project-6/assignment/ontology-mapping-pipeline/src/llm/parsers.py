"""
Response Parsers for LLM Outputs

Handles parsing and validation of structured responses from LLMs.
"""

import json
import re
from dataclasses import dataclass
from typing import Any, Optional

from pydantic import BaseModel, Field, ValidationError


class CandidateMapping(BaseModel):
    """A single candidate mapping from LLM response."""
    target_iri: str
    predicate: str
    confidence: float = Field(ge=0.0, le=1.0)
    justification: str


class CandidateGenerationResponse(BaseModel):
    """Response from candidate generation prompt."""
    mappings: list[CandidateMapping] = Field(default_factory=list)
    no_match_reason: Optional[str] = None


class RewrittenLabel(BaseModel):
    """Response from label rewriting prompt."""
    normalized_label: str
    simplified_definition: str
    key_terms: list[str] = Field(default_factory=list)
    suggested_synonyms: list[str] = Field(default_factory=list)
    domain_context: Optional[str] = None


class AlternativeConsidered(BaseModel):
    """An alternative mapping that was considered."""
    concept: str
    reason_rejected: str


class MappingExplanation(BaseModel):
    """Response from explanation prompt."""
    summary: str
    evidence: list[str] = Field(default_factory=list)
    caveats: list[str] = Field(default_factory=list)
    alternatives_considered: list[AlternativeConsidered] = Field(default_factory=list)


class ScoreBreakdown(BaseModel):
    """Breakdown of mapping scores."""
    lexical: float = Field(ge=0.0, le=1.0)
    semantic: float = Field(ge=0.0, le=1.0)
    structural: float = Field(ge=0.0, le=1.0)
    predicate_fit: float = Field(ge=0.0, le=1.0)


class ScoringResponse(BaseModel):
    """Response from scoring prompt."""
    scores: ScoreBreakdown
    overall_score: float = Field(ge=0.0, le=1.0)
    recommended_predicate: Optional[str] = None
    reasoning: str


class SHACLShape(BaseModel):
    """A suggested SHACL shape."""
    name: str
    description: str
    turtle: str


class SHACLSuggestionResponse(BaseModel):
    """Response from SHACL suggestion prompt."""
    shapes: list[SHACLShape] = Field(default_factory=list)
    rationale: str


class SPARQLQuery(BaseModel):
    """A suggested SPARQL QC query."""
    name: str
    description: str
    severity: str = Field(pattern="^(error|warning|info)$")
    sparql: str


class SPARQLQCResponse(BaseModel):
    """Response from SPARQL QC prompt."""
    queries: list[SPARQLQuery] = Field(default_factory=list)


def extract_json(text: str) -> str:
    """Extract JSON from text that may contain markdown or other content."""
    # Try to find JSON in code blocks
    code_block_match = re.search(r"```(?:json)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_block_match:
        return code_block_match.group(1).strip()
    
    # Try to find raw JSON object
    json_match = re.search(r"\{.*\}", text, re.DOTALL)
    if json_match:
        return json_match.group(0)
    
    # Return original text if no JSON found
    return text


def parse_candidate_response(text: str) -> CandidateGenerationResponse:
    """Parse candidate generation response."""
    json_str = extract_json(text)
    try:
        data = json.loads(json_str)
        return CandidateGenerationResponse(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        # Return empty response on parse failure
        return CandidateGenerationResponse(
            mappings=[],
            no_match_reason=f"Failed to parse LLM response: {e}"
        )


def parse_rewriting_response(text: str) -> RewrittenLabel:
    """Parse label rewriting response."""
    json_str = extract_json(text)
    try:
        data = json.loads(json_str)
        return RewrittenLabel(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Failed to parse rewriting response: {e}")


def parse_explanation_response(text: str) -> MappingExplanation:
    """Parse explanation response."""
    json_str = extract_json(text)
    try:
        data = json.loads(json_str)
        return MappingExplanation(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        # Return minimal explanation on parse failure
        return MappingExplanation(
            summary="Unable to generate explanation",
            evidence=[],
            caveats=[f"Parse error: {e}"],
            alternatives_considered=[]
        )


def parse_scoring_response(text: str) -> ScoringResponse:
    """Parse scoring response."""
    json_str = extract_json(text)
    try:
        data = json.loads(json_str)
        return ScoringResponse(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        raise ValueError(f"Failed to parse scoring response: {e}")


def parse_shacl_response(text: str) -> SHACLSuggestionResponse:
    """Parse SHACL suggestion response."""
    json_str = extract_json(text)
    try:
        data = json.loads(json_str)
        return SHACLSuggestionResponse(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        return SHACLSuggestionResponse(
            shapes=[],
            rationale=f"Failed to parse: {e}"
        )


def parse_sparql_response(text: str) -> SPARQLQCResponse:
    """Parse SPARQL QC response."""
    json_str = extract_json(text)
    try:
        data = json.loads(json_str)
        return SPARQLQCResponse(**data)
    except (json.JSONDecodeError, ValidationError) as e:
        return SPARQLQCResponse(queries=[])
