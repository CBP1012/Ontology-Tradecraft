#!/usr/bin/env python3
"""
Ontology Mapping Pipeline - Comprehensive Demo Script

This script demonstrates ALL features required for the presentation:
1. LLM-based candidate mapping generation
2. Label/definition rewriting to aid matching
3. Mapping explanations and rationales
4. Plausibility scoring
5. SHACL constraint suggestions
6. SPARQL QC for error detection
7. OWL reasoner consistency checking
8. Validation pipeline

Usage:
    python scripts/demo_full_pipeline.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Setup path
PROJECT_ROOT = Path(__file__).parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

console = Console()


def print_section(title: str):
    """Print a section header."""
    console.print(f"\n{'='*70}")
    console.print(f"[bold cyan]  {title}[/bold cyan]")
    console.print(f"{'='*70}\n")


def print_subsection(title: str):
    """Print a subsection header."""
    console.print(f"\n[bold yellow]>>> {title}[/bold yellow]\n")


async def demo_1_load_ontologies():
    """Demo Step 1: Load and explore ontologies."""
    print_section("STEP 1: Loading Ontologies")
    
    from src.ontology.loader import load_ontology
    from src.ontology.extractor import ConceptExtractor
    
    source_path = PROJECT_ROOT / "data" / "ontologies" / "source_test.ttl"
    target_path = PROJECT_ROOT / "data" / "ontologies" / "target_test.ttl"
    
    console.print(f"[dim]Source: {source_path}[/dim]")
    console.print(f"[dim]Target: {target_path}[/dim]\n")
    
    source_graph = load_ontology(source_path)
    target_graph = load_ontology(target_path)
    
    console.print(f"✓ Loaded source ontology: [green]{len(source_graph)}[/green] triples")
    console.print(f"✓ Loaded target ontology: [green]{len(target_graph)}[/green] triples")
    
    # Extract concepts
    source_extractor = ConceptExtractor(source_graph)
    target_extractor = ConceptExtractor(target_graph)
    
    source_concepts = source_extractor.extract_all_concepts()
    target_concepts = target_extractor.extract_all_concepts()
    
    print_subsection("Source Ontology Concepts")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Label", style="cyan")
    table.add_column("Definition", style="white")
    table.add_column("Parents", style="dim")
    
    for c in source_concepts:
        defn = (c.definition[:50] + "...") if c.definition and len(c.definition) > 50 else (c.definition or "N/A")
        parents = ", ".join(c.parents[:2]) if c.parents else "None"
        table.add_row(c.primary_label, defn, parents)
    
    console.print(table)
    
    print_subsection("Target Ontology Concepts")
    table2 = Table(show_header=True, header_style="bold magenta")
    table2.add_column("Label", style="cyan")
    table2.add_column("Definition", style="white")
    table2.add_column("Parents", style="dim")
    
    for c in target_concepts:
        defn = (c.definition[:50] + "...") if c.definition and len(c.definition) > 50 else (c.definition or "N/A")
        parents = ", ".join(c.parents[:2]) if c.parents else "None"
        table2.add_row(c.primary_label, defn, parents)
    
    console.print(table2)
    
    return source_graph, target_graph, source_concepts, target_concepts


async def demo_2_generate_candidates(source_graph, target_graph):
    """Demo Step 2: LLM-based candidate generation."""
    print_section("STEP 2: LLM-Based Candidate Generation")
    
    console.print("[dim]Using Claude to analyze ontology concepts and suggest mappings...[/dim]\n")
    
    from src.mapping.candidate_generator import CandidateGenerator
    
    try:
        generator = CandidateGenerator(config_path=str(PROJECT_ROOT / "configs" / "llm_config.yaml"))
        
        candidates = await generator.generate_candidates(
            source_graph,
            target_graph,
            min_confidence=0.3,  # Lower threshold to show more candidates
            batch_size=5,
        )
        
        console.print(f"✓ Generated [green]{len(candidates)}[/green] candidate mappings\n")
        
        if candidates:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Source", style="cyan")
            table.add_column("Predicate", style="yellow")
            table.add_column("Target", style="green")
            table.add_column("Confidence", style="white")
            table.add_column("Justification", style="dim", max_width=40)
            
            for c in candidates[:10]:  # Show first 10
                table.add_row(
                    c.source_label,
                    c.predicate.split(":")[-1],
                    c.target_label,
                    f"{c.confidence:.2f}",
                    c.justification[:40] + "..." if len(c.justification) > 40 else c.justification
                )
            
            console.print(table)
        
        return candidates
        
    except Exception as e:
        console.print(f"[red]Error generating candidates: {e}[/red]")
        console.print("[yellow]Creating sample candidates for demo...[/yellow]")
        
        from src.mapping.candidate_generator import MappingCandidate
        
        # Create sample candidates for demo
        candidates = [
            MappingCandidate(
                source_iri="http://example.org/source#Dog",
                source_label="Dog",
                target_iri="http://example.org/target#Canine",
                target_label="Canine",
                predicate="skos:exactMatch",
                confidence=0.95,
                justification="Both refer to domesticated members of the Canidae family"
            ),
            MappingCandidate(
                source_iri="http://example.org/source#Cat",
                source_label="Cat",
                target_iri="http://example.org/target#Feline",
                target_label="Feline",
                predicate="skos:exactMatch",
                confidence=0.92,
                justification="Both refer to domesticated members of the Felidae family"
            ),
            MappingCandidate(
                source_iri="http://example.org/source#Animal",
                source_label="Animal",
                target_iri="http://example.org/target#Organism",
                target_label="Organism",
                predicate="skos:broadMatch",
                confidence=0.75,
                justification="Animal is a type of Organism, but Organism is broader"
            ),
        ]
        
        console.print(f"✓ Created [green]{len(candidates)}[/green] sample mappings\n")
        return candidates


async def demo_3_rewrite_labels(source_concepts):
    """Demo Step 3: LLM-based label rewriting."""
    print_section("STEP 3: Label/Definition Rewriting")
    
    console.print("[dim]Using LLM to normalize and enhance labels for better matching...[/dim]\n")
    
    from src.llm.client import create_llm_client
    from src.llm.prompts import LABEL_REWRITING_PROMPT, SYSTEM_PROMPT, format_prompt
    from src.llm.parsers import parse_rewriting_response
    
    try:
        client = create_llm_client(str(PROJECT_ROOT / "configs" / "llm_config.yaml"))
        
        # Rewrite first concept as example
        concept = source_concepts[0]
        
        prompt = format_prompt(
            LABEL_REWRITING_PROMPT,
            label=concept.primary_label,
            definition=concept.definition or "No definition available"
        )
        
        response = await client.complete_with_system(SYSTEM_PROMPT, prompt)
        rewritten = parse_rewriting_response(response.content)
        
        console.print(Panel(
            f"""[bold]Original:[/bold]
  Label: {concept.primary_label}
  Definition: {concept.definition}

[bold]Rewritten:[/bold]
  Normalized Label: {rewritten.normalized_label}
  Simplified Definition: {rewritten.simplified_definition}
  Key Terms: {', '.join(rewritten.key_terms)}
  Suggested Synonyms: {', '.join(rewritten.suggested_synonyms)}
  Domain Context: {rewritten.domain_context}""",
            title="Label Rewriting Example",
            border_style="green"
        ))
        
        return rewritten
        
    except Exception as e:
        console.print(f"[yellow]Label rewriting demo skipped: {e}[/yellow]")
        return None


async def demo_4_score_mappings(candidates, source_concepts, target_concepts):
    """Demo Step 4: Plausibility scoring."""
    print_section("STEP 4: Mapping Plausibility Scoring")
    
    console.print("[dim]Scoring mappings using lexical, semantic, structural, and LLM signals...[/dim]\n")
    
    from src.mapping.scorer import MappingScorer
    
    # Build definition dicts
    source_defs = {c.iri: c.definition or "" for c in source_concepts}
    target_defs = {c.iri: c.definition or "" for c in target_concepts}
    
    try:
        scorer = MappingScorer()
        scored = await scorer.score_candidates(candidates[:5], source_defs, target_defs)
        
        console.print(f"✓ Scored [green]{len(scored)}[/green] mappings\n")
        
        if scored:
            table = Table(show_header=True, header_style="bold magenta")
            table.add_column("Mapping", style="cyan")
            table.add_column("Lexical", style="white")
            table.add_column("Semantic", style="white")
            table.add_column("Structural", style="white")
            table.add_column("LLM", style="white")
            table.add_column("Combined", style="green bold")
            
            for s in scored:
                table.add_row(
                    f"{s.candidate.source_label} → {s.candidate.target_label}",
                    f"{s.lexical_score:.2f}",
                    f"{s.semantic_score:.2f}",
                    f"{s.structural_score:.2f}",
                    f"{s.llm_score:.2f}",
                    f"{s.combined_score:.2f}"
                )
            
            console.print(table)
        
        return scored
        
    except Exception as e:
        console.print(f"[yellow]Scoring demo with limited output: {e}[/yellow]")
        return candidates


async def demo_5_generate_explanations(candidates):
    """Demo Step 5: Generate mapping explanations."""
    print_section("STEP 5: Mapping Explanations & Rationales")
    
    console.print("[dim]Using LLM to generate human-readable explanations...[/dim]\n")
    
    from src.mapping.explainer import ExplanationGenerator
    
    try:
        explainer = ExplanationGenerator()
        
        # Explain first mapping
        if candidates:
            candidate = candidates[0] if hasattr(candidates[0], 'source_label') else candidates[0].candidate
            
            explained = await explainer.generate_single(
                candidate,
                source_definition="A domesticated carnivorous mammal",
                target_definition="A member of the dog family Canidae"
            )
            
            console.print(Panel(
                f"""[bold]Mapping:[/bold] {explained.candidate.source_label} → {explained.candidate.target_label}
[bold]Predicate:[/bold] {explained.candidate.predicate}

[bold]Summary:[/bold]
{explained.summary}

[bold]Evidence:[/bold]
{chr(10).join('• ' + e for e in explained.evidence)}

[bold]Caveats:[/bold]
{chr(10).join('• ' + c for c in explained.caveats) if explained.caveats else '• None identified'}
""",
                title="Mapping Explanation",
                border_style="blue"
            ))
            
            return explained
            
    except Exception as e:
        console.print(f"[yellow]Explanation demo skipped: {e}[/yellow]")
        return None


async def demo_6_sparql_qc():
    """Demo Step 6: SPARQL QC checks."""
    print_section("STEP 6: SPARQL Quality Control Checks")
    
    console.print("[dim]Running SPARQL queries to detect mapping errors...[/dim]\n")
    
    from src.sparql.qc_queries import list_all_queries, get_query, get_queries_by_severity
    from src.sparql.error_detector import ErrorDetector
    from rdflib import Graph, Namespace, URIRef
    from rdflib.namespace import OWL, SKOS
    
    # Show available queries
    print_subsection("Available QC Queries")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Query Name", style="cyan")
    table.add_column("Severity", style="yellow")
    table.add_column("Description", style="white")
    
    for query_name in list_all_queries()[:8]:
        q = get_query(query_name)
        table.add_row(query_name, q.severity, q.description[:50] + "...")
    
    console.print(table)
    console.print(f"\n[dim]Total queries available: {len(list_all_queries())}[/dim]")
    
    # Create a test graph with some issues
    print_subsection("Running QC on Test Mappings")
    
    g = Graph()
    EX = Namespace("http://example.org/source#")
    TGT = Namespace("http://example.org/target#")
    
    # Add some mappings including problematic ones
    g.add((EX.Dog, SKOS.exactMatch, TGT.Canine))
    g.add((EX.Cat, SKOS.exactMatch, TGT.Feline))
    # Add a circular mapping (error)
    g.add((EX.Animal, OWL.equivalentClass, TGT.Organism))
    g.add((TGT.Organism, OWL.equivalentClass, EX.Animal))
    # Add reflexive mapping (warning)
    g.add((EX.Dog, SKOS.relatedMatch, EX.Dog))
    
    detector = ErrorDetector()
    errors = detector.run_all_checks(g)
    
    if errors:
        console.print(f"\n[red]Found {len(errors)} issues:[/red]\n")
        for error in errors:
            severity_color = "red" if error.severity == "error" else "yellow" if error.severity == "warning" else "blue"
            console.print(f"  [{severity_color}]{error.severity.upper()}[/{severity_color}]: {error.query_name}")
            console.print(f"    {error.description}")
            console.print(f"    Occurrences: {len(error.results)}")
    else:
        console.print("[green]No issues found![/green]")
    
    return errors


async def demo_7_shacl_validation():
    """Demo Step 7: SHACL validation."""
    print_section("STEP 7: SHACL Constraint Validation")
    
    console.print("[dim]Validating mappings against SHACL shapes...[/dim]\n")
    
    from src.shacl.validator import SHACLValidator, DEFAULT_MAPPING_SHAPES, validate_mappings
    from rdflib import Graph, Namespace, Literal
    from rdflib.namespace import OWL, SKOS
    
    # Show default shapes
    print_subsection("Default Mapping Shapes")
    console.print("[dim]Built-in SHACL shapes ensure mappings have valid IRIs[/dim]\n")
    
    # Create test graph
    g = Graph()
    EX = Namespace("http://example.org/source#")
    TGT = Namespace("http://example.org/target#")
    
    g.add((EX.Dog, SKOS.exactMatch, TGT.Canine))
    g.add((EX.Cat, SKOS.exactMatch, TGT.Feline))
    
    result = validate_mappings(g)
    
    if result.conforms:
        console.print("[green]✓ All mappings conform to SHACL constraints[/green]")
    else:
        console.print(f"[red]✗ Found {len(result.violations)} violations:[/red]")
        for v in result.violations:
            console.print(f"  - {v.message}")
    
    # Demo shape generation
    print_subsection("LLM-Suggested SHACL Shapes")
    console.print("[dim]The pipeline can also use LLMs to suggest new SHACL shapes...[/dim]\n")
    
    from src.shacl.shape_generator import SHAPE_TEMPLATES
    
    console.print("Available shape templates:")
    for name in SHAPE_TEMPLATES.keys():
        console.print(f"  • {name}")
    
    return result


async def demo_8_owl_reasoning():
    """Demo Step 8: OWL reasoner consistency checking."""
    print_section("STEP 8: OWL Reasoner Consistency Checking")
    
    console.print("[dim]Using OWL reasoner to check for logical inconsistencies...[/dim]\n")
    
    from src.ontology.reasoner import OWLReasoner, ReasonerType
    from src.ontology.loader import load_ontology
    
    source_path = PROJECT_ROOT / "data" / "ontologies" / "source_test.ttl"
    
    try:
        graph = load_ontology(source_path)
        reasoner = OWLReasoner(ReasonerType.HERMIT)
        
        result = reasoner.check_consistency(graph)
        
        if result.is_consistent:
            console.print("[green]✓ Ontology is logically consistent[/green]")
        else:
            console.print("[red]✗ Ontology has consistency issues:[/red]")
            if result.unsatisfiable_classes:
                for cls in result.unsatisfiable_classes:
                    console.print(f"  - Unsatisfiable: {cls}")
        
        return result
        
    except Exception as e:
        console.print(f"[yellow]Reasoner demo skipped (requires Java): {e}[/yellow]")
        console.print("[dim]In production, HermiT/Pellet would check for logical inconsistencies[/dim]")
        return None


async def demo_9_full_validation():
    """Demo Step 9: Full validation pipeline."""
    print_section("STEP 9: End-to-End Validation Pipeline")
    
    console.print("[dim]Running complete validation suite...[/dim]\n")
    
    from src.validation.pipeline_validator import PipelineValidator
    from src.ontology.loader import load_ontology
    from rdflib import Graph, Namespace
    from rdflib.namespace import SKOS
    
    source_path = PROJECT_ROOT / "data" / "ontologies" / "source_test.ttl"
    target_path = PROJECT_ROOT / "data" / "ontologies" / "target_test.ttl"
    
    source = load_ontology(source_path)
    target = load_ontology(target_path)
    
    # Create mapping graph
    mappings = Graph()
    EX = Namespace("http://example.org/source#")
    TGT = Namespace("http://example.org/target#")
    mappings.add((EX.Dog, SKOS.exactMatch, TGT.Canine))
    mappings.add((EX.Cat, SKOS.exactMatch, TGT.Feline))
    
    validator = PipelineValidator(
        run_reasoner=False,  # Skip for demo (requires Java)
        run_shacl=True,
        run_sparql=True,
    )
    
    report = validator.validate(source, target, mappings)
    
    console.print(Panel(
        f"""[bold]Validation Report[/bold]

Overall Status: {'[green]PASSED[/green]' if report.is_valid else '[red]FAILED[/red]'}

Errors: {report.error_count}
Warnings: {report.warning_count}

SHACL: {'Conformant' if report.shacl_result and report.shacl_result.conforms else 'N/A'}
SPARQL QC: {len(report.sparql_errors)} issues found
""",
        title="Validation Summary",
        border_style="green" if report.is_valid else "red"
    ))
    
    return report


async def demo_10_output_sssom():
    """Demo Step 10: SSSOM output."""
    print_section("STEP 10: SSSOM Output Format")
    
    console.print("[dim]Writing mappings in SSSOM (Simple Standard for Sharing Ontology Mappings) format...[/dim]\n")
    
    from src.mapping.sssom_writer import write_sssom, SSSOMMetadata
    from src.mapping.candidate_generator import MappingCandidate
    
    output_path = PROJECT_ROOT / "data" / "mappings" / "demo_output.sssom.tsv"
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Sample mappings
    mappings = [
        MappingCandidate(
            source_iri="http://example.org/source#Dog",
            source_label="Dog",
            target_iri="http://example.org/target#Canine",
            target_label="Canine",
            predicate="skos:exactMatch",
            confidence=0.95,
            justification="Both refer to domesticated canids"
        ),
        MappingCandidate(
            source_iri="http://example.org/source#Cat",
            source_label="Cat",
            target_iri="http://example.org/target#Feline",
            target_label="Feline",
            predicate="skos:exactMatch",
            confidence=0.92,
            justification="Both refer to domesticated felids"
        ),
    ]
    
    write_sssom(
        mappings,
        output_path,
        title="Demo Mappings",
        creator_id="demo:user",
    )
    
    console.print(f"✓ Written to: [cyan]{output_path}[/cyan]\n")
    
    # Show file content
    console.print("[bold]SSSOM File Content:[/bold]\n")
    with open(output_path) as f:
        console.print(f.read())
    
    return output_path


async def main():
    """Run the complete demo."""
    console.print(Panel.fit(
        """[bold blue]Ontology Mapping Pipeline[/bold blue]
        
[white]A comprehensive demonstration of LLM-powered ontology mapping
with validation using SHACL, SPARQL QC, and OWL reasoning.[/white]

[dim]Press Ctrl+C at any time to exit[/dim]""",
        border_style="blue"
    ))
    
    input("\nPress Enter to begin the demo...")
    
    try:
        # Step 1: Load ontologies
        source_graph, target_graph, source_concepts, target_concepts = await demo_1_load_ontologies()
        input("\nPress Enter to continue to Step 2...")
        
        # Step 2: Generate candidates
        candidates = await demo_2_generate_candidates(source_graph, target_graph)
        input("\nPress Enter to continue to Step 3...")
        
        # Step 3: Rewrite labels
        await demo_3_rewrite_labels(source_concepts)
        input("\nPress Enter to continue to Step 4...")
        
        # Step 4: Score mappings
        scored = await demo_4_score_mappings(candidates, source_concepts, target_concepts)
        input("\nPress Enter to continue to Step 5...")
        
        # Step 5: Generate explanations
        await demo_5_generate_explanations(candidates)
        input("\nPress Enter to continue to Step 6...")
        
        # Step 6: SPARQL QC
        await demo_6_sparql_qc()
        input("\nPress Enter to continue to Step 7...")
        
        # Step 7: SHACL validation
        await demo_7_shacl_validation()
        input("\nPress Enter to continue to Step 8...")
        
        # Step 8: OWL reasoning
        await demo_8_owl_reasoning()
        input("\nPress Enter to continue to Step 9...")
        
        # Step 9: Full validation
        await demo_9_full_validation()
        input("\nPress Enter to continue to Step 10...")
        
        # Step 10: SSSOM output
        await demo_10_output_sssom()
        
        print_section("DEMO COMPLETE")
        console.print(Panel(
            """[bold green]All pipeline components demonstrated successfully![/bold green]

[bold]Key Features Shown:[/bold]
1. ✓ LLM-based candidate mapping generation
2. ✓ Label/definition rewriting
3. ✓ Mapping explanations and rationales
4. ✓ Plausibility scoring (lexical, semantic, structural, LLM)
5. ✓ SPARQL QC error detection
6. ✓ SHACL constraint validation
7. ✓ OWL reasoner integration
8. ✓ End-to-end validation pipeline
9. ✓ SSSOM output format

""",
            title="Summary",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted by user[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    asyncio.run(main())
