# Detailed Implementation Outline

## 1. LLM Integration Module

### 1.1 LLM Client (`src/llm/client.py`)

**Purpose**: Provide a unified interface for interacting with different LLM providers.

**Key Classes**:
```python
class LLMClient(ABC):
    """Abstract base class for LLM providers"""
    @abstractmethod
    async def complete(self, prompt: str, **kwargs) -> LLMResponse
    
class ClaudeClient(LLMClient):
    """Anthropic Claude implementation"""
    
class OpenAIClient(LLMClient):
    """OpenAI GPT implementation"""
    
class LocalClient(LLMClient):
    """Local model support (Ollama, vLLM)"""
```

**Features**:
- Async/await support for parallel processing
- Retry logic with exponential backoff
- Token counting and rate limiting
- Response caching for reproducibility

### 1.2 Prompt Templates (`src/llm/prompts.py`)

**Prompt Categories**:

1. **Candidate Generation Prompt**
   - Input: Source concept (label, definition, hierarchy), Target ontology context
   - Output: List of candidate target concepts with mapping predicates

2. **Label Rewriting Prompt**
   - Input: Original label/definition
   - Output: Normalized, disambiguated version

3. **Explanation Generation Prompt**
   - Input: Mapping triple, source/target context
   - Output: Human-readable rationale

4. **Plausibility Scoring Prompt**
   - Input: Mapping with context
   - Output: Confidence score + reasoning

5. **SHACL Suggestion Prompt**
   - Input: Ontology domain patterns
   - Output: SHACL shape definitions

### 1.3 Response Parsers (`src/llm/parsers.py`)

**Parsing Strategies**:
- JSON structured output parsing
- Fallback regex extraction
- Validation against expected schema
- Error recovery and retry

---

## 2. Ontology Handling Module

### 2.1 Ontology Loader (`src/ontology/loader.py`)

**Supported Formats**:
- OWL/XML
- RDF/XML
- Turtle (.ttl)
- N-Triples

**Key Functions**:
```python
def load_ontology(path: str) -> Graph
def merge_ontologies(graphs: List[Graph]) -> Graph
def extract_namespace_prefixes(graph: Graph) -> Dict[str, str]
```

**Libraries**: rdflib, owlready2

### 2.2 Concept Extractor (`src/ontology/extractor.py`)

**Extracted Information**:
- Class IRIs and labels (rdfs:label, skos:prefLabel)
- Definitions (rdfs:comment, skos:definition, obo:IAO_0000115)
- Synonyms (skos:altLabel, oboInOwl:hasExactSynonym)
- Hierarchical position (rdfs:subClassOf chains)
- Related concepts (object properties, equivalence)

**Output Format**:
```python
@dataclass
class OntologyConcept:
    iri: str
    labels: List[str]
    definition: Optional[str]
    synonyms: List[str]
    parents: List[str]
    children: List[str]
    related: List[Tuple[str, str]]  # (predicate, target)
```

### 2.3 OWL Reasoner (`src/ontology/reasoner.py`)

**Supported Reasoners**:
- HermiT (via owlready2 or Java bridge)
- Pellet (via Java bridge)
- ELK (for EL++ reasoning)

**Key Operations**:
```python
def check_consistency(ontology: Graph) -> bool
def classify(ontology: Graph) -> Graph  # Inferred hierarchy
def get_unsatisfiable_classes(ontology: Graph) -> List[str]
def test_entailment(ontology: Graph, axiom: str) -> bool
```

---

## 3. Mapping Generation Module

### 3.1 Candidate Generator (`src/mapping/candidate_generator.py`)

**Algorithm**:
1. Extract all concepts from source ontology
2. For each source concept:
   a. Build context (label, definition, parents, related terms)
   b. Query LLM with target ontology vocabulary
   c. Parse candidate mappings from response
   d. Apply initial filtering (e.g., syntactic similarity threshold)

**Mapping Types Supported**:
- `owl:equivalentClass` - Logical equivalence
- `skos:exactMatch` - Exact semantic match
- `skos:closeMatch` - Similar but not identical
- `skos:broadMatch` - Source is narrower than target
- `skos:narrowMatch` - Source is broader than target
- `skos:relatedMatch` - Related but different

**Batching Strategy**:
- Group concepts by domain/branch for context coherence
- Limit batch size based on LLM context window
- Parallel processing with async calls

### 3.2 Plausibility Scorer (`src/mapping/scorer.py`)

**Scoring Dimensions**:
1. **Lexical Similarity** (0-1): Label/synonym overlap
2. **Semantic Similarity** (0-1): Definition embedding cosine similarity
3. **Structural Similarity** (0-1): Hierarchy position alignment
4. **LLM Confidence** (0-1): Model's self-assessed certainty
5. **Combined Score**: Weighted average with learned weights

**Confidence Calibration**:
- Use held-out gold standard mappings for calibration
- Platt scaling for probability calibration
- Output calibrated confidence intervals

### 3.3 Explanation Generator (`src/mapping/explainer.py`)

**Explanation Components**:
1. **Summary**: One-line mapping description
2. **Evidence**: Specific supporting facts from ontologies
3. **Caveats**: Potential issues or limitations
4. **Alternatives**: Other considered mappings and why rejected

**Output Format**:
```python
@dataclass
class MappingExplanation:
    summary: str
    evidence: List[str]
    caveats: List[str]
    alternatives: List[Tuple[str, str]]  # (mapping, rejection_reason)
```

### 3.4 SSSOM Writer (`src/mapping/sssom_writer.py`)

**SSSOM Columns**:
- subject_id, subject_label
- predicate_id
- object_id, object_label
- mapping_justification
- confidence
- comment (explanation)
- author_id, mapping_tool

**Features**:
- YAML metadata header
- TSV body
- Curie compression
- Validation against SSSOM schema

---

## 4. Validation Module

### 4.1 Consistency Checker (`src/validation/consistency_checker.py`)

**Validation Steps**:
1. Load source + target ontologies
2. Add proposed mapping axioms
3. Run reasoner consistency check
4. Identify minimal unsatisfiable subsets
5. Report problematic mappings

**Output**:
```python
@dataclass
class ConsistencyReport:
    is_consistent: bool
    unsatisfiable_classes: List[str]
    problematic_mappings: List[Mapping]
    explanation: str
```

### 4.2 Entailment Tester (`src/validation/entailment_tester.py`)

**Test Categories**:
1. **Expected Entailments**: Things that should be true after mapping
2. **Unexpected Entailments**: Things that shouldn't become true
3. **Transitivity Tests**: Cross-mapping inference chains

**Test Definition Format** (YAML):
```yaml
entailment_tests:
  - name: "Gene-Protein transitivity"
    given_mappings:
      - "source:Gene owl:equivalentClass target:Gene"
    expected_true:
      - "source:GeneExpression rdfs:subClassOf target:BiologicalProcess"
    expected_false:
      - "source:Gene owl:equivalentClass target:Protein"
```

### 4.3 Pipeline Validator (`src/validation/pipeline_validator.py`)

**End-to-End Validation**:
1. Run all validation components
2. Aggregate results
3. Generate summary report
4. Return pass/fail status for CI

---

## 5. SHACL Module

### 5.1 Shape Generator (`src/shacl/shape_generator.py`)

**LLM-Assisted Shape Generation**:
1. Analyze ontology patterns
2. Generate domain-appropriate constraints
3. Convert LLM output to valid SHACL

**Common Constraint Types**:
- Cardinality constraints (sh:minCount, sh:maxCount)
- Value type constraints (sh:class, sh:datatype)
- Pattern constraints (sh:pattern for IRI formats)
- Mapping-specific constraints (custom shapes)

**Example Generated Shape**:
```turtle
ex:MappingShape a sh:NodeShape ;
    sh:targetClass sssom:Mapping ;
    sh:property [
        sh:path sssom:subject_id ;
        sh:minCount 1 ;
        sh:maxCount 1 ;
        sh:pattern "^[A-Z]+:[0-9]+$" ;
    ] ;
    sh:property [
        sh:path sssom:confidence ;
        sh:minInclusive 0.0 ;
        sh:maxInclusive 1.0 ;
    ] .
```

### 5.2 SHACL Validator (`src/shacl/validator.py`)

**Features**:
- Load shapes from files
- Validate mapping graph against shapes
- Generate human-readable violation reports
- Integration with pySHACL

---

## 6. SPARQL QC Module

### 6.1 QC Query Library (`src/sparql/qc_queries.py`)

**Query Categories**:

1. **Completeness Checks**:
   - Unmapped high-importance concepts
   - Missing required metadata

2. **Consistency Checks**:
   - Conflicting mapping predicates
   - Circular mappings
   - Reflexive mappings

3. **Quality Checks**:
   - Low-confidence mappings
   - Missing explanations
   - Unusual predicate usage

**Example Query**:
```sparql
# Find circular mappings
SELECT ?a ?b WHERE {
    ?a owl:equivalentClass ?b .
    ?b owl:equivalentClass ?a .
    FILTER(?a != ?b)
}
```

### 6.2 Error Detector (`src/sparql/error_detector.py`)

**Features**:
- Run query library against mapping graph
- Categorize errors by severity
- Generate actionable error reports
- Suggest fixes using LLM

---

## 7. CI/CD Integration

### 7.1 GitHub Actions Workflow

**Triggers**:
- Push to main/develop branches
- Pull requests with mapping changes
- Scheduled weekly validation

**Jobs**:
1. **lint**: Check mapping file syntax
2. **validate**: Run full validation pipeline
3. **test**: Run unit and integration tests
4. **report**: Generate and publish quality report

### 7.2 Validation Script (`scripts/run_pipeline.py`)

**CLI Interface**:
```bash
python run_pipeline.py \
    --source ontologies/source.owl \
    --target ontologies/target.owl \
    --output mappings/output.sssom.tsv \
    --validate \
    --explain \
    --ci-mode
```

**Exit Codes**:
- 0: Success, all validations passed
- 1: Validation failures
- 2: Configuration error
- 3: Runtime error

---

## 8. Testing Strategy

### 8.1 Unit Tests
- Mock LLM responses for deterministic testing
- Test individual components in isolation
- Coverage target: 80%+

### 8.2 Integration Tests
- End-to-end pipeline with small test ontologies
- Known gold-standard mapping comparisons
- Performance benchmarks

### 8.3 Evaluation Metrics
- Precision, Recall, F1 against gold standard
- Mapping quality scores distribution
- Processing time per concept
- LLM token usage and cost

---

## 9. Configuration

### 9.1 Pipeline Config (`configs/pipeline_config.yaml`)

```yaml
pipeline:
  batch_size: 50
  parallel_workers: 4
  cache_enabled: true
  
mapping:
  predicates: [owl:equivalentClass, skos:exactMatch, skos:closeMatch]
  min_confidence: 0.7
  require_explanation: true
  
validation:
  run_reasoner: true
  reasoner: hermit
  run_shacl: true
  run_sparql_qc: true
  fail_on_inconsistency: true
```

### 9.2 LLM Config (`configs/llm_config.yaml`)

```yaml
provider: anthropic  # or openai, local
model: claude-sonnet-4-20250514
temperature: 0.1
max_tokens: 4096
timeout: 30

# Rate limiting
requests_per_minute: 50
tokens_per_minute: 100000

# Caching
cache_responses: true
cache_dir: .cache/llm
```
