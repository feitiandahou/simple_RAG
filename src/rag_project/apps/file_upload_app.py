import time

import streamlit as st

from rag_project.errors import RagProjectError
from rag_project.services.knowledge_base import KnowledgeBaseService


def main() -> None:
    st.title("知识库更新服务")

    uploader_file = st.file_uploader(
        "请上传 txt 文件",
        type=["txt"],
        accept_multiple_files=False,
    )

    if "service" not in st.session_state:
        try:
            st.session_state["service"] = KnowledgeBaseService()
        except RagProjectError as exc:
            st.error(str(exc))
            return

    if uploader_file is not None:
        st.subheader(f"文件名：{uploader_file.name}")
        st.subheader(f"文件类型：{uploader_file.type}")
        st.subheader(f"文件大小：{uploader_file.size / 1024:.2f} KB")

        text = uploader_file.getvalue().decode("utf-8")
        with st.spinner("载入知识库中..."):
            time.sleep(1)
            try:
                result = st.session_state["service"].upload_by_str(text, uploader_file.name)
            except RagProjectError as exc:
                st.error(str(exc))
            else:
                st.write(result)


if __name__ == "__main__":
    main()