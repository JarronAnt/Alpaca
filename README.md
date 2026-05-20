# 🦙 Alpaca

Production-grade multi-agent AI coding assistant using local LLMs via Ollama.

## Architecture

Alpaca uses a multi-agent architecture where specialized agents collaborate to complete coding tasks:

| Agent | Role | Responsibility |
|-------|------|----------------|
| **THAG** | Router | Decides if input is a coding task or conversation |
| **OOGA** | Planner | Creates structured project plans |
| **GROG** | Builder | Executes plans using filesystem and shell tools |
| **BRAK** | Tester | Runs tests and validates code |
| **ROG** | Reviewer | Reviews code for bugs and quality |

## Features

- **Local-First**: Uses Ollama for 100% local LLM inference
- **Secure**: Sandboxed workspace with path boundary enforcement
- **Type-Safe**: Full Pydantic models and type hints
- **Observable**: Structured logging with rich console output
- **Tested**: Comprehensive test suite with pytest
- **Extensible**: Plugin architecture for custom tools

## Quick Start

### Prerequisites

- Python 3.11+
- [Ollama](https://ollama.ai/) installed and running
- At least one model pulled (e.g., `ollama pull llama3`)

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/alpaca.git
cd alpaca

# Install with uv (recommended)
uv pip install -e .

# Or with pip
pip install -e .

### Usage

# Activate venv
source .venv/bin/activate

# Run Alpaca
alpaca run --interactive
