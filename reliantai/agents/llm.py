from langchain_google_genai import ChatGoogleGenerativeAI
import os

_gemini_pro = None
_gemini_flash = None


def get_gemini_pro():
    global _gemini_pro
    if _gemini_pro is None:
        _gemini_pro = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            temperature=0.5,
            max_output_tokens=4096,
            google_api_key=os.environ.get("GOOGLE_AI_API_KEY", ""),
        )
    return _gemini_pro


def get_gemini_flash():
    global _gemini_flash
    if _gemini_flash is None:
        _gemini_flash = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            temperature=0.3,
            max_output_tokens=2048,
            google_api_key=os.environ.get("GOOGLE_AI_API_KEY", ""),
        )
    return _gemini_flash
