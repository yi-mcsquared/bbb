import streamlit as st
import requests
from bs4 import BeautifulSoup
import difflib
import re
import json

def get_api_key():
    """Get the API key from Streamlit secrets or environment variable."""
    try:
        return st.secrets["CONGRESS_API_KEY"]
    except:
        st.error("""
        API key not found. Please add your congress.gov API key to Streamlit secrets:
        1. Go to https://share.streamlit.io/
        2. Select your app
        3. Click 'Manage app'
        4. Go to 'Secrets'
        5. Add the following:
        ```toml
        CONGRESS_API_KEY = "your-api-key-here"
        ```
        6. Click 'Save'
        7. Click 'Reboot app'
        """)
        return None

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

            # Get API key
            api_key = get_api_key()
            if not api_key:
                return None

            # Determine if it's a bill or amendment
            is_amendment = 'amendment' in url
            chamber = 'senate' if 'senate' in url else 'house'
            
            # Construct API URL with proper format
            if is_amendment:
                # For amendments, we need to get the text URL first
                api_url = f"https://api.congress.gov/v3/amendment/{congress}/{chamber}/{number}?api_key={api_key}"
                response = requests.get(api_url, headers={'Accept': 'application/json'})
                response.raise_for_status()
                data = response.json()
                
                # Get the text URL from the response
                if 'amendment' in data and 'textVersions' in data['amendment']:
                    latest_version = data['amendment']['textVersions'][0]
                    if 'formats' in latest_version:
                        for format_data in latest_version['formats']:
                            if format_data['type'] == 'Formatted Text':
                                # Fetch the actual text content
                                text_response = requests.get(format_data['url'], headers={'Accept': 'text/html'})
                                text_response.raise_for_status()
                                return text_response.text
            else:
                # For bills, get the latest text version
                api_url = f"https://api.congress.gov/v3/bill/{congress}/{chamber}/{number}/text?api_key={api_key}"
                response = requests.get(api_url, headers={'Accept': 'application/json'})
                response.raise_for_status()
                data = response.json()
                
                if 'textVersions' in data and len(data['textVersions']) > 0:
                    latest_version = data['textVersions'][0]
                    if 'formats' in latest_version:
                        for format_data in latest_version['formats']:
                            if format_data['type'] == 'Formatted Text':
                                # Fetch the actual text content
                                text_response = requests.get(format_data['url'], headers={'Accept': 'text/html'})
                                text_response.raise_for_status()
                                return text_response.text

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

def format_diff_line(line):
    """Format a diff line with appropriate styling."""
    if line.startswith('+'):
        return f'<span style="color: green; background-color: #e6ffe6;">{line}</span>'
    elif line.startswith('-'):
        return f'<span style="color: red; background-color: #ffe6e6;">{line}</span>'
    elif line.startswith('@'):
        return f'<span style="color: blue; font-weight: bold;">{line}</span>'
    return line

def compare_texts(original_text, amendment_text):
    """Compare two texts and return formatted differences."""
    if not original_text or not amendment_text:
        return "One or both texts are empty"
    
    # Split texts into sections
    original_sections = re.split(r'\n\s*\n', original_text)
    amendment_sections = re.split(r'\n\s*\n', amendment_text)
    
    # Create HTML for side-by-side comparison
    html_output = """
    <style>
        .comparison-container {
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }
        .text-column {
            flex: 1;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 5px;
            background-color: #f9f9f9;
        }
        .section-title {
            font-weight: bold;
            margin-bottom: 10px;
            color: #333;
        }
        .diff-line {
            margin: 2px 0;
            padding: 2px 5px;
            font-family: monospace;
            white-space: pre-wrap;
        }
    </style>
    """
    
    # Compare each section
    for i, (orig_section, amend_section) in enumerate(zip(original_sections, amendment_sections)):
        if orig_section.strip() and amend_section.strip():
            html_output += f'<div class="comparison-container">'
            
            # Original text column
            html_output += '<div class="text-column">'
            html_output += f'<div class="section-title">Original Text (Section {i+1})</div>'
            diff = difflib.unified_diff(
                orig_section.splitlines(),
                amend_section.splitlines(),
                lineterm=''
            )
            for line in diff:
                if line.startswith('-'):
                    html_output += f'<div class="diff-line">{format_diff_line(line)}</div>'
            html_output += '</div>'
            
            # Amendment text column
            html_output += '<div class="text-column">'
            html_output += f'<div class="section-title">Amendment Text (Section {i+1})</div>'
            diff = difflib.unified_diff(
                orig_section.splitlines(),
                amend_section.splitlines(),
                lineterm=''
            )
            for line in diff:
                if line.startswith('+'):
                    html_output += f'<div class="diff-line">{format_diff_line(line)}</div>'
            html_output += '</div>'
            
            html_output += '</div>'
    
    return html_output

def main():
    st.title("Legislative Amendment Comparison Tool")
    
    st.markdown("""
    This tool compares legislative amendments with their original bills.
    
    **Instructions:**
    1. Copy and paste the original bill text in the first text area
    2. Copy and paste the amendment text in the second text area
    3. Click 'Compare' to see the differences
    
    The comparison will show:
    - 🟢 Green: Added text in the amendment
    - 🔴 Red: Removed text from the original
    """)
    
    # Input fields for text
    original_text = st.text_area("Original Bill Text:", 
                                height=300,
                                placeholder="Paste the original bill text here...")
    
    amendment_text = st.text_area("Amendment Text:", 
                                 height=300,
                                 placeholder="Paste the amendment text here...")
    
    if st.button("Compare"):
        if original_text and amendment_text:
            with st.spinner("Comparing texts..."):
                # Compare texts
                differences = compare_texts(original_text, amendment_text)
                
                # Display results
                st.subheader("Comparison Results")
                st.markdown(differences, unsafe_allow_html=True)
        else:
            st.warning("Please provide both texts to compare.")

if __name__ == "__main__":
    main()
