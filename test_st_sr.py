import streamlit as st
import sys
import os

st.write("Python Executable:", sys.executable)
st.write("Python Version:", sys.version)
st.write("CWD:", os.getcwd())
st.write("Sys Path:", sys.path)

try:
    import speech_recognition as sr
    st.success(f"Imported SpeechRecognition: {sr.__version__}")
    st.write("File:", sr.__file__)
except Exception as e:
    st.error(f"Failed to import: {e}")
    import traceback
    st.text(traceback.format_exc())
