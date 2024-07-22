import openai
import streamlit as st

def test_api_key(api_key):
    try:
        openai.api_key = api_key
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say this is a test"}
            ]
        )
        return "Valid", response.choices[0].message['content']
    except openai.error.AuthenticationError:
        return "Invalid", "Invalid API key."
    except openai.error.APIConnectionError:
        return "Connection Error", "Failed to connect to the API."
    except openai.error.APIError as e:
        return "API Error", f"API error: {e}"
    except Exception as e:
        return "Unexpected Error", f"An unexpected error occurred: {e}"

def process_keys(api_keys_input):
    api_keys = [key.strip() for key in api_keys_input.split(',')]
    results = []
    for key in api_keys:
        status, message = test_api_key(key)
        results.append((key, status, message))
    return results

# Streamlit app layout
st.title("OpenAI API Key Tester")

api_keys_input = st.text_area("Enter API keys (comma separated for multiple keys):")

if st.button("Test API Keys"):
    results = process_keys(api_keys_input)
    for key, status, message in results:
        st.write(f"API Key: {key}")
        st.write(f"Status: {status}")
        st.write(f"Message: {message}")
        st.write("---")
