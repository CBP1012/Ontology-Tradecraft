#!/usr/bin/env python3
"""
Mapping Evaluation Script

Evaluates the quality of generated mappings against gold standards
and computes various metrics.

Usage:
    python scripts/evaluate_mappings.py --predicted mappings.sssom.tsv --gold gold.sssom.tsv
"""

import argparse
import json
import sys
import os
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# Add the project root to Python path BEFORE importing other modules
PROJECT_ROOT = Path(__file__).parent.parent.absolute()
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import pandas as pd
from rich.console import Console
from rich.table import Table


@dataclass
class MappingPair:
    """A mapping pair for evaluation."""
    subject: str
    object: str
    predicate: str
    confidence: float = 1.0


@dataclass
class EvaluationMetrics:
    """Evaluation metrics for mapping quality."""
    true_positives: int = 0
    false_positives: int = 0
    false_negatives: int = 0
    
    # Per-predicate breakdown
    per_predicate: dict = field(default_factory=dict)
    
    # Confidence statistics
    avg_confidence_tp: float = 0.0
    avg_confidence_fp: float = 0.0
    
    @property
    def precision(self) -> float:
        """Calculate precision."""
        total = self.true_positives + self.false_positives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def recall(self) -> float:
        """Calculate recall."""
        total = self.true_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0
    
    @property
    def f1_score(self) -> float:
        """Calculate F1 score."""
        p, r = self.precision, self.recall
        return 2 * p * r / (p + r) if (p + r) > 0 else 0.0
    
    @property
    def accuracy(self) -> float:
        """Calculate accuracy."""
        total = self.true_positives + self.false_positives + self.false_negatives
        return self.true_positives / total if total > 0 else 0.0
    
    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "true_positives": self.true_positives,
            "false_positives": self.false_positives,
            "false_negatives": self.false_negatives,
            "precision": round(self.precision, 4),
            "recall": round(self.recall, 4),
            "f1_score": round(self.f1_score, 4),
            "accuracy": round(self.accuracy, 4),
            "avg_confidence_tp": round(self.avg_confidence_tp, 4),
            "avg_confidence_fp": round(self.avg_confidence_fp, 4),
            "per_predicate": self.per_predicate,
        }


class MappingEvaluator:
    """Evaluates mapping quality against gold standard."""
    
    # Equivalent predicate groups (for flexible matching)
    EQUIVALENT_PREDICATES = {
        frozenset(["owl:equivalentClass", "skos:exactMatch"]),
        frozenset(["skos:closeMatch", "skos:relatedMatch"]),
    }
    
    def __init__(
        self,
        strict_predicate: bool = False,
        ignore_direction: bool = True,
    ):
        """
        Initialize the evaluator.
        
        Args:
            strict_predicate: If True, predicates must match exactly
            ignore_direction: If True, treat (A,B) same as (B,A) for symmetric predicates
        """
        self.strict_predicate = strict_predicate
        self.ignore_direction = ignore_direction
    
    def load_sssom(self, path: str | Path) -> list[MappingPair]:
        """
        Load mappings from SSSOM TSV file.
        
        Args:
            path: Path to SSSOM file
            
        Returns:
            List of MappingPair objects
        """
        path = Path(path)
        
        # Skip YAML header (lines starting with #)
        with open(path) as f:
            lines = f.readlines()
        
        # Find where data starts
        data_start = 0
        for i, line in enumerate(lines):
            if not line.startswith("#") and line.strip():
                data_start = i
                break
        
        # Read as TSV
        df = pd.read_csv(
            path,
            sep="\t",
            skiprows=data_start,
            comment="#",
        )
        
        mappings = []
        for _, row in df.iterrows():
            subject = row.get("subject_id", "")
            obj = row.get("object_id", "")
            predicate = row.get("predicate_id", "skos:exactMatch")
            confidence = float(row.get("confidence", 1.0)) if pd.notna(row.get("confidence")) else 1.0
            
            if subject and obj:
                mappings.append(MappingPair(
                    subject=str(subject),
                    object=str(obj),
                    predicate=str(predicate),
                    confidence=confidence,
                ))
        
        return mappings
    
    def evaluate(
        self,
        predicted: list[MappingPair],
        gold: list[MappingPair],
    ) -> EvaluationMetrics:
        """
        Evaluate predicted mappings against gold standard.
        
        Args:
            predicted: Predicted mappings
            gold: Gold standard mappings
            
        Returns:
            EvaluationMetrics object
        """
        metrics = EvaluationMetrics()
        
        # Build gold set for efficient lookup
        gold_set = self._build_mapping_set(gold)
        predicted_set = self._build_mapping_set(predicted)
        
        # Track confidences
        tp_confidences = []
        fp_confidences = []
        
        # Per-predicate tracking
        pred_metrics = defaultdict(lambda: {"tp": 0, "fp": 0, "fn": 0})
        
        # Calculate TP and FP
        for mapping in predicted:
            key = self._make_key(mapping)
            
            if self._is_match(key, gold_set):
                metrics.true_positives += 1
                tp_confidences.append(mapping.confidence)
                pred_metrics[mapping.predicate]["tp"] += 1
            else:
                metrics.false_positives += 1
                fp_confidences.append(mapping.confidence)
                pred_metrics[mapping.predicate]["fp"] += 1
        
        # Calculate FN
        for mapping in gold:
            key = self._make_key(mapping)
            
            if not self._is_match(key, predicted_set):
                metrics.false_negatives += 1
                pred_metrics[mapping.predicate]["fn"] += 1
        
        # Calculate average confidences
        if tp_confidences:
            metrics.avg_confidence_tp = sum(tp_confidences) / len(tp_confidences)
        if fp_confidences:
            metrics.avg_confidence_fp = sum(fp_confidences) / len(fp_confidences)
        
        # Store per-predicate metrics
        metrics.per_predicate = dict(pred_metrics)
        
        return metrics
    
    def _build_mapping_set(self, mappings: list[MappingPair]) -> set:
        """Build a set of mapping keys for efficient lookup."""
        keys = set()
        for mapping in mappings:
            keys.add(self._make_key(mapping))
        return keys
    
    def _make_key(self, mapping: MappingPair) -> tuple:
        """Create a lookup key for a mapping."""
        subj, obj = mapping.subject, mapping.object
        
        # Normalize direction for symmetric predicates
        if self.ignore_direction and mapping.predicate in [
            "owl:equivalentClass", "skos:exactMatch", "skos:closeMatch", "skos:relatedMatch"
        ]:
            subj, obj = tuple(sorted([subj, obj]))
        
        if self.strict_predicate:
            return (subj, obj, mapping.predicate)
        else:
            return (subj, obj)
    
    def _is_match(self, key: tuple, mapping_set: set) -> bool:
        """Check if a key matches any mapping in the set."""
        if key in mapping_set:
            return True
        
        # Check equivalent predicates if not strict
        if not self.strict_predicate and len(key) == 3:
            subj, obj, pred = key
            for equiv_group in self.EQUIVALENT_PREDICATES:
                if pred in equiv_group:
                    for equiv_pred in equiv_group:
                        if (subj, obj, equiv_pred) in mapping_set:
                            return True
        
        return False
    
    def evaluate_at_threshold(
        self,
        predicted: list[MappingPair],
        gold: list[MappingPair],
        threshold: float,
    ) -> EvaluationMetrics:
        """
        Evaluate with confidence threshold.
        
        Args:
            predicted: Predicted mappings
            gold: Gold standard
            threshold: Minimum confidence threshold
            
        Returns:
            Metrics for mappings above threshold
        """
        filtered = [m for m in predicted if m.confidence >= threshold]
        return self.evaluate(filtered, gold)
    
    def compute_precision_recall_curve(
        self,
        predicted: list[MappingPair],
        gold: list[MappingPair],
        steps: int = 20,
    ) -> list[dict]:
        """
        Compute precision-recall curve at different thresholds.
        
        Args:
            predicted: Predicted mappings
            gold: Gold standard
            steps: Number of threshold steps
            
        Returns:
            List of {threshold, precision, recall, f1} dicts
        """
        curve = []
        
        for i in range(steps + 1):
            threshold = i / steps
            metrics = self.evaluate_at_threshold(predicted, gold, threshold)
            
            curve.append({
                "threshold": threshold,
                "precision": metrics.precision,
                "recall": metrics.recall,
                "f1": metrics.f1_score,
                "count": metrics.true_positives + metrics.false_positives,
            })
        
        return curve


def print_metrics(metrics: EvaluationMetrics, console: Console) -> None:
    """Print metrics in a nice table format."""
    table = Table(title="Evaluation Metrics")
    
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")
    
    table.add_row("True Positives", str(metrics.true_positives))
    table.add_row("False Positives", str(metrics.false_positives))
    table.add_row("False Negatives", str(metrics.false_negatives))
    table.add_row("", "")
    table.add_row("Precision", f"{metrics.precision:.4f}")
    table.add_row("Recall", f"{metrics.recall:.4f}")
    table.add_row("F1 Score", f"{metrics.f1_score:.4f}")
    table.add_row("", "")
    table.add_row("Avg Confidence (TP)", f"{metrics.avg_confidence_tp:.4f}")
    table.add_row("Avg Confidence (FP)", f"{metrics.avg_confidence_fp:.4f}")
    
    console.print(table)
    
    # Per-predicate breakdown
    if metrics.per_predicate:
        pred_table = Table(title="Per-Predicate Breakdown")
        pred_table.add_column("Predicate", style="cyan")
        pred_table.add_column("TP", style="green")
        pred_table.add_column("FP", style="red")
        pred_table.add_column("FN", style="yellow")
        
        for pred, counts in metrics.per_predicate.items():
            pred_table.add_row(
                pred,
                str(counts["tp"]),
                str(counts["fp"]),
                str(counts["fn"]),
            )
        
        console.print(pred_table)


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Evaluate ontology mapping quality"
    )
    parser.add_argument(
        "--predicted", "-p",
        required=True,
        help="Path to predicted mappings (SSSOM TSV)"
    )
    parser.add_argument(
        "--gold", "-g",
        required=True,
        help="Path to gold standard mappings (SSSOM TSV)"
    )
    parser.add_argument(
        "--strict-predicate",
        action="store_true",
        help="Require exact predicate match"
    )
    parser.add_argument(
        "--output", "-o",
        help="Output path for JSON results"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=0.0,
        help="Confidence threshold (default: 0.0)"
    )
    parser.add_argument(
        "--curve",
        action="store_true",
        help="Compute precision-recall curve"
    )
    
    args = parser.parse_args()
    
    console = Console()
    
    # Load mappings
    console.print("\n[bold]Loading mappings...[/bold]")
    evaluator = MappingEvaluator(strict_predicate=args.strict_predicate)
    
    try:
        predicted = evaluator.load_sssom(args.predicted)
        gold = evaluator.load_sssom(args.gold)
    except Exception as e:
        console.print(f"[red]Error loading mappings: {e}[/red]")
        sys.exit(1)
    
    console.print(f"  Predicted: {len(predicted)} mappings")
    console.print(f"  Gold: {len(gold)} mappings")
    
    # Evaluate
    if args.threshold > 0:
        console.print(f"\n[bold]Evaluating at threshold {args.threshold}...[/bold]")
        metrics = evaluator.evaluate_at_threshold(predicted, gold, args.threshold)
    else:
        console.print("\n[bold]Evaluating...[/bold]")
        metrics = evaluator.evaluate(predicted, gold)
    
    # Print results
    print_metrics(metrics, console)
    
    # Compute curve if requested
    if args.curve:
        console.print("\n[bold]Precision-Recall Curve[/bold]")
        curve = evaluator.compute_precision_recall_curve(predicted, gold)
        
        curve_table = Table()
        curve_table.add_column("Threshold")
        curve_table.add_column("Precision")
        curve_table.add_column("Recall")
        curve_table.add_column("F1")
        curve_table.add_column("Count")
        
        for point in curve:
            curve_table.add_row(
                f"{point['threshold']:.2f}",
                f"{point['precision']:.3f}",
                f"{point['recall']:.3f}",
                f"{point['f1']:.3f}",
                str(point['count']),
            )
        
        console.print(curve_table)
    
    # Save results if output specified
    if args.output:
        results = metrics.to_dict()
        if args.curve:
            results["curve"] = curve
        
        with open(args.output, "w") as f:
            json.dump(results, f, indent=2)
        
        console.print(f"\n[green]Results saved to {args.output}[/green]")


if __name__ == "__main__":
    main()

    