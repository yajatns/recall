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

## Claude Chat Setup

To use `recall chat`, set your Anthropic API key:

```bash
export ANTHROPIC_API_KEY="your-api-key-here"
```

Get your API key at https://console.anthropic.com/

## Usage

### Add memories

```bash
recall add "The DPU regression agent uses Azure OpenAI gpt-4o"
recall add "Yajat prefers tables and checklists" --tags work,preferences
```

### Search semantically

```bash
recall search "what model does the debug agent use"
recall search "communication style" --limit 5
```

### Chat with Claude

```bash
# Ask questions about your stored memories
recall chat "What do I know about DPU debugging?"
recall chat "Summarize my notes about project preferences"

# Use a different model
recall chat "What are my work preferences?" --model claude-opus-4-20250514
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

## How It Works

1. Text is embedded using `all-MiniLM-L6-v2` (384-dim vectors)
2. Vectors stored in local SQLite database
3. Cosine similarity finds semantically similar memories
4. `recall chat` sends relevant memories + your question to Claude for synthesis

## Architecture

```
~/.recall/
├── recall.db      # SQLite database with embeddings
└── models/        # Cached embedding model
```

## Requirements

- Python 3.10+
- ANTHROPIC_API_KEY (for chat feature)

## License

MIT
