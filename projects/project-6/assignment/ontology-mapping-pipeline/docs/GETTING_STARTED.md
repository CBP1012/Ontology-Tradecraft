# Getting Started Guide

This guide walks you through setting up and running the Ontology Mapping Pipeline.

## Step 1: Install Dependencies

```bash
# Navigate to the project directory
cd ontology-mapping-pipeline

# Create a virtual environment (recommended)
python -m venv venv

# Activate the virtual environment
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Configure LLM Provider

Copy the example config and add your API key:

```bash
# The config file is already created, just edit it
# configs/llm_config.yaml
```

Edit `configs/llm_config.yaml` and set your API key:

```yaml
provider: anthropic  # or openai

anthropic:
  api_key: "your-anthropic-api-key-here"  # Or set ANTHROPIC_API_KEY env var
  model: "claude-sonnet-4-20250514"
```

Or set the environment variable:

```bash
# Windows
set ANTHROPIC_API_KEY=your-api-key-here

# macOS/Linux
export ANTHROPIC_API_KEY=your-api-key-here
```

## Step 3: Prepare Sample Ontologies

Create two small test ontologies to verify the setup works:

**Source ontology** (`data/ontologies/source_test.ttl`):
```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix ex: <http://example.org/source#> .

ex:Animal a owl:Class ;
    rdfs:label "Animal" ;
    rdfs:comment "A living organism that feeds on organic matter" .

ex:Dog a owl:Class ;
    rdfs:label "Dog" ;
    rdfs:subClassOf ex:Animal ;
    rdfs:comment "A domesticated carnivorous mammal" .

ex:Cat a owl:Class ;
    rdfs:label "Cat" ;
    rdfs:subClassOf ex:Animal ;
    rdfs:comment "A small domesticated feline" .
```

**Target ontology** (`data/ontologies/target_test.ttl`):
```turtle
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix tgt: <http://example.org/target#> .

tgt:Organism a owl:Class ;
    rdfs:label "Organism" ;
    rdfs:comment "A living entity" .

tgt:Canine a owl:Class ;
    rdfs:label "Canine" ;
    rdfs:subClassOf tgt:Organism ;
    rdfs:comment "A member of the dog family Canidae" .

tgt:Feline a owl:Class ;
    rdfs:label "Feline" ;
    rdfs:subClassOf tgt:Organism ;
    rdfs:comment "A member of the cat family Felidae" .
```

## Step 4: Run a Quick Test (No LLM Required)

First, verify the basic components work without needing an LLM:

```bash
python -c "
import sys
sys.path.insert(0, '.')

from src.ontology.loader import load_ontology
from src.ontology.extractor import ConceptExtractor

# Load ontologies
source = load_ontology('data/ontologies/source_test.ttl')
target = load_ontology('data/ontologies/target_test.ttl')

print(f'Source triples: {len(source)}')
print(f'Target triples: {len(target)}')

# Extract concepts
extractor = ConceptExtractor(source)
concepts = extractor.extract_all_concepts()

print(f'\nSource concepts found: {len(concepts)}')
for c in concepts:
    print(f'  - {c.primary_label}: {c.definition[:50] if c.definition else \"No definition\"}...')
"
```

## Step 5: Run the Full Pipeline

Once your API key is configured:

```bash
python scripts/run_pipeline.py \
    --source data/ontologies/source_test.ttl \
    --target data/ontologies/target_test.ttl \
    --output data/mappings/test_mappings.sssom.tsv \
    --min-confidence 0.5
```

## Step 6: View Results

The output will be in SSSOM format:

```bash
# View the generated mappings
cat data/mappings/test_mappings.sssom.tsv
```

## Troubleshooting

### Import Errors

If you see `ModuleNotFoundError`, make sure you're running from the project root:

```bash
cd ontology-mapping-pipeline
python scripts/run_pipeline.py ...
```

### API Key Issues

If you see authentication errors:

```bash
# Check if env var is set
echo $ANTHROPIC_API_KEY  # Linux/macOS
echo %ANTHROPIC_API_KEY%  # Windows

# Or hardcode in config (not recommended for production)
```

### Missing Dependencies

```bash
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

## Next Steps

1. **Try with real ontologies** - Download ontologies from sources like:
   - [OBO Foundry](http://obofoundry.org/)
   - [BioPortal](https://bioportal.bioontology.org/)

2. **Customize the pipeline** - Edit `configs/pipeline_config.yaml` to adjust:
   - Confidence thresholds
   - Mapping predicates
   - Validation settings

3. **Evaluate results** - If you have gold standard mappings:
   ```bash
   python scripts/evaluate_mappings.py \
       --predicted data/mappings/test_mappings.sssom.tsv \
       --gold data/mappings/gold_standard.sssom.tsv
   ```

4. **Run validation only** - Check existing mappings:
   ```bash
   python -c "
   from src.sparql.error_detector import ErrorDetector, run_qc_checks
   from src.ontology.loader import load_ontology
   
   mappings = load_ontology('data/mappings/your_mappings.ttl')
   errors = run_qc_checks(mappings)
   
   for e in errors:
       print(f'{e.severity}: {e.query_name} - {len(e.results)} issues')
   "
   ```
