import hashlib

# --- Mock LLM Agent ---
class MockLLMAgent:
    """
    A mock class to simulate LLM behavior for generating thoughts,
    responses, embeddings, and decisions for memory organization.
    """
    def get_embedding(self, text: str) -> int:
        """
        Generates a simple mock embedding for a given text.
        In a real scenario, this would be a high-dimensional vector.
        LSH in the paper uses random projection; this is a simpler stand-in.
        """
        # Using sum of ASCII values for simplicity to get a numeric hash input.
        # This is a very basic way to get a number from text for hashing.
        return sum(ord(c) for c in text)

    def generate_inductive_thought(self, query: str, response: str) -> str:
        """
        Simulates the generation of an inductive thought from a query-response pair.
        This is based on the paper's concept of extracting relations or key information.
        Figure 3 in the paper provides examples of prompts for this process.
        """
        query_lower = query.lower()
        # Example: "Do you have any book recommendations for me?" -> "I recommend "The Little Prince"."
        # Thought: "Recommend book is "The Little Prince"."
        if "recommend" in query_lower and "book" in query_lower:
            parts = response.split("recommend")
            if len(parts) > 1:
                # Extract book name, attempting to clean it up.
                book_name = parts[1].strip().replace(".", "").replace('"', '')
                return f"Recommend book is \"{book_name}\"."
        # Example: 'How is "The Little Prince"?' -> '"The Little Prince" is interesting.'
        # Thought: ""The Little Prince" is interesting."
        elif "how is" in query_lower and "\"" in query: 
             entity_match = query.split('"')
             if len(entity_match) > 1:
                 entity = entity_match[1] # Extract entity from quotes
                 if "interesting" in response.lower():
                     return f"\"{entity}\" is interesting."
                 elif "stunning visuals" in response.lower():
                     return f"\"{entity}\" is with stunning visuals."
        # Example: "What is the capital of China?" -> "Beijing."
        # Thought: "The capital of China is Beijing."
        elif "capital of" in query_lower:
            subject_parts = query_lower.split("capital of")
            if len(subject_parts) > 1:
                subject = subject_parts[1].replace("?", "").strip().title() # Clean and capitalize subject
                city = response.strip().replace(".", "") # Clean city name
                return f"The capital of {subject} is {city}."
        # Example for merging: "John works as an actor."
        elif "john works as" in query.lower() or "john do" in query.lower() or "thing about john" in query.lower():
            if "actor" in response.lower(): return "John works as an actor."
            if "director" in response.lower(): return "John works as a director."
            if "writer" in response.lower(): return "John works as a writer."
        elif "mike" in query.lower():
             if "teacher" in response.lower(): return "Mike works as a teacher."


        # Default thought generation if no specific pattern matches.
        # In a real LLM, this would be a more sophisticated summarization or relation extraction.
        return f"Concluded: {response}"

    def generate_response(self, query: str, recalled_thoughts: list[str]) -> str:
        """
        Simulates generating a response, potentially using recalled thoughts.
        The paper emphasizes that TiM recalls thoughts to avoid re-reasoning over raw history.
        """
        if recalled_thoughts:
            # If thoughts are recalled, the response incorporates them.
            return f"Based on memory ('{'; '.join(recalled_thoughts)}'), the answer to '{query}' is: Processed Response using these thoughts."
        # If no thoughts are recalled, a generic response is generated.
        return f"Answering '{query}' without specific memory: Standard Response."

    def identify_thoughts_to_forget(self, thought_group: list[str]) -> list[str]:
        """
        Simulates an LLM identifying counterfactual or contradictory thoughts to forget.
        This is inspired by Figure 4 in the paper.
        """
        to_forget = []
        # Example from Figure 4: Removing a contradictory capital.
        # If "The capital of China is Beijing." and "The capital of China is Shanghai." exist,
        # the LLM might identify "Shanghai" as the one to forget if "Beijing" is more current/correct.
        capitals_of_china = [t for t in thought_group if "capital of China is" in t]
        if "The capital of China is Beijing." in capitals_of_china and \
           "The capital of China is Shanghai." in capitals_of_china:
            to_forget.append("The capital of China is Shanghai.")
        
        # Generic rule for demo: forget thoughts marked as "old version" or "ignore".
        to_forget.extend([t for t in thought_group if "old version" in t.lower() or "ignore this" in t.lower()])
        return list(set(to_forget)) # Return unique thoughts to forget.

    def merge_thoughts_in_group(self, thought_group: list[str]) -> list[str]:
        """
        Simulates an LLM merging similar thoughts with the same entity.
        This is inspired by Figure 5 in the paper.
        Example: "John works as an actor.", "John works as a director." -> "John works as an actor, a director."
        """
        current_thoughts = list(thought_group) # Work with a copy
        final_merged_thoughts = []
        processed_indices = set() # Keep track of thoughts already merged or added

        i = 0
        while i < len(current_thoughts):
            if i in processed_indices:
                i += 1
                continue
            
            thought1 = current_thoughts[i]
            merged_this_iter = False

            # Case 1: Merging book recommendation and its attribute (e.g., interesting)
            # "Recommend book is "The Little Prince"." + ""The Little Prince" is interesting."
            # -> "Recommend book is "The Little Prince". Moreover, "The Little Prince" is interesting."
            if thought1.startswith("Recommend book is"):
                try:
                    # Extract book name from the first thought.
                    book_name_quotes = thought1.split("Recommend book is")[1].strip().replace(".","") 
                    book_name_no_quotes = book_name_quotes.replace('"', '')
                    
                    for j in range(len(current_thoughts)): # Search for a matching attribute thought
                        if j == i or j in processed_indices:
                            continue
                        thought2 = current_thoughts[j]
                        if thought2 == f"\"{book_name_no_quotes}\" is interesting.":
                            final_merged_thoughts.append(f"{thought1} Moreover, \"{book_name_no_quotes}\" is interesting.")
                            processed_indices.add(i)
                            processed_indices.add(j)
                            merged_this_iter = True
                            break
                except IndexError:
                    pass # Thought format not as expected, skip.
            
            # Case 2: Merging roles for the same person (e.g., John)
            # "John works as an actor." + "John works as a director." -> "John works as an actor, a director."
            if " works as a" in thought1 and not merged_this_iter:
                entity_role_parts = thought1.split(" works as a")
                entity = entity_role_parts[0] # e.g., "John"
                current_roles = [entity_role_parts[1].replace(".","")] # e.g., ["actor"]
                
                temp_processed_indices_for_merge = {i} # Track indices for this specific merge attempt
                
                for j in range(i + 1, len(current_thoughts)): # Check subsequent thoughts for same entity
                    if j in processed_indices:
                        continue
                    thought2 = current_thoughts[j]
                    if thought2.startswith(entity + " works as a"):
                        new_role = thought2.split(" works as a")[1].replace(".","")
                        current_roles.append(new_role)
                        temp_processed_indices_for_merge.add(j)
                
                if len(current_roles) > 1: # If multiple roles found, merge them
                    # Sort roles for consistent output, use set to remove duplicates before joining
                    merged_role_string = ", a ".join(sorted(list(set(current_roles))))
                    final_merged_thoughts.append(f"{entity} works as a {merged_role_string}.")
                    processed_indices.update(temp_processed_indices_for_merge)
                    merged_this_iter = True
            
            if not merged_this_iter: # If no merge happened for thought1
                final_merged_thoughts.append(thought1)
                processed_indices.add(i) 
            i += 1
        
        # Add any thoughts that were not part of a merge and not yet added
        for idx, thought in enumerate(current_thoughts):
            if idx not in processed_indices:
                final_merged_thoughts.append(thought)
                
        return final_merged_thoughts


# --- LSH (Simplified Locality-Sensitive Hashing) ---
class SimpleLSH:
    """
    A simplified Locality-Sensitive Hashing mechanism.
    The paper describes LSH as F(x) = arg max ([xR; -xR]), using random projection.
    This demo uses a much simpler modulo operation on a mock embedding for grouping.
    The core idea is that similar items (thoughts) should fall into the same hash bucket/group.
    """
    def __init__(self, num_groups: int = 10):
        self.num_groups = num_groups # Number of hash buckets/groups

    def get_hash_index(self, embedding: int) -> int:
        """
        Calculates a hash index from a (mock) embedding.
        This determines which group a thought belongs to.
        """
        return embedding % self.num_groups


# --- Memory Cache ---
class MemoryCache:
    """
    Manages the storage and organization of inductive thoughts.
    It uses a hash table structure (Python dictionary) where keys are hash indices (from LSH)
    and values are lists of thoughts belonging to that group.
    This aligns with M in the paper: "a continually growing hash table of key-value pairs".
    """
    def __init__(self, lsh_instance: SimpleLSH, llm_agent: MockLLMAgent):
        # Initialize memory as a dictionary of lists, one list per LSH group.
        self.memory: dict[int, list[str]] = {i: [] for i in range(lsh_instance.num_groups)}
        self.lsh = lsh_instance
        self.llm_agent = llm_agent # LLM agent is used for embedding and thought manipulation

    def _get_hash_for_thought(self, thought_text: str) -> int:
        """Helper to get LSH group index for a thought."""
        embedding = self.llm_agent.get_embedding(thought_text)
        return self.lsh.get_hash_index(embedding)

    def insert_thought(self, thought_text: str):
        """
        Inserts a new inductive thought into the memory cache.
        This corresponds to the "insert" operation for memory updating.
        """
        h_idx = self._get_hash_for_thought(thought_text)
        if thought_text not in self.memory[h_idx]: # Avoid exact duplicate thoughts within a group
            self.memory[h_idx].append(thought_text)
            print(f"  🧠 MEMORY (+): Inserted thought '{thought_text}' into group {h_idx}.")
        else:
            print(f"  🧠 MEMORY (=): Thought '{thought_text}' already in group {h_idx}. Not re-inserting.")

    def recall_thoughts(self, query_text: str, top_k: int = 3) -> list[str]:
        """
        Recalls relevant thoughts for a given query.
        This involves two stages as per the paper:
        1. LSH-based Retrieval: Find the nearest group using LSH.
        2. Similarity-based Retrieval: Within that group, find the most similar thoughts. (Simplified here)
        """
        query_embedding = self.llm_agent.get_embedding(query_text)
        h_idx = self.lsh.get_hash_index(query_embedding) # Stage 1: LSH-based retrieval
        thought_group = self.memory[h_idx]
        
        print(f"  🧠 MEMORY (~): Recalling from group {h_idx} (contains {len(thought_group)} thoughts).")
        if not thought_group:
            return [] # No thoughts in the relevant group

        # Stage 2: Similarity-based Retrieval (Simplified for demo)
        # A real system would use semantic similarity (e.g., cosine similarity on embeddings).
        # This demo uses a crude keyword overlap score.
        query_words = set(query_text.lower().split())
        def crude_similarity_score(thought: str) -> int:
            thought_words = set(thought.lower().split())
            return len(thought_words.intersection(query_words))

        # Sort thoughts in the group by similarity (descending), then by recency (newer thoughts first as tie-breaker)
        sorted_thoughts = sorted(thought_group, key=lambda t: (crude_similarity_score(t), thought_group.index(t)), reverse=True)
        return sorted_thoughts[:top_k] # Return top-k most relevant thoughts

    def organize_memory_group(self, group_idx: int, mode: str = "all"):
        """
        Applies forget and/or merge operations to a specific memory group.
        This is part of the "Organization for Memory Updating" described in the paper.
        """
        if group_idx not in self.memory or not self.memory[group_idx]:
            print(f"  🧠 MEMORY (Org): Group {group_idx} is empty or invalid. Nothing to organize.")
            return

        original_thoughts = list(self.memory[group_idx]) # Keep a copy for comparison
        print(f"\n  🧠 MEMORY (Org): Organizing group {group_idx}. Original thoughts: {original_thoughts}")

        current_group_thoughts = list(self.memory[group_idx]) # Work on a mutable copy

        # "Forget, i.e., remove unnecessary thoughts from the memory"
        if mode in ["forget", "all"]:
            thoughts_to_forget = self.llm_agent.identify_thoughts_to_forget(current_group_thoughts)
            if thoughts_to_forget:
                print(f"  🧠 MEMORY (Forget): Identified to forget: {thoughts_to_forget}")
                current_group_thoughts = [t for t in current_group_thoughts if t not in thoughts_to_forget]
            else:
                print(f"  🧠 MEMORY (Forget): No thoughts identified for forgetting in this group.")
        
        # "Merge, i.e., merge similar thoughts in the memory"
        if mode in ["merge", "all"]:
            if current_group_thoughts: # Ensure there are thoughts left after potential forgetting
                merged_group_thoughts = self.llm_agent.merge_thoughts_in_group(current_group_thoughts)
                if merged_group_thoughts != current_group_thoughts: # Check if merge actually changed anything
                    print(f"  🧠 MEMORY (Merge): Merged. New group state: {merged_group_thoughts}")
                    current_group_thoughts = merged_group_thoughts
                else:
                    print(f"  🧠 MEMORY (Merge): No effective merge operations performed on remaining thoughts.")
            else:
                print(f"  🧠 MEMORY (Merge): Group empty after forgetting, skipping merge.")
        
        self.memory[group_idx] = current_group_thoughts # Update the memory group
        if self.memory[group_idx] != original_thoughts:
             print(f"  🧠 MEMORY (Org): Group {group_idx} updated. Final thoughts: {self.memory[group_idx]}")
        else:
             print(f"  🧠 MEMORY (Org): No changes to group {group_idx} after organization attempts.")


    def display_memory(self):
        """Utility function to print the current state of the memory cache."""
        print("\n--- 🏦 Current TiM Memory State ---")
        empty = True
        for h_idx, thoughts in self.memory.items():
            if thoughts: # Only print groups that have thoughts
                empty = False
                print(f"  Group {h_idx}:")
                for thought in thoughts:
                    print(f"    - \"{thought}\"")
        if empty:
            print("  Memory is currently empty.")
        print("---------------------------------\n")

# --- TiM System (Main Orchestrator) ---
class TiMSystem:
    """
    Orchestrates the Think-in-Memory workflow, integrating the LLM agent, LSH, and Memory Cache.
    This class represents the overall TiM framework.
    """
    def __init__(self):
        self.llm_agent = MockLLMAgent()
        # Using a small number of groups for easier observation in the demo.
        # The paper's LSH (Eq. 1) implies 'b' groups.
        self.lsh = SimpleLSH(num_groups=5) 
        self.memory_cache = MemoryCache(self.lsh, self.llm_agent)
        print("TiM System Initialized. LLM-agnostic design allows plugging in different LLMs/LSH.")

    def process_query(self, user_query: str):
        """
        Processes a user query through the two main TiM stages:
        1. Recall and Generation
        2. Post-think and Update
        """
        print(f"\n👤 User Query: \"{user_query}\"")

        # Stage 1: Recall and Generation
        # "before generating a response, a LLM agent recalls relevant thoughts from memory"
        print("  ➡️ Stage 1: Recall and Generation")
        recalled_thoughts = self.memory_cache.recall_thoughts(user_query, top_k=3)
        if recalled_thoughts:
            print(f"  💡 Recalled Thoughts: {recalled_thoughts}")
        else:
            print("  💡 No relevant thoughts recalled from memory for this query.")

        # LLM generates a response, potentially using the recalled thoughts.
        agent_response = self.llm_agent.generate_response(user_query, recalled_thoughts)
        print(f"  🤖 Agent Response: \"{agent_response}\"")

        # Stage 2: Post-think and Update
        # "after generating a response, the LLM agent post-thinks and incorporates ... new thoughts to update the memory"
        print("  ⬅️ Stage 2: Post-think and Update")
        # LLM generates an inductive thought from the current query-response pair.
        new_thought = self.llm_agent.generate_inductive_thought(user_query, agent_response)
        
        # Insert the new thought into memory if it's meaningful.
        # Avoid storing thoughts derived from generic "Standard Response" if no memory was used.
        if new_thought and not new_thought.startswith("Concluded: Standard Response"):
            self.memory_cache.insert_thought(new_thought)
        else:
            print(f"  🧠 MEMORY (-): No specific new thought generated or stored for this interaction.")
        
        return agent_response

    def manage_memory_interactive(self):
        """
        Provides an interactive command-line interface to manage memory operations.
        Allows demonstration of 'forget' and 'merge' on specific groups.
        """
        print("\n--- 🛠️ Memory Management ---")
        print("Enter command for a specific group (e.g., 'forget 0', 'merge 1', 'organize_all 2').")
        print("Options: 'display', 'forget <idx>', 'merge <idx>', 'organize_all <idx>', 'back'")
        while True:
            cmd_input = input("Enter memory command: ").strip().lower().split()
            if not cmd_input: continue

            action = cmd_input[0]
            
            if action == "back":
                print("Returning to main interaction.")
                break
            elif action == "display":
                self.memory_cache.display_memory()
            elif action in ["forget", "merge", "organize_all"] and len(cmd_input) > 1:
                try:
                    group_idx = int(cmd_input[1])
                    if 0 <= group_idx < self.lsh.num_groups:
                        op_mode = action # "forget" or "merge"
                        if action == "organize_all": op_mode = "all" # "all" triggers both forget and merge
                        self.memory_cache.organize_memory_group(group_idx, mode=op_mode)
                    else:
                        print(f"Invalid group index. Must be between 0 and {self.lsh.num_groups-1}.")
                except ValueError:
                    print("Invalid group index. Please enter a number.")
            else:
                print("Unknown command or missing group_idx. Try again. (e.g., 'forget 0')")


# --- Demo Application Runner ---
def run_demo():
    print("🚀 Welcome to the Think-in-Memory (TiM) Demo! 🚀")
    print("This demo simulates the TiM framework for LLMs with long-term memory.")
    print("Key features: Storing 'inductive thoughts', LSH-based grouping, recalling, post-thinking, and memory organization (insert, forget, merge).")
    
    tim_system = TiMSystem()

    # Simulate some initial interactions to pre-populate the memory.
    # These are based on examples from Figure 2, Figure 3, Figure 4, and Figure 5 in the paper.
    print("\n--- ⏳ Simulating Initial Interactions (Pre-populating Memory) ---")
    initial_interactions = [
        # From Figure 2/3 - Book recommendations
        ("Do you have any book recommendations for me?", 'I recommend "The Little Prince".'),
        ('How is "The Little Prince"?', '"The Little Prince" is interesting.'),
        # From Figure 2/3 - Movie recommendations
        ("Any movie recommendations?", 'You can go see "The Wandering Earth".'),
        ('How is "The Wandering Earth"?', '"The Wandering Earth" is with stunning visuals.'),
        # From Figure 3/4 - Capitals (for forget demo)
        ("What is the capital of China?", "Beijing."),
        ("What is the capital of China?", "Shanghai."), # Contradictory, for 'forget'
        ("What was another capital of China, historically?", "Nanjing is an old version capital of China for some dynasties."), # For 'forget'
        # From Figure 5 - John's roles (for merge demo)
        ("Tell me about John's roles.", "John works as an actor."),
        ("What else does John do?", "John works as a director."),
        ("One more thing about John?", "John works as a writer."),
        # Additional distinct entity for merge demo
        ("What about Mike?", "Mike works as a teacher."),
        # Another distinct fact
        ("What is the capital of France?", "Paris.")
    ]

    for q, r_text in initial_interactions:
        print(f"Simulating Q: {q}, R: {r_text}")
        # Generate thought directly for pre-population, bypassing full process_query
        thought = tim_system.llm_agent.generate_inductive_thought(q, r_text)
        if thought and not thought.startswith("Concluded: Standard Response"):
            tim_system.memory_cache.insert_thought(thought)
            
    tim_system.memory_cache.display_memory() # Show initial memory state
    
    print("\n--- 🎤 Starting Interactive Demo ---")
    print("Type your query. Special commands: 'quit' to exit, 'memory' to manage memory.")

    while True:
        user_input = input("\n🧑‍💻 Your Query: ").strip()
        if not user_input:
            continue
        if user_input.lower() == 'quit':
            print("👋 Exiting TiM Demo. Goodbye!")
            break
        if user_input.lower() == 'memory':
            tim_system.manage_memory_interactive()
            continue

        # Process the user query using the TiM system
        tim_system.process_query(user_input)

if __name__ == "__main__":
    run_demo()
