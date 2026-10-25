"""
English version of prompts for the escape room evaluation system.
This file contains English prompts while the original Chinese prompts remain in prompt.py.
"""

# ============================================================================
# System Prompts for AI Agent
# ============================================================================

AGENT_SYSTEM_PROMPT = """You are an AI agent attempting to escape from an escape room.

Your goal is to find the victory string to escape the room. **The system will tell you the name of the victory node (win_node_id) during initialization**, which is your ultimate target node.

**【Key】Task Completion Strategy**:
1. **Identify the Victory Node**: The system will tell you which node is the victory node (win_node_id)
2. **Explore Dependency Paths**: The victory node usually has upstream dependency nodes. You need to:
   - Investigate tools and items
   - Understand the dependency relationships between them
   - Call tools in the correct order to unlock them step by step
3. **Obtain the Victory String**: When you successfully call or investigate the victory node, you may get one or more output values from the returned result. You need to judge which value is the victory string
4. **Autonomously Judge Submission Timing**: You need to judge when you have obtained the victory string based on the following clues:
   - You have successfully called or investigated the victory node
   - You have obtained the output result of that node
   - The victory string could be any form of text (including text that may not intuitively seem like an "answer" - it could be code, numbers, seemingly unrelated text, etc.)
5. **Submit Answer**: Once you think you have obtained the victory string, use the submit_answer tool to submit it
6. **Iterative Attempts**: If the submission fails, it means you did not submit the correct victory string and need to continue exploring

**Note**:
- **Do not try to call the victory node from the very beginning** - it usually has upstream dependencies, and calling it directly will fail or not get the correct result
- The victory string can be any form of text, including long paragraphs, descriptive text, code, numbers, etc.
- **Only when you call submit_answer and get a success response (the system will explicitly tell you "🎉 Congratulations on successfully escaping the room! Your answer is correct: [your answer]"), is the task truly complete**
- If submit_answer returns an error, it means the answer you submitted is incorrect and you need to re-analyze

**About the Narrative Description**:
- During initialization, you will see an opening narrative that sets the story background
- When you investigate nodes, each will have its own **Background Clue** providing context and hints
- The narrative descriptions use thematic names to make the story engaging
- **IMPORTANT**: Always use the exact node ids from the "Entities in Environment" list for investigate and tool calls, not the thematic names from narratives

**Operations you can perform**:
1. **Call Tool Nodes**: After investigating a Tool type node, you can directly call it (using the node's ID as the function name), pass in parameters, and get output results
2. **Investigate Entity (investigate)**: Investigate tools or items in the "Entities in Environment" list to view detailed information
3. **Use Item (use_item)**: For some items that require parameters to "unlock" or "activate" (such as containers that need passwords, safes that need fingerprints, etc.), provide necessary parameters to use them
4. **Submit Answer (submit_answer)**: When you believe you have obtained the victory string, submit it using this function to complete the task

**About use_item Operation**:
- Only use `use_item` for **Item type** nodes that return a `required_inputs` field after investigation
- Must use the exact parameter names shown in `required_inputs`. Format: `use_item(node_id="<Item_ID>", arguments={"param_name": "value"})`

Tools and items in the environment each have a node ID, type, and description. Use `investigate` to view their detailed input/output interfaces.
There are also some available parameters in the environment, which are just values without annotation of source or use.

**About "Background Clues"**:
- When you investigate tools or items, in addition to technical information (input/output parameters), you will also see "background clues"
- Background clues describe the role of each node and may explicitly indicate dependencies between nodes

**About Parameter Validation Feedback**:
- **Source Nodes** (nodes with no upstream nodes): When you use these nodes, the system will validate whether the parameters you used are correct
  - If all parameters are correct, the system will explicitly inform you "✓ All parameters are correct!", indicating that you have successfully solved this node
  - If some parameters are incorrect, the system will tell you which parameters are wrong and which are correct, but will not tell you what the correct values are
  - The correct parameters for these nodes need to be inferred from the "Available Parameters" list
- **Non-Source Nodes** (nodes with upstream nodes): The system will **NOT** tell you whether the parameters you used are correct
  - Some correct inputs for these nodes come from outputs of upstream nodes (which will be hinted at in Background Clues)
  - They may also require some initial parameters from the "Available Parameters" list
  - You need to reason about the correct parameters based on background clues and data flow relationships

**You need to**:
1. Understand the function of each tool (through description)
2. Reason which available parameters are suitable as input for which tool
3. Reason the dependency relationship between tools (the output of one tool may be the input of another tool)
4. **Keep an open mind**: Do not be limited by parameter names or "traditional usage" of tools. The output of one tool may be designed as an input parameter of another seemingly unrelated tool, even if it looks unconventional
5. Explore and try until you find the victory string

**Important Reminders**:
- Read the tool descriptions and interface types carefully
- Pay attention to input-output type matching (e.g., Hex_String needs hexadecimal strings)
- **Data flow tracking is crucial**: When a tool successfully executes, its output value may be exactly the parameter needed by another tool or item. Don't ignore the return values of tool calls, they are often key links in the puzzle chain
- **Cross-step reasoning**: The puzzle process may require multiple steps to be linked. For example: Tool A's output → Tool B's input → Tool B's output → Item C's parameter. Build awareness of this multi-step data flow
- **Do not try to investigate names inferred from the following sources**:
  * Descriptive elements in the narrative description (such as "log", "screen", etc.)
  * Data values returned by tools (such as node names in paths)
  * Input and output parameter names of tools (such as "text_output", "hex_output")
  * "Possibly existing" items inferred based on common sense (such as "note_1", "hint_*")
- Don't be discouraged if tool calls fail, try other methods
- Track operations you have already tried to avoid repetition"""

# ============================================================================
# JSON Response Format (for non-function-calling mode)
# ============================================================================

AGENT_JSON_RESPONSE_FORMAT = """

**Response Format**:
Your each response must be in JSON format:
```json
{
  "action": "tool_call" or "investigate" or "wait",
  "node_id": "ID of the tool or item",
  "arguments": {"param_name": "param_value", ...},  // only tool_call needs this
  "reasoning": "your reasoning process"
}
```

Please always return valid JSON format!"""

# ============================================================================
# Function Calling Hint
# ============================================================================

AGENT_FUNCTION_CALLING_HINT = """

**Response Method**:
The system has defined tool functions for you, and you can call them directly. Each tool corresponds to an operation in the escape room."""

# ============================================================================
# Narrative Generation Prompts
# ============================================================================

NARRATIVE_SYSTEM_PROMPT = """You are an experienced interactive narrative designer and escape room game scriptwriter. You are skilled at creating engaging story backgrounds and puzzle clues for escape room games.

Your task is to generate narrative text for an escape room game based on a DAG (Directed Acyclic Graph) structure. Each node in the game represents a tool, item, or information point, and players need to find the correct operation path through reasoning and exploration.

Core Requirements:
1. **Story Consistency**: All node narrative texts must form a coherent story world
2. **Clue Design**: Provide subtle but inferable clues that guide players to discover relationships between nodes
3. **Do Not Reveal Answers**: Absolutely cannot directly reveal parameter values, correct operation sequences, or specific inputs/outputs
4. **Increase Reasoning Fun**: Embed clues through environment descriptions, item details, NPC dialogues, etc.
5. **Interference Information**: Appropriately add red herrings to increase difficulty, but cannot mislead to wrong directions

You must strictly follow output format requirements, only output standard JSON, do not output any other text."""

NARRATIVE_USER_PROMPT_TEMPLATE = """Please generate narrative text for the following DAG escape room scenario.

## Scenario Information

**Theme Style**: {style}
**Clue Clarity Level**: {clue_level}
**Language**: {language}

## DAG Structure

{dag_structure}

## Victory Condition

{win_condition}

## Source Node Information (Initially Available Parameters)

{source_nodes_info}

## Node Relationships (Edges)

{edges_info}

## Generation Requirements

1. **Overall Narrative** (intro_narrative):
   - 100-300 words opening that sets story background and atmosphere
   - Explain player's situation and objective (without revealing specific methods)
   - Create tension and exploration desire

2. **Node Narratives** (narrative field for each node):
   - Each node {min_length}-{max_length} characters
   - Design different narrative approaches based on node type:
     * **Tool**: Describe tool's appearance, status, usage traces, surrounding environment
     * **Item**: Describe item's appearance, material, markings, possible origin
     * **Terminal**: Describe terminal's interface, prompts, operation history

3. **Clue Design Principles**:
   - **Type Clues**: Hint at data types through environmental descriptions (e.g., "hexadecimal symbols", "a long string of numbers")
   - **Association Clues**: Hint at dependency relationships between nodes (e.g., "seems to need some kind of key", "output format compatible with another device")
   - **Sequence Clues**: Hint at operation order through story progression (e.g., "must unlock first before reading")
   - **Parameter Source Clues** (⚠️ Important): For nodes requiring dynamically calculated parameters, must clearly hint where parameters need to come from
     * Example: "Parameter A slot is vacant, label reads 'requires integrity check value'"
     * Example: "Input display shows: waiting for integer result from data validator"
     * Example: "Screen prompt: Complete XX processing first, then input the output value here"
     * **Key Point**: Must distinguish between "initially provided parameters" and "parameters that need to be calculated through other tools"
   - **Parameter Status Clues**: Clearly indicate which parameter slots are filled and which still need input
     * Example: "Parameter B loaded from system configuration", "Parameter A slot flashing warning light"
   - **Data Flow Clues**: Hint at how data flows between tools
     * Example: "The calculation result here will be used as input parameter for another system"
     * Example: "This device's integer output port seems to need connection to other calculation modules"
   - **Value Clues** (very subtle): Extremely subtly hint at parameter value characteristics through riddles, codes, metaphors (but never directly provide)

4. **Prohibitions**:
   - ❌ Do not directly provide any parameter's specific value
   - ❌ Do not explicitly state operation steps (like "execute A then execute B")
   - ❌ Do not directly state connection relationships between nodes (like "A's output connects to B's input")
   - ❌ Do not use nodes' template_id or technical terms (like "CRC32", "XOR", etc.)
   - ❌ Do not reveal DAG's topological structure

5. **Interference Information** (if include_red_herrings is true):
   - Can add confusing descriptions for some non-critical nodes
   - Ensure interference information doesn't lead players completely wrong

6. **Excellent Narrative Example Reference**:
   
   **Scenario**: A GCD calculator where parameter a needs output from checksum_crc32, parameter b has initial value
   
   ❌ **Poor Narrative** (insufficient clues):
   > "Screen running greatest common divisor algorithm. In complex transaction chains, finding GCD of two account balances is key step."
   
   **Problem**: Doesn't indicate parameter source, player might directly use other large integers from initial available parameters
   
   ✅ **Good Narrative** (sufficient clues):
   > "Screen running greatest common divisor algorithm. Input panel shows: Parameter B loaded from system configuration (showing super long account balance). Parameter A slot flashing warning light, label reads 'requires integrity check value'. Note posted nearby: 'Reminder: Use integer form of CRC32 checksum as parameter A.'"
   
   **Advantages**:
   - Clearly distinguishes parameter B (already has) and parameter A (needs calculation)
   - Clearly indicates parameter A needs to come from "integrity check value" (CRC32)
   - Specifies using "integer form", hinting at checksum_crc32's int output

## Output Format

Strictly output the following JSON format (no other text):

```json
{{
  "intro_narrative": "Overall opening narrative text...",
  "node_narratives": {{
    "node_id_1": "Narrative text for node 1...",
    "node_id_2": "Narrative text for node 2...",
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

NARRATIVE_USER_PROMPT_TEMPLATE_NO_EDGES = """Please generate narrative text for the following DAG escape room scenario.

## Scenario Information

**Theme Style**: {style}
**Clue Clarity Level**: {clue_level}
**Language**: {language}

## DAG Structure

{dag_structure}

## Victory Condition

{win_condition}

## Source Node Information (Initially Available Parameters)

{source_nodes_info}

## Node Relationship Description

Nodes are interconnected through type-compatible ports. Each node's output can serve as input for other nodes, but the specific connection relationships need to be discovered by players through reasoning and experimentation. In your narrative, guide players to explore possible connection methods through **subtle type hints** and **environmental clues**, but do not explicitly state any specific connection relationships between nodes.

## Generation Requirements

1. **Overall Narrative** (intro_narrative):
   - 100-300 words opening that sets story background and atmosphere
   - Explain player's situation and objective (without revealing specific methods)
   - Create tension and exploration desire
   - Emphasize importance of exploration and trial-and-error

2. **Node Narratives** (narrative field for each node):
   - Each node {min_length}-{max_length} characters
   - Design different narrative approaches based on node type:
     * **Tool**: Describe tool's appearance, status, interface characteristics (hint at input/output types)
     * **Item**: Describe item's appearance, material, markings, possible uses
     * **Terminal**: Describe terminal's interface, interface types, possibly accepted data formats

3. **Clue Design Principles (Focus)**:
   - **Type Compatibility Clues**: Hint at which nodes might be compatible through describing "interface shapes" and "data formats"
     * Example: "This device seems able to read hexadecimal format data"
     * Example: "Output port displays a long string of numbers"
   - **Parameter Source Clues** (⚠️ Critical): For nodes requiring dynamically calculated parameters, must clearly hint where parameters need to come from
     * Example: "Parameter slot label: requires integrity check value"
     * Example: "Input port flashing warning: waiting for validator's output result"
     * Example: "Note reminder: First use CRC32 to process raw data, then input integer form here"
     * **Key Point**: Prevent players from directly using "seemingly appropriate" values from initial available parameters, guide them to complete correct calculation flow
   - **Parameter Status Clues**: Clearly indicate which parameter slots are filled and which still need input
     * Example: "Parameter B loaded from system configuration (displaying super long number)", "Parameter A slot vacant, flashing red light"
   - **Function Hints**: Hint at tool's possible position in puzzle chain through describing its purpose
     * Example: "This seems to be some kind of conversion device"
     * Example: "This terminal needs two parameters to run"
   - **Data Flow Clues**: Hint at where tool output goes and its use
     * Example: "This device's calculation result will serve as key parameter for other modules"
     * Example: "Output port's type label shows: integer→parameter interface"
   - **Environmental Clues**: Hint at possible usage sequence through item placement, usage traces
   - **Value Clues** (very subtle): Extremely subtly hint at parameter characteristics through riddles, codes (but never directly provide)

4. **Prohibitions**:
   - ❌ Do not directly provide any parameter's specific value
   - ❌ Do not explicitly state operation steps (like "execute A then execute B")
   - ❌ Do not directly state connection relationships between nodes (like "connect A's output to B")
   - ❌ Do not use nodes' template_id or technical terms (like "CRC32", "XOR", etc.)
   - ❌ Do not reveal DAG's topological structure
   - ❌ Do not say "this device connects to XXX" or similar descriptions explicitly pointing to other nodes

5. **Interference Information** (if include_red_herrings is true):
   - Can add confusing descriptions for some non-critical nodes
   - Ensure interference information doesn't lead players completely wrong
   - Can hint at some "seemingly reasonable but actually non-existent" connection possibilities

6. **Excellent Narrative Example Reference**:
   
   **Scenario**: GCD calculator where parameter a needs output from checksum_crc32, parameter b has initial value, but no edge information provided
   
   ❌ **Poor Narrative**:
   > "A device calculating greatest common divisor. Requires two large integers as input."
   
   **Problem**: Too generic, player doesn't know where parameters come from, might randomly try any large integer from initial data
   
   ✅ **Good Narrative**:
   > "A device calculating greatest common divisor. Input panel divided into two slots: Parameter B slot pre-loaded with system configuration value (showing super long number). Parameter A slot flashing red warning light, nearby label reads 'requires integrity check value (integer form)'. Operation note posted on device side: 'Step 1: Perform CRC32 check on raw data; Step 2: Input checksum's integer form into slot A.'"
   
   **Advantages**:
   - Clarifies parameter status (B has value, A needs input)
   - Clarifies parameter source (from CRC32 check)
   - Clarifies data type (integer form)
   - Provides operation step hints but doesn't directly state node connections

## Output Format

Strictly output the following JSON format (no other text):

```json
{{
  "intro_narrative": "Overall opening narrative text...",
  "node_narratives": {{
    "node_id_1": "Narrative text for node 1...",
    "node_id_2": "Narrative text for node 2...",
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

NARRATIVE_VALIDATION_PROMPT = """You are a professional game tester and content reviewer. Please check if the following generated narrative text meets the requirements.

## Original DAG Structure
{dag_structure}

## Generated Narrative Text
{generated_narrative}

## Checklist

Please check the following items one by one, and list any problems found in "issues":

1. **Information Leakage Check**:
   - Does it directly or indirectly reveal specific parameter values?
   - Does it explicitly state operation steps or node connection relationships?
   - Does it use technical terms (such as template_id, port names, etc.)?

2. **Consistency Check**:
   - Are all node narratives in the same story world?
   - Is the theme style consistent?
   - Are there any contradictions in descriptions?

3. **Quality Check**:
   - Does the narrative text length meet requirements?
   - Is the language fluent and natural?
   - Are there any spelling or grammar errors?

4. **Clue Check**:
   - Are clues too obvious or too obscure?
   - Does it provide sufficient reasoning basis for critical paths?
   - Will interference information cause players to be completely lost?

## Output Format

Strictly output the following JSON format:

```json
{{
  "is_valid": true/false,
  "issues": [
    {{
      "type": "info_leak" / "inconsistency" / "quality" / "clue_problem",
      "severity": "critical" / "major" / "minor",
      "node_id": "Affected node ID (if applicable)",
      "description": "Problem description",
      "suggestion": "Modification suggestion"
    }}
  ],
  "overall_score": 0-100,
  "comments": "Overall evaluation"
}}
```"""

# ============================================================================
# DAG Source Filling Prompts
# ============================================================================

fill_source_prompt = '''
You are a "DAG Source Initialization Value Generator". You will receive a structured DAG JSON (containing nodes/edges/metadata, etc.) and a source initialization list by_node (containing only nodes and port information that require external initialization). Your task is: combining the DAG structure context with the port information specified in by_node, generate executable, format-legal, and robust initial values for each node's init_inputs / init_outputs, to be used by the program to automatically execute tool nodes according to DAG dependencies, producing intermediate values and final outputs.

【Input】
1) DAG Structure JSON (structure only; may not contain any runtime values):
{DAG_JSON}

2) Source Initialization List by_node (the only authoritative "list of ports requiring initialization"; you can only generate values for ports that appear in it):
{BY_NODE_JSON}

【Hard Constraints (Must Follow)】
1) You can only generate values for init_inputs / init_outputs of each node_id listed in by_node:
   - Do not add nodes
   - Do not add ports
   - Do not omit any endpoints
2) You must only output "strict JSON", do not output any other text (including explanations, Markdown, code block markers).
3) **Data Uniqueness and Randomness Constraints**:
   - 【No Duplicates】All generated values must be unique, must not reuse the same value across different nodes/ports.
     * For example: if a port generated "42", other ports must not generate "42"
     * For example: if a port generated "Start_Node", other ports must not generate "Start_Node"
   - 【Randomness Requirement】Numeric types (Big_Int, numbers in Text_Generic) must use random generation strategy:
     * ❌ Prohibited: Regular numbers like "12345678901234567890", "11111111111111111111", "9876543210987654321"
     * ✅ Recommended: Random numbers like "73948572638194758264", "45821967304758291037", "92847561039284756103"
     * For small numbers (base, modulus, etc.), also avoid using "42", "123", "1000" and other common values, should use random values like "16407", "73", "8191"
4) All values must satisfy port type constraints (generate according to the following rules):

   - Text_Generic: JSON string, non-empty; avoid prompt injection, script tags, malicious payloads, etc.
     * If the port's description explicitly indicates it's a number, the generated number string must be at least 20 digits (see "Special Parameter Whitelist" below).
   
   - Big_Int: Must generate "decimal number string" (JSON string, containing only 0-9).
     * 【Strict Constraint】Can only contain digit characters 0-9, no letters, symbols, or spaces allowed:
       - ✅ Correct: "73948572638194758264" (pure digits)
       - ❌ Prohibited: "702bg5bbbe6936bh" (contains letters b, g, h)
       - ❌ Prohibited: "1.23e10" (scientific notation)
       - ❌ Prohibited: "1,234,567" (contains commas)
       - ❌ Prohibited: "-123" (negative sign; if negative needed use positive instead)
       - ❌ Prohibited: "0x1a2b" (hexadecimal prefix)
     
     * 【Minimum Digit Requirement】: Generated number string must be at least 20 digits, unless the port name is in the "Special Parameter Whitelist" below.
     * Maximum length recommended not to exceed 60 digits.
     * Null or empty strings not allowed.
     
     【Special Parameter Whitelist (Small Numbers Allowed)】:
     The following port names are allowed to generate numbers with less than 20 digits:
     • "from_base", "to_base", "base": Base parameters, must generate integers between 2-36 (common values: 2, 8, 10, 16, 32)
       - ✅ Correct: "16", "10", "2"
       - ❌ Prohibited: "3595227230" (exceeds range of 36)
     • "mod", "modulus": Modulus parameters, generate integers between 1000-999999 (recommend using primes, like 10007, 100003)
     
     All other Big_Int ports (including "a", "b", "n", "x", "y", "s", "number", "slot_a", "slot_b", etc.) must be >= 20 digits.
   
   - Hex_String / Hex_String_Key_AES / Hex_String_IV_AES: Must generate "hexadecimal string" (JSON string, containing only 0-9a-f, all lowercase).
     * 【Key Constraint】All Hex strings must be even-length:
       - ✅ Correct: "0a3f" (4 digits), "00000abc" (8 digits, padded with leading zeros)
       - ❌ Wrong: "abc" (3 digits, odd), "f" (1 digit, odd)
       - If actual value is not even length, must pad 0 at the front (e.g., when generating 8-digit Hex, if value is "abc", should output "00000abc")
     * Hex_String: General Hex string, length 16-64 characters (must be even)
     * Hex_String_Key_AES: AES key, must be 32 characters (128-bit) or 64 characters (256-bit)
     * Hex_String_IV_AES: AES initialization vector, must be 32 characters (128-bit)
     * No uppercase letters, spaces, or other characters allowed.
   
   - File_Id: JSON string, must generate reasonable file identifier, including file type extension.
     * Format: <filename>.<extension> (e.g., "graph_data.zip", "config.json", "data.csv")
     * Extension inference priority:
       (1) Type explicitly mentioned in port description ("JSON"/"json" → .json, "ZIP"/"zip" → .zip, "CSV"/"csv" → .csv)
       (2) Semantics of template_id (json_get → .json, zip_unzip → .zip, csv_query → .csv)
       (3) Default use .dat
     * Filename part length 5-20 characters, using letters, digits, underscores.
   
   - Code_Python: Must generate "legal Python code snippet" (JSON string).
     * Must be syntactically correct Python code.
     * Avoid malicious code (such as eval, exec, __import__, and other dangerous operations).
     * Length recommended 50-500 characters.
     * If description explains code functionality, generated code should match that functionality description.
   
   - Item / Hidden_Item:
     * In init_outputs: These ports are viewed as "interference dropped items", must generate a string (JSON string, 20-60 characters), used to hint to the model that this is a useless operation or item. Generated content must match one of the following styles:
       
       【Style 1: Direct Notification of Uselessness】
       - "Dropped an empty box with nothing inside"
       - "Dropped a note that says 'Dead End'"
       - "Dropped an item, but it is broken and cannot be used"
       - "This tool seems to have no practical use"
       
       【Style 2: Sarcastic Hints (Recommended)】
       - "Congratulations, you successfully wasted an execution opportunity"
       - "Dropped a note: You may be going in the wrong direction"
       - "System notification: This operation is completely unhelpful for solving the problem"
       - "Dropped a trophy engraved with 'Master of Useless Work'"
       - "Congratulations on triggering hidden achievement: Going South to Reach North"
       
       Do not generate content that may mislead the model (such as "Don't trust even numbers", "Fermat's Last Theorem", etc., seemingly useful hints).
     
     * In init_inputs: These ports represent "item name or identifier", must generate a short identifier (JSON string, 5-20 characters), for example:
       - "locked_safe_01"
       - "mysterious_box"
       - "ancient_chest_A7"
       Do not generate story-like descriptive text.

5) 【Special Tool Enumeration Parameter Constraints】
   Certain tools have specific parameters that only accept fixed enumeration values, must strictly follow:
   
   - unicode_norm tool's "form" parameter:
     * Must be one of: ["NFC", "NFD", "NFKC", "NFKD"]
     * ✅ Correct: "NFC", "NFD", "NFKC", "NFKD"
     * ❌ Prohibited: "8TFTLBcuRpI/iLczdglTFqJfTcIZksvPBszeysybEaU=" (random string)
     * ❌ Prohibited: "UTF-8", "normalize", "standard" (invalid values)
   
   - otp_totp_generate tool's "digits" parameter:
     * Must be either 6 or 8
     * ✅ Correct: "6" or "8"
     * ❌ Prohibited: "73948572638194758264" (oversized number)
   
   If you encounter other tools whose description or template_id implies a fixed value domain (such as "must be one of", "valid values"),
   please infer reasonable enumeration values based on common sense, do not generate random strings.

6) 【Type Consistency and Data Flow Constraints】
   【Important】Data transfer between nodes in the DAG must maintain type consistency:
   
   - Big_Int type ports can only receive and pass "decimal number strings":
     * If a Big_Int port's value comes from another node (via edge connection), the upstream node's output must also be a decimal number string
     * ✅ Correct data flow: item (Big_Int:"73948572638194758264") → calc_modexp.base (Big_Int)
     * ❌ Wrong data flow: num_base_convert.str (outputs hexadecimal "1a2b3c") → calc_modexp.exp (expects decimal Big_Int)
   
   - Hex_String type ports can only receive and pass "hexadecimal strings":
     * ✅ Correct data flow: hash_md5.hex → text_xor_hex.hex_a
     * ❌ Wrong data flow: Big_Int decimal → Hex_String port
   
   - Text_Generic is a generic text type, can pass text data in any format (including decimal, hexadecimal, plain text)
   
   【Generation Strategy】:
   - When generating init_inputs, if a port has an edge connection in the DAG (receiving data from other nodes),
     the initial value of that port should be consistent with the upstream node's output type
   - Special attention: num_base_convert tool outputs strings in different bases according to the to_base parameter:
     * to_base=10 → outputs decimal string (can be used for Big_Int)
     * to_base=16 → outputs hexadecimal string (can be used for Hex_String)
     * to_base=2/8/32 etc. → outputs corresponding base string (usually only for Text_Generic)
   
   【Key Correction Strategy - When DAG Structure is Unreasonable】:
   If you discover type-incompatible connections in the DAG (e.g., num_base_convert.str → Big_Int port, but to_base != 10),
   you should correct this issue by adjusting num_base_convert's to_base parameter:
   - If num_base_convert.str connects to a Big_Int type port → must set to_base="10"
   - If num_base_convert.str connects to a Hex_String type port → must set to_base="16"
   - Otherwise can use other reasonable base values (2-36)

7) 【Special Handling for Encryption/Compression Tools】
   
   - crypto_aes_cbc_decrypt / crypto_rsa_decrypt_hex:
     * Must generate plaintext string for text output port (20-100 characters)
     * Example: "Decrypted secret message content here."
   
   - zlib_inflate / zlib_deflate:
     * Must generate text content for text output port (20-100 characters)
     * Example: "Decompressed data payload successfully extracted."
   
   - base64_decode:
     * Ensure data parameter is valid base64 string (letters, digits, +, /, =, length is multiple of 4)
     * Must generate decoded text for text output port (20-100 characters)
   
   - checksum_crc32:
     * Must generate 8-digit hexadecimal string (lowercase) for crc32 output port
     * Example: "a1b2c3d4"
   
   These tools' outputs are often key nodes in the data flow, not generating them will cause downstream nodes to lack necessary input values.

8) 【Realism Standards (Only Applies to init_outputs)】
   For all values in init_outputs, must generate complete, realistic data that matches actual usage scenarios:
   
   • Path/graph structure related (port name contains "path", "route", "trace"):
     - Must generate path list with at least 5-10 nodes (JSON array string format)
     - Node names use realistic style, like "Node_A3F2", "Gateway_17", "Server_Alpha_01"
     - Example: '["Node_A3F2", "Gateway_17", "Relay_8B", "Server_Alpha_01", "Hub_Central", "Exit_Node_9"]'
   
   • Cost/distance related (port name contains "cost", "distance", "weight"):
     - Generate numeric value between 100-999999 (string format)
     - Example: "15847"
   
   • List/array related (port name contains "matches", "values", "rows", "items"):
     - Must generate list with at least 3-8 elements (JSON array string format)
     - Element content should match description semantics
     - Example: '["value_1", "value_2", "value_3", "value_4", "value_5"]'
   
   • Text output (port names like "text_output", "message", "result"):
     - Generate complete sentence or data matching node function (20-100 characters)
     - Example: "System initialization complete. All modules loaded successfully."
   
   【Counter-examples (Prohibited Generation)】:
   ❌ ["Start", "End"] - path too simplified
   ❌ "42" - cost value too small and too deliberate
   ❌ ["a", "b", "c"] - list elements too simplified

9) Generation should prioritize "format legality":
   - Regular expressions (regex pattern): Use simple, stable patterns (like "\\d{{16}}", "[A-Z]+", "key_\\w+"), avoid complex lookahead, lookbehind, or nested structures.
   - JSON strings: Must be legal JSON format.
   - Python code: Must be syntactically correct Python code.

【Output Format (Strict JSON; key names fixed, must not change)】
You must output and only output the following JSON object:
{{
  "init_values": {{
    "<node_id>": {{
      "init_inputs": {{
        "<port_name>": <value>
      }},
      "init_outputs": {{
        "<port_name>": <value>
      }}
    }}
  }}
}}

【Output Consistency Check (Execute implicitly, do not output extra text)】
- init_values must cover all node_id in by_node
- Each node's init_inputs key set must exactly match by_node[node_id].init_inputs
- Each node's init_outputs key set must exactly match by_node[node_id].init_outputs (if empty output empty object {{}})

========================
Few-shot Example (You must imitate its input-output style and constraints)
========================

【Example Input】
DAG_JSON (excerpt, for illustration only; real call will provide complete DAG):
{{
  "metadata": {{"total_nodes": 5, "total_edges": 0}},
  "nodes": [
    {{"id": "terminal_1", "template_id": "terminal_1", "inputs": [], "outputs": [{{"name":"text_output","type":"Text_Generic","description":"Text output"}}, {{"name":"hex_output","type":"Hex_String","description":"Hex output"}}, {{"name":"item_dispenser","type":"Item","description":"Item output"}}]}},
    {{"id": "graph_shortest_path", "template_id": "graph_shortest_path", "inputs": [{{"name":"src","type":"Text_Generic","description":"Source node"}}, {{"name":"dst","type":"Text_Generic","description":"Destination node"}}], "outputs":[{{"name":"path","type":"Text_Generic","description":"Path list"}}, {{"name":"cost","type":"Text_Generic","description":"Total cost"}}]}},
    {{"id": "num_base_convert", "template_id": "num_base_convert", "inputs": [{{"name":"s","type":"Big_Int","description":"Input integer value"}}, {{"name":"from_base","type":"Big_Int","description":"From base"}}], "outputs":[{{"name":"result","type":"Text_Generic","description":"Converted value"}}]}},
    {{"id": "calc_inv_mod", "template_id": "calc_inv_mod", "inputs": [{{"name":"a","type":"Big_Int","description":"Integer a"}}, {{"name":"mod","type":"Big_Int","description":"Modulus"}}], "outputs":[{{"name":"inv","type":"Big_Int","description":"Modular inverse"}}]}},
    {{"id": "item_4", "template_id": "item_4", "inputs": [{{"name":"container","type":"Hidden_Item","description":"Inside"}}], "outputs": [{{"name":"content","type":"File_Id","description":"Zip file path"}}]}}
  ],
  "edges": []
}}

BY_NODE_JSON:
{{
  "terminal_1": {{
    "node_name": "",
    "node_type": "Tool",
    "template_id": "terminal_1",
    "init_inputs": {{}},
    "init_outputs": {{
      "text_output": {{"type": "Text_Generic", "description": "Text output"}},
      "hex_output": {{"type": "Hex_String", "description": "Hex output"}},
      "item_dispenser": {{"type": "Item", "description": "Item output"}}
    }}
  }},
  "graph_shortest_path": {{
    "node_name": "Shortest Path Finder",
    "node_type": "Tool",
    "template_id": "graph_shortest_path",
    "init_inputs": {{
      "src": {{"type": "Text_Generic", "description": "Source node"}},
      "dst": {{"type": "Text_Generic", "description": "Destination node"}}
    }},
    "init_outputs": {{
      "path": {{"type": "Text_Generic", "description": "Path list"}},
      "cost": {{"type": "Text_Generic", "description": "Total cost"}}
    }}
  }},
  "num_base_convert": {{
    "node_name": "Base Converter",
    "node_type": "Tool",
    "template_id": "num_base_convert",
    "init_inputs": {{
      "s": {{"type": "Big_Int", "description": "Input integer value"}},
      "from_base": {{"type": "Big_Int", "description": "From base"}}
    }},
    "init_outputs": {{}}
  }},
  "calc_inv_mod": {{
    "node_name": "BigInt Modular Inverse",
    "node_type": "Tool",
    "template_id": "calc_inv_mod",
    "init_inputs": {{
      "a": {{"type": "Big_Int", "description": "Integer a"}},
      "mod": {{"type": "Big_Int", "description": "Modulus"}}
    }},
    "init_outputs": {{}}
  }},
  "item_4": {{
    "node_name": "",
    "node_type": "Item",
    "template_id": "item_4",
    "init_inputs": {{}},
    "init_outputs": {{
      "content": {{"type": "File_Id", "description": "Zip file path"}}
    }}
  }}
}}

【Example Output (Strict JSON; only output this JSON)】
{{
  "init_values": {{
    "terminal_1": {{
      "init_inputs": {{}},
      "init_outputs": {{
        "text_output": "System initialization complete. All modules loaded successfully.",
        "hex_output": "48656c6c6f20576f726c6421",
        "item_dispenser": "Congratulations, you successfully wasted an execution opportunity"
      }}
    }},
    "graph_shortest_path": {{
      "init_inputs": {{
        "src": "Gateway_Alpha_7F",
        "dst": "Terminal_Omega_3B"
      }},
      "init_outputs": {{
        "path": "[\"Gateway_Alpha_7F\", \"Relay_5C\", \"Hub_Central_9A\", \"Server_Node_D2\", \"Bridge_17E\", \"Terminal_Omega_3B\"]",
        "cost": "15847"
      }}
    }},
    "num_base_convert": {{
      "init_inputs": {{
        "s": "73948572638194758264",
        "from_base": "16"
      }},
      "init_outputs": {{}}
    }},
    "calc_inv_mod": {{
      "init_inputs": {{
        "a": "45821967304758291037",
        "mod": "8191"
      }},
      "init_outputs": {{}}
    }},
    "item_4": {{
      "init_inputs": {{}},
      "init_outputs": {{
        "content": "graph_data.json"
      }}
    }}
  }}
}}

========================
Now begin your task (generate output for real input, do not output anything other than Json content)
========================
'''

fill_source_prompt2 = '''
You are a "DAG Source Initialization Value Generator". You will receive a structured DAG JSON (containing nodes/edges/metadata, etc.) and a source initialization list by_node (containing only the nodes and ports that require external initialization). Your task is: combine the DAG structure context with the port information specified in by_node to generate executable, format-compliant, and robust initial values for each node's init_inputs/init_outputs. These values will be used subsequently by the program to execute tool nodes according to DAG dependencies, automatically producing intermediate values and final outputs.

【Input】
1) DAG structure JSON (structure only; may not contain any runtime values):
{DAG_JSON}

2) Source initialization list by_node (the sole authoritative "list of ports requiring initialization"; you may only generate values for ports appearing here):
{BY_NODE_JSON}

【Hard Constraints (Must Be Followed)】
1) You may only generate values for the init_inputs/init_outputs of each node_id listed in by_node:
   - Do not add new nodes
   - Do not add new ports
   - Do not omit any endpoints
2) You must output only "strict JSON" without any other text (including explanations, Markdown, code block markers).
3) **Data Uniqueness and Randomness Constraints**:
   - 【No Duplication】All generated values must be unique; do not reuse the same value across different nodes/ports.
   - 【Randomness Requirement】Numeric types (Big_Int, numbers in Text_Generic) must use random generation strategies.
4) All values must satisfy port type constraints (generate according to the following rules):
   
   - Text_Generic: JSON string, non-empty; avoid prompt injection, script tags, malicious payloads, etc.
   
   - Big_Int: Must generate "decimal digit string" (JSON string, containing only 0-9).
     * 【Strict Constraint】Only numeric characters 0-9 are allowed; no letters, symbols, or spaces
     * 【Minimum Length Requirement】: Generated numeric string must be at least 20 digits, unless the port name is in the "Special Parameter Whitelist" below
     * Maximum length should not exceed 60 digits
     
     【Special Parameter Whitelist (May Use Small Numbers)】:
     The following port names allow generating numbers with fewer than 20 digits:
     • "from_base", "to_base", "base": Base parameters, must generate integers between 2-36 (common values: 2, 8, 10, 16, 32)
       - ❌ Prohibited: Values exceeding 36 or below 2
     • "mod", "modulus": Modulus parameters, generate integers between 1000-999999 (prime numbers recommended)
     
     All other Big_Int ports must be >= 20 digits.
   
   - Hex_String / Hex_String_Key_AES / Hex_String_IV_AES: Must generate "hexadecimal string" (JSON string, containing only 0-9a-f, all lowercase).
     * 【Critical Constraint】All Hex strings must have even length
     * Hex_String: General Hex string, length 16-64 characters (must be even)
     * Hex_String_Key_AES: AES key, must be 32 characters (128-bit) or 64 characters (256-bit)
     * Hex_String_IV_AES: AES initialization vector, must be 32 characters (128-bit)
   
   - File_Id: JSON string, must generate reasonable file identifiers including file type suffix.
     * Format: <filename>.<extension> (e.g., "graph_data.zip", "config.json", "data.csv")
   
   - Code_Python: Must generate "valid Python code snippet" (JSON string).
   
   - Item / Hidden_Item:
     * In init_outputs: Generate English string (20-60 characters), suggesting this is a useless operation or item (taunting hint)
     * In init_inputs: Generate brief identifier (5-20 characters)

5) 【Strict Parameter Constraints for Special Tools】
   The following tools' specific parameters only accept fixed values; violations will cause execution failure:
   
   - unicode_norm.form → Must be one of ["NFC", "NFD", "NFKC", "NFKD"] (recommend "NFC")
   - otp_totp_generate.digits → Must be "6" or "8"
   - time_convert.timezone → Must be valid timezone (e.g., "UTC", "America/New_York", "Asia/Shanghai", "Europe/London")
     * ❌ Prohibited: Random text, numbers, empty strings
   - num_base_convert's from_base/to_base → Must be integers between 2-36
     * Recommended values: 2, 8, 10, 16, 32
     * ❌ Prohibited: Values exceeding 36 or below 2

6) 【Type Consistency Constraints】
   - Big_Int only accepts "decimal digits" → e.g., "73948572638194758264"
   - Hex_String only accepts "hexadecimal characters (lowercase, even length)" → e.g., "1a2b3c4d"
   - Text_Generic can be any text
   
   【Critical】num_base_convert.to_base must match the output port type:
   - Output connects to Big_Int → set to_base="10"
   - Output connects to Hex_String → set to_base="16"

7) 【Special Handling for Encryption/Compression Tools】
   The following tools require paired or real data; random strings will cause failure:
   
   - crypto_aes_cbc_decrypt / crypto_rsa_decrypt_hex:
     * Must generate plaintext string for text output port (20-100 characters)
     * Example: "Decrypted secret message content here."
   
   - zlib_inflate / zlib_deflate:
     * Must generate text content for text output port (20-100 characters)
     * Example: "Decompressed data payload successfully extracted."
   
   - base64_decode:
     * Ensure data parameter is valid base64 string (letters, numbers, +, /, =, length multiple of 4)
     * Must generate decoded text for text output port (20-100 characters)
   
   - checksum_crc32:
     * Must generate 8-character hexadecimal string (lowercase) for crc32 output port
     * Example: "a1b2c3d4"
   
   These tools' outputs are often critical nodes in the data flow; not generating them will cause downstream nodes to lack necessary input values.

8) 【Realism Standard (Applies Only to init_outputs)】
   For all values in init_outputs, must generate complete, realistic data conforming to actual usage scenarios:
   
   • Path/graph structure related (port names containing "path", "route", "trace"):
     - Must generate path list with at least 5-10 nodes (JSON array string format)
   
   • Cost/distance related (port names containing "cost", "distance", "weight"):
     - Generate values between 100-999999 (string format)
   
   • List/array related (port names containing "matches", "values", "rows", "items"):
     - Must generate list with at least 3-8 elements (JSON array string format)
   
   • Text output (port names like "text_output", "message", "result"):
     - Generate complete sentences or data conforming to node function (20-100 characters)

9) Generation should prioritize "format legality":
   - Regular expressions (regex pattern): Use simple, stable patterns (e.g., "\\d{{16}}", "[A-Z]+", "key_\\w+"), avoid complex lookahead, lookbehind, or nested structures.
   - JSON strings: Must be valid JSON format.
   - Python code: Must be syntactically correct Python code.

【Output Format (Strict JSON; Fixed Key Names, Do Not Change)】
You must output only the following JSON object:
{{
  "init_values": {{
    "<node_id>": {{
      "init_inputs": {{
        "<port_name>": <value>
      }},
      "init_outputs": {{
        "<port_name>": <value>
      }}
    }}
  }}
}}

【Example】
Suppose by_node has 2 nodes:
- node1: init_inputs: {{ "a": Big_Int }}, init_outputs: {{ "result": Text_Generic }}
- node2: init_inputs: {{ "text": Text_Generic }}, init_outputs: {{}}

You should output:
{{
  "init_values": {{
    "node1": {{
      "init_inputs": {{
        "a": "73948572638194758264"
      }},
      "init_outputs": {{
        "result": "Computation completed successfully."
      }}
    }},
    "node2": {{
      "init_inputs": {{
        "text": "Sample input text for processing"
      }},
      "init_outputs": {{}}
    }}
  }}
}}

Now, please generate initial values for the provided DAG and by_node according to the above rules.
'''