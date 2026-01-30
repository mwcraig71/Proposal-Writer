import trafilatura
import requests
import re
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup


def get_website_text_content(url: str) -> str:
    """
    This function takes a url and returns the main text content of the website.
    The text content is extracted using trafilatura and easier to understand.
    """
    downloaded = trafilatura.fetch_url(url)
    if not downloaded:
        return ""
    text = trafilatura.extract(downloaded)
    return text or ""


def extract_contact_from_html(html: str) -> str:
    """Extract contact information directly from HTML using patterns."""
    soup = BeautifulSoup(html, 'html.parser')
    
    for script in soup(["script", "style", "noscript"]):
        script.decompose()
    
    text = soup.get_text(separator=' ', strip=True)
    
    phones = re.findall(r'[\(]?\d{3}[\)\-\.\s]?\d{3}[\-\.\s]?\d{4}', text)
    emails = re.findall(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}', text)
    
    contact_info = []
    if phones:
        contact_info.append(f"Phone numbers found: {', '.join(set(phones[:5]))}")
    if emails:
        contact_info.append(f"Email addresses found: {', '.join(set(emails[:5]))}")
    
    return '\n'.join(contact_info)


def fetch_raw_html(url: str) -> str:
    """Fetch raw HTML content from a URL."""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except:
        return ""


def get_firm_website_content(url: str) -> str:
    """
    Fetch multiple pages from a firm's website to get comprehensive info.
    Uses both trafilatura and direct HTML parsing for better coverage.
    """
    all_content = []
    
    main_html = fetch_raw_html(url)
    if main_html:
        contact_from_html = extract_contact_from_html(main_html)
        if contact_from_html:
            all_content.append(f"=== CONTACT INFO EXTRACTED ===\n{contact_from_html}")
    
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
            page_html = fetch_raw_html(page_url)
            if page_html and len(page_html) > 500:
                contact_info = extract_contact_from_html(page_html)
                if contact_info:
                    all_content.append(f"=== {page.upper()} PAGE CONTACT ===\n{contact_info}")
                
                page_content = get_website_text_content(page_url)
                if page_content and len(page_content) > 100:
                    all_content.append(f"=== {page.upper()} PAGE ===\n{page_content}")
        except:
            pass
        
        if len(all_content) >= 6:
            break
    
    return "\n\n".join(all_content)


def scrape_portfolio_projects(url: str, max_pages: int = 5) -> dict:
    """
    Scrape a portfolio/projects page to extract project information.
    Handles pagination and follows individual project links for more details.
    Returns dict with 'content' (text for AI parsing) and 'project_links' (found URLs).
    """
    all_content = []
    project_links = []
    pages_scraped = 0
    current_url = url
    
    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"
    
    while current_url and pages_scraped < max_pages:
        html = fetch_raw_html(current_url)
        if not html:
            break
            
        soup = BeautifulSoup(html, 'html.parser')
        
        for script in soup(["script", "style", "noscript"]):
            script.decompose()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            if '/portfolio/' in href or '/project/' in href or '/projects/' in href:
                full_url = urljoin(base_url, href)
                if full_url not in project_links and full_url != current_url:
                    if not any(x in full_url for x in ['/page/', 'portfolio_category']):
                        project_links.append(full_url)
        
        text_content = get_website_text_content(current_url)
        if text_content:
            all_content.append(f"=== PAGE {pages_scraped + 1} ===\n{text_content}")
        
        pages_scraped += 1
        
        next_url = None
        for link in soup.find_all('a', href=True):
            href = link['href']
            link_text = link.get_text(strip=True).lower()
            if 'next' in link_text or f'/page/{pages_scraped + 1}' in href:
                next_url = urljoin(base_url, href)
                break
        
        if next_url and next_url != current_url:
            current_url = next_url
        else:
            break
    
    project_details = []
    for project_url in project_links[:15]:
        try:
            project_content = get_website_text_content(project_url)
            if project_content and len(project_content) > 100:
                project_details.append(f"=== PROJECT: {project_url} ===\n{project_content}")
        except:
            pass
    
    if project_details:
        all_content.extend(project_details)
    
    return {
        'content': "\n\n".join(all_content),
        'project_links': project_links,
        'pages_scraped': pages_scraped
    }
