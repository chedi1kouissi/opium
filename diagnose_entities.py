import json
import sys
import os

# Check trace for normalizer output
print("="*70)
print("DIAGNOSTIC CHECK - Why No Entities?")
print("="*70)

try:
    with open('data/trace.json', 'r') as f:
        trace = json.load(f)
    
    print(f"\n✅ Found {len(trace)} trace entries\n")
    
    for i, entry in enumerate(trace, 1):
        print(f"\n--- Entry {i} ---")
        print(f"Agent: {entry.get('agent')}")
        print(f"Action: {entry.get('action')}")
        print(f"Timestamp: {entry.get('timestamp')}")
        
        if 'details' in entry:
            details = entry['details']
            
            # Check for entities
            if 'entities' in details:
                entities = details['entities']
                total_entities = sum(len(v) for v in entities.values() if isinstance(v, list))
                print(f"Total Entities Extracted: {total_entities}")
                
                if total_entities > 0:
                    print("\nEntity Breakdown:")
                    for etype, items in entities.items():
                        if isinstance(items, list) and items:
                            print(f"  {etype}: {items}")
                else:
                    print("⚠️  NO ENTITIES EXTRACTED!")
            
            # Check primary entity
            if 'primary_entity' in details:
                print(f"Primary Entity: '{details['primary_entity']}'")
            
            # Check if raw_text exists
            if 'deep_metadata' in details and 'raw_text' in details['deep_metadata']:
                raw_text = details['deep_metadata']['raw_text']
                print(f"Raw Text Length: {len(raw_text)} chars")
                print(f"Raw Text Preview: {raw_text[:100]}...")
        
        print()

except FileNotFoundError:
    print("❌ trace.json not found!")
except json.JSONDecodeError as e:
    print(f"❌ Error parsing trace.json: {e}")

print("="*70)
print("\n💡 DIAGNOSIS:")
print("If entities are empty, the Normalizer LLM call is failing or")
print("returning malformed JSON. Check if Ollama is responding correctly.")
print("="*70)
