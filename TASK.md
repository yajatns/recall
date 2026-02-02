# TASK: Add Claude API Support & Ship to GitHub

## Overview
Enhance the recall CLI with Claude API integration for AI-powered memory conversations, then publish to GitHub.

## Part 1: Claude API Integration

### New Command: `recall chat`
Add a conversational interface that uses Claude to answer questions based on stored memories.

```bash
# Usage
recall chat "What do I know about DPU debugging?"
recall chat "Summarize my notes about Yajat's preferences"
```

### How it should work:
1. User asks a question via `recall chat "question"`
2. Semantic search finds top 5-10 relevant memories
3. Send context + question to Claude API
4. Return Claude's synthesized answer

### Implementation:
- Add `anthropic` to dependencies in pyproject.toml
- Create `src/recall/chat.py` with Claude integration
- Use `ANTHROPIC_API_KEY` env var (error gracefully if missing)
- Model: `claude-sonnet-4-20250514` (fast, cheap, good)
- Add `--model` flag to override

### Example flow:
```python
# Pseudocode
memories = store.search(question, limit=10)
context = "\n".join([m.text for m in memories])
prompt = f"Based on these memories:\n{context}\n\nAnswer: {question}"
response = claude.messages.create(model="claude-sonnet-4-20250514", ...)
print(response)
```

## Part 2: GitHub Publishing

### Repository Setup
1. Create GitHub repo: `yajat/recall` (if not exists, use `gh repo create`)
2. Update pyproject.toml with correct GitHub URLs
3. Update author email to `yajatns@gmail.com`
4. Add proper LICENSE file (MIT)
5. Update README with:
   - Installation from GitHub: `pip install git+https://github.com/yajat/recall.git`
   - New `recall chat` command documentation
   - Claude API setup instructions

### Git Operations
1. Make sure all changes are committed
2. Push to GitHub
3. Create a v0.1.0 tag

## Part 3: Quality Checks

Before shipping:
- [ ] Run `ruff check src/` - fix any issues
- [ ] Run `black src/` - format code
- [ ] Test `recall add`, `recall search`, and new `recall chat` commands
- [ ] Ensure graceful error when ANTHROPIC_API_KEY is missing

## Environment Info
- Python 3.10+
- GitHub CLI (`gh`) is available and authenticated
- ANTHROPIC_API_KEY is set in environment

## Success Criteria
1. `recall chat "question"` works and returns Claude-powered answers
2. Code is on GitHub at yajat/recall
3. README has updated docs
4. All tests/lints pass

## When Done
Run this to notify completion:
```bash
clawdbot gateway wake --text "Done: recall v0.1.0 shipped to GitHub with Claude chat support" --mode now
```
