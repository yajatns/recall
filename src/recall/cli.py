"""CLI interface for recall."""

import json
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .config import DEFAULT_CONFIG, get_config
from .store import MemoryStore

console = Console()


def get_store() -> MemoryStore:
    """Get the memory store instance."""
    config = get_config()
    return MemoryStore(db_path=config.db_path)


SHELL_COMPLETIONS = {
    "bash": """\
_recall_completion() {
    local IFS=$'\\n'
    COMPREPLY=( $( env COMP_WORDS="${COMP_WORDS[*]}" \\
                   COMP_CWORD=$COMP_CWORD \\
                   _RECALL_COMPLETE=bash_complete $1 ) )
    return 0
}
complete -o default -F _recall_completion recall
""",
    "zsh": """\
#compdef recall

_recall() {
    local -a completions
    local -a completions_with_descriptions
    local -a response
    (( ! $+commands[recall] )) && return 1

    response=("${(@f)$(env COMP_WORDS="${words[*]}" COMP_CWORD=$((CURRENT-1)) _RECALL_COMPLETE=zsh_complete recall)}")

    for key descr in ${(kv)response}; do
        if [[ "$descr" == "_" ]]; then
            completions+=("$key")
        else
            completions_with_descriptions+=("$key":"$descr")
        fi
    done

    if [ -n "$completions_with_descriptions" ]; then
        _describe -V unsorted completions_with_descriptions -U
    fi

    if [ -n "$completions" ]; then
        compadd -U -V unsorted -a completions
    fi
}

compdef _recall recall
""",
    "fish": """\
function _recall_completion
    set -l response (env _RECALL_COMPLETE=fish_complete COMP_WORDS=(commandline -cp) COMP_CWORD=(commandline -t) recall)

    for completion in $response
        set -l metadata (string split "," -- $completion)

        if test (count $metadata) -eq 1
            echo $metadata
        else
            echo -e $metadata[1]\\t$metadata[2]
        end
    end
end

complete -c recall -f -a "(_recall_completion)"
""",
}


def install_completion(shell: str):
    """Install shell completion for the specified shell."""
    if shell not in SHELL_COMPLETIONS:
        console.print(f"[red]Unknown shell: {shell}[/]")
        console.print(f"Supported shells: {', '.join(SHELL_COMPLETIONS.keys())}")
        return

    script = SHELL_COMPLETIONS[shell]
    home = Path.home()

    if shell == "bash":
        rc_file = home / ".bashrc"
        completion_file = home / ".recall" / "completion.bash"
    elif shell == "zsh":
        rc_file = home / ".zshrc"
        completion_file = home / ".recall" / "completion.zsh"
    elif shell == "fish":
        rc_file = home / ".config" / "fish" / "completions" / "recall.fish"
        completion_file = rc_file  # Fish uses the completions directory directly

    completion_file.parent.mkdir(parents=True, exist_ok=True)
    completion_file.write_text(script)

    if shell in ("bash", "zsh"):
        source_line = f'source "{completion_file}"'
        if rc_file.exists():
            rc_content = rc_file.read_text()
            if source_line not in rc_content:
                with open(rc_file, "a") as f:
                    f.write(f"\n# recall shell completion\n{source_line}\n")
                console.print(f"[green]Added completion to {rc_file}[/]")
            else:
                console.print(f"[yellow]Completion already in {rc_file}[/]")
        else:
            with open(rc_file, "w") as f:
                f.write(f"# recall shell completion\n{source_line}\n")
            console.print(f"[green]Created {rc_file} with completion[/]")
    else:
        console.print(f"[green]Installed completion to {completion_file}[/]")

    console.print("\n[bold]Restart your shell or run:[/]")
    if shell == "fish":
        console.print(f"  source {completion_file}")
    else:
        console.print(f"  source {rc_file}")


@click.group()
@click.version_option(version="0.1.0", package_name="recall-cli")
@click.option(
    "--install-completion",
    type=click.Choice(["bash", "zsh", "fish"]),
    help="Install shell completion for the specified shell",
    is_eager=True,
    expose_value=False,
    callback=lambda ctx, param, value: (install_completion(value), ctx.exit()) if value else None,
)
def main():
    """Local semantic memory search for your terminal."""
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
@click.argument("memory_id", type=int)
@click.option("-c", "--content", help="New content (inline edit)")
@click.option("-t", "--tags", help="New tags (comma-separated)")
def edit(memory_id: int, content: Optional[str], tags: Optional[str]):
    """Edit an existing memory."""
    store = get_store()
    config = get_config()

    # Fetch the memory first
    memory = store.get(memory_id)
    if not memory:
        console.print(f"[red]Memory #{memory_id} not found[/]")
        store.close()
        return

    new_content = content
    new_tags = [t.strip() for t in tags.split(",")] if tags else None

    # If no inline content, open in editor
    if content is None and tags is None:
        # Use configured editor, or $EDITOR, or click default
        editor = config.editor or os.environ.get("EDITOR")
        edited = click.edit(memory.content, editor=editor)

        if edited is None:
            console.print("[yellow]Edit cancelled[/]")
            store.close()
            return

        new_content = edited.strip()
        if new_content == memory.content:
            console.print("[yellow]No changes made[/]")
            store.close()
            return

    # Update the memory
    with console.status("[bold green]Updating...[/]"):
        updated = store.update(memory_id, content=new_content, tags=new_tags)

    if updated:
        console.print(f"[green]Updated memory #{memory_id}[/]")
        if new_content and new_content != memory.content:
            console.print("  [dim]Content updated (embedding recomputed)[/]")
        if new_tags:
            console.print(f"  Tags: {', '.join(new_tags)}")
    else:
        console.print(f"[red]Failed to update memory #{memory_id}[/]")

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
            title="Stats",
        )
    )
    store.close()


# Config command group
@main.group(invoke_without_command=True)
@click.pass_context
def config(ctx):
    """View and manage configuration."""
    if ctx.invoked_subcommand is None:
        ctx.invoke(config_show)


@config.command("show")
def config_show():
    """Show current configuration."""
    cfg = get_config()
    all_config = cfg.all()

    table = Table(title="Configuration")
    table.add_column("Setting", style="cyan")
    table.add_column("Value")

    for key, value in all_config.items():
        display_value = str(value) if value is not None else "[dim]not set[/]"
        table.add_row(key, display_value)

    table.add_row("[dim]config file[/]", f"[dim]{cfg.config_path}[/]")
    console.print(table)


@config.command("set")
@click.argument("key")
@click.argument("value")
def config_set(key: str, value: str):
    """Set a configuration value."""
    cfg = get_config()
    valid_keys = list(DEFAULT_CONFIG.keys())

    if key not in valid_keys:
        console.print(f"[red]Unknown setting: {key}[/]")
        console.print(f"Valid settings: {', '.join(valid_keys)}")
        return

    cfg.set(key, value)
    console.print(f"[green]Set {key} = {value}[/]")


@config.command("get")
@click.argument("key")
def config_get(key: str):
    """Get a configuration value."""
    cfg = get_config()
    value = cfg.get(key)

    if value is not None:
        console.print(f"{key} = {value}")
    else:
        console.print(f"[yellow]{key} is not set[/]")


@main.command()
@click.option("-o", "--output", type=click.Path(), help="Output file path")
@click.option("--git", is_flag=True, help="Commit backup to git repository")
def backup(output: Optional[str], git: bool):
    """Backup all memories to JSON file."""
    store = get_store()
    data = store.export_json()

    if not data:
        console.print("[yellow]No memories to backup[/]")
        store.close()
        return

    # Determine output path
    if output:
        output_path = Path(output)
    else:
        backup_dir = Path.home() / ".recall" / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        filename_timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = backup_dir / f"recall_backup_{filename_timestamp}.json"

    # Write backup
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2, default=str)

    file_size = output_path.stat().st_size
    console.print(f"[green]Backed up {len(data)} memories[/]")
    console.print(f"  Location: {output_path}")
    console.print(f"  Size: {file_size / 1024:.1f} KB")

    # Git commit if requested
    if git:
        if not shutil.which("git"):
            console.print("[red]Error: git is not installed[/]")
            store.close()
            raise SystemExit(1)

        backup_dir = output_path.parent

        # Initialize git repo if needed
        git_dir = backup_dir / ".git"
        if not git_dir.exists():
            subprocess.run(["git", "init"], cwd=backup_dir, capture_output=True)
            console.print(f"  [dim]Initialized git repo at {backup_dir}[/]")

        # Add and commit
        subprocess.run(["git", "add", output_path.name], cwd=backup_dir, capture_output=True)
        commit_timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        commit_msg = f"Backup: {len(data)} memories at {commit_timestamp}"
        result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            cwd=backup_dir,
            capture_output=True,
            text=True,
        )

        if result.returncode == 0:
            console.print("  [green]Committed to git[/]")
        else:
            console.print("  [yellow]Git commit skipped (no changes or error)[/]")

    store.close()


@main.command()
@click.argument("question")
@click.option(
    "-m", "--model", default=None, help="LLM model (e.g. gpt-4o, claude-sonnet-4-20250514)"
)
@click.option("-l", "--limit", default=None, type=int, help="Max memories to include as context")
def chat(question: str, model: Optional[str], limit: Optional[int]):
    """Chat with an LLM about your memories."""
    from .chat import chat_with_memories

    cfg = get_config()
    model = model or cfg.model
    limit = limit or cfg.search_limit
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
