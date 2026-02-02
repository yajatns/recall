# recall

**Local semantic memory search for your terminal**

A CLI tool that stores and retrieves memories using semantic search. Now with Claude-powered chat to have conversations about your stored knowledge.

## Features

- **Store memories** - Add text snippets with optional tags
- **Semantic search** - Find by meaning, not just keywords
- **Chat with Claude** - Ask questions, get answers based on your memories
- **Tag support** - Organize with tags, filter searches
- **Import markdown** - Bulk import .md files
- **Local-only** - Embeddings and storage stay on your machine
- **Fast** - Sentence transformers run locally

## Installation

```bash
# Install from GitHub
pip install git+https://github.com/yajatns/recall.git

# Or clone and install locally
git clone https://github.com/yajatns/recall.git
cd recall
pip install -e .
```

## Chat Setup (Any LLM)

`recall chat` works with 100+ LLM providers via [litellm](https://docs.litellm.ai/). Set the appropriate API key:

```bash
# OpenAI (default)
export OPENAI_API_KEY="sk-..."

# Anthropic
export ANTHROPIC_API_KEY="sk-ant-..."

# Ollama (no key needed - runs locally)
ollama serve
```

## Usage

### Add memories

```bash
recall add "Python virtual environments keep dependencies isolated"
recall add "Meeting notes: Q1 roadmap finalized, launch in March" --tags work,meetings
```

### Search semantically

```bash
recall search "how to manage python packages"
recall search "Q1 plans" --limit 5
```

### Chat with Claude

```bash
# Ask questions about your stored memories
recall chat "What were the key decisions from recent meetings?"
recall chat "Summarize what I know about Python best practices"

# Use different models
recall chat "What are my work preferences?" --model gpt-4o
recall chat "Summarize my notes" --model claude-sonnet-4-20250514
recall chat "Quick answer" --model ollama/llama3
```

### Edit memories

```bash
recall edit 5                        # Opens $EDITOR with memory content
recall edit 5 --content "new text"   # Inline edit
recall edit 5 --tags "new,tags"      # Update tags only
```

### Configuration

```bash
recall config                        # Alias for 'recall config show'
recall config show                   # Show current config
recall config set model gpt-4o       # Set default model
recall config set db_path ~/.my-recall/recall.db
recall config get model              # Get specific value
```

**Config file:** `~/.recall/config.yaml`

**Supported settings:**
- `model` - Default LLM model for chat (default: gpt-4o-mini)
- `db_path` - Database location (default: ~/.recall/recall.db)
- `search_limit` - Default search results (default: 10)
- `editor` - Preferred editor for edit command

### Backup

```bash
recall backup                        # Export to ~/.recall/backups/
recall backup --output ./backup.json # Custom output path
recall backup --git                  # Commit to git repo
```

### Other commands

```bash
# List recent memories
recall list
recall list --tags work

# Import markdown files
recall import ~/workspace/memory/

# Export for backup
recall export memories.json

# View stats
recall stats

# Delete a memory
recall delete 42
```

### Shell Completions

```bash
recall --install-completion bash     # Install for bash
recall --install-completion zsh      # Install for zsh
recall --install-completion fish     # Install for fish
```

## How It Works

1. Text is embedded using `all-MiniLM-L6-v2` (384-dim vectors)
2. Vectors stored in local SQLite database
3. Cosine similarity finds semantically similar memories
4. `recall chat` sends relevant memories + your question to Claude for synthesis

## Architecture

```
~/.recall/
├── recall.db      # SQLite database with embeddings
├── config.yaml    # Configuration file
├── models/        # Cached embedding model
└── backups/       # Backup directory (with optional git)
```

## Requirements

- Python 3.10+
- API key for your chosen provider (or Ollama for local models)

## License

MIT
