import streamlit as st
import re
from openai import OpenAI
from requests.exceptions import HTTPError

# Function to extract API keys from text using regex
def extract_keys(text):
    patterns = [
        r'(?i)api[_ ]?key[\s=:]*([\w-]{32,})',
        r'(?i)access[_ ]?key[\s=:]*([\w-]{32,})',
        r'(?i)secret[_ ]?key[\s=:]*([\w-]{32,})',
        r'(?i)access[_ ]?token[\s=:]*([\w-]{32,})',
        r'(?i)apikey[\s=:]*([\w-]{32,})',
        r'(?i)api[_ ]?secret[\s=:]*([\w-]{32,})',
        r'(?i)app[_ ]?secret[\s=:]*([\w-]{32,})',
        r'(?i)auth[_ ]?token[\s=:]*([\w-]{32,})',
        r'(?i)authsecret[\s=:]*([\w-]{32,})',
        r'sk-[a-zA-Z0-9]{48}',  # Adjusted regex pattern for sk-<key>
        r'key-[a-zA-Z0-9]{32,}'
    ]
    keys = set()
    for pattern in patterns:
        keys.update(re.findall(pattern, text))
    return keys

# Function to test a single API key
def test_api_key(api_key):
    client = OpenAI(api_key=api_key)
    
    try:
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": "Say this is a test"},
            ]
        )
        if response:
            return True
    except HTTPError as http_err:
        st.error(f"HTTP error occurred: {http_err}")
    except Exception as err:
        st.error(f"An error occurred: {err}")
    return False

# Function to handle key testing
def test_keys(api_keys):
    results = {}
    for key in api_keys:
        st.write(f"Testing key: {key}")
        if test_api_key(key):
            results[key] = "Valid"
            st.write(f"{key} - **Valid**")
        else:
            results[key] = "Invalid"
            st.write(f"{key} - **Invalid**")
    return results

def main():
    st.title("API Key Extractor and Tester")
    
    # User input for text
    input_text = st.text_area("Enter the text containing API keys:", height=300)
    
    if st.button("Extract and Test Keys"):
        if not input_text.strip():
            st.error("Input text is required.")
        else:
            # Extract API keys from the provided text
            extracted_keys = extract_keys(input_text)
            
            if extracted_keys:
                st.write("Found potential API keys:")
                for key in extracted_keys:
                    st.write(key)
                
                st.write("Testing API keys...")
                results = test_keys(extracted_keys)
                
                if results:
                    st.subheader("Testing complete. Check results above.")
                else:
                    st.write("No valid API keys found.")
            else:
                st.write("No potential keys found.")
                st.info("No API keys were found in the provided text.")

if __name__ == "__main__":
    main()
