#!/usr/bin/env python3
"""
File Integrity Checker

Checks for missing files in the ontology-mapping-pipeline project
and provides the content to recreate them.

Usage:
    python check_files.py           # Check for missing files
    python check_files.py --fix     # Show content for missing files
"""

import argparse
import sys
from pathlib import Path

# Get project root
PROJECT_ROOT = Path(__file__).parent.absolute()

# Required files and their descriptions
REQUIRED_FILES = {
    # Config files
    "configs/llm_config.yaml": "LLM configuration",
    "configs/pipeline_config.yaml": "Pipeline configuration",
    
    # Data files
    "data/ontologies/source_test.ttl": "Sample source ontology",
    "data/ontologies/target_test.ttl": "Sample target ontology",
    "data/shacl_shapes/mapping_shapes.ttl": "SHACL shapes for validation",
    
    # Source modules - LLM
    "src/__init__.py": "Main package init",
    "src/llm/__init__.py": "LLM module init",
    "src/llm/client.py": "LLM client implementations",
    "src/llm/prompts.py": "Prompt templates",
    "src/llm/parsers.py": "Response parsers",
    
    # Source modules - Ontology
    "src/ontology/__init__.py": "Ontology module init",
    "src/ontology/loader.py": "Ontology loader",
    "src/ontology/extractor.py": "Concept extractor",
    "src/ontology/reasoner.py": "OWL reasoner integration",
    
    # Source modules - Mapping
    "src/mapping/__init__.py": "Mapping module init",
    "src/mapping/candidate_generator.py": "Candidate generation",
    "src/mapping/scorer.py": "Mapping scorer",
    "src/mapping/explainer.py": "Explanation generator",
    "src/mapping/sssom_writer.py": "SSSOM output writer",
    
    # Source modules - Validation
    "src/validation/__init__.py": "Validation module init",
    "src/validation/pipeline_validator.py": "Pipeline validator",
    
    # Source modules - SHACL
    "src/shacl/__init__.py": "SHACL module init",
    "src/shacl/validator.py": "SHACL validator",
    "src/shacl/shape_generator.py": "Shape generator",
    
    # Source modules - SPARQL
    "src/sparql/__init__.py": "SPARQL module init",
    "src/sparql/error_detector.py": "Error detector",
    "src/sparql/qc_queries.py": "QC query library",
    
    # Scripts
    "scripts/__init__.py": "Scripts package init",
    "scripts/run_pipeline.py": "Main pipeline script",
    "scripts/evaluate_mappings.py": "Evaluation script",
    "scripts/test_installation.py": "Installation test",
    
    # Tests
    "tests/__init__.py": "Tests package init",
    "tests/conftest.py": "Pytest fixtures",
    "tests/test_llm_client.py": "LLM client tests",
    "tests/test_candidate_generator.py": "Candidate generator tests",
    "tests/test_validation.py": "Validation tests",
    
    # Project files
    "requirements.txt": "Python dependencies",
    "pyproject.toml": "Project configuration",
    "README.md": "Project readme",
    "docs/OUTLINE.md": "Implementation outline",
    "docs/API.md": "API documentation",
    "docs/GETTING_STARTED.md": "Getting started guide",
}

# File contents for critical missing files
FILE_CONTENTS = {
    "src/__init__.py": '''"""
Ontology Mapping Pipeline

A pipeline that uses LLMs to generate, evaluate, and validate ontology mappings.
"""

__version__ = "0.1.0"
__author__ = "Your Name"

# Note: Imports are intentionally not included here to avoid circular dependencies.
# Import directly from submodules:
#   from src.mapping.candidate_generator import CandidateGenerator
#   from src.ontology.loader import load_ontology
#   etc.
''',

    "src/ontology/__init__.py": '''"""
Ontology handling module.

Import directly from submodules:
    from src.ontology.loader import load_ontology, OntologyLoader
    from src.ontology.extractor import ConceptExtractor, OntologyConcept
    from src.ontology.reasoner import OWLReasoner
"""
''',

    "src/llm/__init__.py": '''"""
LLM integration module.

Import directly from submodules:
    from src.llm.client import LLMClient, create_llm_client, ClaudeClient
    from src.llm.prompts import CANDIDATE_GENERATION_PROMPT, format_prompt
    from src.llm.parsers import parse_candidate_response
"""
''',

    "src/mapping/__init__.py": '''"""
Mapping generation and scoring module.

Import directly from submodules:
    from src.mapping.candidate_generator import CandidateGenerator, MappingCandidate
    from src.mapping.scorer import MappingScorer, ScoredMapping
    from src.mapping.explainer import ExplanationGenerator
    from src.mapping.sssom_writer import write_sssom
"""
''',

    "src/validation/__init__.py": '''"""
Validation module.

Import directly from submodules:
    from src.validation.pipeline_validator import PipelineValidator, ValidationReport
"""
''',

    "src/shacl/__init__.py": '''"""
SHACL validation module.

Import directly from submodules:
    from src.shacl.validator import SHACLValidator, validate_mappings
    from src.shacl.shape_generator import ShapeGenerator
"""
''',

    "src/sparql/__init__.py": '''"""
SPARQL QC module.

Import directly from submodules:
    from src.sparql.error_detector import ErrorDetector, run_qc_checks
    from src.sparql.qc_queries import get_query, list_all_queries
"""
''',

    "scripts/__init__.py": '''"""Pipeline scripts."""
''',

    "tests/__init__.py": '''"""Test suite for ontology mapping pipeline."""
''',

    "configs/llm_config.yaml": '''# LLM Provider Configuration
# Set your API key via environment variable or directly here

provider: anthropic  # or openai

anthropic:
  api_key: ${ANTHROPIC_API_KEY}  # Set via environment variable
  model: "claude-sonnet-4-20250514"
  max_tokens: 4096
  temperature: 0.1
  timeout: 60

openai:
  api_key: ${OPENAI_API_KEY}
  model: "gpt-4-turbo"
  max_tokens: 4096
  temperature: 0.1
  timeout: 60

rate_limiting:
  enabled: true
  requests_per_minute: 50
  tokens_per_minute: 100000
  retry_attempts: 3
  retry_delay: 1.0
  backoff_multiplier: 2.0

caching:
  enabled: true
  cache_dir: ".cache/llm"
  ttl: 86400
  max_size_mb: 500
''',

    "configs/pipeline_config.yaml": '''# Pipeline Configuration

pipeline:
  batch_size: 50
  parallel_workers: 4
  cache_enabled: true
  cache_dir: ".cache/pipeline"
  log_level: INFO
  log_file: "logs/pipeline.log"

mapping:
  predicates:
    - "owl:equivalentClass"
    - "skos:exactMatch"
    - "skos:closeMatch"
    - "skos:broadMatch"
    - "skos:narrowMatch"
    - "skos:relatedMatch"
  min_confidence: 0.7
  high_confidence: 0.9
  require_explanation: true
  include_alternatives: false
  rewrite_labels: true
  extract_synonyms: true

scoring:
  weights:
    lexical_similarity: 0.2
    semantic_similarity: 0.3
    structural_similarity: 0.2
    llm_confidence: 0.3
  embedding_model: "all-MiniLM-L6-v2"

validation:
  run_reasoner: true
  reasoner: "hermit"
  reasoner_timeout: 300
  run_shacl: true
  shacl_shapes_dir: "data/shacl_shapes"
  generate_shapes: true
  run_sparql_qc: true
  sparql_queries_dir: "src/sparql/queries"
  fail_on_inconsistency: true
  fail_on_shacl_violation: false
  max_violations_allowed: 10

output:
  format: "sssom"
  compression: null
  mapping_tool: "ontology-mapping-pipeline"
  mapping_tool_version: "0.1.0"
  author_id: "orcid:0000-0000-0000-0000"
  generate_report: true
  report_format: "html"
''',

    "data/ontologies/source_test.ttl": '''@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix ex: <http://example.org/source#> .

<http://example.org/source> a owl:Ontology ;
    rdfs:label "Source Test Ontology" ;
    rdfs:comment "A simple test ontology for the mapping pipeline" .

ex:Animal a owl:Class ;
    rdfs:label "Animal" ;
    rdfs:comment "A living organism that feeds on organic matter" .

ex:Mammal a owl:Class ;
    rdfs:label "Mammal" ;
    rdfs:subClassOf ex:Animal ;
    rdfs:comment "A warm-blooded vertebrate with hair or fur" .

ex:Dog a owl:Class ;
    rdfs:label "Dog" ;
    rdfs:subClassOf ex:Mammal ;
    rdfs:comment "A domesticated carnivorous mammal" .

ex:Cat a owl:Class ;
    rdfs:label "Cat" ;
    rdfs:subClassOf ex:Mammal ;
    rdfs:comment "A small domesticated carnivorous mammal" .

ex:Bird a owl:Class ;
    rdfs:label "Bird" ;
    rdfs:subClassOf ex:Animal ;
    rdfs:comment "A warm-blooded egg-laying vertebrate with feathers" .

ex:Fish a owl:Class ;
    rdfs:label "Fish" ;
    rdfs:subClassOf ex:Animal ;
    rdfs:comment "A limbless cold-blooded vertebrate with gills" .
''',

    "data/ontologies/target_test.ttl": '''@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix tgt: <http://example.org/target#> .

<http://example.org/target> a owl:Ontology ;
    rdfs:label "Target Test Ontology" ;
    rdfs:comment "A simple test ontology to map against" .

tgt:Organism a owl:Class ;
    rdfs:label "Organism" ;
    rdfs:comment "A living entity" .

tgt:Vertebrate a owl:Class ;
    rdfs:label "Vertebrate" ;
    rdfs:subClassOf tgt:Organism ;
    rdfs:comment "An animal with a backbone" .

tgt:Canine a owl:Class ;
    rdfs:label "Canine" ;
    rdfs:subClassOf tgt:Vertebrate ;
    rdfs:comment "A member of the dog family Canidae" .

tgt:Feline a owl:Class ;
    rdfs:label "Feline" ;
    rdfs:subClassOf tgt:Vertebrate ;
    rdfs:comment "A member of the cat family Felidae" .

tgt:Avian a owl:Class ;
    rdfs:label "Avian" ;
    rdfs:subClassOf tgt:Vertebrate ;
    rdfs:comment "Relating to birds" .

tgt:Pisces a owl:Class ;
    rdfs:label "Pisces" ;
    rdfs:subClassOf tgt:Organism ;
    rdfs:comment "Fish - aquatic vertebrates with gills" .
''',

    "data/shacl_shapes/mapping_shapes.ttl": '''@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix skos: <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/shapes/> .

ex:MappingSubjectShape a sh:NodeShape ;
    sh:targetSubjectsOf owl:equivalentClass, skos:exactMatch, skos:closeMatch,
                        skos:broadMatch, skos:narrowMatch, skos:relatedMatch ;
    sh:name "Mapping Subject Shape" ;
    sh:nodeKind sh:IRI ;
    sh:message "Mapping subject must be a valid IRI" .

ex:MappingObjectShape a sh:NodeShape ;
    sh:targetObjectsOf owl:equivalentClass, skos:exactMatch, skos:closeMatch,
                       skos:broadMatch, skos:narrowMatch, skos:relatedMatch ;
    sh:name "Mapping Object Shape" ;
    sh:nodeKind sh:IRI ;
    sh:message "Mapping object must be a valid IRI" .
''',
}


def check_files():
    """Check for missing files."""
    missing = []
    present = []
    
    for file_path, description in REQUIRED_FILES.items():
        full_path = PROJECT_ROOT / file_path
        if full_path.exists():
            present.append(file_path)
        else:
            missing.append((file_path, description))
    
    return present, missing


def create_missing_file(file_path: str) -> bool:
    """Create a missing file if we have its content."""
    if file_path not in FILE_CONTENTS:
        return False
    
    full_path = PROJECT_ROOT / file_path
    full_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(full_path, 'w', encoding='utf-8') as f:
        f.write(FILE_CONTENTS[file_path])
    
    return True


def main():
    parser = argparse.ArgumentParser(description="Check for missing project files")
    parser.add_argument("--fix", action="store_true", help="Attempt to create missing files")
    parser.add_argument("--show", type=str, help="Show content for a specific file")
    args = parser.parse_args()
    
    print("=" * 60)
    print("  Ontology Mapping Pipeline - File Integrity Check")
    print("=" * 60)
    print(f"\nProject root: {PROJECT_ROOT}\n")
    
    if args.show:
        if args.show in FILE_CONTENTS:
            print(f"Content for {args.show}:\n")
            print("-" * 40)
            print(FILE_CONTENTS[args.show])
            print("-" * 40)
        else:
            print(f"No stored content for: {args.show}")
            print("\nAvailable files with stored content:")
            for f in sorted(FILE_CONTENTS.keys()):
                print(f"  - {f}")
        return 0
    
    present, missing = check_files()
    
    print(f"Files present: {len(present)}")
    print(f"Files missing: {len(missing)}")
    
    if missing:
        print("\n" + "=" * 60)
        print("  Missing Files")
        print("=" * 60 + "\n")
        
        can_fix = []
        cannot_fix = []
        
        for file_path, description in missing:
            if file_path in FILE_CONTENTS:
                can_fix.append((file_path, description))
                status = "[can auto-create]"
            else:
                cannot_fix.append((file_path, description))
                status = "[manual fix needed]"
            print(f"  ✗ {file_path}")
            print(f"      {description} {status}")
        
        if args.fix and can_fix:
            print("\n" + "=" * 60)
            print("  Creating Missing Files")
            print("=" * 60 + "\n")
            
            for file_path, description in can_fix:
                if create_missing_file(file_path):
                    print(f"  ✓ Created: {file_path}")
                else:
                    print(f"  ✗ Failed: {file_path}")
            
            print("\nRe-run this script to verify all files are present.")
        
        elif can_fix and not args.fix:
            print(f"\n{len(can_fix)} file(s) can be auto-created.")
            print("Run with --fix to create them:")
            print(f"  python {Path(__file__).name} --fix")
        
        if cannot_fix:
            print(f"\n{len(cannot_fix)} file(s) need manual restoration.")
            print("These are core source files that should be downloaded from the project.")
        
        return 1
    
    else:
        print("\n✓ All required files are present!")
        return 0


if __name__ == "__main__":
    sys.exit(main())
    