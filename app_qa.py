from logging import config

from dotenv import load_dotenv, find_dotenv
import config_data as config
from rag import RagService
load_dotenv(find_dotenv())
import streamlit as st
#标题
st.title("RAG问答系统")
st.divider()

if "message" not in st.session_state:
    st.session_state["message"] = [{"role": "assistant", "content": "你好！请问有什么可以帮助你的吗？"}]

if "rag" not in st.session_state:
    st.session_state["rag"] = RagService()

for message in st.session_state["message"]:
    st.chat_message(message["role"]).write(message["content"])

prompt = st.chat_input()

if prompt:
    st.chat_message("user").write(prompt)
    st.session_state["message"].append({"role":"user", "content": prompt})

    ai_res_list = []
    with st.spinner("AI思考中..."):
        res_stream = st.session_state["rag"].chain.stream({"input": prompt}, config.session_config)
        #yield

        def capture(generator, cache_list):
            for chunk in generator:
                cache_list.append(chunk)
                yield chunk
        
        st.chat_message("assistant").write_stream(capture(res_stream, ai_res_list))
    st.session_state["message"].append({"role":"assistant", "content": "".join(ai_res_list)})
