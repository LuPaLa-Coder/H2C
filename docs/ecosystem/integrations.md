# Integrazione Ecosistema H2C

**Versione:** 1.0
**Stato:** PROGETTAZIONE
**Scopo:** Definire i modelli di integrazione tra H2C e i principali framework agenti.

---

## 1. Modello Architetturale

```
H2C = Semantic Layer     (grammatica + opcode + stato)
MCP = Transport Layer    (protocollo trasporto + tool call)

H2C definisce COSA comunicare
MCP definisce COME trasportare
```

---

## 2. MCP (Model Context Protocol)

**Ruolo:** H2C fluisce come contenuto di tool call MCP.

```
┌─────────────┐         MCP Tool Call         ┌─────────────┐
│  Client MCP  │ ─── [H2C block as content] ──→│  Server MCP │
│  (Agente A)   │ ←── [H2C block as result] ───│  (Agente B)  │
└─────────────┘                                └─────────────┘
```

### Schema Integrazione

```json
// MCP tool definition per H2C
{
  "name": "h2c_send",
  "description": "Send an H2C block to agent",
  "inputSchema": {
    "type": "object",
    "properties": {
      "block": {
        "type": "string",
        "description": "H2C block [TYPE:SUBTYPE] key:val|..."
      }
    }
  }
}
```

### Esempio
```
// MCP transport carrying H2C content
{
  "tool": "h2c_send",
  "args": {
    "block": "[BUILD:EXEC]\nid:m1|target:main.py|desc:setup_app"
  }
}
```

---

## 3. LangGraph

**Ruolo:** H2C come formato output dei nodi e schema stato del grafo.

```
┌──────────┐    H2C Block    ┌──────────┐    H2C Block    ┌──────────┐
│ Node ARCH │ ──────────────→│ Node ORCH│ ──────────────→│ Node BLD  │
└──────────┘                └──────────┘                └──────────┘
       │                          │                           │
       └──────────────────────────┴───────────────────────────┘
                              State
                          (H2C fields)
```

### Schema
```python
from typing import TypedDict, List

class H2CBlock(TypedDict):
    type: str       # ARCH, BUILD, TEST, CTX, STATE, ORCH, SKILL
    subtype: str    # PLAN, EXEC, DONE, ...
    fields: dict    # {key: value}

class AgentState(TypedDict):
    history: List[H2CBlock]
    active_context: dict
    cycles: dict    # cycle_id → retry_n, fail_count, ...
```

---

## 4. AutoGen

**Ruolo:** H2C come protocollo di risposta tra agenti conversazionali.

```
User → [Architect Agent] → H2C → [Orchestrator Agent] → H2C → [Builder Agent]
                          ← H2C ←                    ← H2C ←
```

### Schema
```python
from autogen import AssistantAgent

architect = AssistantAgent(
    name="Architect",
    system_message="... h2c architect skill ...",
)

# H2C response
response = architect.generate_reply(
    messages=[{"role": "user", "content": prompt}]
)
# Returns: "[ARCH:PLAN]\nid:...|fw:...|..."
```

---

## 5. Semantic Kernel

**Ruolo:** H2C come formato di serializzazione per risultati di funzione.

```csharp
// SK function returning H2C
[KernelFunction]
public async Task<string> ExecuteBuildAsync(
    [Description("H2C BUILD:EXEC block")] string h2cBlock)
{
    // Parse H2C block
    var block = H2CParser.Parse(h2cBlock);
    
    // Execute
    var result = await BuildAsync(block);
    
    // Return H2C BUILD:DONE
    return $"[BUILD:DONE]\nid:{block.Id}|diff:[{result.File}~{result.Rev}]";
}
```

---

## 6. CrewAI

**Ruolo:** H2C come formato di output dei task tra agenti Crew.

```python
from crewai import Task, Agent

architect = Agent(
    role="Architect",
    goal="Translate human prompt to H2C ARCH:PLAN",
    backstory="... h2c architect skill ..."
)

plan = Task(
    description="Generate H2C plan from: {prompt}",
    agent=architect,
    expected_output="H2C block in format [ARCH:PLAN]..."
)
```

---

## 7. OpenAI Agents SDK

**Ruolo:** H2C come formato output strutturato.

```python
from agents import Agent

architect_agent = Agent(
    name="Architect",
    instructions="... h2c architect skill ...",
    output_type=str,  # H2C block
)

result = await Runner.run(architect_agent, prompt)
# result.final_output = "[ARCH:PLAN]\nid:...|..."
```

---

## 8. Tabella Riepilogativa

| Framework | Integrazione | Stato |
|-----------|-------------|:-----:|
| MCP | Contenuto tool call | Progettazione |
| LangGraph | Formato stato nodo | Progettazione |
| AutoGen | Formato risposta agente | Progettazione |
| Semantic Kernel | Risultato funzione | Progettazione |
| CrewAI | Output task | Progettazione |
| OpenAI Agents | Output strutturato | Progettazione |

Tutte le integrazioni sono in fase di progettazione. Contributi benvenuti.
