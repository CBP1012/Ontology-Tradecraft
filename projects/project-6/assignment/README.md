# Ontology Mapping Pipeline with LLM Integration

A pipeline that leverages Large Language Models (LLMs) to generate, evaluate, and validate ontology mappings with automated quality control.

## Project Overview

This pipeline demonstrates how LLMs can enhance ontology mapping workflows by:
1. **Generating candidate mapping axioms** between source and target ontologies
2. **Rewriting labels and definitions** to improve semantic matching
3. **Producing mapping explanations** with human-readable rationales
4. **Scoring mapping plausibility** using confidence metrics
5. **Suggesting SHACL/SPARQL QC constraints** for mapping validation

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Ontology Mapping Pipeline                        │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────────┐  │
│  │   Source     │    │   Target     │    │   LLM Service        │  │
│  │   Ontology   │    │   Ontology   │    │   (Claude/GPT/etc)   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────────┬───────────┘  │
│         │                   │                       │              │
│         └─────────┬─────────┘                       │              │
│                   ▼                                 │              │
│         ┌─────────────────┐                         │              │
│         │ Label Extractor │◄────────────────────────┤              │
│         └────────┬────────┘                         │              │
│                  │                                  │              │
│                  ▼                                  │              │
│         ┌─────────────────┐                         │              │
│         │ LLM Candidate   │◄────────────────────────┤              │
│         │ Generator       │                         │              │
│         └────────┬────────┘                         │              │
│                  │                                  │              │
│                  ▼                                  │              │
│         ┌─────────────────┐                         │              │
│         │ Mapping Scorer  │◄────────────────────────┘              │
│         │ & Explainer     │                                        │
│         └────────┬────────┘                                        │
│                  │                                                 │
│                  ▼                                                 │
│         ┌─────────────────────────────────────────────────────┐   │
│         │              Validation Layer                        │   │
│         │  ┌───────────┐  ┌───────────┐  ┌─────────────────┐  │   │
│         │  │   OWL     │  │   SHACL   │  │    SPARQL QC    │  │   │
│         │  │ Reasoner  │  │ Validator │  │    Queries      │  │   │
│         │  └───────────┘  └───────────┘  └─────────────────┘  │   │
│         └────────┬────────────────────────────────────────────┘   │
│                  │                                                 │
│                  ▼                                                 │
│         ┌─────────────────┐                                        │
│         │ Validated       │                                        │
│         │ Mapping Output  │                                        │
│         └─────────────────┘                                        │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
ontology-mapping-pipeline/
├── README.md                     # This file
├── requirements.txt              # Python dependencies
├── pyproject.toml               # Project configuration
├── configs/
│   ├── pipeline_config.yaml     # Main pipeline configuration
│   └── llm_config.yaml          # LLM provider settings
├── src/
│   ├── __init__.py
│   ├── llm/                     # LLM integration modules
│   │   ├── __init__.py
│   │   ├── client.py            # Generic LLM client interface
│   │   ├── prompts.py           # Prompt templates for mapping tasks
│   │   └── parsers.py           # Response parsers
│   ├── ontology/                # Ontology handling
│   │   ├── __init__.py
│   │   ├── loader.py            # Load OWL/RDF ontologies
│   │   ├── extractor.py         # Extract labels, definitions, axioms
│   │   └── reasoner.py          # OWL reasoner integration
│   ├── mapping/                 # Core mapping logic
│   │   ├── __init__.py
│   │   ├── candidate_generator.py  # LLM-based mapping generation
│   │   ├── scorer.py            # Plausibility scoring
│   │   ├── explainer.py         # Rationale generation
│   │   └── sssom_writer.py      # Output in SSSOM format
│   ├── validation/              # Quality control
│   │   ├── __init__.py
│   │   ├── consistency_checker.py  # OWL consistency checks
│   │   ├── entailment_tester.py    # Cross-ontology inference
│   │   └── pipeline_validator.py   # End-to-end validation
│   ├── shacl/                   # SHACL constraints
│   │   ├── __init__.py
│   │   ├── shape_generator.py   # LLM-assisted shape generation
│   │   └── validator.py         # SHACL validation runner
│   └── sparql/                  # SPARQL QC
│       ├── __init__.py
│       ├── qc_queries.py        # Quality control queries
│       └── error_detector.py    # Mapping error identification
├── data/
│   ├── ontologies/              # Sample ontologies for testing
│   ├── mappings/                # Generated/validated mappings
│   └── shacl_shapes/            # SHACL shape files
├── tests/
│   ├── __init__.py
│   ├── test_llm_client.py
│   ├── test_candidate_generator.py
│   ├── test_validation.py
│   └── conftest.py              # Pytest fixtures
├── scripts/
│   ├── run_pipeline.py          # Main CLI entry point
│   └── evaluate_mappings.py     # Evaluation utilities
└── docs/
    ├── OUTLINE.md               # Detailed implementation outline
    └── API.md                   # API documentation
```

## Key Components

### 1. LLM Integration (`src/llm/`)
- Abstract client supporting multiple LLM providers (Claude, GPT, local models)
- Carefully designed prompts for ontology mapping tasks
- Structured output parsing for reliable extraction

### 2. Candidate Generation (`src/mapping/candidate_generator.py`)
- Extracts concepts from source/target ontologies
- Uses LLM to propose equivalent/related mappings
- Supports different mapping predicates (skos:exactMatch, owl:equivalentClass, etc.)

### 3. Scoring & Explanation (`src/mapping/scorer.py`, `explainer.py`)
- LLM-based confidence scoring (0-1)
- Human-readable rationales for each mapping
- Uncertainty quantification

### 4. Validation Layer (`src/validation/`)
- **OWL Reasoner**: HermiT/Pellet integration for consistency checking
- **SHACL**: Custom shapes to enforce mapping constraints
- **SPARQL QC**: Queries to detect common mapping errors

### 5. CI/CD Integration (`scripts/`, GitHub Actions)
- Automated validation on mapping changes
- Regression testing for mapping quality
- Report generation

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Configure LLM provider
cp configs/llm_config.yaml.example configs/llm_config.yaml
# Edit llm_config.yaml with your API keys

# Run the pipeline
python scripts/run_pipeline.py \
    --source data/ontologies/source.owl \
    --target data/ontologies/target.owl \
    --output data/mappings/result.sssom.tsv
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1)
- [ ] Set up project structure and dependencies
- [ ] Implement LLM client abstraction
- [ ] Create ontology loader and label extractor

### Phase 2: Mapping Generation (Week 2)
- [ ] Design and test prompts for candidate generation
- [ ] Implement label/definition rewriting
- [ ] Build SSSOM output writer

### Phase 3: Scoring & Explanation (Week 3)
- [ ] Implement plausibility scorer
- [ ] Add explanation/rationale generation
- [ ] Create confidence calibration

### Phase 4: Validation (Week 4)
- [ ] Integrate OWL reasoner (HermiT/Pellet)
- [ ] Implement SHACL shape generator and validator
- [ ] Build SPARQL QC query library

### Phase 5: CI/CD & Polish (Week 5)
- [ ] Set up GitHub Actions workflow
- [ ] Add comprehensive tests
- [ ] Documentation and examples

## License

MIT License - See LICENSE file
