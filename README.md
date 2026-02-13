# Recursive Yak Shaver (RYS)

**Recursive Yak Shaver (RYS)** is an autonomous multi-agent pipeline designed to transform ambiguous natural language instructions into safe, atomic, and executable shell operations. Powered by Gemma-3N, it handles translation, planning, implementation, and verification through a rigorous 6-phase process.

## 🚀 Key Architectural Pillars

- **Mono-Role Responsibility**: Each phase is governed by a single, specialized role (Engineer for planning, Coder for implementation) to ensure focused reasoning and prevent logic leakage.
- **Golden Pattern Adherence**: Standardized file operations follow a strict "Golden Pattern": `find` -> `du` -> `sort` -> `head` -> `cut` -> `cat`.
- **Atomic Command Fragments**: The system enforces "One Command per Step" logic. Snippets are treated as pure pipe segments, stripped of redundant prefixes or nested pipe chains.
- **Affirmative Control**: All role directives and cheatsheets use purely affirmative language ("Do this") to maximize LLM instruction-following and stability.

## 🛠 The 6-Phase Pipeline

### Phase 1: Translation (Translater)
Normalizes ambiguous, multi-lingual user input into clear, standardized English tasks.

### Phase 2: Dispatch (Dispatcher)
Categorizes tasks into specific domains and assigns the appropriate **Skill** (e.g., `shell_exec`, `python_math`). This phase acts as the primary router for domain-specific knowledge.

### Phase 3: Visualization (Titler)
Organizes tasks into logical request groups with descriptive titles for transparency.

### Phase 4: Strategic Planning (Engineer)
Utilizes the assigned **Skill Context** to design a roadmap. The Engineer breaks down the goal into atomic milestones, ensuring each milestone represents exactly one logical transformation (e.g., "Milestone 3: Sort data").

### Phase 5: Step-by-Step Coding (Coder)
Implements the roadmap milestones. For each step:
1. **Context Injection**: The Coder receives the specific milestone task and the corresponding **Skill Cheatsheet** (GoodParts).
2. **Affirmative Implementation**: The Coder generates a single, atomic command fragment based on the cheatsheet patterns.
3. **Pipe Stripper**: The system automatically extracts the last segment of the generated code to ensure no redundancy and strict adherence to the pipeline flow.

### Phase 6: Execution Loop
Aggregates snippets into a native shell or Python orchestrator, provides a final review, and executes the sequence.

## 📖 Skills & Cheatsheets

Skills are not just tool labels; they are the **Knowledge Anchors** of the system.
- **Planning**: In Phase 4, skills provide the Engineer with the "vocabulary" of available tools.
- **Implementation**: In Phase 5, skills provide the Coder with "best-practice patterns," forcing the model to mirror the exact syntax defined in `config/skills/*.json`.

## 🛡 Security & Reliability

- **Auditor Role**: Plans are checked against a Risk Knowledge Base before execution.
- **Granular Caching**: Every step is cached. Use `RYS_FORCE_CACHE=1` to debug specific milestones and verify granular logic without re-running stable phases.

## ⚖️ License
MIT License
