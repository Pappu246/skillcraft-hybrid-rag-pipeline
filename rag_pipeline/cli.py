"""Command-line interface."""
from __future__ import annotations

import json
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .core import HybridIndex, format_context, generate_answer, ingest_pdfs, retrieve_comparison

app = typer.Typer(help="Hybrid RAG pipeline with source citations")
console = Console()


@app.command()
def ingest(
    input: Path = typer.Option(Path("data/documents"), "--input", "-i", help="Directory containing PDF files"),
    index_dir: Path = typer.Option(Path(".rag_index"), "--index-dir", help="Local index directory"),
    chunk_size: int = typer.Option(900, min=100, help="Chunk size in characters"),
    overlap: int = typer.Option(150, min=0, help="Chunk overlap in characters"),
) -> None:
    """Extract PDF pages, chunk text, and save provenance metadata."""
    chunks = ingest_pdfs(input, chunk_size=chunk_size, overlap=overlap)
    HybridIndex(chunks).save(index_dir)
    console.print(f"[green]Indexed {len(chunks)} chunks from PDFs in {input}.[/green]")
    console.print(f"Saved local chunk metadata to {index_dir / 'chunks.json'}")


@app.command()
def compare(
    question: str = typer.Option(..., "--question", "-q", help="Question to retrieve evidence for"),
    index_dir: Path = typer.Option(Path(".rag_index"), "--index-dir"),
    top_k: int = typer.Option(5, min=1, max=20),
    output: Path | None = typer.Option(None, help="Optional JSON output path"),
) -> None:
    """Compare BM25, dense, and hybrid retrieval for one question."""
    index = HybridIndex.load(index_dir)
    report = retrieve_comparison(index, question, top_k=top_k)
    table = Table(title="Retrieval comparison (latency is not an accuracy metric)")
    table.add_column("Method")
    table.add_column("Latency (ms)", justify="right")
    table.add_column("Top source chunks")
    for name, details in report["methods"].items():
        citations = ", ".join(item["citation"] for item in details["results"]) or "(none)"
        table.add_row(name, str(details["latency_ms"]), citations)
    console.print(table)
    if output:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        console.print(f"Saved report: {output}")


@app.command()
def ask(
    question: str = typer.Option(..., "--question", "-q"),
    index_dir: Path = typer.Option(Path(".rag_index"), "--index-dir"),
    top_k: int = typer.Option(5, min=1, max=20),
    rerank: bool = typer.Option(False, help="Use configured CrossEncoder reranker"),
) -> None:
    """Retrieve evidence and produce a cited answer when generation is configured."""
    index = HybridIndex.load(index_dir)
    results = index.search_hybrid(question, top_k=top_k, rerank=rerank)
    answer = generate_answer(question, results)
    console.print(Panel(answer, title="Answer with source evidence", expand=False))


if __name__ == "__main__":
    app()
