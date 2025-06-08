import streamlit as st
import requests
from bs4 import BeautifulSoup
import difflib
import re

def fetch_text_from_url(url):
    """Fetch and extract text content from a URL."""
    try:
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
        
        # For congress.gov, we need to find the specific div containing the bill/amendment text
        if 'congress.gov' in url:
            if 'amendment' in url:
                # Look for amendment text
                text_div = soup.find('div', {'class': 'amendment-text'})
            else:
                # Look for bill text
                text_div = soup.find('div', {'class': 'bill-text'})
            
            if text_div:
                # Clean up the text
                text_content = text_div.get_text(separator='\n', strip=True)
                # Remove extra whitespace
                text_content = re.sub(r'\n\s*\n', '\n\n', text_content)
                return text_content
            else:
                st.warning("Could not find the specific text content on the page. The page structure might have changed.")
                return None
        else:
            # For other websites, return all text
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
    # Basic text comparison using difflib
    # We'll need to enhance this to better handle legislative text formatting
    diff = difflib.unified_diff(
        original_text.splitlines(),
        amendment_text.splitlines(),
        lineterm=''
    )
    return '\n'.join(diff)

def main():
    st.title("Legislative Amendment Comparison Tool")
    
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
