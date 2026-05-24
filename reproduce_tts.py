from backend.voice_processor import text_to_speech
import os

text = """
باش تجدد لاكارط ناسيونال ديالك، ها شنو خاصك دير:

الوراق اللي خاصينك:

لاكارط ناسيونال القديمة ديالك.
2 تصاور جداد صغار ديال لاكارط.
لوفورميلير (الاستمارة) معمرا.
شهادة السكنى (هادي غير إيلا كنتي بدلتي لادريس فين ساكن).
فين غتمشي:

للمقاطعة أولا الكوميسارية اللي تابعة للبلاصة فين ساكن.
"""

print(f"Testing TTS with text: {text[:50]}...")
output_file = "test_output_darija.mp3"

try:
    result = text_to_speech(text, output_file)
    if result and os.path.exists(result):
        print(f"Success! Audio saved to {result}")
    else:
        print("Failed to generate audio.")
except Exception as e:
    print(f"An error occurred: {e}")
