from dotenv import load_dotenv
from openai import OpenAI, ChatCompletion
import os

def submit_test(client: OpenAI) -> ChatCompletion:
    chat_completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Say this is a test",
            }
        ],
        model="gpt-3.5-turbo",
    )
    return chat_completion

def test_openai_usage():
    OPENAI_API_KEY=os.environ.get("OPENAI_API_KEY")
    client = OpenAI()
    chat_completion = submit_test(client)
    return chat_completion

def main():
    load_dotenv()
    chat_completion = test_openai_usage()
    print(chat_completion.choices[0].message.content)

if __name__ == "__main__":
    main()
