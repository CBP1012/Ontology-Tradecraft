"""
Prompt Templates for Ontology Mapping Tasks

This module contains carefully crafted prompts for different LLM-assisted
mapping operations.
"""

# System prompt establishing the LLM's role
SYSTEM_PROMPT = """You are an expert ontology engineer specializing in semantic 
mappings between biomedical and scientific ontologies. You have deep knowledge of:
- OWL, RDF, SKOS, and other semantic web standards
- Common ontology design patterns
- Mapping predicates and their precise semantics
- Quality criteria for good ontology mappings

Always provide structured, precise responses. When uncertain, indicate your 
confidence level and reasoning."""


# Candidate generation prompt
CANDIDATE_GENERATION_PROMPT = """Given a concept from the source ontology, identify 
potential mappings to concepts in the target ontology.

## Source Concept
- IRI: {source_iri}
- Label: {source_label}
- Definition: {source_definition}
- Synonyms: {source_synonyms}
- Parent classes: {source_parents}

## Target Ontology Concepts
{target_concepts}

## Task
Identify all plausible mappings from the source concept to target concepts.
For each mapping, specify:
1. The target concept IRI
2. The mapping predicate (owl:equivalentClass, skos:exactMatch, skos:closeMatch, 
   skos:broadMatch, skos:narrowMatch, or skos:relatedMatch)
3. A confidence score (0.0 to 1.0)
4. Brief justification (one sentence)

## Response Format (JSON)
{{
  "mappings": [
    {{
      "target_iri": "string",
      "predicate": "string", 
      "confidence": 0.0,
      "justification": "string"
    }}
  ],
  "no_match_reason": "string or null if mappings found"
}}

Respond ONLY with valid JSON, no additional text."""


# Label rewriting prompt
LABEL_REWRITING_PROMPT = """Rewrite the following ontology label and definition to 
improve matching potential while preserving semantic meaning.

## Original
- Label: {label}
- Definition: {definition}

## Task
1. Normalize the label (expand abbreviations, standardize terminology)
2. Extract key semantic components
3. Identify potential synonyms
4. Simplify complex definitions

## Response Format (JSON)
{{
  "normalized_label": "string",
  "simplified_definition": "string",
  "key_terms": ["term1", "term2"],
  "suggested_synonyms": ["syn1", "syn2"],
  "domain_context": "string"
}}

Respond ONLY with valid JSON."""


# Explanation generation prompt
EXPLANATION_PROMPT = """Generate a human-readable explanation for the following 
ontology mapping.

## Mapping
- Source: {source_label} ({source_iri})
- Target: {target_label} ({target_iri})
- Predicate: {predicate}
- Confidence: {confidence}

## Source Context
- Definition: {source_definition}
- Parents: {source_parents}

## Target Context  
- Definition: {target_definition}
- Parents: {target_parents}

## Task
Provide a clear explanation of:
1. Why these concepts are mapped
2. Evidence supporting the mapping
3. Any caveats or limitations
4. Alternative mappings that were considered

## Response Format (JSON)
{{
  "summary": "One sentence summary of the mapping rationale",
  "evidence": ["Evidence point 1", "Evidence point 2"],
  "caveats": ["Caveat 1", "Caveat 2"],
  "alternatives_considered": [
    {{"concept": "...", "reason_rejected": "..."}}
  ]
}}

Respond ONLY with valid JSON."""


# Plausibility scoring prompt
SCORING_PROMPT = """Evaluate the plausibility of the following ontology mapping.

## Mapping
- Source: {source_label} ({source_iri})
  Definition: {source_definition}
  
- Target: {target_label} ({target_iri})
  Definition: {target_definition}
  
- Proposed predicate: {predicate}

## Scoring Criteria
Evaluate on these dimensions (0.0 to 1.0 each):

1. **Lexical Match**: How similar are the labels/synonyms?
2. **Semantic Match**: Do the definitions describe the same concept?
3. **Structural Fit**: Are the hierarchical positions compatible?
4. **Predicate Appropriateness**: Is the mapping predicate correct?

## Response Format (JSON)
{{
  "scores": {{
    "lexical": 0.0,
    "semantic": 0.0,
    "structural": 0.0,
    "predicate_fit": 0.0
  }},
  "overall_score": 0.0,
  "recommended_predicate": "string or null",
  "reasoning": "Brief explanation of scores"
}}

Respond ONLY with valid JSON."""


# SHACL shape suggestion prompt
SHACL_SUGGESTION_PROMPT = """Based on the ontology domain and mapping patterns, 
suggest SHACL shapes to enforce mapping quality constraints.

## Domain
{domain_description}

## Sample Mappings
{sample_mappings}

## Common Issues to Address
{common_issues}

## Task
Generate SHACL shapes that would help validate mapping quality by:
1. Enforcing required metadata
2. Validating IRI patterns
3. Checking confidence ranges
4. Ensuring predicate appropriateness

## Response Format (JSON)
{{
  "shapes": [
    {{
      "name": "ShapeName",
      "description": "What this shape validates",
      "turtle": "SHACL shape in Turtle syntax"
    }}
  ],
  "rationale": "Why these shapes are recommended"
}}

Respond ONLY with valid JSON."""


# SPARQL QC query suggestion prompt  
SPARQL_QC_PROMPT = """Suggest SPARQL queries to detect potential mapping errors.

## Mapping Context
{mapping_context}

## Known Issues to Detect
- Circular mappings
- Conflicting predicates
- Missing required metadata
- Low confidence mappings without justification
- Cross-ontology consistency violations

## Task
Generate SPARQL queries that identify each type of issue.

## Response Format (JSON)
{{
  "queries": [
    {{
      "name": "QueryName",
      "description": "What issue this detects",
      "severity": "error|warning|info",
      "sparql": "SELECT query string"
    }}
  ]
}}

Respond ONLY with valid JSON."""


def format_prompt(template: str, **kwargs) -> str:
    """Format a prompt template with the given values."""
    # Handle missing optional fields
    for key in ["source_synonyms", "source_parents", "target_parents"]:
        if key not in kwargs:
            kwargs[key] = "None provided"
    
    return template.format(**kwargs)
