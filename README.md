# MemoraOS: Digital Nervous System

MemoraOS is a local, privacy-first **Digital Nervous System** that captures your "Whole Life" context (Audio, Screen, Email, Calendar) and converts it into an interlinked **Knowledge Graph**.

## 🧠 Architecture "Winning Cards"
1.  **Dual-Layer Graph**: 'Quick' layer for recent context (<48h) + 'Core' layer for long-term memory.
2.  **Hidden Context**: Multi-agent pipeline allowing "Time" and "Entity" based linking.
3.  **<4B Constraints**: Designed to run on small open-source models (Phi-3, TinyLlama).
4.  **Windows Native**: deeply integrated with Outlook and Windows Audio/Screen subsystems.

## 🚀 Getting Started

### Prerequisites
- Python 3.10+
- **Windows OS** (required for `pywin32`, `mss`, `pyaudio`)
- Outlook (optional, for Calendar/Email listeners)
- [FFmpeg](https://ffmpeg.org/download.html) (required for Audio processing if you expand features)

### Installation

1.  **Install Dependencies**:
    ```bash
    pip install -r memora_os/requirements.txt
    ```

2.  **Configuration**:
    Edit `memora_os/config/settings.yaml` to adjust listening intervals or toggle specific "Senses".

### Running the System
To activate the "Digital Nervous System", run the main entry point. This will start the background listeners.

```bash
python memora_os/main.py
```

## 🧪 Testing the Listeners

Once `main.py` is running, you will see logs indicating "Senses" are active.

1.  **Audio**: Speak into your microphone. If you speak for >1s, the `[Ear]` will trigger and save a `.wav` file to `data/audio`.
2.  **Screenshot**: Wait 10-30 seconds (configured in settings). The `[Eye]` will capture a `.png` to `data/screenshots`.
3.  **Outlook**: If you have a calendar event or email with "Project X" in the subject/body, the `[Calendar]` and `[Email]` listeners will pick it up.

## 🔄 Data Flow (Next Steps)

Currently, the system is in **Phase 1 (Ingestion)**.

**Current Flow:**
`Reality` -> `Listeners (mss/pyaudio/win32)` -> `Event Queue` -> `Print to Console`

**Next Phase (Normalization & Linking):**
We will implement the **Normalizer Agent** to take these events from the Queue and pass them to a local LLM.

**Target Flow:**
`Event Queue` -> **`Normalizer Agent`** (LLM) -> `Structured JSON` -> **`Linker Agent`** -> `Knowledge Graph`

## Directory Structure
- `core/`: Core data structures (`Event` class).
- `pipeline/ingestors/`: The Listeners (Audio, Screen, Email, Calendar).
- `pipeline/normalizers/`: (Coming Soon) LLM-based data cleaning.
- `pipeline/linkers/`: (Coming Soon) Graph relation logic.
- `config/`: Settings and Prompts.
