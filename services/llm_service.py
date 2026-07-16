import requests

from app.config import LLM_API_KEY, LLM_API_URL


def ask_llm(prompt: str) -> str:
    if not LLM_API_KEY:
        raise RuntimeError("缺少 LLM_API_KEY，请检查 .env 文件")

    if not LLM_API_URL:
        raise RuntimeError("缺少 LLM_API_URL，请检查 .env 文件")

    headers = {
        "x-goog-api-key": LLM_API_KEY,
        "Content-Type": "application/json",
    }

    body = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {
                        "text": prompt
                    }
                ],
            }
        ]
    }

    response = requests.post(
        LLM_API_URL,
        headers=headers,
        json=body,
        timeout=120,
    )

    response.raise_for_status()
    data = response.json()

    try:
        return data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError):
        return str(data)