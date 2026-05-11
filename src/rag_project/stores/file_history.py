import json
from collections.abc import Sequence

from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage, message_to_dict, messages_from_dict

from rag_project.config import settings


def get_history(session_id: str) -> "FileChatMessageHistory":
    return FileChatMessageHistory(session_id=session_id, storage_path=settings.chat_history_dir)


class FileChatMessageHistory(BaseChatMessageHistory):
    def __init__(self, session_id: str, storage_path) -> None:
        self.session_id = session_id
        self.storage_path = storage_path
        self.file_path = self.storage_path / self.session_id
        self.file_path.parent.mkdir(parents=True, exist_ok=True)

    def add_messages(self, messages: Sequence[BaseMessage]) -> None:
        all_messages = [*self.messages, *messages]
        serialized = [message_to_dict(message) for message in all_messages]
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump(serialized, file, ensure_ascii=False, indent=2)

    @property
    def messages(self) -> list[BaseMessage]:
        try:
            with self.file_path.open("r", encoding="utf-8") as file:
                return messages_from_dict(json.load(file))
        except FileNotFoundError:
            return []

    def clear(self) -> None:
        with self.file_path.open("w", encoding="utf-8") as file:
            json.dump([], file)