# 🧠 MemoraOS: Your Private Digital Nervous System

> "Stop searching. Start remembering."

**MemoraOS** is an intelligent layer for your computer that connects your fragmented digital life (Emails, Meetings, Chats, Screen context) into a single, searchable **Knowledge Graph**. 

It runs **100% locally** on your machine, ensuring your data never leaves your control.

---

## 🌟 Why MemoraOS? (The Value Add)

### 1. The Problem: "Digital Amnesia"
You have a meeting about "Project Alpha". You receive an email about "Budget constraints". You see a Slack message about a "Delay". 
**These events are connected, but your computer doesn't know that.** They live in separate apps, and you have to manually connect the dots in your brain.

### 2. The Solution: "The Winning Card" (Knowledge Graph)
MemoraOS acts as a **Digital Nervous System**. It watches what you do, understands the context, and **automatically connects the dots**.
*   It knows the "Budget" email *caused* the "Delay".
*   It knows "Sarah" attended the "Project Alpha" meeting.
*   **It builds a web of memories (a Graph) instead of a list of files.**

### 3. Privacy First
*   **No Cloud**: No data is sent to OpenAI, Google, or Microsoft.
*   **Local AI**: Uses your own computer's power (Ollama + 4B models) to read and think.
*   **Local Storage**: Your memory lives on your hard drive (`graph.json` / Neo4j).

---

## 🏗️ How It Works (The Architecture)

Think of MemoraOS as a team of 4 specialized AI Agents working for you 24/7:

### 1. The Senses (Perception Layer)
Just like you have eyes and ears, MemoraOS has "Listeners":
*   **👀 Eye (OCR)**: Reads text from your screen every few seconds.
*   **👂 Ear (STT)**: Listens to your microphone during meetings.
*   **📅 Calendar**: Checks your Outlook/Google schedule.
*   **📧 Email**: Reads incoming messages.

### 2. The Lens (Normalizer Agent)
Raw data is messy. This agent cleans it up.
*   *Input*: "Uhh, so yeah, let's delay the launch." (Audio)
*   *Output*: `{ "topic": "Launch Delay", "who": "User", "action": "Decision" }`

### 3. The Brain (Linker Agent)
This is where the magic happens. It looks for connections in your past.
*   *"Wait, this 'Launch Delay' email is related to the 'Budget Meeting' from Monday!"*
*   It creates a **Semantic Link**: `(Email)-[CAUSED_BY]->(Meeting)`

### 4. The Analyst (Reflect Agent)
You can ask questions to your memory.
*   *You*: "Why was the launch delayed?"
*   *Analyst*: "The launch was delayed due to API performance issues identified by Marcus's team on Monday." (It traverses the graph to find the answer).

---

## 🚀 Getting Started

### Prerequisites
1.  **Python 3.10+**
2.  **Ollama**: Install from [ollama.com](https://ollama.com) and run `ollama run phi3:mini`.
3.  **Neo4j** (Optional): For 3D visualization.

### Installation
```powershell
# 1. Clone & Install
pip install -r requirements.txt
```

### Usage
**1. Run the System (The Listeners)**
This starts the background agents.
```powershell
python main.py
```

**2. Test with a Scenario**
Simulate a week of life (Emails, Meetings) to populate the graph immediately.
```powershell
python scenario_realistic.py
```

**3. Chat with your Memory**
Ask questions about what happened.
```powershell
python query.py
```

**4. Visualize (Neo4j)**
Open `http://localhost:7474` to see your beautiful Knowledge Graph web.

---

## 🛠️ Technical Highlights

*   **GraphRAG**: Retrieval Augmented Generation using Graph traversal + Vector search.
*   **Dual-Write Storage**: Saves to `JSON` (simple) and `Neo4j` (powerful) simultaneously.
*   **Small Language Models (SLM)**: Optimized for `phi3:mini` (3.8B implementation) for low latency on consumer hardware.
*   **Modular Pipeline**: Easily plug in new Listeners (e.g., Slack, Discord) or Linkers.

---

*"Your Life, Connected."*
