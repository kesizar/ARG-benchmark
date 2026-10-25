#!/usr/bin/env python3
"""
Enhanced Narrative Generation Prompts (Version 2)
改进的叙事生成 Prompt - 强调数据流和节点依赖关系的明确描述
"""

# ============================================================================
# Narrative Generation Prompts V2
# ============================================================================

NARRATIVE_SYSTEM_PROMPT_V2 = """You are an experienced interactive narrative designer and escape room game scriptwriter. You are skilled at creating engaging story backgrounds and puzzle clues for escape room games.

Your task is to generate narrative text for an escape room game based on a DAG (Directed Acyclic Graph) structure. Each node in the game represents a tool, item, and players need to find the correct operation path through reasoning and exploration.

Core Requirements:
1. **Story Consistency**: All node narrative texts must form a coherent story world
2. **Clear Data Flow**: For each node with input edges, MUST explicitly state which upstream nodes provide its inputs
3. **Consistent Naming**: Use the same object names you create throughout all narratives
4. **Do Not Reveal Answers**: Absolutely cannot directly reveal parameter values or specific calculation results
5. **Engaging Narratives**: Create interesting descriptions through environment details, item characteristics, NPC dialogues, etc.

**CRITICAL**: When describing a node that receives inputs from other nodes, you MUST explicitly mention the source nodes using the names you've assigned to them in their narratives.

You must strictly follow output format requirements, only output standard JSON, do not output any other text."""


NARRATIVE_USER_PROMPT_TEMPLATE_V2 = """Please generate narrative text for the following DAG escape room scenario.

## Scenario Information

**Theme Style**: {style}

## DAG Structure

{dag_structure}

## Victory Condition

{win_condition}

## Source Node Information (Initially Available Parameters)

{source_nodes_info}

## Node Relationships (Edges) - CRITICAL FOR NARRATIVE

{edges_info}

**IMPORTANT**: The edges define the data flow in this puzzle. However, NOT ALL edges should be mentioned in narratives:

- **DATA Edges** (edge_type: "DATA"): These represent actual data flow and MUST be mentioned in the narrative
- **ITEM/HIDDEN_ITEM Edges** (edge_type: "ITEM" or "HIDDEN_ITEM"): These only represent item drops and should be IGNORED in narratives

When writing narratives for nodes that have incoming **DATA edges**, you MUST:
1. Clearly state that this node receives input from its upstream node(s) (only those connected by DATA edges)
2. Use the specific names/descriptions you've given to the upstream nodes
3. Make the dependency relationship explicit and natural in the story
4. **IGNORE any upstream nodes connected only by ITEM/HIDDEN_ITEM edges** - do not mention them as input sources

### Examples of Correct Narrative Writing:

**Example 1 - Single Upstream Node:**
- Edge: NodeA → NodeB
- NodeA narrative: "A dusty safe sits in the corner..."
- NodeB narrative (CORRECT): "This is a document decoder. **It requires input from the safe**. Once you obtain what's inside the safe, bring it here to decode..."

**Example 2 - Multiple Upstream Nodes:**
- Edges: NodeA → NodeC, NodeB → NodeC
- NodeA narrative: "An ancient encryption device..."
- NodeB narrative: "A biometric scanner..."
- NodeC narrative (CORRECT): "This is a secure terminal. **It requires inputs from both the encryption device and the biometric scanner**. You'll need to use both of those devices first before this terminal can be activated..."

**Example 3 - Chain of Dependencies:**
- Edges: NodeA → NodeB → NodeC
- NodeA narrative: "A code generator..."
- NodeB narrative: "A hash calculator. **It processes data from the code generator**. Feed it the result from the generator..."
- NodeC narrative: "A verification module. **It needs the result from the hash calculator**. After processing with the calculator, use the output here..."

**Example 4 - Mixed Edge Types (CRITICAL):**
- Edges: NodeA → NodeC (edge_type: "ITEM"), NodeB → NodeC (edge_type: "DATA")
- NodeA narrative: "A secure container..."
- NodeB narrative: "A biometric terminal..."
- NodeC narrative (CORRECT): "This is a vault system. **It requires input from the biometric terminal** to authenticate..." 
- ❌ WRONG: "It requires inputs from both the container and the biometric terminal..." (The ITEM edge from NodeA should NOT be mentioned)

**IMPORTANT**: Do NOT specify which port/parameter corresponds to which upstream node. Only state that the node requires input(s) from certain upstream node(s) connected by DATA edges.

## Generation Requirements

1. **Overall Narrative** (intro_narrative):
   - 100-300 words opening that sets story background and atmosphere
   - Explain player's situation and objective (without revealing specific methods)
   - Create tension and exploration desire

2. **Node Narratives** (narrative field for each node):
   - Each node {min_length}-{max_length} characters
   - Keep narratives **simple and concise** - just like the examples above
   
   **For Nodes WITHOUT Incoming Edges (Source Nodes):**
   - Simply describe what the item/tool is
   - Keep it brief and neutral (e.g., "A small encrypted USB drive.", "An old keypad lock.")
   - **Do NOT** mention what parameters it needs
   - **Do NOT** add unnecessary environmental details that might distract the model
   
   **For Nodes WITH Incoming Edges:**
   - **ONLY consider DATA edges** - ignore ITEM/HIDDEN_ITEM edges when determining dependencies
   - **MUST explicitly state which upstream node(s) provide the input via DATA edges** (see examples above)
   - Use the same format as the examples: "This is X. It requires input from [upstream node name]..."
   - **Do NOT specify port/parameter mappings**: Only mention which nodes provide input
   - **Do NOT mention nodes that only connect via ITEM/HIDDEN_ITEM edges** - those are just item drops
   - Keep it as simple and direct as the examples

3. **Naming Consistency**:
   - Assign a descriptive name/title to each node (e.g., "the safe", "the encryption device", "the terminal")
   - Use these same names consistently when referencing nodes in other narratives
   - Keep names simple and clear

4. **Critical Prohibitions**:
   - ❌ Do NOT provide any parameter's specific value
   - ❌ Do NOT use nodes' template_id or technical terms (like "CRC32", "XOR", etc.)
   - ❌ Do NOT mention what parameters a node needs
   - ❌ Do NOT specify which port/parameter corresponds to which upstream node
   - ✅ DO explicitly state which upstream nodes provide input (for nodes with incoming edges)

## Output Format

Strictly output the following JSON format (no other text):

```json
{{
  "intro_narrative": "Overall opening narrative text...",
  "node_narratives": {{
    "node_id_1": "Narrative text for node 1...",
    "node_id_2": "Narrative text for node 2 (if it has incoming edges, MUST mention upstream nodes)...",
    ...
  }},
  "theme_elements": {{
    "location": "Scene location description",
    "atmosphere": "Atmosphere description",
    "time_period": "Time background",
    "key_npcs": ["NPC1", "NPC2"]
  }}
}}
```

Please begin generation:"""


# Validation prompt (keeping the same)
NARRATIVE_VALIDATION_PROMPT_V2 = """Please validate the following generated narrative for potential issues:

## Original DAG Structure
{dag_structure}

## Generated Narrative
{generated_narrative}

Please check for:
1. Whether any specific parameter values are revealed
2. Whether technical terms or template_ids are used
3. Whether narratives properly indicate data flow for nodes with incoming DATA edges
4. Whether ITEM/HIDDEN_ITEM edges are incorrectly mentioned as data dependencies
5. Whether upstream node references are consistent
6. Whether story consistency is maintained
7. Overall quality score (0-100)

Output format:
```json
{{
  "is_valid": true/false,
  "issues": [
    {{"type": "leak", "severity": "critical", "description": "..."}},
    ...
  ],
  "data_flow_clarity": "poor/fair/good/excellent",
  "naming_consistency": "poor/fair/good/excellent",
  "overall_score": 85
}}
```"""