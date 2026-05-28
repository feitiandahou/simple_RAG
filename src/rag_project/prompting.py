from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from rag_project.config import settings


PROMPT_REGISTRY = {
    "v1": [
        ("system", "以我提供的已知参考资料为主，简洁和专业地回答用户问题。参考资料:{context}。"),
        ("system", "并且我提供用户的对话历史记录，如下："),
        MessagesPlaceholder("history"),
        ("user", "请回答用户提问：{input}"),
    ],
    "v2_enterprise_demo": [
        (
            "system",
            "你是企业知识问答助手。必须严格基于参考资料回答，不允许臆测。"
            "当证据不足时，请明确回复: '根据当前检索结果，暂无充分依据回答该问题。'",
        ),
        ("system", "参考资料如下:{context}"),
        ("system", "用户历史对话如下:"),
        MessagesPlaceholder("history"),
        ("user", "用户问题: {input}"),
    ],
}


def build_prompt_template() -> ChatPromptTemplate:
    version = settings.prompt_version
    messages = PROMPT_REGISTRY.get(version, PROMPT_REGISTRY["v2_enterprise_demo"])
    return ChatPromptTemplate.from_messages(messages)
