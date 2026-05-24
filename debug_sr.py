import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version}")

try:
    import speech_recognition as sr
    print(f"SpeechRecognition imported successfully. Version: {sr.__version__}")
    print(f"File: {sr.__file__}")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Other Error during import: {e}")
