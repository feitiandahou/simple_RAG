import time

import streamlit as st

from rag_project.bootstrap import build_knowledge_base_service, initialize_runtime
from rag_project.errors import RagProjectError


def main() -> None:
    initialize_runtime()
    st.title("知识库更新服务")
    operator = st.text_input("操作人", value="user_001").strip() or "user_001"
    tenant_id = st.text_input("Tenant ID", value="tenant_demo").strip() or "tenant_demo"
    owner = st.text_input("Owner", value="system").strip() or "system"
    permission_tag = st.text_input("Permission Tag", value="internal").strip() or "internal"
    version = st.text_input("Version", value="v1").strip() or "v1"

    uploader_file = st.file_uploader(
        "请上传 txt 文件",
        type=["txt"],
        accept_multiple_files=False,
    )

    if "service" not in st.session_state:
        try:
            st.session_state["service"] = build_knowledge_base_service()
        except RagProjectError as exc:
            st.error(str(exc))
            return

    if uploader_file is not None:
        st.subheader(f"文件名：{uploader_file.name}")
        st.subheader(f"文件类型：{uploader_file.type}")
        st.subheader(f"文件大小：{uploader_file.size / 1024:.2f} KB")

        raw = uploader_file.getvalue()
        if not raw:
            st.warning("文件内容为空，未写入知识库。")
            return

        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError:
            st.error("当前仅支持 UTF-8 编码文本，请转换编码后重试。")
            return

        with st.spinner("载入知识库中..."):
            time.sleep(1)
            try:
                result = st.session_state["service"].upload_by_str(
                    text,
                    uploader_file.name,
                    operator=operator,
                    tenant_id=tenant_id,
                    owner=owner,
                    permission_tag=permission_tag,
                    version=version,
                )
            except RagProjectError as exc:
                st.error(str(exc))
            else:
                st.write(result)


if __name__ == "__main__":
    main()