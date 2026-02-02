"""CLI interface for recall."""

import json
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .store import MemoryStore

console = Console()


def get_store() -> MemoryStore:
    """Get the memory store instance."""
    return MemoryStore()


@click.group()
@click.version_option(version="0.1.0", package_name="recall-cli")
def main():
    """🧠 recall - Local semantic memory search for your terminal."""
    pass


@main.command()
@click.argument("content")
@click.option("-t", "--tags", help="Comma-separated tags")
def add(content: str, tags: Optional[str]):
    """Add a new memory."""
    store = get_store()
    tag_list = [t.strip() for t in tags.split(",")] if tags else []

    with console.status("[bold green]Embedding...[/]"):
        memory = store.add(content, tag_list)

    console.print(f"[green]✓[/] Added memory #{memory.id}")
    if tag_list:
        console.print(f"  Tags: {', '.join(tag_list)}")
    store.close()


@main.command()
@click.argument("query")
@click.option("-l", "--limit", default=5, help="Max results")
@click.option("-t", "--tags", help="Filter by tags (comma-separated)")
@click.option("-m", "--min-score", default=0.3, help="Minimum similarity score")
def search(query: str, limit: int, tags: Optional[str], min_score: float):
    """Search memories semantically."""
    store = get_store()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    with console.status("[bold blue]Searching...[/]"):
        results = store.search(query, limit=limit, tags=tag_list, min_score=min_score)

    if not results:
        console.print("[yellow]No matching memories found.[/]")
        store.close()
        return

    console.print(f"\n[bold]Found {len(results)} matches:[/]\n")

    for mem in results:
        score_color = "green" if mem.score > 0.7 else "yellow" if mem.score > 0.5 else "red"

        # Truncate long content
        content = mem.content
        if len(content) > 200:
            content = content[:200] + "..."

        panel = Panel(
            content,
            title=f"[{score_color}]{mem.score:.2f}[/] • #{mem.id}",
            subtitle=f"{mem.created_at.strftime('%Y-%m-%d %H:%M')}"
            + (f" • {', '.join(mem.tags)}" if mem.tags else ""),
            border_style="dim",
        )
        console.print(panel)

    store.close()


@main.command("list")
@click.option("-l", "--limit", default=10, help="Max results")
@click.option("-t", "--tags", help="Filter by tags (comma-separated)")
def list_memories(limit: int, tags: Optional[str]):
    """List recent memories."""
    store = get_store()
    tag_list = [t.strip() for t in tags.split(",")] if tags else None

    memories = store.list(limit=limit, tags=tag_list)

    if not memories:
        console.print("[yellow]No memories found.[/]")
        store.close()
        return

    table = Table(title=f"Recent Memories ({store.count()} total)")
    table.add_column("ID", style="dim")
    table.add_column("Content", max_width=60)
    table.add_column("Tags")
    table.add_column("Created", style="dim")

    for mem in memories:
        content = mem.content
        if len(content) > 60:
            content = content[:57] + "..."

        table.add_row(
            str(mem.id),
            content,
            ", ".join(mem.tags) if mem.tags else "-",
            mem.created_at.strftime("%Y-%m-%d %H:%M"),
        )

    console.print(table)
    store.close()


@main.command()
@click.argument("memory_id", type=int)
def delete(memory_id: int):
    """Delete a memory by ID."""
    store = get_store()

    if store.delete(memory_id):
        console.print(f"[green]✓[/] Deleted memory #{memory_id}")
    else:
        console.print(f"[red]✗[/] Memory #{memory_id} not found")

    store.close()


@main.command("import")
@click.argument("path", type=click.Path(exists=True))
@click.option("--json", "is_json", is_flag=True, help="Import from JSON file")
def import_cmd(path: str, is_json: bool):
    """Import memories from markdown files or JSON."""
    store = get_store()
    path = Path(path)

    if is_json:
        # Import from JSON
        with open(path) as f:
            data = json.load(f)
        count = store.import_json(data)
        console.print(f"[green]✓[/] Imported {count} memories from JSON")
    else:
        # Import markdown files
        if path.is_file():
            files = [path]
        else:
            files = list(path.glob("**/*.md"))

        if not files:
            console.print("[yellow]No markdown files found.[/]")
            store.close()
            return

        items = []
        for file in files:
            content = file.read_text()
            # Use filename as a tag
            tag = file.stem.replace("-", "_")

            # Split by paragraphs for granular memories
            paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]

            for para in paragraphs:
                # Skip very short paragraphs or headers only
                if len(para) > 20 and not para.startswith("#"):
                    items.append((para, [tag]))

        if items:
            with console.status(f"[bold green]Embedding {len(items)} snippets...[/]"):
                count = store.add_batch(items)
            console.print(f"[green]✓[/] Imported {count} memories from {len(files)} files")
        else:
            console.print("[yellow]No suitable content found to import.[/]")

    store.close()


@main.command()
@click.argument("output", type=click.Path())
def export(output: str):
    """Export all memories to JSON."""
    store = get_store()
    data = store.export_json()

    with open(output, "w") as f:
        json.dump(data, f, indent=2, default=str)

    console.print(f"[green]✓[/] Exported {len(data)} memories to {output}")
    store.close()


@main.command()
def stats():
    """Show memory statistics."""
    store = get_store()
    count = store.count()
    db_size = store.db_path.stat().st_size if store.db_path.exists() else 0

    console.print(
        Panel(
            f"[bold]Memories:[/] {count}\n"
            f"[bold]Database:[/] {store.db_path}\n"
            f"[bold]Size:[/] {db_size / 1024:.1f} KB",
            title="📊 Stats",
        )
    )
    store.close()


@main.command()
@click.argument("question")
@click.option("-m", "--model", default="gpt-4o-mini", help="LLM model (e.g. gpt-4o, claude-sonnet-4-20250514, ollama/llama3)")
@click.option("-l", "--limit", default=10, help="Max memories to include as context")
def chat(question: str, model: str, limit: int):
    """Chat with Claude about your memories."""
    from .chat import chat_with_memories

    store = get_store()

    # Search for relevant memories
    with console.status("[bold blue]Searching memories...[/]"):
        memories = store.search(question, limit=limit, min_score=0.2)

    if memories:
        console.print(f"[dim]Found {len(memories)} relevant memories[/]\n")

    # Chat with Claude
    with console.status("[bold green]Thinking...[/]"):
        try:
            response = chat_with_memories(question, memories, model=model)
        except ValueError as e:
            console.print(f"[red]Error:[/] {e}")
            store.close()
            return
        except Exception as e:
            console.print(f"[red]Error calling Claude API:[/] {e}")
            store.close()
            return

    console.print(Panel(response, title="Claude", border_style="green"))
    store.close()


if __name__ == "__main__":
    main()
