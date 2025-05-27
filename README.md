# TiM (Think-in-Memory) Demo Application

This Python script is a simplified demonstration of the **Think-in-Memory (TiM)** framework, as proposed in the research paper "Think-in-Memory: Recalling and Post-thinking Enable LLMs with Long-Term Memory" (arXiv:2311.08719v1).

The demo simulates how a Large Language Model (LLM) can maintain and utilize a long-term memory by storing, recalling, and organizing "inductive thoughts" derived from interactions.

## Features Demonstrated

* **Inductive Thought Storage:** Simulates the creation and storage of concise thoughts representing key information from conversations.
* **Simplified Locality-Sensitive Hashing (LSH):** Shows how thoughts can be grouped for efficient retrieval.
* **Recall Stage:** Demonstrates retrieving relevant thoughts from memory before generating a response.
* **Post-thinking Stage:** Shows how new thoughts are generated after an interaction and used to update the memory.
* **Memory Organization Operations:**
    * **Insert:** Adding new thoughts to memory.
    * **Forget:** Removing contradictory or outdated thoughts (simulated).
    * **Merge:** Combining similar thoughts into more comprehensive ones (simulated).
* **Interactive Interface:** Allows users to query the system and manually trigger memory organization.

## How it Works (High-Level)

The demo is built around a few key components:

1.  **`MockLLMAgent`**: A class that simulates the behavior of an LLM. It uses predefined rules and string matching to:
    * Generate "inductive thoughts" from query-response pairs.
    * Formulate responses (potentially using recalled thoughts).
    * Decide which thoughts to "forget" or "merge."
    * Generate simple "embeddings" (integer hashes) for thoughts.

2.  **`SimpleLSH`**: A simplified version of Locality-Sensitive Hashing. It takes the integer embedding of a thought and assigns it to a group (hash bucket).

3.  **`MemoryCache`**: The core memory system. It's a hash table (dictionary) where keys are LSH group indices and values are lists of thoughts. It handles storing, retrieving, and organizing thoughts.

4.  **`TiMSystem`**: The main orchestrator. It integrates the other components and manages the TiM workflow:
    * **User Query:** Receives input.
    * **Recall & Generation:** Retrieves relevant thoughts from `MemoryCache` and uses `MockLLMAgent` to generate a response.
    * **Post-think & Update:** Uses `MockLLMAgent` to create a new thought from the interaction and stores it in `MemoryCache`.

## Running the Demo

### Prerequisites

* Python 3.x

### Instructions

1.  Save the code as a Python file (e.g., `tim_demo.py`).
2.  Open a terminal or command prompt.
3.  Navigate to the directory where you saved the file.
4.  Run the script using:
    ```bash
    python tim_demo.py
    ```

## Interactive Commands

Once the demo is running:

* **Type your query:** Enter any question or statement for the simulated agent.
* **`quit`**: Type `quit` to exit the demo.
* **`memory`**: Type `memory` to enter the memory management mode.

### Memory Management Commands (after typing `memory`):

* **`display`**: Shows the current state of all thoughts in memory, grouped by their LSH index.
* **`forget <group_idx>`**: Simulates the "forget" operation on the specified LSH group index (e.g., `forget 0`).
* **`merge <group_idx>`**: Simulates the "merge" operation on the specified LSH group index (e.g., `merge 1`).
* **`organize_all <group_idx>`**: Applies both forget and merge operations to the specified group.
* **`back`**: Exits memory management mode and returns to the main query interaction.

## Key Concepts Simulated (from the TiM paper)

* **Inductive Thoughts:** Storing processed, relational information instead of raw text.
* **Locality-Sensitive Hashing (LSH):** Grouping similar thoughts for efficient retrieval (highly simplified in this demo).
* **Recall Stage:** Retrieving relevant thoughts *before* generating a response to guide the generation process and avoid re-reasoning.
* **Post-thinking Stage:** Generating new thoughts *after* a response and updating the memory, allowing the memory to evolve.
* **Memory Organization (Insert, Forget, Merge):** Dynamically updating and curating the thoughts in memory.

## Limitations

* **Mock LLM:** The `MockLLMAgent` is **not** a real AI. Its intelligence is based on simple rules and string matching. It does not understand language in a human-like way.
* **Simplified LSH:** The LSH implementation is extremely basic and serves only to demonstrate the concept of grouping.
* **Basic Similarity:** Thought similarity for recall within a group is based on simple keyword overlap.
* **Deterministic Behavior:** Due to the mock nature, the agent's responses and thought generation are largely deterministic based on the implemented rules.

This demo is intended for educational purposes to illustrate the core mechanisms of the Think-in-Memory framework in a tangible way.

## Based On

* Liu, L., Hu, B., Zhang, Z., Yang, X., Gu, J., Shen, Y., & Zhang, G. (2023). *Think-in-Memory: Recalling and Post-thinking Enable LLMs with Long-Term Memory*. arXiv preprint arXiv:2311.08719.
