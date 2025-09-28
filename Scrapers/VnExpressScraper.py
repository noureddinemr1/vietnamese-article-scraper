import requests, json, uuid, re, time
from urllib.parse import urljoin
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from langdetect import DetectorFactory
from tqdm import tqdm
from utils.headers import headers
from utils.clean_text import clean_text
from utils.Vietnames import is_vietnamese_text
from utils.helpers import count_words

DetectorFactory.seed = 0

class VnExpressScraper:

    def __init__(self, delay: float = 0.1):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update(headers)
        
    def fetch_url(self, url: str) -> Optional[BeautifulSoup]:

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if not any(ct in content_type for ct in ('text/html', 'application/xhtml+xml')):
                return None
                
            soup = BeautifulSoup(response.content, 'lxml')
            return soup
            
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None
        except Exception as e:
            print(f"Error parsing {url}: {e}")
            return None
    
    def extract_article_content(self, soup: BeautifulSoup, url: str) -> Optional[Dict[str, str]]:
        try:
            title = None
            title_selectors = [
                'h1.title-detail',
                'h1.title_news_detail', 
                'h1.title_detail',
                '.title-news h1',
                'h1[class*="title"]',
                'h1',
                '.article-title',
                '[class*="title"] h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    title = title_elem.get_text().strip()
                    if title and len(title) > 10 : 
                        break
            
            if not title or '406' in title:
                return None
            
            content = ""
            content_selectors = [
                'article.fck_detail',
                '.fck_detail',
                'div.fck_detail',
                'article[class*="detail"]',
                '.article-content',
                '.Normal',
                'div.content_detail',
                '.content-detail',
                '[class*="article-body"]',
                '.article-body',
                'div[class*="content"]',
                'div[class*="detail"]',
                'article',
                '.content'
            ]
            
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Remove unwanted elements
                    for unwanted in content_elem.find_all(['script', 'style', 'nav', 'header', 'footer', 'aside', 'iframe', 'form']):
                        unwanted.decompose()
                    
                    # Remove ads and social media elements
                    for ad_class in ['ads', 'advertisement', 'social', 'share', 'comment', 'related', 'sidebar', 'widget']:
                        for elem in content_elem.find_all(attrs={'class': re.compile(ad_class, re.I)}):
                            elem.decompose()
                    
                    content = content_elem.get_text()
                    if content and len(content) > 100:
                        break
            
            # If no content found with specific selectors, try to find largest text block
            if not content:
                all_divs = soup.find_all('div')
                largest_text = ""
                for div in all_divs:
                    div_text = div.get_text().strip()
                    if len(div_text) > len(largest_text) and len(div_text) > 200:
                        largest_text = div_text
                
                if largest_text:
                    content = largest_text
            
            if not content:
                return None
                
            return {
                'title': title,
                'content': content
            }
            
        except Exception as e:
            print(f"Error extracting content from {url}: {e}")
            return None
       
    def scrape_url(self, url: str) -> Optional[Dict]:

        soup = self.fetch_url(url)
        if not soup:
            return None
        
        # Extract content
        article_data = self.extract_article_content(soup, url)
        if not article_data:
            return None
        
        # Clean title and content
        title = clean_text(article_data['title'])
        content = clean_text(article_data['content'])
        
        # Combine title and content
        full_text = f"{title}. {content}".strip()
        
        # Validate Vietnamese content
        is_vietnamese, confidence = is_vietnamese_text(full_text)
        if not is_vietnamese:
            print(f"Skipping non-Vietnamese content: {url} (confidence: {confidence:.2f})")
            return None
        
        # Check word count
        word_count = count_words(full_text)
        if word_count < 200:
            print(f"Skipping short article: {url} ({word_count} words)")
            return None
        
        # Create formatted entry
        entry = {
            "id": str(uuid.uuid4()),
            "language": "vi",
            "source_url": url,
            "title": title,
            "text": full_text,
            "clean_status": "clean",
            "category": "news"
        }
        
        return entry
    
    def find_article_urls(self, category_url: str, max_depth: int , visited_urls: Optional[set] = None) -> List[str]:

        if visited_urls is None:
            visited_urls = set()
        
        if category_url in visited_urls or max_depth < 0:
            return []
        
        visited_urls.add(category_url)
        soup = self.fetch_url(category_url)
        if not soup:
            return []
        
        article_urls = set()
        navigation_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if href.startswith('/'):
                href = urljoin(category_url, href)
            
            if 'vnexpress.net' not in href:
                continue
                
            if href.endswith('.html'):
                article_urls.add(href)
            elif (max_depth > 0 and href not in visited_urls and 
                  any(section in href.lower() for section in [
                      '/the-thao', '/kinh-doanh', '/giai-tri', '/phap-luat',
                      '/giao-duc', '/suc-khoe', '/gia-dinh', '/du-lich',
                      '/so-hoa', '/xe', '/y-kien', '/tam-su', '/cuoi'
                  ])):
                navigation_urls.add(href)
        
        # Recursively explore navigation URLs with depth limit
        for nav_url in list(navigation_urls)[:3]:  # Limit to prevent excessive requests
            try:
                recursive_articles = self.find_article_urls(nav_url, max_depth - 1, visited_urls)
                article_urls.update(recursive_articles)
                time.sleep(self.delay)
            except Exception as e:
                print(f"Error exploring {nav_url}: {e}")
                continue
        
        return list(article_urls)
    
    def find_internal_article_links(self, article_urls: List[str]) -> List[str]:
        all_articles = set(article_urls)
        articles_to_check = article_urls
        
        for article_url in tqdm(articles_to_check, desc="Finding internal links"):
            try:
                soup = self.fetch_url(article_url)
                if not soup:
                    continue
                
                # Check content areas for internal links
                content_selectors = ['.fck_detail', '.article-content', '.content-detail', 'article']
                for selector in content_selectors:
                    content_area = soup.select_one(selector)
                    if content_area:
                        for link in content_area.find_all('a', href=True):
                            href = link['href']
                            
                            if href.startswith('/'):
                                href = urljoin(article_url, href)
                            
                            if 'vnexpress.net' in href and href.endswith('.html'):
                                all_articles.add(href)
                        break
                
                time.sleep(self.delay)
                
            except Exception as e:
                print(f"Error checking internal links in {article_url}: {e}")
                continue
        
        return list(all_articles)
    
    def scrape_urls_from_file(self, input_file: str, output_file: str, max_categories: Optional[int] = None, use_recursive: bool = True, use_internal_links: bool = True):

        # Read category URLs
        with open(input_file, 'r', encoding='utf-8') as f:
            category_urls = [line.strip() for line in f if line.strip()]
        
        if max_categories:
            category_urls = category_urls[:max_categories]
        
        # Collect all article URLs
        all_article_urls = []
        for category_url in tqdm(category_urls, desc="Finding articles"):
            try:
                # Use recursive discovery if enabled
                max_depth = 4 if use_recursive else 0
                article_urls = self.find_article_urls(category_url, max_depth=max_depth)
                
                # Find internal links if enabled
                if use_internal_links and article_urls:
                    article_urls = self.find_internal_article_links(article_urls)
                
                all_article_urls.extend(article_urls)
                print(f"Found {len(article_urls)} articles in {category_url}")
                time.sleep(self.delay)
            except Exception as e:
                print(f"Error finding articles in {category_url}: {e}")
                continue
        
        # Remove duplicates
        all_article_urls = list(set(all_article_urls))
        print("=" * 50)
        print(f"Total unique articles found: {len(all_article_urls)}")
        print("=" * 50)
        
        # Create output file
        with open(output_file, 'w', encoding='utf-8') as f:
            successful_count = 0
            
            for url in tqdm(all_article_urls, desc="Scraping articles"):
                try:
                    entry = self.scrape_url(url)
                    if entry:
                        f.write(json.dumps(entry, ensure_ascii=False) + '\n')
                        f.flush()  # Ensure data is written immediately
                        successful_count += 1
                        print(f"✓ Scraped: {entry['title'][:50]}... ({count_words(entry['text'])} words)")
                    
                    # Be respectful to the server
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"Error processing {url}: {e}")
                    continue
            
            print(f"\nCompleted! Successfully scraped {successful_count} articles to {output_file}")

