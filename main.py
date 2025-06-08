import streamlit as st
import requests
from bs4 import BeautifulSoup
import difflib
import re
import json

def extract_congress_info(url):
    """Extract congress number and bill/amendment ID from URL."""
    # Example URL patterns:
    # https://www.congress.gov/bill/119th-congress/senate-bill/1582
    # https://www.congress.gov/amendment/119th-congress/senate-amendment/2295
    pattern = r'congress\.gov/(?:bill|amendment)/(\d+)th-congress/(?:senate|house)-(?:bill|amendment)/(\d+)'
    match = re.search(pattern, url)
    if match:
        congress = match.group(1)
        number = match.group(2)
        return congress, number
    return None, None

def fetch_text_from_url(url):
    """Fetch and extract text content from a URL."""
    try:
        if 'congress.gov' in url:
            congress, number = extract_congress_info(url)
            if not congress or not number:
                st.error("Invalid congress.gov URL format")
                return None

            # Determine if it's a bill or amendment
            is_amendment = 'amendment' in url
            chamber = 'senate' if 'senate' in url else 'house'
            
            # Construct API URL
            if is_amendment:
                api_url = f"https://api.congress.gov/v3/amendment/{congress}/{chamber}/{number}?api_key=demo"
            else:
                api_url = f"https://api.congress.gov/v3/bill/{congress}/{chamber}/{number}/text?api_key=demo"

            headers = {
                'Accept': 'application/json',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }

            response = requests.get(api_url, headers=headers)
            response.raise_for_status()
            
            data = response.json()
            
            # Extract text based on response structure
            if is_amendment:
                # For amendments, we need to handle the specific structure
                if 'amendment' in data and 'text' in data['amendment']:
                    return data['amendment']['text']
            else:
                # For bills, we need to handle the specific structure
                if 'textVersions' in data and len(data['textVersions']) > 0:
                    latest_version = data['textVersions'][0]
                    if 'formats' in latest_version:
                        for format_data in latest_version['formats']:
                            if format_data['type'] == 'Formatted Text':
                                return format_data['url']

            st.warning("Could not find text content in the API response")
            return None
            
        else:
            # For other websites, use the original scraping approach
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            return soup.get_text()
            
    except requests.exceptions.HTTPError as e:
        st.error(f"HTTP Error: {str(e)}")
        return None
    except requests.exceptions.RequestException as e:
        st.error(f"Error fetching content: {str(e)}")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def compare_texts(original_text, amendment_text):
    """Compare two texts and return the differences."""
    if not original_text or not amendment_text:
        return "One or both texts are empty"
        
    # Basic text comparison using difflib
    diff = difflib.unified_diff(
        original_text.splitlines(),
        amendment_text.splitlines(),
        lineterm=''
    )
    return '\n'.join(diff)

def main():
    st.title("Legislative Amendment Comparison Tool")
    
    st.markdown("""
    This tool compares legislative amendments with their original bills.
    
    **Note:** Currently using the demo API key. For production use, you'll need to:
    1. Register for a congress.gov API key at https://api.congress.gov/sign-up/
    2. Replace 'demo' in the code with your API key
    """)
    
    # Input fields for URLs
    amendment_url = st.text_input("Enter the amendment URL:", 
                                 placeholder="https://www.congress.gov/amendment/...")
    bill_url = st.text_input("Enter the original bill URL:", 
                            placeholder="https://www.congress.gov/bill/...")
    
    if st.button("Compare"):
        if amendment_url and bill_url:
            with st.spinner("Fetching and comparing texts..."):
                # Fetch texts
                amendment_text = fetch_text_from_url(amendment_url)
                bill_text = fetch_text_from_url(bill_url)
                
                if amendment_text and bill_text:
                    # Compare texts
                    differences = compare_texts(bill_text, amendment_text)
                    
                    # Display results
                    st.subheader("Comparison Results")
                    st.text_area("Differences:", differences, height=400)
                else:
                    st.error("Could not fetch one or both texts. Please check the URLs.")
        else:
            st.warning("Please provide both URLs to compare.")

if __name__ == "__main__":
    main()
