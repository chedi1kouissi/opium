import json
from memora_os.core.llm import LocalLLM
from memora_os.core.graph import GraphStorage

class ReflectAgent:
    """
    Agent A.4: Reflect (The Analyst)
    - Pull-based agent triggered by user queries.
    - Retrieves context from Knowledge Graph.
    - Synthesizes answers using LLM.
    """
    def __init__(self):
        self.llm = LocalLLM()
        self.graph = GraphStorage() # Load existing graph
        
    def query(self, user_query):
        print(f"\n[Reflect] Analyzing query: '{user_query}'")
        
        # 1. Extract Search Terms (Entities)
        search_terms = self._extract_search_terms(user_query)
        print(f"[Reflect] Extracted terms: {search_terms}")
        
        if not search_terms:
            return "I couldn't identify specific topics to search for in your memory."

        # 2. Search Graph
        candidates = self.graph.search_nodes(search_terms)
        print(f"[Reflect] Found {len(candidates)} candidate nodes.")
        
        if not candidates:
            return f"I couldn't find any information about {', '.join(search_terms)} in your graph."
            
        # Take top 5 most relevant nodes
        top_candidates = [n[0] for n in candidates[:5]]
        
        # 3. Traverse for Context
        # Get 1-hop neighborhood for context
        subgraph = self.graph.get_traversal(top_candidates, depth=1)
        node_count = len(subgraph['nodes'])
        edge_count = len(subgraph['edges'])
        print(f"[Reflect] Retrieved subgraph: {node_count} nodes, {edge_count} edges.")
        
        # 4. Synthesize Answer
        context_str = self._format_context(subgraph)
        answer = self._synthesize_answer(user_query, context_str)
        
        return answer

    def _extract_search_terms(self, query):
        """
        Uses LLM to extract key entities/topics from query.
        """
        # Optimized prompt for phi3:mini
        prompt = f"""
        Analyze this query and extract key search terms.
        Query: "{query}"
        
        Return a JSON object with a single key "terms" containing a list of strings.
        EXTRACT: People, Projects, Technologies, key concepts.
        IMPORTANT: Split compound terms (e.g., "technical blockers" -> "technical", "blockers").
        
        Example:
        {{"terms": ["Marcus Johnson", "launch", "delay", "API"]}}
        
        JSON ONLY. NO MARKDOWN. NO TEXT.
        """
        
        terms = []
        try:
            response = self.llm.generate(prompt, json_mode=True)
            # Cleanup potential markdown code blocks
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]
            
            data = json.loads(response)
            terms = data.get("terms", [])
            # CLEANUP: Filter None and non-strings
            terms = [t for t in terms if isinstance(t, str) and t.strip()]
        except Exception as e:
            print(f"[Reflect] Extraction error: {e}")
        
        # STRONG Fallback: If LLM fails or returns empty, rule-based extraction
        if not terms:
            print("[Reflect] Using fallback extraction.")
            # Remove common stopwords
            stopwords = {"what", "where", "when", "who", "why", "how", "is", "are", "the", "a", "an", "in", "on", "at", "for", "to", "of", "about"}
            words = query.replace("?", "").replace(".", "").split()
            # Keep capitalized words (names) and long words
            terms = [w for w in words if w.lower() not in stopwords and (len(w) > 3 or w[0].isupper())]
            
        return terms

    def _format_context(self, subgraph):
        """
        Formats subgraph into a readable context string for LLM.
        """
        nodes = subgraph['nodes']
        edges = subgraph['edges']
        
        context = "### KNOWLEDGE GRAPH CONTEXT ###\n"
        
        # List Nodes
        context += "\n[ENTITIES & EVENTS]\n"
        for node_id, data in nodes.items():
            kind = data.get('type', 'UNKNOWN')
            name = data.get('name', '') or data.get('primary_entity', '') or node_id
            details = data.get('summary', '') or f"Timestamp: {data.get('timestamp', '')}"
            context += f"- {kind} [{node_id}]: {name} | {details}\n"
            
        # List Relationships
        context += "\n[RELATIONSHIPS]\n"
        for edge in edges:
            src = edge['source']
            tgt = edge['target']
            rel = edge['relation']
            
            # Helper to get name
            src_name = nodes.get(src, {}).get('name') or nodes.get(src, {}).get('primary_entity') or src
            tgt_name = nodes.get(tgt, {}).get('name') or nodes.get(tgt, {}).get('primary_entity') or tgt
            
            context += f"- {src_name} --[{rel}]--> {tgt_name}\n"
            
        print(f"[Reflect] Context Length: {len(context)} chars")
        return context

    def _synthesize_answer(self, query, context):
        """
        Asks LLM to answer query based on context.
        """
        system_prompt = """
        You are Memora, an AI assistant with access to the user's personal knowledge graph.
        Answer the user's question using ONLY the provided Context.
        If the answer is not in the context, say you don't know based on current memories.
        Cite specific events or entities (e.g., "In an email on Monday...") when possible.
        """
        
        prompt = f"""
        User Query: {query}
        
        {context}
        
        Answer:
        """
        
        return self.llm.generate(prompt, system_prompt=system_prompt)
