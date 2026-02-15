import sys
import os

# Setup Path to include project root (parent of memora_os)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.append(parent_dir)

from memora_os.pipeline.reflect.agent import ReflectAgent
import time

def main():
    print("="*60)
    print("🧠 MemoraOS Reflect Interface")
    print("   Chat with your Knowledge Graph")
    print("="*60)
    print("Initializing Reflect Agent...")
    
    try:
        agent = ReflectAgent()
        print("✅ Ready! (Type 'quit' to exit)")
        print("-" * 60)
        
        while True:
            try:
                query = input("\nYou: ")
                if query.lower() in ['quit', 'exit', 'q']:
                    break
                    
                if not query.strip():
                    continue
                    
                start_t = time.time()
                print("Thinking...", end="", flush=True)
                response = agent.query(query)
                duration = time.time() - start_t
                
                print(f"\rMemora ({duration:.1f}s):")
                print(response)
                print("-" * 60)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"\nError processing query: {e}")
                
    except Exception as e:
        print(f"Failed to initialize: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
