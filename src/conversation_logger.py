"""
    Conversation Logger:
    Logs the conversation between Patient (bot) and Operator in formatted text files.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import List, Tuple

class ConversationLogger:
    """
        Logs conversation history in format:
        Patient: ...
        Operator: ...
    """

    def __init__(self, scenario: str, base_dir: Path = None):
        self.scenario = scenario
        self.messages: List[Tuple[str, str]] = []  # List of (speaker, message) tuples

        if base_dir is None:
            self.base_dir = Path(__file__).parent.parent
        else:
            self.base_dir = base_dir
        
        self.logs_dir = self.base_dir / 'logs'
        self.logs_dir.mkdir(exist_ok = True)

        self.run_number = self._get_next_run_number()
        self.log_file = self.logs_dir / f"{self.scenario}_run_{self.run_number}.txt"

        self.prompts = self._load_prompts()

    
    def _load_prompts(self) -> dict:
        prompt_path = Path(__file__).parent / 'prompts' / 'prompt.json'
        with open(prompt_path, 'r') as f:
            prompts = json.load(f)
        return prompts

    
    def _get_next_run_number(self) -> int:
        pattern = f"{self.scenario}_run_*.txt"
        existing_files = list(self.logs_dir.glob(pattern))

        if not existing_files:
            return 1
        
        run_numbers = []
        for file in existing_files:
            try:
                parts = file.stem.split("_")
                if len(parts) >= 3 and parts[1] == "run":
                    run_numbers.append(int(parts[2]))

            except (ValueError, IndexError):
                continue

        if not run_numbers:
            return 1
        
        return max(run_numbers) + 1

    def log_operator(self, message: str):
        """Log a message from the operator."""
        if message and message.strip():
            self.messages.append(("Operator", message.strip()))
    
    def log_patient(self, message: str):
        """Log a message from the patient (bot)."""
        if message and message.strip():
            self.messages.append(("Patient", message.strip()))

    def save(self):
        try:
            with open(self.log_file, 'w', encoding = 'utf-8') as f:
                f.write(f"Scenario: {self.scenario}\n")
                f.write(f"Run: {self.run_number}\n")
                f.write(f"System Prompt: {self.prompts['scenarios'][self.scenario]}\n")
                f.write("=" * 80 + "\n\n")

                # Log conversation history
                for speaker, message in self.messages:
                    f.write(f"{speaker}: {message}\n\n")
            
            print(f"Conversation log saved to: {self.log_file}")
            return self.log_file
        except Exception as e:
            print(f"Error saving conversation log: {e}")
            return None