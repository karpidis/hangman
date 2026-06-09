import os
import json
import requests
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

class DeepseekClient:
    def __init__(self):
        self.api_key = os.getenv("DEEPSEEK_API_KEY")
        self.model = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
        self.timeout = int(os.getenv("DEEPSEEK_TIMEOUT", "30"))
        self.base_url = "https://api.deepseek.com/v1"

        if not self.api_key:
            raise ValueError("DEEPSEEK_API_KEY not found in environment. Please set it in .env file.")

    def get_definition(self, word: str, language: str, max_retries: int = 2) -> Optional[str]:
        """Fetch definition for a word in the given language."""
        prompt = (
            f"Provide a concise definition (1-2 sentences) for the {language} word "
            f"'{word}'. Write the definition in {language}. Return only the definition, "
            "no extra text."
        )
        return self._call_api(prompt, max_retries)

    def get_etymology(self, word: str, language: str, max_retries: int = 2) -> Optional[str]:
        """Fetch etymology for a word in the given language."""
        prompt = (
            f"Provide a brief etymology (1-2 sentences) for the {language} word "
            f"'{word}'. Write the etymology in {language}. Return only the etymology, "
            "no extra text."
        )
        return self._call_api(prompt, max_retries)

    def _call_api(self, prompt: str, max_retries: int = 2) -> Optional[str]:
        """Make API call to deepseek with retry logic."""
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    f"{self.base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "model": self.model,
                        "messages": [
                            {"role": "system", "content": "You are a helpful assistant providing concise, accurate information."},
                            {"role": "user", "content": prompt}
                        ],
                        "temperature": 0.3,
                        "max_tokens": 200
                    },
                    timeout=self.timeout
                )

                if response.status_code == 200:
                    data = response.json()
                    if "choices" in data and len(data["choices"]) > 0:
                        content = data["choices"][0].get("message", {}).get("content", "").strip()
                        return content if content else None
                    return None

                elif response.status_code == 401:
                    raise ValueError(f"Authentication failed: {response.status_code}. Check your API key.")
                elif response.status_code == 402:
                    raise ValueError(f"Payment required: {response.status_code}. Check your Deepseek account balance or API key validity.")
                elif response.status_code == 429:
                    print(f"Rate limited (attempt {attempt + 1}/{max_retries})")
                    if attempt < max_retries - 1:
                        continue
                    return None
                else:
                    print(f"API error ({attempt + 1}/{max_retries}): {response.status_code}")
                    if attempt < max_retries - 1:
                        continue
                    return None

            except requests.Timeout:
                print(f"Timeout (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    continue
                return None
            except requests.RequestException as e:
                print(f"Network error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    continue
                return None

        return None


if __name__ == "__main__":
    client = DeepseekClient()
    definition = client.get_definition("hello", "English")
    print(f"Definition: {definition}")
