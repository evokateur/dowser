import pyperclip
import logging
from typing import Optional


class ClipboardManager:
    @staticmethod
    def copy_to_clipboard(text: str) -> bool:
        try:
            pyperclip.copy(text)
            logging.info(f"Copied to clipboard: {text}")
            return True
        except Exception as e:
            logging.error(f"Failed to copy to clipboard: {e}")
            return False

    @staticmethod
    def get_from_clipboard() -> Optional[str]:
        try:
            content = pyperclip.paste()
            return content
        except Exception as e:
            logging.error(f"Failed to read from clipboard: {e}")
            return None

