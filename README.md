# 🧠 recall

**Local semantic memory search for your terminal**

A CLI tool that stores and retrieves memories using semantic search — entirely offline, entirely private.

## Why This Is Trending

The AI memory wave is real:
- **memU** hit 6K stars with +604/day growth
- Developers want context-aware AI that remembers
- Privacy concerns push demand for local-first tools
- Apple Silicon users want fast, local AI processing

**recall** brings semantic search to your notes, memories, and snippets without sending data anywhere.

## Features

- 📝 **Store memories** — Add text snippets with optional tags
- 🔍 **Semantic search** — Find by meaning, not just keywords
- 🏷️ **Tag support** — Organize with tags, filter searches
- 📁 **Import markdown** — Bulk import .md files
- 💾 **Local-only** — Everything stays on your machine
- ⚡ **Fast** — Sentence transformers run locally via ONNX

## Installation

```bash
# Clone and install
cd /Users/yajat/workspace/daily-builds/2026-01-31-recall
pip install -e .

# Or just run directly
python -m recall --help
```

## Usage

```bash
# Add a memory
recall add "The DPU regression agent uses Azure OpenAI gpt-4o"
recall add "Yajat prefers tables and checklists" --tags work,preferences

# Search semantically
recall search "what model does the debug agent use"
recall search "communication style" --limit 5

# List recent memories
recall list
recall list --tags work

# Import markdown files
recall import ~/workspace/memory/

# Export for backup
recall export memories.json
```

## How It Works

1. Text is embedded using `all-MiniLM-L6-v2` (384-dim vectors)
2. Vectors stored in local SQLite with vec0 extension
3. Cosine similarity finds semantically similar memories
4. No API calls, no data leaves your machine

## Architecture

```
~/.recall/
├── recall.db      # SQLite database with vec0 extension
└── config.yaml    # Optional configuration
```

## Requirements

- Python 3.10+
- sentence-transformers
- sqlite-vec (or numpy fallback)

---

*Built as part of Daily AI Builder — January 31, 2026*
