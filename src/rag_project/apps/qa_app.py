from dotenv import find_dotenv, load_dotenv
import streamlit as st

from rag_project.bootstrap import build_rag_service, initialize_runtime
from rag_project.config import settings
from rag_project.errors import RagProjectError
from rag_project.stores.file_history import clear_session_history

load_dotenv(find_dotenv())


def main() -> None:
    initialize_runtime()
    st.title("RAG 问答系统")
    st.divider()

    with st.sidebar:
        st.subheader("会话设置")
        session_id = st.text_input("Session ID", value=settings.default_session_id).strip()
        tenant_id = st.text_input("Tenant ID", value="tenant_demo").strip() or "tenant_demo"
        permission_tag = st.text_input("Permission Tag", value="internal").strip() or "internal"
        if not session_id:
            session_id = settings.default_session_id
        if st.button("清空当前会话历史", use_container_width=True):
            clear_session_history(session_id)
            st.session_state.setdefault("message_store", {})[session_id] = [
                {"role": "assistant", "content": "会话已清空。请继续提问。"}
            ]
            st.success(f"会话 {session_id} 已清空")

    message_store = st.session_state.setdefault("message_store", {})
    if session_id not in message_store:
        message_store[session_id] = [
            {"role": "assistant", "content": "你好！请问有什么可以帮助你的吗？"}
        ]
    messages = message_store[session_id]

    if "rag" not in st.session_state:
        try:
            st.session_state["rag"] = build_rag_service()
        except RagProjectError as exc:
            st.error(str(exc))
            return

    for message in messages:
        st.chat_message(message["role"]).write(message["content"])

    prompt = st.chat_input()
    if not prompt:
        return

    st.chat_message("user").write(prompt)
    messages.append({"role": "user", "content": prompt})

    ai_res_list: list[str] = []
    with st.spinner("AI 思考中..."):
        try:
            def capture(generator, cache_list):
                for chunk in generator:
                    cache_list.append(chunk)
                    yield chunk

            res_stream = st.session_state["rag"].stream_answer(
                prompt,
                settings.session_config_for(session_id),
                tenant_id=tenant_id,
                permission_tag=permission_tag,
            )
            st.chat_message("assistant").write_stream(capture(res_stream, ai_res_list))
        except RagProjectError as exc:
            st.error(str(exc))
            return

    messages.append({"role": "assistant", "content": "".join(ai_res_list)})


if __name__ == "__main__":
    main()