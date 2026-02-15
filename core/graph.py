import networkx as nx
import json
import os
from datetime import datetime

class GraphStorage:
    """
    Unified Graph Storage (Quick + Core Layers).
    Currently powered by NetworkX for the prototype.
    """
    def __init__(self, storage_path="./data/graph.json"):
        self.storage_path = storage_path
        self.graph = nx.DiGraph()
        self._load()
        
        # Neo4j Handler
        from memora_os.config import settings
        self.neo4j = None
        if hasattr(settings, "NEO4J") and settings.NEO4J.get("ENABLED"):
             from memora_os.core.neo4j_handler import Neo4jHandler
             self.neo4j = Neo4jHandler(settings.NEO4J)

    def add_event_node(self, event, normalized_data=None):
        """
        Adds an Event Node to the graph.
        """
        node_id = event.id
        
        # Handle timestamp conversion
        from datetime import datetime
        if isinstance(event.timestamp, datetime):
            timestamp_str = event.timestamp.isoformat()
        elif isinstance(event.timestamp, (int, float)):
            timestamp_str = datetime.fromtimestamp(event.timestamp).isoformat()
        else:
            timestamp_str = str(event.timestamp)
        
        attrs = {
            "type": "EVENT",
            "event_type": event.event_type,
            "timestamp": timestamp_str,
            "source": event.source,
            "layer": "QUICK" # Default to Quick layer
        }
        
        if normalized_data:
            attrs.update({
                "summary": normalized_data.get("content_summary"),
                "primary_entity": normalized_data.get("primary_entity"),
                "file_path": normalized_data.get("deep_metadata", {}).get("file_path", "")
            })
            
        self.graph.add_node(node_id, **attrs)
        
        # Stream to Neo4j
        if self.neo4j:
            self.neo4j.add_event(event, normalized_data)
            
        return node_id

    def add_entity_node(self, name, label="ENTITY"):
        """
        Adds a Core Entity Node (e.g., Person, Project).
        """
        node_id = f"{label}:{name}"
        if not self.graph.has_node(node_id):
            self.graph.add_node(node_id, type="ENTITY", label=label, name=name, layer="CORE")
            
            # Stream to Neo4j
            if self.neo4j:
                self.neo4j.add_entity(name, label)
                
        return node_id

    def add_relation(self, source_id, target_id, relation_type):
        self.graph.add_edge(source_id, target_id, relation=relation_type)
        
        # Stream to Neo4j
        if self.neo4j:
            self.neo4j.create_relationship(source_id, target_id, relation_type)

    def find_nodes_by_attribute(self, attr, value):
        found = []
        for node, data in self.graph.nodes(data=True):
            if data.get(attr) == value:
                found.append(node)
        return found
        
    def get_context_window(self, timestamp, window_minutes=30):
        """
        Finds events that happened within X minutes of the timestamp.
        """
        from datetime import datetime, timedelta
        
        # Convert input timestamp to datetime if needed
        if isinstance(timestamp, (int, float)):
            target_time = datetime.fromtimestamp(timestamp)
        elif isinstance(timestamp, datetime):
            target_time = timestamp
        else:
            target_time = datetime.fromisoformat(str(timestamp))
        
        context_nodes = []
        for node, data in self.graph.nodes(data=True):
            if data.get("type") == "EVENT" and data.get("timestamp"):
                try:
                    # Parse timestamp from node (ISO format string)
                    node_time = datetime.fromisoformat(data["timestamp"])
                    diff = abs((node_time - target_time).total_seconds())
                    
                    if diff <= (window_minutes * 60):
                        context_nodes.append(node)
                except:
                    continue
        return context_nodes

    def _load(self):
        if os.path.exists(self.storage_path):
            try:
                with open(self.storage_path, 'r') as f:
                    data = json.load(f)
                    self.graph = nx.node_link_graph(data)
            except:
                print("[Graph] New graph initialized.")

    def save(self):
        data = nx.node_link_data(self.graph)
        with open(self.storage_path, 'w') as f:
            json.dump(data, f)
