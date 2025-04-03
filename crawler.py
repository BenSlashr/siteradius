import requests
import asyncio
import aiohttp
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urljoin
import re
from tqdm import tqdm
import logging
import time
from concurrent.futures import ThreadPoolExecutor

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

class WebCrawler:
    def __init__(self, max_pages=100, same_domain_only=True, delay=0.1, max_workers=10):
        self.visited_urls = set()
        self.urls_to_visit = []
        self.pages_content = {}
        self.max_pages = max_pages
        self.same_domain_only = same_domain_only
        self.delay = delay  # Add delay between requests to be respectful
        self.max_workers = max_workers  # Maximum number of concurrent workers
        
    def is_valid_url(self, url, base_domain):
        """Check if URL is valid and belongs to the same domain if required."""
        parsed = urlparse(url)
        
        # Check if URL is absolute and has http/https scheme
        if not parsed.netloc or not parsed.scheme or parsed.scheme not in ['http', 'https']:
            return False
            
        # Check if URL belongs to the same domain if required
        if self.same_domain_only and parsed.netloc != base_domain:
            return False
            
        # Avoid crawling common non-HTML resources
        if re.search(r'\.(jpg|jpeg|png|gif|pdf|doc|zip|mp4|mp3|css|js)$', parsed.path, re.IGNORECASE):
            return False
            
        return True
    
    def extract_text_from_html(self, html_content):
        """Extract meaningful text content from HTML."""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script_or_style in soup(['script', 'style', 'header', 'footer', 'nav']):
            script_or_style.decompose()
            
        # Get text and clean it
        text = soup.get_text(separator=' ', strip=True)
        text = re.sub(r'\s+', ' ', text)  # Replace multiple spaces with single space
        
        return text
    
    def extract_links_from_html(self, html_content, base_url, base_domain):
        """Extract valid links from HTML content."""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for a_tag in soup.find_all('a', href=True):
            href = a_tag['href']
            full_url = urljoin(base_url, href)
            
            if self.is_valid_url(full_url, base_domain):
                links.append(full_url)
                
        return links
    
    async def fetch_url(self, session, url):
        """Fetch a URL asynchronously."""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                    html_content = await response.text()
                    return url, html_content
        except Exception as e:
            logging.warning(f"Error fetching {url}: {e}")
        return url, None
    
    async def process_batch(self, urls_batch, base_domain):
        """Process a batch of URLs asynchronously."""
        async with aiohttp.ClientSession() as session:
            tasks = []
            for url in urls_batch:
                if url not in self.visited_urls and len(self.pages_content) < self.max_pages:
                    tasks.append(self.fetch_url(session, url))
                    self.visited_urls.add(url)
                    # Small delay to be respectful
                    await asyncio.sleep(self.delay)
            
            results = await asyncio.gather(*tasks)
            
            new_links = []
            for url, html_content in results:
                if html_content:
                    text_content = self.extract_text_from_html(html_content)
                    
                    # Only store pages with meaningful content
                    if len(text_content) > 100:
                        self.pages_content[url] = text_content
                        
                        # Extract new links to visit
                        links = self.extract_links_from_html(html_content, url, base_domain)
                        for link in links:
                            if link not in self.visited_urls and link not in self.urls_to_visit and link not in new_links:
                                new_links.append(link)
            
            return new_links
    
    def crawl(self, start_url):
        """Crawl the website starting from the given URL."""
        parsed_start_url = urlparse(start_url)
        base_domain = parsed_start_url.netloc
        
        self.urls_to_visit = [start_url]
        
        with tqdm(total=self.max_pages, desc="Crawling") as pbar:
            while self.urls_to_visit and len(self.pages_content) < self.max_pages:
                # Take a batch of URLs to process
                batch_size = min(self.max_workers, len(self.urls_to_visit))
                urls_batch = self.urls_to_visit[:batch_size]
                self.urls_to_visit = self.urls_to_visit[batch_size:]
                
                # Process the batch asynchronously
                new_links = asyncio.run(self.process_batch(urls_batch, base_domain))
                self.urls_to_visit.extend(new_links)
                
                # Update progress bar
                current_pages = len(self.pages_content)
                pbar.update(current_pages - pbar.n)
                
        logging.info(f"Crawling completed. Visited {len(self.visited_urls)} URLs, stored {len(self.pages_content)} pages.")
        return self.pages_content
    
    def crawl_parallel(self, start_url):
        """Crawl the website using thread pool for parallel processing."""
        parsed_start_url = urlparse(start_url)
        base_domain = parsed_start_url.netloc
        
        self.urls_to_visit = [start_url]
        
        def process_url(url):
            if url in self.visited_urls or len(self.pages_content) >= self.max_pages:
                return []
            
            self.visited_urls.add(url)
            
            try:
                response = requests.get(url, timeout=10)
                
                if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                    html_content = response.text
                    text_content = self.extract_text_from_html(html_content)
                    
                    # Only store pages with meaningful content
                    if len(text_content) > 100:
                        self.pages_content[url] = text_content
                        
                        # Extract new links to visit
                        return self.extract_links_from_html(html_content, url, base_domain)
            except Exception as e:
                logging.warning(f"Error processing {url}: {e}")
            
            return []
        
        with tqdm(total=self.max_pages, desc="Crawling") as pbar:
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                while self.urls_to_visit and len(self.pages_content) < self.max_pages:
                    # Take a batch of URLs to process
                    batch_size = min(self.max_workers, len(self.urls_to_visit))
                    current_batch = self.urls_to_visit[:batch_size]
                    self.urls_to_visit = self.urls_to_visit[batch_size:]
                    
                    # Process URLs in parallel
                    future_to_url = {executor.submit(process_url, url): url for url in current_batch}
                    
                    # Collect results and new URLs
                    for future in future_to_url:
                        new_links = future.result()
                        for link in new_links:
                            if link not in self.visited_urls and link not in self.urls_to_visit:
                                self.urls_to_visit.append(link)
                    
                    # Update progress bar
                    current_pages = len(self.pages_content)
                    pbar.update(current_pages - pbar.n)
                    
                    # Small delay between batches to be respectful
                    time.sleep(self.delay)
        
        logging.info(f"Crawling completed. Visited {len(self.visited_urls)} URLs, stored {len(self.pages_content)} pages.")
        return self.pages_content
