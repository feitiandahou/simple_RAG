import os
from collections.abc import Iterator

from dotenv import load_dotenv
from langchain_community.chat_models.tongyi import ChatTongyi
from langchain_community.embeddings import DashScopeEmbeddings
from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableConfig
from langchain_core.runnables import RunnableLambda, RunnablePassthrough, RunnableWithMessageHistory

from rag_project.config import settings
from rag_project.errors import ensure_dashscope_api_key, wrap_external_error
from rag_project.services.vector_store import VectorStoreService
from rag_project.stores.file_history import get_history

load_dotenv()


def print_prompt(prompt):
    print("=" * 20)
    print(prompt.to_string())
    print("=" * 20)
    return prompt


class RagService:
    def __init__(self) -> None:
        ensure_dashscope_api_key(os.environ.get("DASHSCOPE_API_KEY"))

        self.vector_service = VectorStoreService(
            embedding=DashScopeEmbeddings(model=settings.embedding_model_name)
        )
        self.prompt_template = ChatPromptTemplate.from_messages(
            [
                ("system", "以我提供的已知参考资料为主，简洁和专业地回答用户问题。参考资料:{context}。"),
                ("system", "并且我提供用户的对话历史记录，如下："),
                MessagesPlaceholder("history"),
                ("user", "请回答用户提问：{input}"),
            ]
        )
        self.chat_model = ChatTongyi(model=settings.chat_model_name)  # type: ignore[call-arg]
        self.chain = self._build_chain()

    def _build_chain(self):
        retriever = self.vector_service.get_retriever()

        def format_document(docs: list[Document]) -> str:
            if not docs:
                return "无相关参考资料。"
            return "\n\n".join(
                f"文档片段：{doc.page_content}\n文档元数据: {doc.metadata}" for doc in docs
            )

        def format_for_retriever(value: dict) -> str:
            return value["input"]

        def format_for_prompt_template(value: dict) -> dict:
            return {
                "input": value["input"]["input"],
                "context": value["context"],
                "history": value["input"]["history"],
            }

        chain = (
            {
                "input": RunnablePassthrough(),
                "context": RunnableLambda(format_for_retriever) | retriever | format_document,
            }
            | RunnableLambda(format_for_prompt_template)
            | self.prompt_template
            | print_prompt
            | self.chat_model
            | StrOutputParser()
        )

        return RunnableWithMessageHistory(
            chain,
            get_history,
            input_message_key="input",
            history_messages_key="history",
        )

    def ask(self, question: str, config: RunnableConfig) -> str:
        try:
            return self.chain.invoke({"input": question}, config)
        except Exception as exc:
            raise wrap_external_error(exc, "执行 RAG 问答") from exc

    def stream_answer(self, question: str, config: RunnableConfig) -> Iterator[str]:
        try:
            for chunk in self.chain.stream({"input": question}, config):
                yield chunk
        except Exception as exc:
            raise wrap_external_error(exc, "执行 RAG 问答") from exc