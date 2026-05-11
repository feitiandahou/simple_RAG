from dotenv import find_dotenv, load_dotenv
import streamlit as st

from rag_project.config import settings
from rag_project.errors import RagProjectError
from rag_project.services.rag_service import RagService

load_dotenv(find_dotenv())


def main() -> None:
    st.title("RAG 问答系统")
    st.divider()

    if "message" not in st.session_state:
        st.session_state["message"] = [
            {"role": "assistant", "content": "你好！请问有什么可以帮助你的吗？"}
        ]

    if "rag" not in st.session_state:
        try:
            st.session_state["rag"] = RagService()
        except RagProjectError as exc:
            st.error(str(exc))
            return

    for message in st.session_state["message"]:
        st.chat_message(message["role"]).write(message["content"])

    prompt = st.chat_input()
    if not prompt:
        return

    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role": "user", "content": prompt})

    ai_res_list: list[str] = []
    with st.spinner("AI 思考中..."):
        try:
            def capture(generator, cache_list):
                for chunk in generator:
                    cache_list.append(chunk)
                    yield chunk

            res_stream = st.session_state["rag"].stream_answer(prompt, settings.session_config)
            st.chat_message("assistant").write_stream(capture(res_stream, ai_res_list))
        except RagProjectError as exc:
            st.error(str(exc))
            return

    st.session_state["message"].append({"role": "assistant", "content": "".join(ai_res_list)})


if __name__ == "__main__":
    main()