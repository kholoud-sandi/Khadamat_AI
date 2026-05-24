try:
    from .rag_engine import initialize_rag_system, get_answer
    from .voice_processor import transcribe_audio, text_to_speech
except ImportError:
    # Use proper absolute imports based on where the file is located relative to execution
    import sys
    import os
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from rag_engine import initialize_rag_system, get_answer
    from voice_processor import transcribe_audio, text_to_speech