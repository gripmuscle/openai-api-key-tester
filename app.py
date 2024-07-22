import streamlit as st
from openai import OpenAI

def get_api_key():
    return st.text_input("Enter your OpenAI API key:", type="password")

def stream_openai_response(api_key):
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Say this is a test"},
            ],
            stream=True,
        )
        
        st.write("Streaming response:")
        for chunk in response:
            content = chunk.choices[0].delta.content or ""
            st.write(content, end="")
    
    except Exception as e:
        st.error(f"An error occurred: {e}")

def main():
    st.title("OpenAI Chat Completion with Streaming")
    
    api_key = get_api_key()
    
    if api_key:
        st.write("API key received. Initializing connection...")
        stream_openai_response(api_key)

if __name__ == "__main__":
    main()
