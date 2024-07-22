import streamlit as st
import openai

# Function to get OpenAI API key from user input
def get_api_key():
    api_key = st.text_input("Enter your OpenAI API Key:", type="password")
    return api_key

# Function to initialize OpenAI connection
def initialize_openai(api_key):
    openai.api_key = api_key

# Function to make a request to OpenAI API and stream the response
def stream_openai_response(user_message):
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": user_message}],
        stream=True
    )
    
    # Stream response
    for chunk in response:
        content = chunk.choices[0].delta.get("content", "")
        if content:
            st.write(content, end="")

# Streamlit App
def main():
    st.title("OpenAI Chat Completion with Streaming")
    
    api_key = get_api_key()
    
    if api_key:
        st.write("API key received. Initializing connection...")
        initialize_openai(api_key)
        st.write("Connection initialized.")
        
        user_message = st.text_input("Enter your message for OpenAI:", value="Say this is a test")
        
        if st.button("Send"):
            st.write("Streaming response...")
            stream_openai_response(user_message)

if __name__ == "__main__":
    main()
