import openai
import streamlit as st

def get_api_key():
    # Replace this with your actual method of retrieving the API key
    return st.secrets["OPENAI_API_KEY"]

def stream_openai_response(api_key, prompt):
    client = openai.OpenAI(api_key=api_key)

    # Create a completion with streaming enabled
    stream = client.chat.completions.create(
        model="gpt-3.5-turbo",  # You can specify the model you want to use
        messages=[{"role": "user", "content": prompt}],
        stream=True,
    )
    
    # Process the streaming response
    for chunk in stream:
        if chunk.get('choices') and chunk['choices'][0].get('delta'):
            content = chunk['choices'][0]['delta'].get('content', '')
            st.write(content, end="")

def main():
    st.title("OpenAI Chat Completion with Streaming")

    api_key = get_api_key()

    if api_key:
        st.write("API key received. Initializing connection...")
        
        # Input for the user to provide the prompt
        prompt = st.text_area("Enter your prompt:", "Say this is a test")
        
        if st.button("Submit"):
            stream_openai_response(api_key, prompt)

if __name__ == "__main__":
    main()
