# API Documentation

This document provides detailed API documentation for the Ontology Mapping Pipeline.

## Table of Contents

1. [LLM Module](#llm-module)
2. [Ontology Module](#ontology-module)
3. [Mapping Module](#mapping-module)
4. [Validation Module](#validation-module)
5. [SHACL Module](#shacl-module)
6. [SPARQL Module](#sparql-module)

---

## LLM Module

### `src.llm.client`

#### `LLMClient` (Abstract Base Class)

Base class for LLM provider implementations.

```python
from src.llm.client import LLMClient

class LLMClient(ABC):
    async def complete(self, prompt: str, **kwargs) -> LLMResponse
    async def complete_with_system(self, system: str, user: str, **kwargs) -> LLMResponse
```

#### `ClaudeClient`

Anthropic Claude implementation.

```python
from src.llm.client import ClaudeClient

client = ClaudeClient({
    "api_key": "your-api-key",  # or set ANTHROPIC_API_KEY env var
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 4096,
    "temperature": 0.1,
})

response = await client.complete("Your prompt here")
print(response.content)
```

#### `OpenAIClient`

OpenAI GPT implementation.

```python
from src.llm.client import OpenAIClient

client = OpenAIClient({
    "api_key": "your-api-key",  # or set OPENAI_API_KEY env var
    "model": "gpt-4-turbo",
})
```

#### `create_llm_client(config_path: str) -> LLMClient`

Factory function to create an LLM client from configuration file.

```python
from src.llm.client import create_llm_client

client = create_llm_client("configs/llm_config.yaml")
```

#### `LLMResponse`

Response dataclass from LLM calls.

```python
@dataclass
class LLMResponse:
    content: str          # Response text
    model: str            # Model used
    usage: dict[str, int] # Token usage
    raw_response: Any     # Original response object
```

---

### `src.llm.prompts`

Prompt templates for mapping tasks.

#### Available Prompts

| Constant | Description |
|----------|-------------|
| `SYSTEM_PROMPT` | Base system prompt for ontology engineering |
| `CANDIDATE_GENERATION_PROMPT` | Generate mapping candidates |
| `LABEL_REWRITING_PROMPT` | Normalize labels and definitions |
| `EXPLANATION_PROMPT` | Generate mapping explanations |
| `SCORING_PROMPT` | Score mapping plausibility |
| `SHACL_SUGGESTION_PROMPT` | Suggest SHACL constraints |
| `SPARQL_QC_PROMPT` | Suggest QC queries |

#### `format_prompt(template: str, **kwargs) -> str`

Format a prompt template with values.

```python
from src.llm.prompts import CANDIDATE_GENERATION_PROMPT, format_prompt

prompt = format_prompt(
    CANDIDATE_GENERATION_PROMPT,
    source_iri="http://example.org/Dog",
    source_label="Dog",
    source_definition="A domesticated mammal",
    target_concepts="- Cat\n- Wolf",
)
```

---

### `src.llm.parsers`

Response parsing utilities.

#### Response Models

```python
class CandidateMapping(BaseModel):
    target_iri: str
    predicate: str
    confidence: float  # 0.0-1.0
    justification: str

class CandidateGenerationResponse(BaseModel):
    mappings: list[CandidateMapping]
    no_match_reason: Optional[str]

class ScoringResponse(BaseModel):
    scores: ScoreBreakdown
    overall_score: float
    recommended_predicate: Optional[str]
    reasoning: str

class MappingExplanation(BaseModel):
    summary: str
    evidence: list[str]
    caveats: list[str]
    alternatives_considered: list[AlternativeConsidered]
```

#### Parsing Functions

```python
from src.llm.parsers import parse_candidate_response, parse_scoring_response

# Parse LLM response
candidates = parse_candidate_response(llm_response.content)
scores = parse_scoring_response(llm_response.content)
```

---

## Ontology Module

### `src.ontology.loader`

#### `OntologyLoader`

Load ontologies from files or URLs.

```python
from src.ontology.loader import OntologyLoader

loader = OntologyLoader()

# Load from file
graph = loader.load("ontology.owl")

# Load from URL
graph = loader.load_from_url("http://example.org/ontology.owl")

# Merge multiple ontologies
merged = loader.merge([graph1, graph2])
```

#### `load_ontology(path: str, format: str = None) -> Graph`

Convenience function for loading.

```python
from src.ontology.loader import load_ontology

graph = load_ontology("my_ontology.ttl")
```

**Supported formats:** `.owl`, `.rdf`, `.xml`, `.ttl`, `.n3`, `.nt`, `.jsonld`

---

### `src.ontology.extractor`

#### `OntologyConcept`

Dataclass representing an extracted concept.

```python
@dataclass
class OntologyConcept:
    iri: str
    labels: list[str]
    definition: Optional[str]
    synonyms: list[str]
    parents: list[str]
    children: list[str]
    related: list[tuple[str, str]]
    deprecated: bool
    
    @property
    def primary_label(self) -> str
    
    @property
    def all_labels(self) -> list[str]
    
    def to_context_string(self) -> str
```

#### `ConceptExtractor`

Extract concepts from ontology graphs.

```python
from src.ontology.extractor import ConceptExtractor

extractor = ConceptExtractor(graph)

# Extract all concepts
concepts = extractor.extract_all_concepts()

# Extract single concept
concept = extractor.extract_concept("http://example.org/MyClass")

# Get vocabulary string for prompts
vocab = extractor.get_concept_vocabulary(max_concepts=100)
```

---

### `src.ontology.reasoner`

#### `OWLReasoner`

OWL reasoning capabilities.

```python
from src.ontology.reasoner import OWLReasoner, ReasonerType

reasoner = OWLReasoner(reasoner_type=ReasonerType.HERMIT)

# Check consistency
result = reasoner.check_consistency(graph)
print(f"Consistent: {result.is_consistent}")

# Classify (compute inferred hierarchy)
inference = reasoner.classify(graph)
print(f"New axioms: {inference.new_axioms_count}")

# Test entailment
is_entailed = reasoner.test_entailment(ontology_graph, axiom_graph)
```

#### `ConsistencyResult`

```python
@dataclass
class ConsistencyResult:
    is_consistent: bool
    unsatisfiable_classes: list[str]
    error_message: Optional[str]
```

---

## Mapping Module

### `src.mapping.candidate_generator`

#### `CandidateGenerator`

Generate mapping candidates using LLMs.

```python
from src.mapping.candidate_generator import CandidateGenerator

generator = CandidateGenerator()

# Generate all candidates
candidates = await generator.generate_candidates(
    source_graph,
    target_graph,
    min_confidence=0.7,
    batch_size=10,
)

# Generate for single concept
candidates = await generator.generate_single(concept, target_graph)
```

#### `MappingCandidate`

```python
@dataclass
class MappingCandidate:
    source_iri: str
    source_label: str
    target_iri: str
    target_label: str
    predicate: str
    confidence: float
    justification: str
```

---

### `src.mapping.scorer`

#### `MappingScorer`

Score mapping plausibility.

```python
from src.mapping.scorer import MappingScorer

scorer = MappingScorer(
    weights={
        "lexical": 0.2,
        "semantic": 0.3,
        "structural": 0.2,
        "llm": 0.3,
    }
)

scored = await scorer.score_candidates(
    candidates,
    source_definitions,
    target_definitions,
)
```

#### `ScoredMapping`

```python
@dataclass
class ScoredMapping:
    candidate: MappingCandidate
    lexical_score: float
    semantic_score: float
    structural_score: float
    llm_score: float
    combined_score: float
    recommended_predicate: Optional[str]
    reasoning: str
```

---

### `src.mapping.explainer`

#### `ExplanationGenerator`

Generate human-readable explanations.

```python
from src.mapping.explainer import ExplanationGenerator

explainer = ExplanationGenerator()

explained = await explainer.generate_explanations(
    candidates,
    source_context,
    target_context,
)
```

#### `ExplainedMapping`

```python
@dataclass
class ExplainedMapping:
    candidate: MappingCandidate
    summary: str
    evidence: list[str]
    caveats: list[str]
    alternatives_considered: list[tuple[str, str]]
```

---

### `src.mapping.sssom_writer`

#### `SSSOMWriter`

Write mappings in SSSOM format.

```python
from src.mapping.sssom_writer import SSSOMWriter, SSSOMMetadata

metadata = SSSOMMetadata(
    mapping_set_id="urn:example:mappings",
    mapping_set_title="My Mappings",
    creator_id="orcid:0000-0001-2345-6789",
)

writer = SSSOMWriter(metadata)
writer.write(mappings, "output.sssom.tsv")
```

#### `write_sssom(mappings, path, **kwargs)`

Convenience function.

```python
from src.mapping.sssom_writer import write_sssom

write_sssom(mappings, "output.sssom.tsv", title="My Mappings")
```

---

## Validation Module

### `src.validation.pipeline_validator`

#### `PipelineValidator`

End-to-end validation orchestrator.

```python
from src.validation.pipeline_validator import PipelineValidator

validator = PipelineValidator(
    run_reasoner=True,
    run_shacl=True,
    run_sparql=True,
    fail_on_inconsistency=True,
)

report = validator.validate(source_graph, target_graph, mapping_graph)

print(f"Valid: {report.is_valid}")
print(f"Errors: {report.error_count}")
print(f"Warnings: {report.warning_count}")
```

#### `ValidationReport`

```python
@dataclass
class ValidationReport:
    is_valid: bool
    consistency_result: Optional[ConsistencyResult]
    shacl_result: Optional[SHACLValidationResult]
    sparql_errors: list[SPARQLError]
    issues: list[ValidationIssue]
    
    @property
    def error_count(self) -> int
    
    @property
    def warning_count(self) -> int
    
    def to_dict(self) -> dict
```

---

## SHACL Module

### `src.shacl.validator`

#### `SHACLValidator`

Validate graphs against SHACL shapes.

```python
from src.shacl.validator import SHACLValidator

validator = SHACLValidator()
validator.load_shapes("shapes.ttl")

result = validator.validate(data_graph)
print(f"Conforms: {result.conforms}")

for violation in result.violations:
    print(f"  {violation.message}")
```

#### `validate_mappings(graph, shapes_path=None, use_defaults=True)`

Convenience function with default mapping shapes.

```python
from src.shacl.validator import validate_mappings

result = validate_mappings(mapping_graph)
```

---

### `src.shacl.shape_generator`

#### `ShapeGenerator`

Generate SHACL shapes using LLMs.

```python
from src.shacl.shape_generator import ShapeGenerator

generator = ShapeGenerator()

shapes = await generator.generate_shapes(
    domain_description="Biomedical ontology mappings",
    sample_mappings=[...],
    common_issues=["Missing metadata", "Invalid IRIs"],
)

for shape in shapes:
    print(f"{shape.name}: {shape.description}")
    print(shape.turtle)
```

---

## SPARQL Module

### `src.sparql.qc_queries`

#### Query Library

```python
from src.sparql.qc_queries import (
    QC_QUERY_LIBRARY,
    get_query,
    get_queries_by_category,
    get_queries_by_severity,
)

# Get specific query
query = get_query("circular_equivalence")
print(query.sparql)

# Get all error queries
errors = get_queries_by_severity("error")

# Get consistency queries
consistency = get_queries_by_category("consistency")
```

#### Available Categories

- `consistency` - Logical consistency checks
- `completeness` - Missing mapping checks
- `quality` - Quality and metadata checks
- `structure` - Structural validity checks

---

### `src.sparql.error_detector`

#### `ErrorDetector`

Run QC queries to detect errors.

```python
from src.sparql.error_detector import ErrorDetector

detector = ErrorDetector()

# Run all checks
errors = detector.run_all_checks(mapping_graph)

# Run specific check
error = detector.run_query(graph, "circular_equivalence")

# Run by severity
errors = detector.run_checks_by_severity(graph, min_severity="warning")
```

#### `SPARQLError`

```python
@dataclass
class SPARQLError:
    query_name: str
    description: str
    severity: str  # error, warning, info
    results: list[dict]
```

---

## CLI Tools

### `scripts/run_pipeline.py`

Main pipeline runner.

```bash
python scripts/run_pipeline.py \
    --source source.owl \
    --target target.owl \
    --output mappings.sssom.tsv \
    --min-confidence 0.7 \
    --validate \
    --explain
```

### `scripts/evaluate_mappings.py`

Evaluate mapping quality.

```bash
python scripts/evaluate_mappings.py \
    --predicted generated.sssom.tsv \
    --gold goldstandard.sssom.tsv \
    --output results.json \
    --curve
```

---

## Configuration

### `configs/pipeline_config.yaml`

```yaml
pipeline:
  batch_size: 50
  parallel_workers: 4
  cache_enabled: true

mapping:
  predicates: [owl:equivalentClass, skos:exactMatch, ...]
  min_confidence: 0.7
  require_explanation: true

validation:
  run_reasoner: true
  run_shacl: true
  run_sparql: true
```

### `configs/llm_config.yaml`

```yaml
provider: anthropic  # or openai, local

anthropic:
  api_key: ${ANTHROPIC_API_KEY}
  model: claude-sonnet-4-20250514
  temperature: 0.1

rate_limiting:
  requests_per_minute: 50
  tokens_per_minute: 100000
```
