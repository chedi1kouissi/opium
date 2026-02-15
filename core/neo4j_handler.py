from neo4j import GraphDatabase
import logging

class Neo4jHandler:
    """
    Handles connection and streaming of graph data to Neo4j.
    Mirroring the logic of GraphStorage but for a property graph database.
    """
    def __init__(self, settings):
        # Handle dict or object
        if isinstance(settings, dict):
            self.uri = settings.get("URI", "bolt://localhost:7687")
            auth_val = settings.get("AUTH", ["neo4j", "password"])
            self.auth = tuple(auth_val) if isinstance(auth_val, list) else auth_val
        else:
            self.uri = getattr(settings, "URI", "bolt://localhost:7687")
            self.auth = tuple(getattr(settings, "AUTH", ["neo4j", "password"]))
            
        self.driver = None
        self.connect()

    def connect(self):
        try:
            self.driver = GraphDatabase.driver(self.uri, auth=self.auth)
            # Verify connection
            self.driver.verify_connectivity()
            print("[Neo4j] Connected to database.")
        except Exception as e:
            print(f"[Neo4j] Connection Failed: {e}")
            self.driver = None

    def close(self):
        if self.driver:
            self.driver.close()

    def add_event(self, event, normalized_data=None):
        if not self.driver: 
            return

        query = """
        MERGE (e:Event {id: $id})
        SET e.type = "EVENT",
            e.event_type = $event_type,
            e.timestamp = $timestamp,
            e.source = $source,
            e.layer = "QUICK",
            e.summary = $summary,
            e.file_path = $file_path,
            e.content = $content
        """
        
        # Prepare parameters
        from datetime import datetime
        timestamp_str = event.timestamp.isoformat() if isinstance(event.timestamp, datetime) else str(event.timestamp)
        
        # Safe content extraction
        summary = ""
        file_path = ""
        if normalized_data:
             summary = normalized_data.get("content_summary", "")
             file_path = normalized_data.get("deep_metadata", {}).get("file_path", "")
        
        # Truncate content for DB if too huge
        content = str(event.content)[:5000]

        params = {
            "id": event.id,
            "event_type": event.event_type,
            "timestamp": timestamp_str,
            "source": event.source,
            "summary": summary,
            "file_path": file_path,
            "content": content
        }

        try:
            with self.driver.session() as session:
                session.run(query, params)
        except Exception as e:
            print(f"[Neo4j] Error adding event: {e}")

    def add_entity(self, name, label="ENTITY"):
        if not self.driver:
            return

        # Sanitize label to prevent injection (though typically controlled code)
        clean_label = "".join(filter(str.isalnum, label))
        if not clean_label: clean_label = "ENTITY"

        query = f"""
        MERGE (n:`{clean_label}` {{name: $name}})
        SET n.type = "ENTITY", n.layer = "CORE"
        """
        
        try:
            with self.driver.session() as session:
                session.run(query, name=name)
        except Exception as e:
            print(f"[Neo4j] Error adding entity: {e}")

    def create_relationship(self, source_id, target_id, relation_type):
        if not self.driver:
            return

        # Identify if source/target are Events (UUIDs) or Entities (Label:Name)
        # GraphStorage Entity IDs are "Label:Name". Neo4j doesn't use that as ID.
        
        def parse_id(node_id):
            if ":" in node_id and len(node_id.split(":")) == 2 and " " not in node_id.split(":")[0]:
                # Heuristic: "PERSON:Sarah", "PROJECT:Apollo"
                parts = node_id.split(":")
                return None, parts[1], parts[0] # Returns (UUID, Name, Label)
            else:
                # Likely an event UUID
                return node_id, None, None

        src_uuid, src_name, src_label = parse_id(source_id)
        tgt_uuid, tgt_name, tgt_label = parse_id(target_id)
        
        # Construct Match Query
        # We need to find the specific nodes first
        
        match_clauses = []
        params = {"rel_type": relation_type}
        
        # Source Match
        if src_uuid:
            match_clauses.append("MATCH (a:Event {id: $src_id})")
            params["src_id"] = src_uuid
        else:
            match_clauses.append(f"MATCH (a:`{src_label}` {{name: $src_name}})")
            params["src_name"] = src_name

        # Target Match
        if tgt_uuid:
            match_clauses.append("MATCH (b:Event {id: $tgt_id})")
            params["tgt_id"] = tgt_uuid
        else:
            match_clauses.append(f"MATCH (b:`{tgt_label}` {{name: $tgt_name}})")
            params["tgt_name"] = tgt_name
            
        # Combine
        full_query = "\n".join(match_clauses) + "\n"
        
        # Sanitization for relation type
        clean_rel = "".join(filter(lambda x: x.isalnum() or x == "_", relation_type)).upper()
        
        full_query += f"MERGE (a)-[r:`{clean_rel}`]->(b)"
        
        try:
            with self.driver.session() as session:
                session.run(full_query, params)
        except Exception as e:
            # print(f"[Neo4j] Error adding relation {clean_rel}: {e}")
            pass # Suppress minor relation errors during heavy sync
