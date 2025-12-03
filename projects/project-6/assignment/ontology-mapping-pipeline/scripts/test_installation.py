#!/usr/bin/env python3
"""
Quick Test Script

Verifies that the basic components of the pipeline are working.
Run this first to check your installation before using the full pipeline.

Usage:
    python scripts/test_installation.py
"""

import sys
from pathlib import Path

# Setup path - add project root to sys.path
# This must happen BEFORE any src.* imports
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Verify the path is correct
if not (PROJECT_ROOT / "src").exists():
    print(f"ERROR: Could not find 'src' directory in {PROJECT_ROOT}")
    print("Make sure you're running from the project directory.")
    sys.exit(1)


def print_status(message: str, success: bool):
    """Print a status message with color."""
    status = "✓" if success else "✗"
    color = "\033[92m" if success else "\033[91m"
    reset = "\033[0m"
    print(f"{color}{status}{reset} {message}")

def test_imports():
    """Test that all modules can be imported."""
    print("\n=== Testing Imports ===\n")
    
    modules = [
        ("rdflib", "RDF library"),
        ("yaml", "YAML parser"),
        ("click", "CLI framework"),
        ("rich", "Rich console output"),
        ("pydantic", "Data validation"),
    ]
    
    all_passed = True
    for module, description in modules:
        try:
            __import__(module)
            print_status(f"{description} ({module})", True)
        except ImportError as e:
            print_status(f"{description} ({module}): {e}", False)
            all_passed = False
    
    # Test internal modules using importlib for proper nested imports
    import importlib
    
    internal_modules = [
        "src.ontology.loader",
        "src.ontology.extractor",
        "src.mapping.candidate_generator",
        "src.mapping.scorer",
        "src.mapping.sssom_writer",
        "src.validation.pipeline_validator",
        "src.shacl.validator",
        "src.sparql.error_detector",
        "src.llm.client",
        "src.llm.prompts",
    ]
    
    print("\n=== Testing Internal Modules ===\n")
    
    for module in internal_modules:
        try:
            importlib.import_module(module)
            print_status(module, True)
        except ImportError as e:
            print_status(f"{module}: {e}", False)
            all_passed = False
    
    return all_passed

def test_ontology_loading():
    """Test that we can load the sample ontologies."""
    print("\n=== Testing Ontology Loading ===\n")
    
    from src.ontology.loader import load_ontology
    from src.ontology.extractor import ConceptExtractor
    
    source_path = PROJECT_ROOT / "data" / "ontologies" / "source_test.ttl"
    target_path = PROJECT_ROOT / "data" / "ontologies" / "target_test.ttl"
    
    try:
        # Load source
        source = load_ontology(source_path)
        print_status(f"Loaded source ontology: {len(source)} triples", True)
        
        # Load target
        target = load_ontology(target_path)
        print_status(f"Loaded target ontology: {len(target)} triples", True)
        
        # Extract concepts
        extractor = ConceptExtractor(source)
        concepts = extractor.extract_all_concepts()
        print_status(f"Extracted {len(concepts)} concepts from source", True)
        
        print("\n  Source concepts:")
        for c in concepts:
            defn = c.definition[:40] + "..." if c.definition and len(c.definition) > 40 else c.definition
            print(f"    - {c.primary_label}: {defn or 'No definition'}")
        
        return True
        
    except Exception as e:
        print_status(f"Failed to load ontologies: {e}", False)
        return False

def test_sparql_queries():
    """Test that SPARQL QC queries work."""
    print("\n=== Testing SPARQL QC ===\n")
    
    from src.sparql.qc_queries import list_all_queries, get_query
    
    try:
        queries = list_all_queries()
        print_status(f"Loaded {len(queries)} QC queries", True)
        
        # Test one query
        query = get_query("circular_equivalence")
        if query:
            print_status(f"Sample query '{query.name}' loaded", True)
            print(f"    Description: {query.description}")
            print(f"    Severity: {query.severity}")
        
        return True
        
    except Exception as e:
        print_status(f"SPARQL QC test failed: {e}", False)
        return False

def test_llm_config():
    """Test LLM configuration (doesn't make actual API calls)."""
    print("\n=== Testing LLM Configuration ===\n")
    
    import os
    
    # Check for API keys
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    openai_key = os.environ.get("OPENAI_API_KEY")
    
    if anthropic_key:
        print_status("ANTHROPIC_API_KEY is set", True)
    else:
        print_status("ANTHROPIC_API_KEY not set (set it or use config file)", False)
    
    if openai_key:
        print_status("OPENAI_API_KEY is set", True)
    else:
        print_status("OPENAI_API_KEY not set (optional)", False)
    
    # Check config file
    config_path = PROJECT_ROOT / "configs" / "llm_config.yaml"
    if config_path.exists():
        print_status(f"Config file exists: {config_path}", True)
    else:
        print_status(f"Config file not found: {config_path}", False)
    
    return anthropic_key is not None or openai_key is not None

def main():
    """Run all tests."""
    print("=" * 60)
    print("  Ontology Mapping Pipeline - Installation Test")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Ontology Loading", test_ontology_loading()))
    results.append(("SPARQL QC", test_sparql_queries()))
    results.append(("LLM Config", test_llm_config()))
    
    print("\n" + "=" * 60)
    print("  Summary")
    print("=" * 60 + "\n")
    
    all_passed = True
    for name, passed in results:
        print_status(name, passed)
        if not passed:
            all_passed = False
    
    print()
    if all_passed:
        print("\033[92m✓ All tests passed! You're ready to run the pipeline.\033[0m")
        print("\nNext steps:")
        print("  1. Set your ANTHROPIC_API_KEY (if not already set)")
        print("  2. Run: python scripts/run_pipeline.py --help")
    else:
        print("\033[91m✗ Some tests failed. Please check the errors above.\033[0m")
        print("\nTry running: pip install -r requirements.txt")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())

    