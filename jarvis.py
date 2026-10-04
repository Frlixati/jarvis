import argparse
import os
import platform
import shlex
import subprocess
import sys
import webbrowser
from datetime import datetime
from pathlib import Path

import pyttsx3
import speech_recognition as sr
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

try:
    from flask import Flask, jsonify, render_template_string, request
except ImportError:
    Flask = None


class JarvisAssistant:
    def __init__(self, interactive=True, wake_word="jarvis"):
        load_dotenv()
        self.interactive = interactive
        self.wake_word = wake_word.lower()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 170)
        self.engine.setProperty("volume", 1.0)

        self.openai_client = None
        if OpenAI is not None:
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key:
                self.openai_client = OpenAI(api_key=api_key)

    def speak(self, text: str):
        print(f"Jarvis: {text}")
        try:
            self.engine.say(text)
            self.engine.runAndWait()
        except Exception:
            pass

    def listen_for_command(self) -> str:
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.speak("Listening...")
            audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)

        try:
            text = self.recognizer.recognize_google(audio)
            return self.clean_command(text)
        except (sr.UnknownValueError, sr.RequestError):
            return ""

    def clean_command(self, text: str) -> str:
        if not text:
            return ""
        cleaned = text.strip()
        lowered = cleaned.lower()
        if self.wake_word in lowered:
            return cleaned.lower().replace(self.wake_word, "", 1).strip(", ")
        return cleaned

    def handle(self, command: str) -> str:
        text = (command or "").strip()
        if not text:
            return "I didn't catch that. Please repeat."

        normalized = text.lower()

        if any(stop in normalized for stop in ["exit", "shutdown", "goodbye", "stop"]):
            return "Shutting down Jarvis."

        if self.openai_client is not None and not any(
            keyword in normalized for keyword in ["time", "date", "joke", "open", "run", "list", "summarize", "status", "git", "hello", "who are you"]
        ):
            ai_reply = self._ask_openai(text)
            if ai_reply:
                return ai_reply

        if "hello" in normalized or "hi" in normalized:
            return "Hello! I am Jarvis, your local assistant. How can I help?"

        if "who are you" in normalized or "what are you" in normalized:
            return "I am Jarvis, your voice-powered AI assistant. I can open websites, manage files, run commands, and summarize your project."

        if "time" in normalized:
            return f"The current time is {datetime.now().strftime('%H:%M:%S')}."

        if "date" in normalized:
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}."

        if "joke" in normalized:
            return "Why do programmers prefer dark mode? Because light attracts bugs."

        if "open google" in normalized:
            webbrowser.open("https://www.google.com")
            return "Opening Google."

        if "open youtube" in normalized:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube."

        if "open github" in normalized:
            webbrowser.open("https://github.com")
            return "Opening GitHub."

        if "list files" in normalized or "ls" in normalized or "show files" in normalized:
            return self._list_directory()

        if "open folder" in normalized or "open workspace" in normalized:
            folder = Path.cwd()
            self._open_path(folder)
            return f"Opening the current workspace: {folder}"

        if "open " in normalized and "app" in normalized:
            app_name = normalized.replace("open ", "").replace(" app", "").strip()
            return self._open_application(app_name)

        if "run " in normalized or "execute " in normalized:
            shell_command = self._extract_shell_command(normalized)
            return self._run_shell(shell_command)

        if "git status" in normalized or "status" in normalized:
            return self._git_status()

        if "summarize project" in normalized or "summarize this project" in normalized or "project summary" in normalized:
            return self._summarize_project()

        if "read" in normalized and "file" in normalized:
            return self._read_file_from_request(text)

        if "help" in normalized:
            return (
                "I can help with time and date, opening websites, listing files, running shell commands, "
                "checking git status, summarizing your project, and launching local apps."
            )

        return "I can help with simple commands like time, files, websites, git status, and project summaries."

    def _list_directory(self) -> str:
        try:
            entries = sorted(os.listdir('.'))
            if not entries:
                return "The current directory is empty."
            return "Files and folders in the current directory: " + ", ".join(entries[:25])
        except Exception as exc:
            return f"I could not list files: {exc}"

    def _open_path(self, path: Path):
        try:
            if sys.platform.startswith("darwin"):
                subprocess.run(["open", str(path)], check=False)
            elif os.name == "nt":
                os.startfile(str(path))
            else:
                subprocess.run(["xdg-open", str(path)], check=False)
        except Exception:
            pass

    def _open_application(self, app_name: str) -> str:
        app_name = app_name.strip()
        if not app_name:
            return "Please specify an application name."

        try:
            if sys.platform.startswith("darwin"):
                subprocess.run(["open", "-a", app_name], check=False)
            elif os.name == "nt":
                os.startfile(app_name)
            else:
                subprocess.run(["bash", "-lc", f"{app_name} &"], check=False)
            return f"Launching {app_name}."
        except Exception as exc:
            return f"I couldn't launch {app_name}: {exc}"

    def _extract_shell_command(self, normalized: str) -> str:
        for keyword in ["run ", "execute "]:
            if keyword in normalized:
                return normalized.split(keyword, 1)[1].strip()
        return normalized

    def _run_shell(self, shell_command: str) -> str:
        if not shell_command:
            return "No command was provided."
        try:
            result = subprocess.run(shell_command, shell=True, capture_output=True, text=True, timeout=20)
            output = result.stdout.strip() or result.stderr.strip() or "Command completed successfully."
            return output[:1500]
        except subprocess.TimeoutExpired:
            return "The command timed out."
        except Exception as exc:
            return f"I could not run that command: {exc}"

    def _git_status(self) -> str:
        if not os.path.exists(".git"):
            return "This directory is not a git repository."
        try:
            result = subprocess.run(["git", "status", "--short", "--branch"], capture_output=True, text=True, timeout=15)
            output = result.stdout.strip() or result.stderr.strip() or "Git status is clean."
            return output[:1500]
        except Exception as exc:
            return f"I could not check git status: {exc}"

    def _summarize_project(self) -> str:
        root = Path('.')
        files = []
        for path in root.rglob('*'):
            if path.is_file() and not any(part in {'.git', '.venv', '__pycache__'} for part in path.parts):
                if path.suffix.lower() in {'.py', '.md', '.txt', '.json', '.yml', '.yaml', '.js', '.ts'}:
                    files.append(path)

        if not files:
            return "No readable project files were found in this directory."

        summaries = []
        for path in files[:10]:
            try:
                with path.open('r', encoding='utf-8', errors='ignore') as handle:
                    lines = [line.strip() for line in handle.readlines()[:20]]
                    content = " ".join(lines)
                    summaries.append(f"{path}: {content[:180]}")
            except Exception:
                continue

        if not summaries:
            return "I found project files, but could not read them."

        return "Project overview: " + " | ".join(summaries)

    def _read_file_from_request(self, text: str) -> str:
        match = None
        for part in text.split():
            if part.endswith(('.py', '.md', '.txt', '.json', '.yaml', '.yml', '.js', '.ts')):
                match = part
                break
        if not match:
            return "Please specify a file name, such as README.md or app.py."
        path = Path(match)
        if not path.exists():
            return f"I could not find the file '{match}' in the current directory."
        try:
            with path.open('r', encoding='utf-8', errors='ignore') as handle:
                return "\n".join(handle.readlines()[:20])
        except Exception as exc:
            return f"I could not read the file: {exc}"

    def _ask_openai(self, prompt: str) -> str:
        if self.openai_client is None:
            return ""
        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are Jarvis, a helpful assistant. Keep your answers concise and practical."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return ""

    def run(self):
        self.speak("Jarvis is online. How can I help?")
        while True:
            if self.interactive:
                command = self.listen_for_command()
            else:
                command = input("You: ").strip()

            if not command:
                if self.interactive:
                    self.speak("I did not catch that. Please repeat.")
                continue

            if "stop" in command.lower() or "exit" in command.lower() or "shutdown" in command.lower():
                self.speak("Shutting down Jarvis.")
                break

            reply = self.handle(command)
            self.speak(reply)


def create_web_app():
    if Flask is None:
        raise RuntimeError("Flask is not installed. Please install the project requirements first.")

    app = Flask(__name__)
    assistant = JarvisAssistant(interactive=False)

    @app.route('/')
    def home():
        return render_template_string(
            """
            <html>
              <head>
                <title>Jarvis Dashboard</title>
                <style>
                  body { font-family: Arial, sans-serif; margin: 40px; background: #0d1117; color: #e6edf3; }
                  .card { max-width: 900px; margin: auto; background: #161b22; padding: 25px; border-radius: 12px; }
                  textarea, button { width: 100%; margin-top: 12px; padding: 12px; border-radius: 8px; border: 1px solid #30363d; }
                  button { background: #238636; color: white; cursor: pointer; }
                  pre { white-space: pre-wrap; background: #0d1117; padding: 16px; border-radius: 8px; }
                </style>
              </head>
              <body>
                <div class="card">
                  <h1>Jarvis Dashboard</h1>
                  <textarea id="command" rows="5" placeholder="Type a command like 'open google', 'list files', 'summarize project'...\"></textarea>
                  <button onclick="sendCommand()\">Send command</button>
                  <h3>Response</h3>
                  <pre id="response\">Jarvis is online.</pre>
                </div>
                <script>
                  async function sendCommand() {
                    const command = document.getElementById('command').value;
                    const responseEl = document.getElementById('response');
                    responseEl.textContent = 'Thinking...';
                    const res = await fetch('/api/command', {
                      method: 'POST',
                      headers: {'Content-Type': 'application/json'},
                      body: JSON.stringify({ command })
                    });
                    const data = await res.json();
                    responseEl.textContent = data.response || 'No response';
                  }
                </script>
              </body>
            </html>
            """
        )

    @app.route('/api/command', methods=['POST'])
    def command():
        payload = request.get_json(silent=True) or {}
        command = payload.get('command', '')
        response = assistant.handle(command)
        return jsonify({"response": response})

    return app


def main():
    parser = argparse.ArgumentParser(description="Jarvis - voice and command assistant")
    parser.add_argument("--text", action="store_true", help="Use command-line text input instead of microphone input")
    parser.add_argument("--web", action="store_true", help="Run the web dashboard instead of the CLI assistant")
    args = parser.parse_args()

    if args.web:
        app = create_web_app()
        print("Starting Jarvis web dashboard at http://127.0.0.1:5000")
        app.run(host="127.0.0.1", port=5000, debug=False)
        return

    assistant = JarvisAssistant(interactive=not args.text)
    assistant.run()


if __name__ == "__main__":
    main()
