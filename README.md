# Recursive Yak Shaver (RYS) v0.1

Recursive Yak Shaver (RYS) is a lightweight agent tool designed to autonomously decompose and execute complex requests using small LLMs, such as gemma3n:e4b.

## Overview

RYS processes ambiguous or multi-step user requests through the following pipeline:
1. **Translation**: Converts input into clear English task segments.
2. **Dispatch**: Analyzes segments and assigns them to "Skills" as individual **TOPICs**.
3. **Request Visualization**: Groups TOPICs into logical **REQUESTs** and generates descriptive titles.
4. **Planning Phase (Triple-Check System)**: A rigorous three-stage thinking process:
   - **Strategic Planning**: Provides a high-level conceptual roadmap.
   - **Technical Analysis**: Selects specific tools and outlines technical steps.
   - **Workflow Synthesis**: Integrates strategy and technical analysis into a final, natural language workflow.
5. **Auditing**: Evaluates the synthesized workflow against safety policies and risks.

> [!IMPORTANT]
> **Current Status**: RYS focuses on **high-precision task planning**. It generates a detailed, triple-verified workflow but **DOES NOT execute actual code** on your system yet.

## Setup

### Environment Variables
RYS requires an OpenAI-compatible API server. Configure the following variables:

- `RYS_LLM_HOST`: API server hostname (Default: localhost)
- `RYS_LLM_PORT`: API server port (Default: auto)
- `RYS_LLM_MODEL`: Target model name (e.g., gemma3n:e4b)
- `RYS_LLM_INSECURE`: Set to `true` to skip SSL verification (for self-signed certs).

### Protocol & Port Resolution
RYS intelligently resolves the endpoint based on your host input:

| Input Example | Protocol | Default Port | TLS |
| :--- | :--- | :--- | :--- |
| `localhost` / `127.0.0.1` | `http` | `11434` | No |
| `192.168.0.25` | `https` | `443` | **Yes** |
| `http://192.168.0.25` | `http` | `11434` | No |
| `https://localhost` | `https` | `443` | **Yes** |
| `anyhost:1234` | (auto) | `1234` | (auto) |

- **Precedence**: Host-string port (`host:port`) > `--port` argument > Protocol default.
- **Auto-TLS**: Non-local hosts default to `https://443`. Explicit `http://` forces port `11434`.

### Running with Ollama (Recommended)
RYS is designed to work with small LLMs. You can use [Ollama](https://ollama.com/) to host them locally:

1. **Pull the model**:
   ```bash
   ollama pull gemma3n:e4b
   ```

2. **Set the environment variable**:
   ```bash
   export RYS_LLM_MODEL=gemma3n:e4b
   ```

3. **Run RYS**:
   ```bash
   ./rys/main.bash "Your task here"
   ```

### Dependencies
- Bash
- Python 3.10+

## Development Standards

This project follows strict coding and documentation standards to ensure maintainability and consistency:

1.  **File Size Limit**: Each source code and Markdown file is kept under **6KiB**. Large modules are split into smaller, focused files.
2.  **Function Design**:
    - **Single Return**: Every function has a single `return` statement at the very end.
    - **Exception-based Error Handling**: Guard clauses use exceptions instead of early returns to maintain the single-return structure.
3.  **Pylint Compliance**: The codebase aims for a Pylint score of **10.00/10**. Specific warnings (`useless-return`, `broad-exception-caught`) are suppressed only when they conflict with these project-specific rules.
4.  **Modular Architecture**: Core functionalities are decomposed into specialized modules (e.g., `chat_api.py`, `chat_ui.py`, `role_utils.py`) to satisfy size constraints and improve clarity.

## Usage

Pass your prompt as an argument or via standard input:

```bash
# Via argument
RYS_LLM_HOST=<LLM_HOST_IP> RYS_LLM_MODEL=gemma3n:e4b ./rys/main.bash "Your prompt here"

# Via pipe (Standard Input)
echo "Find the largest file and calculate primes up to 100" | ./rys/main.bash
```

### Advanced: Interactive Mode
Internal tools (like `invoke_llm.py`) run in quiet mode by default. Use `--interactive` to start a chat session:
```bash
./rys/invoke_llm.py --host <LLM_HOST_IP> --interactive
```

### Example
```bash
./rys/main.bash "Find the largest file in this directory and tell me the prime numbers up to 100."
```

## Architecture

- `rys/main.bash`: The entry point controlling the pipeline.
- `rys/invoke_role.py`: Orchestrates role-based LLM calls.
- `rys/role_utils.py`: Utilities for loading role definitions and constructing system prompts.
- `rys/chat_core.py`: Main logic for OpenAI-compatible API interaction.
- `rys/chat_api.py`, `rys/chat_ui.py`, `rys/chat_types.py`: Modular components for API communication, terminal UI, and shared data structures.
- `rys/group_requests.py`: Parses and groups tasks from the Dispatcher.
- `roles/`: Markdown files defining role behaviors and constraints.
- `config/`: JSON configuration for skills, risks, and default settings.

## Adding Skills

You can extend the agent's capabilities by adding new skills to `config/skills.json`:

```json
{
  "id": "python_exec",
  "type": "primitive",
  "description": "General purpose programming and math.",
  "tools": ["python3", "pip"]
}
```

## Roles

| Role | Responsibility |
| :--- | :--- |
| `translater` | Converts user input into clear instruction segments. |
| `dispatcher` | Splits input into independent **TOPICs** and verbatim phrases. |
| `titler` | Generates professional titles for grouped **REQUESTs**. |
| `planner` | (Strategic Planner) Drafts high-level strategic roadmaps. |
| `engineer` | (Technical Analyst) Performs tool selection and technical step analysis. |
| `refiner` | (Workflow Synthesizer) Merges strategy and analysis into a final workflow. |
| `auditor` | Validates workflows against a risk knowledge base (`risks.json`). |

---
*Status: Development in progress (Auditing Phase implemented)*
