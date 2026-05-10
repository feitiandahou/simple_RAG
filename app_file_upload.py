import streamlit as st

st.title("My File Upload Example")

st.write("Upload a file to see its contents:")

if "count" not in st.session_state:
    st.session_state.count = 0

if st.button("click me +1"):
    st.session_state.count += 1

st.write(f"Button clicked {st.session_state.count} times.")