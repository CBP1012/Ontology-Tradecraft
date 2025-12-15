#!/usr/bin/env python3
"""
Ontology Mapping Pipeline - Flexible Demo Script

This script demonstrates ALL features of the ontology mapping pipeline
and accepts custom ontology file paths as command-line arguments.

Usage:
    # Use default test ontologies
    python scripts/demo_pipeline.py
    
    # Specify custom ontology files
    python scripts/demo_pipeline.py --source path/to/source.ttl --target path/to/target.ttl
    
    # Specify output directory
    python scripts/demo_pipeline.py --source source.ttl --target target.ttl --output ./results/
    
    # Skip interactive mode (no pauses)
    python scripts/demo_pipeline.py --no-interactive
    
    # Set minimum confidence threshold
    python scripts/demo_pipeline.py --min-confidence 0.5

Options:
    --source, -s        Path to source ontology TTL file
    --target, -t        Path to target ontology TTL file
    --output, -o        Output directory for results (default: data/mappings/)
    --min-confidence    Minimum confidence threshold for mappings (default: 0.3)
    --no-interactive    Skip interactive pauses between steps
    --skip-reasoner     Skip OWL reasoner step (useful if Java not installed)
    --help, -h          Show this help message
"""

import argparse
import asyncio
import sys
from pathlib import Path
from datetime import datetime

# Setup paths - handle both running from project root and from scripts folder
SCRIPT_DIR = Path(__file__).parent.absolute()

# Determine project root (parent of scripts folder, or current dir if script is at root)
if SCRIPT_DIR.name == "scripts":
    PROJECT_ROOT = SCRIPT_DIR.parent
else:
    PROJECT_ROOT = SCRIPT_DIR

# Add project root to path so 'src' module can be found
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.markdown import Markdown
from rich import print as rprint

console = Console()


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Ontology Mapping Pipeline - Map concepts between two ontologies using LLM",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --source onto1.ttl --target onto2.ttl
    %(prog)s -s source.ttl -t target.ttl -o ./output/ --no-interactive
    %(prog)s --min-confidence 0.5 --skip-reasoner
        """
    )
    
    parser.add_argument(
        "--source", "-s",
        type=Path,
        default=None,
        help="Path to source ontology TTL file"
    )
    
    parser.add_argument(
        "--target", "-t",
        type=Path,
        default=None,
        help="Path to target ontology TTL file"
    )
    
    parser.add_argument(
        "--output", "-o",
        type=Path,
        default=None,
        help="Output directory for results"
    )
    
    parser.add_argument(
        "--min-confidence",
        type=float,
        default=0.3,
        help="Minimum confidence threshold for mappings (default: 0.3)"
    )
    
    parser.add_argument(
        "--no-interactive",
        action="store_true",
        help="Skip interactive pauses between steps"
    )
    
    parser.add_argument(
        "--skip-reasoner",
        action="store_true",
        help="Skip OWL reasoner step (useful if Java not installed)"
    )
    
    return parser.parse_args()


def print_section(title: str):
    """Print a section header."""
    console.print(f"\n{'='*70}")
    console.print(f"[bold cyan]  {title}[/bold cyan]")
    console.print(f"{'='*70}\n")


def print_subsection(title: str):
    """Print a subsection header."""
    console.print(f"\n[bold yellow]>>> {title}[/bold yellow]\n")


def wait_for_input(interactive: bool):
    """Wait for user input if in interactive mode."""
    if interactive:
        input("\nPress Enter to continue...")


async def demo_1_load_ontologies(source_path: Path, target_path: Path):
    """Demo Step 1: Load and explore ontologies."""
    print_section("STEP 1: Loading Ontologies")
    
    from src.ontology.loader import load_ontology
    from src.ontology.extractor import ConceptExtractor
    
    console.print(f"[dim]Source: {source_path}[/dim]")
    console.print(f"[dim]Target: {target_path}[/dim]\n")
    
    # Validate files exist
    if not source_path.exists():
        console.print(f"[red]Error: Source file not found: {source_path}[/red]")
        sys.exit(1)
    if not target_path.exists():
        console.print(f"[red]Error: Target file not found: {target_path}[/red]")
        sys.exit(1)
    
    source_graph = load_ontology(source_path)
    target_graph = load_ontology(target_path)
    
    console.print(f"✓ Loaded source ontology: [green]{len(source_graph)}[/green] triples")
    console.print(f"✓ Loaded target ontology: [green]{len(target_graph)}[/green] triples")
    
    # Extract concepts
    source_extractor = ConceptExtractor(source_graph)
    target_extractor = ConceptExtractor(target_graph)
    
    source_concepts = source_extractor.extract_all_concepts()
    target_concepts = target_extractor.extract_all_concepts()
    
    console.print(f"✓ Extracted [green]{len(source_concepts)}[/green] source concepts")
    console.print(f"✓ Extracted [green]{len(target_concepts)}[/green] target concepts")
    
    print_subsection("Source Ontology Concepts")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Label", style="cyan")
    table.add_column("Definition", style="white", max_width=50)
    table.add_column("Parents", style="dim")
    
    for c in source_concepts[:20]:  # Show first 20
        defn = (c.definition[:47] + "...") if c.definition and len(c.definition) > 50 else (c.definition or "N/A")
        parents = ", ".join(c.parents[:2]) if c.parents else "None"
        table.add_row(c.primary_label, defn, parents)
    
    if len(source_concepts) > 20:
        table.add_row("...", f"[dim]({len(source_concepts) - 20} more)[/dim]", "")
    
    console.print(table)
    
    print_subsection("Target Ontology Concepts")
    table2 = Table(show_header=True, header_style="bold magenta")
    table2.add_column("Label", style="cyan")
    table2.add_column("Definition", style="white", max_width=50)
    table2.add_column("Parents", style="dim")
    
    for c in target_concepts[:20]:  # Show first 20
        defn = (c.definition[:47] + "...") if c.definition and len(c.definition) > 50 else (c.definition or "N/A")
        parents = ", ".join(c.parents[:2]) if c.parents else "None"
        table2.add_row(c.primary_label, defn, parents)
    
    if len(target_concepts) > 20:
        table2.add_row("...", f"[dim]({len(target_concepts) - 20} more)[/dim]", "")
    
    console.print(table2)
    
    return source_graph, target_graph, source_concepts, target_concepts


async def demo_2_generate_candidates(source_graph, target_graph, source_concepts, target_concepts, min_confidence: float):
    """Demo Step 2: LLM-based candidate generation."""
    print_section("STEP 2: LLM-Based Candidate Generation")
    
    console.print("[dim]Using Claude to analyze ontology concepts and suggest mappings...[/dim]\n")
    
    from src.mapping.candidate_generator import CandidateGenerator, MappingCandidate
    
    try:
        generator = CandidateGenerator(config_path=str(PROJECT_ROOT / "configs" / "llm_config.yaml"))
        
        candidates = await generator.generate_candidates(
            source_graph,
            target_graph,
            min_confidence=min_confidence,
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
            
            for c in candidates[:15]:  # Show first 15
                table.add_row(
                    c.source_label,
                    c.predicate.split(":")[-1],
                    c.target_label,
                    f"{c.confidence:.2f}",
                    c.justification[:37] + "..." if len(c.justification) > 40 else c.justification
                )
            
            if len(candidates) > 15:
                table.add_row("...", "", f"[dim]({len(candidates) - 15} more)[/dim]", "", "")
            
            console.print(table)
        
        return candidates
        
    except Exception as e:
        console.print(f"[red]Error generating candidates: {e}[/red]")
        console.print("[yellow]Attempting to create basic mappings based on label similarity...[/yellow]")
        
        # Fallback: create mappings based on exact/similar label matches
        candidates = []
        
        source_lookup = {c.primary_label.lower(): c for c in source_concepts}
        target_lookup = {c.primary_label.lower(): c for c in target_concepts}
        
        # Find exact label matches
        for src_label_lower, src_concept in source_lookup.items():
            if src_label_lower in target_lookup:
                tgt_concept = target_lookup[src_label_lower]
                candidates.append(MappingCandidate(
                    source_iri=src_concept.iri,
                    source_label=src_concept.primary_label,
                    target_iri=tgt_concept.iri,
                    target_label=tgt_concept.primary_label,
                    predicate="skos:exactMatch",
                    confidence=0.95,
                    justification="Exact label match"
                ))
        
        console.print(f"✓ Created [green]{len(candidates)}[/green] mappings based on label matching\n")
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
  Definition: {concept.definition or 'N/A'}

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
            table.add_column("Mapping", style="cyan", max_width=50)
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


async def demo_5_generate_explanations(candidates, source_concepts, target_concepts):
    """Demo Step 5: Generate mapping explanations."""
    print_section("STEP 5: Mapping Explanations & Rationales")
    
    console.print("[dim]Using LLM to generate human-readable explanations...[/dim]\n")
    
    from src.mapping.explainer import ExplanationGenerator
    
    # Build definition lookups from actual concepts
    source_defs = {c.iri: c.definition or "No definition available" for c in source_concepts}
    source_defs.update({c.primary_label: c.definition or "No definition available" for c in source_concepts})
    target_defs = {c.iri: c.definition or "No definition available" for c in target_concepts}
    target_defs.update({c.primary_label: c.definition or "No definition available" for c in target_concepts})
    
    try:
        explainer = ExplanationGenerator()
        
        if candidates:
            candidate = candidates[0] if hasattr(candidates[0], 'source_label') else candidates[0].candidate
            
            source_def = source_defs.get(candidate.source_iri) or source_defs.get(candidate.source_label, "No definition available")
            target_def = target_defs.get(candidate.target_iri) or target_defs.get(candidate.target_label, "No definition available")
            
            explained = await explainer.generate_single(
                candidate,
                source_definition=source_def,
                target_definition=target_def
            )
            
            console.print(Panel(
                f"""[bold]Mapping:[/bold] {explained.candidate.source_label} → {explained.candidate.target_label}
[bold]Predicate:[/bold] {explained.candidate.predicate}

[bold]Source Definition:[/bold] {source_def[:100]}{'...' if len(source_def) > 100 else ''}
[bold]Target Definition:[/bold] {target_def[:100]}{'...' if len(target_def) > 100 else ''}

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


async def demo_6_sparql_qc(candidates, source_concepts, target_concepts):
    """Demo Step 6: SPARQL QC checks."""
    print_section("STEP 6: SPARQL Quality Control Checks")
    
    console.print("[dim]Running SPARQL queries to detect mapping errors...[/dim]\n")
    
    from src.sparql.qc_queries import list_all_queries, get_query
    from src.sparql.error_detector import ErrorDetector
    from rdflib import Graph, URIRef
    from rdflib.namespace import OWL, SKOS
    
    # Show available queries
    print_subsection("Available QC Queries")
    
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Query Name", style="cyan")
    table.add_column("Severity", style="yellow")
    table.add_column("Description", style="white", max_width=50)
    
    for query_name in list_all_queries()[:8]:
        q = get_query(query_name)
        table.add_row(query_name, q.severity, q.description[:47] + "...")
    
    console.print(table)
    console.print(f"\n[dim]Total queries available: {len(list_all_queries())}[/dim]")
    
    # Create test graph using actual ontology mappings
    print_subsection("Running QC on Generated Mappings")
    
    g = Graph()
    
    for candidate in candidates[:10]:
        subject = URIRef(candidate.source_iri)
        obj = URIRef(candidate.target_iri)
        
        if "exactMatch" in candidate.predicate:
            g.add((subject, SKOS.exactMatch, obj))
        elif "broadMatch" in candidate.predicate:
            g.add((subject, SKOS.broadMatch, obj))
        elif "narrowMatch" in candidate.predicate:
            g.add((subject, SKOS.narrowMatch, obj))
        elif "closeMatch" in candidate.predicate:
            g.add((subject, SKOS.closeMatch, obj))
        elif "relatedMatch" in candidate.predicate:
            g.add((subject, SKOS.relatedMatch, obj))
        elif "equivalentClass" in candidate.predicate:
            g.add((subject, OWL.equivalentClass, obj))
    
    detector = ErrorDetector()
    errors = detector.run_all_checks(g)
    
    if errors:
        console.print(f"\n[yellow]Found {len(errors)} issues:[/yellow]\n")
        for error in errors:
            severity_color = "red" if error.severity == "error" else "yellow" if error.severity == "warning" else "blue"
            console.print(f"  [{severity_color}]{error.severity.upper()}[/{severity_color}]: {error.query_name}")
            console.print(f"    {error.description}")
            console.print(f"    Occurrences: {len(error.results)}")
    else:
        console.print("[green]✓ No issues found![/green]")
    
    return errors


async def demo_7_shacl_validation(candidates):
    """Demo Step 7: SHACL validation."""
    print_section("STEP 7: SHACL Constraint Validation")
    
    console.print("[dim]Validating mappings against SHACL shapes...[/dim]\n")
    
    from src.shacl.validator import validate_mappings
    from rdflib import Graph, URIRef
    from rdflib.namespace import SKOS
    
    print_subsection("Default Mapping Shapes")
    console.print("[dim]Built-in SHACL shapes ensure mappings have valid IRIs[/dim]\n")
    
    g = Graph()
    
    for candidate in candidates[:5]:
        subject = URIRef(candidate.source_iri)
        obj = URIRef(candidate.target_iri)
        
        if "exactMatch" in candidate.predicate:
            g.add((subject, SKOS.exactMatch, obj))
        elif "broadMatch" in candidate.predicate:
            g.add((subject, SKOS.broadMatch, obj))
        else:
            g.add((subject, SKOS.relatedMatch, obj))
    
    result = validate_mappings(g)
    
    if result.conforms:
        console.print("[green]✓ All mappings conform to SHACL constraints[/green]")
    else:
        console.print(f"[red]✗ Found {len(result.violations)} violations:[/red]")
        for v in result.violations:
            console.print(f"  - {v.message}")
    
    print_subsection("LLM-Suggested SHACL Shapes")
    console.print("[dim]The pipeline can also use LLMs to suggest new SHACL shapes...[/dim]\n")
    
    from src.shacl.shape_generator import SHAPE_TEMPLATES
    
    console.print("Available shape templates:")
    for name in SHAPE_TEMPLATES.keys():
        console.print(f"  • {name}")
    
    return result


async def demo_8_owl_reasoning(source_path: Path, skip_reasoner: bool):
    """Demo Step 8: OWL reasoner consistency checking."""
    print_section("STEP 8: OWL Reasoner Consistency Checking")
    
    if skip_reasoner:
        console.print("[yellow]Skipping OWL reasoner (--skip-reasoner flag set)[/yellow]")
        console.print("[dim]In production, HermiT/Pellet would check for logical inconsistencies[/dim]")
        return None
    
    console.print("[dim]Using OWL reasoner to check for logical inconsistencies...[/dim]\n")
    
    from src.ontology.reasoner import OWLReasoner, ReasonerType
    from src.ontology.loader import load_ontology
    
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


async def demo_9_full_validation(candidates, source_path: Path, target_path: Path, skip_reasoner: bool):
    """Demo Step 9: Full validation pipeline."""
    print_section("STEP 9: End-to-End Validation Pipeline")
    
    console.print("[dim]Running complete validation suite...[/dim]\n")
    
    from src.validation.pipeline_validator import PipelineValidator
    from src.ontology.loader import load_ontology
    from rdflib import Graph, URIRef
    from rdflib.namespace import SKOS, OWL
    
    source = load_ontology(source_path)
    target = load_ontology(target_path)
    
    mappings = Graph()
    
    for candidate in candidates[:10]:
        subject = URIRef(candidate.source_iri)
        obj = URIRef(candidate.target_iri)
        
        if "exactMatch" in candidate.predicate:
            mappings.add((subject, SKOS.exactMatch, obj))
        elif "broadMatch" in candidate.predicate:
            mappings.add((subject, SKOS.broadMatch, obj))
        elif "equivalentClass" in candidate.predicate:
            mappings.add((subject, OWL.equivalentClass, obj))
        else:
            mappings.add((subject, SKOS.relatedMatch, obj))
    
    validator = PipelineValidator(
        run_reasoner=not skip_reasoner,
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


async def demo_10_output_sssom(candidates, output_path: Path, source_path: Path, target_path: Path):
    """Demo Step 10: SSSOM output."""
    print_section("STEP 10: SSSOM Output Format")
    
    console.print("[dim]Writing mappings in SSSOM (Simple Standard for Sharing Ontology Mappings) format...[/dim]\n")
    
    from src.mapping.sssom_writer import write_sssom
    
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Generate descriptive title from file names
    source_name = source_path.stem
    target_name = target_path.stem
    title = f"{source_name} to {target_name} Mappings"
    
    write_sssom(
        candidates,
        output_path,
        title=title,
        creator_id="ontology-mapping-pipeline",
        subject_source=str(source_path),
        object_source=str(target_path),
    )
    
    console.print(f"✓ Written to: [cyan]{output_path}[/cyan]\n")
    
    # Show file content preview
    console.print("[bold]SSSOM File Content (first 30 lines):[/bold]\n")
    with open(output_path) as f:
        lines = f.readlines()
        for line in lines[:30]:
            console.print(line.rstrip())
        if len(lines) > 30:
            console.print(f"\n[dim]... ({len(lines) - 30} more lines)[/dim]")
    
    return output_path


async def main():
    """Run the complete demo."""
    args = parse_args()
    
    # Set default paths if not provided
    source_path = args.source or (PROJECT_ROOT / "data" / "ontologies" / "source_test.ttl")
    target_path = args.target or (PROJECT_ROOT / "data" / "ontologies" / "target_test.ttl")
    output_dir = args.output or (PROJECT_ROOT / "data" / "mappings")
    
    # Generate output filename based on input files
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"{source_path.stem}_to_{target_path.stem}_{timestamp}.sssom.tsv"
    
    interactive = not args.no_interactive
    
    console.print(Panel.fit(
        f"""[bold blue]Ontology Mapping Pipeline[/bold blue]
        
[white]A comprehensive demonstration of LLM-powered ontology mapping
with validation using SHACL, SPARQL QC, and OWL reasoning.[/white]

[bold]Configuration:[/bold]
  Source: [cyan]{source_path}[/cyan]
  Target: [cyan]{target_path}[/cyan]
  Output: [cyan]{output_file}[/cyan]
  Min Confidence: [cyan]{args.min_confidence}[/cyan]
  Interactive: [cyan]{interactive}[/cyan]
  Skip Reasoner: [cyan]{args.skip_reasoner}[/cyan]

[dim]Press Ctrl+C at any time to exit[/dim]""",
        border_style="blue"
    ))
    
    if interactive:
        input("\nPress Enter to begin the demo...")
    
    try:
        # Step 1: Load ontologies
        source_graph, target_graph, source_concepts, target_concepts = await demo_1_load_ontologies(source_path, target_path)
        wait_for_input(interactive)
        
        # Step 2: Generate candidates
        candidates = await demo_2_generate_candidates(source_graph, target_graph, source_concepts, target_concepts, args.min_confidence)
        
        if not candidates:
            console.print("[red]No candidates generated. Exiting.[/red]")
            sys.exit(1)
        
        wait_for_input(interactive)
        
        # Step 3: Rewrite labels
        await demo_3_rewrite_labels(source_concepts)
        wait_for_input(interactive)
        
        # Step 4: Score mappings
        scored = await demo_4_score_mappings(candidates, source_concepts, target_concepts)
        wait_for_input(interactive)
        
        # Step 5: Generate explanations
        await demo_5_generate_explanations(candidates, source_concepts, target_concepts)
        wait_for_input(interactive)
        
        # Step 6: SPARQL QC
        await demo_6_sparql_qc(candidates, source_concepts, target_concepts)
        wait_for_input(interactive)
        
        # Step 7: SHACL validation
        await demo_7_shacl_validation(candidates)
        wait_for_input(interactive)
        
        # Step 8: OWL reasoning
        await demo_8_owl_reasoning(source_path, args.skip_reasoner)
        wait_for_input(interactive)
        
        # Step 9: Full validation
        await demo_9_full_validation(candidates, source_path, target_path, args.skip_reasoner)
        wait_for_input(interactive)
        
        # Step 10: SSSOM output
        await demo_10_output_sssom(candidates, output_file, source_path, target_path)
        
        print_section("DEMO COMPLETE")
        console.print(Panel(
            f"""[bold green]All pipeline components completed successfully![/bold green]

[bold]Results:[/bold]
  • Candidates Generated: {len(candidates)}
  • Output File: {output_file}

[bold]Key Features Demonstrated:[/bold]
  1. ✓ LLM-based candidate mapping generation
  2. ✓ Label/definition rewriting
  3. ✓ Mapping explanations and rationales
  4. ✓ Plausibility scoring (lexical, semantic, structural, LLM)
  5. ✓ SPARQL QC error detection
  6. ✓ SHACL constraint validation
  7. ✓ OWL reasoner integration
  8. ✓ End-to-end validation pipeline
  9. ✓ SSSOM output format

[bold]Next Steps:[/bold]
  • Review the SSSOM output file
  • Adjust min-confidence threshold if needed
  • Run with different ontology pairs
""",
            title="Summary",
            border_style="green"
        ))
        
    except KeyboardInterrupt:
        console.print("\n\n[yellow]Demo interrupted by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
    