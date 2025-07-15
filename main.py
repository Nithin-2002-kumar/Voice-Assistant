import os
import speech_recognition as sr
import pyttsx3
import subprocess
from datetime import datetime
import pyautogui
import wikipedia
import spacy
import logging
import webbrowser

# Setup logging
logging.basicConfig(
    filename="assistant.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

class VoiceAssistant:
    def __init__(self):
        # Initialize text-to-speech engine
        self.engine = pyttsx3.init()
        self.engine.setProperty("rate", 150)
        self.engine.setProperty("volume", 0.9)

        # Initialize speech recognizer
        self.recognizer = sr.Recognizer()

        # Load spaCy model for NLP
        self.nlp = spacy.load("en_core_web_sm")

        # User preferences
        self.user_preferences = {
            "name": "User",
            "speech_rate": 150,
            "speech_volume": 0.9,
            "preferred_language": "en",
            "background_noise_level": "normal"
        }

        # Predefined applications
        self.apps = {
            "notepad": "notepad.exe",
            "calculator": "calc.exe",
            "chrome": "C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe"
        }

        # Task management
        self.task_queue = []
        self.task_status = {}
        self.current_context = None

    def speak(self, text, emotion=None):
        """Speak the provided text with optional emotion-based adjustments."""
        if emotion == "happy":
            self.engine.setProperty("rate", 160)
        elif emotion == "sad":
            self.engine.setProperty("rate", 120)
        else:
            self.engine.setProperty("rate", self.user_preferences["speech_rate"])
        
        self.engine.setProperty("volume", self.user_preferences["speech_volume"])
        self.engine.say(text)
        self.engine.runAndWait()

    def listen(self):
        """Listen for voice commands with noise adjustment."""
        with sr.Microphone() as source:
            print("Listening for commands...")
            noise_level = self.user_preferences["background_noise_level"]
            duration = 5 if noise_level == "noisy" else 1 if noise_level == "quiet" else 3
            self.recognizer.adjust_for_ambient_noise(source, duration=duration)

            try:
                audio = self.recognizer.listen(source)
                command = self.recognizer.recognize_google(audio, language=self.user_preferences["preferred_language"]).lower()
                logging.info(f"User said: {command}")
                return command
            except sr.UnknownValueError:
                self.speak("Sorry, I didn't understand that. Could you repeat?")
                return None
            except sr.RequestError:
                self.speak("Sorry, I couldn't reach the service. Please try again.")
                return None

    def process_command(self, command):
        """Process commands using NLP to identify intents."""
        doc = self.nlp(command)
        intents = []

        for token in doc:
            if token.lemma_ in ["open", "start", "launch"]:
                intents.append("open")
            elif token.lemma_ in ["search", "find"]:
                intents.append("search")
            elif token.lemma_ in ["time"]:
                intents.append("time")
            elif token.lemma_ in ["screenshot"]:
                intents.append("screenshot")
            elif token.lemma_ in ["exit", "quit"]:
                intents.append("exit")

        return intents

    def open_application(self, app_name):
        """Open an application by name."""
        app_path = self.apps.get(app_name)
        if app_path:
            try:
                subprocess.Popen(app_path)
                self.speak(f"Opening {app_name}, {self.user_preferences['name']}")
                return True
            except FileNotFoundError:
                self.speak(f"Sorry, I couldn't find {app_name} on your system.")
                return False
        else:
            self.speak(f"I don't have {app_name} in my list of applications.")
            return False

    def execute_command(self, command):
        """Execute the recognized command."""
        intents = self.process_command(command)
        self.task_queue.append(command)
        self.task_status[command] = "active"
        self.current_context = command

        if "open" in intents:
            if "notepad" in command:
                self.open_application("notepad")
            elif "calculator" in command:
                self.open_application("calculator")
            elif "chrome" in command or "browser" in command:
                self.open_application("chrome")
            else:
                app_name = command.replace("open", "").strip()
                if app_name:
                    self.open_application(app_name)
                else:
                    self.speak("Please specify the application to open.")
        
        elif "search" in intents:
            self.speak(f"What do you want to search for, {self.user_preferences['name']}?")
            query = self.listen()
            if query:
                try:
                    result = wikipedia.summary(query, sentences=2)
                    self.speak(f"According to Wikipedia: {result}")
                except wikipedia.exceptions.DisambiguationError as e:
                    self.speak(f"Multiple results found for {query}. Please be more specific.")
                except wikipedia.exceptions.PageError:
                    self.speak(f"No Wikipedia page found for {query}.")
        
        elif "time" in intents:
            current_time = datetime.now().strftime("%H:%M:%S")
            self.speak(f"The time is {current_time}, {self.user_preferences['name']}")
        
        elif "screenshot" in intents:
            screenshot = pyautogui.screenshot()
            screenshot.save("screenshot.png")
            self.speak(f"Screenshot taken and saved, {self.user_preferences['name']}.")
        
        elif "exit" in intents:
            self.speak(f"Goodbye, {self.user_preferences['name']}!")
            exit()
        
        else:
            self.speak(f"Sorry, {self.user_preferences['name']}, I didn't understand that command.")

    def set_preferences(self):
        """Set user preferences for personalization."""
        self.speak("What is your name?")
        name = self.listen()
        if name:
            self.user_preferences["name"] = name
            self.speak(f"Hello, {self.user_preferences['name']}! Let's personalize your experience.")

        self.speak("Do you want to change the speech rate? Say 'yes' or 'no'.")
        response = self.listen()
        if response and "yes" in response:
            self.speak("What speech rate would you prefer? Default is 150.")
            rate = self.listen()
            if rate and rate.isdigit():
                self350user_preferences["speech_rate"] = int(rate)
                self.speak(f"Speech rate set to {self.user_preferences['speech_rate']}.")
            else:
                self.speak("Invalid rate, keeping default.")

        self.speak("Do you want to adjust the volume? Say 'yes' or 'no'.")
        response = self.listen()
        if response and "yes" in response:
            self.speak("What volume level? Between 0.0 and 1.0, default is 0.9.")
            volume = self.listen()
            try:
                volume = float(volume)
                if 0.0 <= volume <= 1.0:
                    self.user_preferences["speech_volume"] = volume
                    self.speak(f"Volume set to {self.user_preferences['speech_volume']}.")
                else:
                    self.speak("Volume out of range, keeping default.")
            except ValueError:
                self.speak("Invalid volume, keeping default.")

    def run(self):
        """Run the voice assistant."""
        self.set_preferences()
        self.speak(f"Hello, {self.user_preferences['name']}. I am your assistant. How can I help you today?")
        while True:
            command = self.listen()
            if command:
                self.execute_command(command)

if __name__ == "__main__":
    try:
        assistant = VoiceAssistant()
        assistant.run()
    except Exception as e:
        logging.error(f"Error running assistant: {e}")
        print(f"Error: {e}")
