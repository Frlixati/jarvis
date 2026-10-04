# Jarvis

A lightweight Python-based Jarvis-style assistant that listens to voice commands, responds with speech, and can optionally use OpenAI for smarter responses.

Features:
- Voice input through the microphone
- Text-to-speech output
- Local command execution
- Open websites or folders
- Optional OpenAI-powered responses
- Simple fallback command handling

## Quick start

1. Create a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate   # Linux/macOS
   .venv\Scripts\activate      # Windows
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Copy the environment example:
   ```bash
   cp .env.example .env
   ```

4. Add your API key if you want OpenAI-powered responses:
   ```env
   OPENAI_API_KEY=your_key_here
   ```

5. Run the assistant:
   ```bash
   python jarvis.py
   ```

## Example commands

- "Jarvis, what time is it?"
- "Jarvis, open Google"
- "Jarvis, list files in the current directory"
- "Jarvis, run pwd"
- "Jarvis, tell me a joke"
- "Jarvis, summarize this project"

## Notes

- This is a starter project designed to be extended.
- Microphone access and audio support depend on your OS and hardware.
- If no OpenAI key is set, Jarvis falls back to local command handling and canned responses.
