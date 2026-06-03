# H2C Ecosystem Integration

**Version:** 1.0
**Status:** DRAFT
**Scope:** Define integration patterns between H2C and major agent frameworks.

---

## 1. Architectural Model

```
H2C = Semantic Layer     (grammar + opcode + state)
MCP = Transport Layer    (transport protocol + tool call)

H2C defines WHAT to communicate
MCP defines HOW to transport
```

---

## 2. MCP (Model Context Protocol)

**Role:** H2C flows as MCP tool call content.

```
┌─────────────┐         MCP Tool Call         ┌─────────────┐
│  MCP Client │ ─── [H2C block as content] ──→│  MCP Server │
│  (Agent A)  │ ←── [H2C block as result ] ───│  (Agent B)  │
└─────────────┘                               └─────────────┘
```

### Integration Schema

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

### Example
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

**Role:** H2C as node output format and graph state schema.

```
┌───────────┐    H2C Block   ┌──────────┐    H2C Block   ┌──────────┐
│ Node ARCH │ ──────────────→│ Node ORCH│ ──────────────→│ Node BLD │
└───────────┘                └──────────┘                └──────────┘
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

**Role:** H2C as response protocol between conversational agents.

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

**Role:** H2C as serialization format for function results.

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

**Role:** H2C as task output format between Crew agents.

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

**Role:** H2C as structured output format.

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

## 8. Summary Table

| Framework | Integration | Status |
|-----------|-------------|:------:|
| MCP | Tool call content | Design |
| LangGraph | Node state format | Design |
| AutoGen | Agent response format | Design |
| Semantic Kernel | Function result | Design |
| CrewAI | Task output | Design |
| OpenAI Agents | Structured output | Design |

All integrations are in the design phase. Contributions welcome.
