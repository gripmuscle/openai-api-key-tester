import streamlit as st
import re
import aiohttp
import asyncio
import logging

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Function to extract keys from text using regex
def extract_keys(text):
    logging.info("Extracting API keys from the provided text.")
    
    # Regex patterns for various API keys
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
    logging.info(f"Extracted keys: {keys}")
    return keys

# Function to test OpenAI keys
async def test_key_async(session, api_key):
    url = "https://api.openai.com/v1/chat/completions"
    headers = {"Authorization": f"Bearer {api_key}"}
    data = {
        "model": "gpt-3.5-turbo",
        "messages": [{"role": "user", "content": "This is a test"}]
    }
    try:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                logging.info(f"API key {api_key} is valid.")
                return api_key, True
            else:
                logging.warning(f"API key {api_key} is invalid.")
                return api_key, False
    except Exception as e:
        logging.error(f"An error occurred while testing key {api_key}: {e}")
        return api_key, False

# Function to handle OpenAI key testing asynchronously
async def test_keys_async(keys):
    async with aiohttp.ClientSession() as session:
        tasks = [test_key_async(session, key) for key in keys]
        results = await asyncio.gather(*tasks)
        return results

# Streamlit UI
st.title("API Key Extractor and Tester")

# User input for text
input_text = st.text_area("Input Text", height=300, help="Paste the text from which to extract API keys.")

if st.button("Extract and Test Keys"):
    if not input_text:
        st.error("Input text is required.")
    else:
        with st.spinner('Extracting API keys...'):
            # Extract API keys from the provided text
            extracted_keys = extract_keys(input_text)
            
            if extracted_keys:
                st.success("Keys extracted successfully!")
                st.write("Found potential API keys:")
                
                with st.spinner('Testing API keys...'):
                    results = asyncio.run(test_keys_async(extracted_keys))
                    
                    valid_keys = []
                    invalid_keys = []
                    
                    for key, valid in results:
                        if valid:
                            valid_keys.append(key)
                            st.write(f"{key} - **Valid**")
                        else:
                            st.write(f"{key} - **Invalid**")
                            
                    if valid_keys:
                        st.subheader("Valid API Keys")
                        st.text_area("Copy all valid keys", "\n".join(valid_keys), height=200)
                    else:
                        st.write("No valid API keys found.")
                    
                    logging.info("Results displayed.")
            else:
                st.write("No potential keys found.")
                logging.info("No potential keys found in the provided text.")
