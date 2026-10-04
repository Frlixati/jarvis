import os
import re
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


class JarvisAssistant:
    def __init__(self):
        load_dotenv()
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

    def listen(self) -> str:
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            self.speak("Listening...")
            audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=10)

        try:
            text = self.recognizer.recognize_google(audio)
            return text.strip()
        except sr.UnknownValueError:
            return ""
        except sr.RequestError:
            return ""

    def _parse_command(self, text: str) -> str:
        if not text:
            return ""
        return text.lower().strip()

    def _handle_local_command(self, command: str) -> str:
        if "time" in command:
            return f"The current time is {datetime.now().strftime('%H:%M:%S')}"
        if "date" in command:
            return f"Today is {datetime.now().strftime('%A, %B %d, %Y')}"
        if "list files" in command or "ls" in command:
            try:
                entries = os.listdir('.')
                return "Files and folders in the current directory: " + ", ".join(entries[:20])
            except Exception as exc:
                return f"I could not list files: {exc}"
        if "open google" in command:
            webbrowser.open("https://www.google.com")
            return "Opening Google in your browser."
        if "open youtube" in command:
            webbrowser.open("https://www.youtube.com")
            return "Opening YouTube in your browser."
        if "run " in command or "execute " in command:
            shell_command = command.replace("jarvis,", "").replace("run ", "").replace("execute ", "")
            try:
                result = subprocess.run(shell_command, shell=True, capture_output=True, text=True)
                output = result.stdout.strip() or result.stderr.strip() or "Command completed successfully."
                return output[:1000]
            except Exception as exc:
                return f"I could not run that command: {exc}"
        if "joke" in command:
            return "Why do programmers prefer dark mode? Because light attracts bugs."
        if "hello" in command or "hi" in command:
            return "Hello! I am Jarvis. How can I assist you today?"
        if "who are you" in command or "what are you" in command:
            return "I am Jarvis, your local AI assistant. I can listen, speak, and help with basic tasks."
        if "folder" in command and "open" in command:
            try:
                folder = Path.cwd()
                if sys.platform.startswith("darwin"):
                    subprocess.run(["open", str(folder)], check=False)
                elif os.name == "nt":
                    os.startfile(str(folder))
                else:
                    subprocess.run(["xdg-open", str(folder)], check=False)
                return f"Opening the current working folder: {folder}"
            except Exception as exc:
                return f"I couldn't open the folder: {exc}"
        return "I can help with simple commands like telling the time, opening a website, listing files, or running a shell command."

    def _ask_openai(self, prompt: str) -> str:
        if self.openai_client is None:
            return ""

        try:
            response = self.openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {"role": "system", "content": "You are Jarvis, a helpful AI assistant. Keep answers brief and practical."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.6,
            )
            return response.choices[0].message.content.strip()
        except Exception:
            return ""

    def handle(self, command: str) -> str:
        normalized = self._parse_command(command)
        if "jarvis" not in normalized and not any(word in normalized for word in ["hello", "hi", "time", "date", "joke", "open", "run", "list", "folder", "who are you", "what are you"]):
            pass

        if self.openai_client is not None:
            ai_response = self._ask_openai(command)
            if ai_response:
                return ai_response

        return self._handle_local_command(normalized)

    def run(self):
        self.speak("Jarvis is online. How can I help?")
        while True:
            command = self.listen()
            if not command:
                self.speak("I did not catch that. Please repeat.")
                continue

            print(f"You said: {command}")
            if "stop" in command.lower() or "exit" in command.lower() or "shutdown" in command.lower():
                self.speak("Shutting down Jarvis.")
                break

            reply = self.handle(command)
            self.speak(reply)


if __name__ == "__main__":
    assistant = JarvisAssistant()
    assistant.run()
