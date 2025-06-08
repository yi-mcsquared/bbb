import streamlit as st
import requests
from bs4 import BeautifulSoup
import difflib
import re

def fetch_text_from_url(url):
    """Fetch and extract text content from a URL."""
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # This is a basic extraction - we'll need to customize this based on the specific website structure
        # For congress.gov, we'll need to identify the specific divs/classes containing the bill text
        text_content = soup.get_text()
        return text_content
    except Exception as e:
        st.error(f"Error fetching content: {str(e)}")
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
