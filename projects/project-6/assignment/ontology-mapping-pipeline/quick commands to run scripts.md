# Use default test ontologies
python scripts/demo_pipeline.py

# Specify custom ontology files
python scripts/demo_pipeline.py -s data/ontologies/source_test.ttl -t data/ontologies/target_test.ttl


# Short form
python scripts/demo_pipeline.py -s onto1.ttl -t onto2.ttl

# Specify output directory
python scripts/demo_pipeline.py -s source.ttl -t target.ttl -o ./results/

# Run without pauses (batch mode)
python scripts/demo_pipeline.py -s source.ttl -t target.ttl --no-interactive

# Set minimum confidence threshold
python scripts/demo_pipeline.py --min-confidence 0.5

# Skip OWL reasoner (if Java not installed)
python scripts/demo_pipeline.py --skip-reasoner

# Combine options
python scripts/demo_pipeline.py -s gene_ontology.ttl -t mesh.ttl -o ./output/ --min-confidence 0.6 --no-interactive
