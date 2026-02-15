import json
import sys
import os

# Load graph and show results
with open('data/graph.json', 'r') as f:
    graph = json.load(f)

print("="*70)
print("KNOWLEDGE GRAPH ANALYSIS")
print("="*70)
print(f"Total Nodes: {len(graph['nodes'])}")
print(f"Total Links: {len(graph['links'])}")
print()

if graph['nodes']:
    print("NODE TYPES:")
    from collections import Counter
    node_types = Counter([n.get('type', 'UNKNOWN') for n in graph['nodes']])
    for ntype, count in node_types.items():
        print(f"  {ntype}: {count}")
    print()
    
    print("SAMPLE NODES (first 5):")
    for i, node in enumerate(graph['nodes'][:5], 1):
        print(f"\n{i}. Type: {node.get('type')}")
        print(f"   ID: {node.get('id', 'N/A')[:50]}")
        if 'name' in node:
            print(f"   Name: {node['name']}")
        if 'event_type' in node:
            print(f"   Event Type: {node['event_type']}")
else:
    print("❌ NO NODES IN GRAPH")

print("\n" + "="*70)

# Load trace
with open('data/trace.json', 'r') as f:
    trace = json.load(f)

print(f"TRACE ENTRIES: {len(trace)}")
if trace:
    print("\nLAST TRACE ENTRY:")
    last = trace[-1]
    print(f"  Agent: {last.get('agent')}")
    print(f"  Action: {last.get('action')}")
    print(f"  Timestamp: {last.get('timestamp')}")

print("="*70)
