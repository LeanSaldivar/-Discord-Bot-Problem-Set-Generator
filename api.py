import os

from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()

client = genai.Client(
    api_key=os.environ.get("GEMINI_API_KEY"),
)

system_instruction="""
You are an advanced STEM exam problem set generator.

Your role:
- Given any topic, subject, or uploaded content (text, image, or PDF),
  generate a comprehensive problem set that covers all major scenarios and subtopics within the given concept.

Formatting and behavior rules:
1. **Always generate both**:
     • A clearly structured **Problem Set** section
     • A complete **Answer Sheet** section at the bottom.
2. Use **Markdown formatting** with numbered problems.
3. Use **LaTeX math formatting** with `$$ ... $$` for all mathematical equations.
4. Ensure at least **5–10 problems**, increasing in difficulty from easy → moderate → hard.
5. When relevant, include applications, real-world contexts, or word problems.
6. For the **Answer Sheet**, include only concise final answers or brief explanations — no repetition of full questions.
7. Never ask clarifying questions — infer what's best from the topic or content.
8. Always start output with:
   **📘 Problem Set: [Topic Name]**
9. Ensure all output is **Discord-friendly**, readable, and visually clean.
"""

# Store chat sessions per user/channel
chat_sessions = {}

def get_or_create_session(session_id):
    """Get existing chat session or create a new one."""
    if session_id not in chat_sessions:
        chat_sessions[session_id] = client.chats.create(
            model="gemini-2.5-flash",
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.5,
            )
        )
    return chat_sessions[session_id]

def send_message(session_id, text):
    """Send a message in a multi-turn conversation."""
    session = get_or_create_session(session_id)
    response = session.send_message(text)
    return response

def send_message_with_file(session_id, text, file_bytes, mime_type):
    """Send a message with a file in a multi-turn conversation."""
    session = get_or_create_session(session_id)
    response = session.send_message([
        types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
        text
    ])
    return response

def clear_session(session_id):
    """Clear a user's conversation history."""
    if session_id in chat_sessions:
        del chat_sessions[session_id]
        return True
    return False

# Legacy functions for backwards compatibility (single-turn, no history)
def generate_with_file(text, file_bytes, mime_type):
    """Single-turn generation with file (no conversation history)."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.5,
            thinking_config=types.ThinkingConfig()
        ),
        contents=[
            types.Part.from_bytes(data=file_bytes, mime_type=mime_type),
            text
        ],
    )

    for chunk in response:
        print(chunk.text, end="")

    return response

def generate(text):
    """Single-turn generation (no conversation history)."""
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        config=types.GenerateContentConfig(
            system_instruction=system_instruction,
            temperature=0.5,
            thinking_config=types.ThinkingConfig()
        ),
        contents=[text],
    )
    return response