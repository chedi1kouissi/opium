import json
import threading
import queue
import time
import re
from memora_os.core.events import Event
from memora_os.core.graph import GraphStorage
from memora_os.core.llm import LocalLLM

class LinkerAgent:
    def __init__(self, input_queue):
        self.input_queue = input_queue
        self.graph = GraphStorage()
        self.llm = LocalLLM()
        self.running = False

    def start(self):
        self.running = True
        print("[System] Linker Agent (The Brain) Active")
        threading.Thread(target=self._process_loop).start()

    def stop(self):
        self.running = False
        self.graph.save()

    def _process_loop(self):
        while self.running:
            try:
                event = self.input_queue.get(timeout=1)
                print(f"[Linker] Linking event: {event.id}...")
                
                # 1. Add Event to Graph (The "New Memory")
                normalized_data = event.metadata.get('normalized', {})
                event_node_id = self.graph.add_event_node(event, normalized_data)
                
                # 2. Intelligent Linking using KG-based retrieval
                self._intelligent_linking(event, event_node_id, normalized_data)
                
                # Setup Auto-Save
                self.graph.save()
                
            except queue.Empty:
                pass
            except Exception as e:
                print(f"[Linker] Error: {e}")

    def _intelligent_linking(self, event, event_node_id, data):
        """
        Intelligent linking using KG-based retrieval.
        1. Extract and link ALL entities
        2. Retrieve relevant context from KG
        3. LLM evaluates relationships with retrieved candidates only
        """
        # Step 1: Extract ALL entities and create explicit links
        self._extract_and_link_entities(event_node_id, data)
        
        # Step 2: KG-based semantic linking
        content_summary = data.get('content_summary', '')
        if content_summary:
            self._kg_based_semantic_linking(event, event_node_id, data, content_summary)

    def _extract_and_link_entities(self, event_node_id, data):
        """Extract and link ALL entity types from normalized data."""
        entities = data.get('entities', {})
        
        # Map entity categories to node types
        entity_mappings = {
            'people': 'PERSON',
            'organizations': 'ORGANIZATION',
            'projects': 'PROJECT',
            'locations': 'LOCATION',
            'technologies': 'TECHNOLOGY',
            'documents': 'DOCUMENT',
            'dates': 'DATE',
            'amounts': 'AMOUNT',
            'urls': 'URL',
            'other': 'ENTITY'
        }
        
        entity_count = 0
        for category, node_type in entity_mappings.items():
            for entity_name in entities.get(category, []):
                if entity_name and entity_name != "N/A":
                    entity_id = self.graph.add_entity_node(entity_name, node_type)
                    self.graph.add_relation(event_node_id, entity_id, "MENTIONS")
                    entity_count += 1
        
        if entity_count > 0:
            print(f"  → Linked to {entity_count} entities")

    def _kg_based_semantic_linking(self, event, event_node_id, data, content_summary):
        """
        Intelligent semantic linking using KG retrieval.
        Instead of comparing with ALL events (N²), retrieve relevant candidates from KG.
        """
        # Step 1: Retrieve relevant candidates from KG
        candidates = self._retrieve_relevant_nodes(
            content_summary=content_summary,
            event_entities=data.get('entities', {}),
            timestamp=event.timestamp,
            current_node_id=event_node_id
        )
        
        if not candidates:
            print("  → No relevant context found in KG")
            return
        
        print(f"  → Evaluating {len(candidates)} candidate relationships...")
        
        # Step 2: LLM evaluates ONLY the retrieved candidates
        for candidate_id, candidate_data, similarity_score, similarity_reasons in candidates:
            # Skip if already explicitly linked
            if self.graph.graph.has_edge(event_node_id, candidate_id):
                continue
            
            # Ask LLM to decide relationship
            relationship = self._llm_evaluate_relationship(
                new_event_summary=content_summary,
                new_event_data=data,
                candidate_id=candidate_id,
                candidate_summary=candidate_data.get('summary', ''),
                candidate_data=candidate_data,
                similarity_reasons=similarity_reasons
            )
            
            if relationship:
                self.graph.add_relation(event_node_id, candidate_id, relationship['type'])
                print(f"  → [Smart Link] {relationship['type']}: {relationship['reason'][:60]}...")

    def _retrieve_relevant_nodes(self, content_summary, event_entities, timestamp, current_node_id, max_results=10):
        """
        Retrieve relevant nodes from KG using multi-factor scoring:
        1. Shared entity mentions (strongest signal)
        2. Keyword overlap in content summary
        3. Temporal proximity
        """
        candidates = []
        
        # Extract keywords from summary
        keywords = self._extract_keywords(content_summary)
        
        # Get all entities from new event for comparison
        new_event_entity_set = set()
        for entity_list in event_entities.values():
            new_event_entity_set.update([e.lower() for e in entity_list if e])
        
        for node_id, node_data in self.graph.graph.nodes(data=True):
            if node_data.get('type') != 'EVENT':
                continue
            if node_id == current_node_id:
                continue
            
            score = 0
            reasons = []
            
            # Factor 1: Shared entity mentions (STRONGEST)
            shared_entities = []
            try:
                event_neighbors = set(self.graph.graph.successors(node_id))
                new_event_neighbors = set(self.graph.graph.successors(current_node_id))
                shared_entities = event_neighbors & new_event_neighbors
                
                if shared_entities:
                    score += len(shared_entities) * 5  # High weight for shared entities
                    entity_names = []
                    for ent_id in list(shared_entities)[:3]:  # Show top 3
                        ent_data = self.graph.graph.nodes.get(ent_id, {})
                        if 'name' in ent_data:
                            entity_names.append(ent_data['name'])
                    if entity_names:
                        reasons.append(f"Shared: {', '.join(entity_names)}")
            except:
                pass
            
            # Factor 2: Keyword overlap
            node_summary = node_data.get('summary', '')
            if node_summary and keywords:
                keyword_matches = sum(1 for kw in keywords if kw in node_summary.lower())
                if keyword_matches > 0:
                    score += keyword_matches * 2
                    reasons.append(f"{keyword_matches} keyword matches")
            
            # Factor 3: Temporal proximity
            try:
                from datetime import datetime
                node_time_str = node_data.get('timestamp')
                if node_time_str:
                    node_time = datetime.fromisoformat(node_time_str)
                    if isinstance(timestamp, datetime):
                        time_diff_hours = abs((node_time - timestamp).total_seconds()) / 3600
                    else:
                        time_diff_hours = 999
                    
                    if time_diff_hours < 1:
                        score += 3
                        reasons.append("within 1 hour")
                    elif time_diff_hours < 24:
                        score += 1
                        reasons.append("same day")
            except:
                pass
            
            # Only keep candidates with non-zero score
            if score > 0:
                candidates.append((node_id, node_data, score, ' | '.join(reasons)))
        
        # Sort by score (descending) and return top K
        candidates.sort(key=lambda x: -x[2])
        return candidates[:max_results]

    def _extract_keywords(self, text):
        """Extract meaningful keywords from text (simple version)."""
        if not text:
            return []
        
        # Common stopwords
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'been',
            'be', 'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
            'could', 'may', 'might', 'must', 'this', 'that', 'these', 'those'
        }
        
        # Extract words
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [w for w in words if w not in stopwords and len(w) > 3]
        return keywords[:15]  # Top 15 keywords

    def _llm_evaluate_relationship(self, new_event_summary, new_event_data, candidate_id, 
                                   candidate_summary, candidate_data, similarity_reasons):
        """
        Use LLM to determine if two events are related and what type of relationship exists.
        """
        prompt = f"""Analyze the relationship between two events in a knowledge graph:

NEW EVENT:
- Type: {new_event_data.get('event_type', 'Unknown')}
- Summary: {new_event_summary}

EXISTING EVENT:
- Type: {candidate_data.get('event_type', 'Unknown')}
- Summary: {candidate_summary or 'No summary'}
- Why retrieved: {similarity_reasons}

Task: Determine if these events are meaningfully related. If yes, classify the relationship.

Response as JSON:
{{
  "related": true/false,
  "relationship_type": "CAUSED_BY | FOLLOWS_UP | DISCUSSES | REFERENCES | PART_OF | RELATED_TO",
  "confidence": "high | medium | low",
  "reason": "brief explanation (max 15 words)"
}}
"""
        
        try:
            response = self.llm.generate(prompt, json_mode=True)
            result = json.loads(response)
            
            if result.get('related') and result.get('confidence') in ['high', 'medium']:
                return {
                    'type': result.get('relationship_type', 'RELATED_TO'),
                    'reason': result.get('reason', ''),
                    'confidence': result.get('confidence')
                }
        except Exception as e:
            print(f"  → LLM relationship eval error: {e}")
        
        return None
