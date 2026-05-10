from groq import Groq
from app.core.config import settings

client = Groq(api_key=settings.groq_api_key)


def generate_response(prompt: str) -> str:
    completion = client.chat.completions.create(
        model="llama-3.3-70b-versatile",  
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt},
        ],
        temperature=0.3,
    )

    return completion.choices[0].message.content