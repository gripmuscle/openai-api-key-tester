import streamlit as st
import re
import aiohttp
import asyncio

# Function to extract keys from text using regex
def extract_keys(text):
    # Regex patterns for various API keys
    patterns = [
        r'(?i)(?:api[_ ]?key|access[_ ]?key|secret[_ ]?key|access[_ ]?token|api[_ ]?key|apikey|api[_ ]?secret|app[_ ]?secret|auth[_ ]?token|authsecret)[\s=:]*([\w-]{32,})',
        r'(?i)sk-[a-zA-Z0-9]{48}',
        r'(?i)key-[a-zA-Z0-9]{32,}',
        r'(?i)api[_ ]?secret[\s=:]*([\w-]{32,})',
        r'(?i)(?:app[_ ]?key|application[_ ]?key|app[_ ]?id|application[_ ]?id)[\s=:]*([\w-]{32,})'
    ]
    keys = set()
    for pattern in patterns:
        keys.update(re.findall(pattern, text))
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
                result = await response.json()
                return api_key, result
            else:
                return api_key, None
    except Exception as e:
        st.error(f"An error occurred while testing key: {e}")
        return api_key, None

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
        # Extract API keys from the provided text
        extracted_keys = extract_keys(input_text)
        
        if extracted_keys:
            st.write("Found potential API keys:")
            st.write(extracted_keys)
            
            with st.spinner("Testing OpenAI keys..."):
                # Test extracted keys asynchronously
                results = asyncio.run(test_keys_async(extracted_keys))
                for key, result in results:
                    if result:
                        st.write(f"API key {key} is valid.")
                    else:
                        st.write(f"API key {key} is invalid.")
        else:
            st.write("No potential keys found.")
