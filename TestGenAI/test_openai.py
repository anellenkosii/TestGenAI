"""Manual OpenAI connection check; this is not part of the pytest suite."""

import os


def main():
    try:
        from dotenv import load_dotenv
        from openai import OpenAI
    except ImportError as exc:
        raise SystemExit(
            "Missing dependency. Run: pip install -r requirements.txt"
        ) from exc

    load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY", "").strip()
    if not api_key or api_key == "your_openai_api_key_here":
        raise SystemExit("Set a real OPENAI_API_KEY in .env first.")

    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=os.getenv("OPENAI_MODEL", "gpt-4o"),
        messages=[{"role": "user", "content": "Reply with exactly: SUCCESS"}],
    )
    print(response.choices[0].message.content)


if __name__ == "__main__":
    main()
