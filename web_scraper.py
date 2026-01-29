import trafilatura
from urllib.parse import urljoin, urlparse


def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    The results is not directly readable, better to be summarized by LLM before consume
    by the user.
    """
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return ""
    text = trafilatura.extract(downloaded)
    return text or ""


def get_firm_website_content(url: str) -> str:
    """
    Fetch multiple pages from a firm's website to get comprehensive info.
    Tries main page plus common pages like About, Contact, etc.
    """
    all_content = []
    
    main_content = get_website_text_content(url)
    if main_content:
        all_content.append(f"=== MAIN PAGE ===\n{main_content}")
    
    common_pages = [
        'contact', 'contact-us', 'about', 'about-us', 
        'company', 'who-we-are', 'our-firm', 'locations'
    ]
    
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    for page in common_pages:
        page_url = urljoin(base_url, f"/{page}")
        try:
            page_content = get_website_text_content(page_url)
            if page_content and len(page_content) > 100:
                all_content.append(f"=== {page.upper()} PAGE ===\n{page_content}")
        except:
            pass
        
        if len(all_content) >= 4:
            break
    
    return "\n\n".join(all_content)
