import streamlit as st
import dashscope
from dashscope import Generation
from dotenv import load_dotenv
import os

# 加载环境变量
load_dotenv()

# 页面配置
st.set_page_config(page_title="通义千问助手", page_icon="🤖")
st.title("通义千问助手")


dashscope.api_key = os.getenv("DASHSCOPE_API_KEY")

if not dashscope.api_key:
    st.error("请在环境变量中设置 DASHSCOPE_API_KEY")

if "message" not in st.session_state:
    st.session_state.message = []

if prompt := st.chat_input("请输入你的问题..."):
    with st.chat_message("user"):
        st.markdown(prompt)
    st.session_state.message.append({"role": "user", "content": prompt})

    with st.chat_message("assistant"):
        response = Generation.call(
            model='qwen-turbo',
            messages=st.session_state.message,
            result_format='message',
            stream=True
        )

        full_response = ""
        placeholder = st.empty()

        for chunk in response:
            if chunk.status_code == 200:
                content = chunk.output.choices[0].message.content

                if isinstance(content, str):
                    content_text = content
                elif isinstance(content, list):
                    content_text = "".join(
                        item.get("text", str(item)) if isinstance(item, dict) else str(item)
                        for item in content
                    )
                else:
                    content_text = str(content)

                full_response += content_text
                placeholder.markdown(full_response + "▌") #显示打字机效果
            else:
                st.error(f"请求失败: {chunk.message}")
                st.stop()
        placeholder.markdown(full_response) #去掉光标
        st.session_state.message.append({"role": "assistant", "content": full_response})