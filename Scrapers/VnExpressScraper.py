import requests
import json
import uuid
import re
import time
from urllib.parse import urljoin, urlparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from langdetect import detect, DetectorFactory
from unidecode import unidecode
from tqdm import tqdm

DetectorFactory.seed = 0

class VnExpressScraper:

    def __init__(self, delay: float = 0.1):
        self.delay = delay
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'vi-VN,vi;q=0.8,en-US;q=0.5,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1'
        })
        
        self.vietnamese_patterns = [
            r'[àáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ]',
            r'\b(và|hoặc|với|của|trong|ngoài|trên|dưới|sau|trước|bằng|theo|về|để|cho|từ|tại|này|đó|những|các|một|hai|ba|tôi|bạn|anh|chị|em)\b'
        ]
        
    def fetch_url(self, url: str) -> Optional[BeautifulSoup]:

        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            content_type = response.headers.get('content-type', '').lower()
            if 'text/html' not in content_type:
                print(f"Skipping non-HTML content: {url}")
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
                    if title and len(title) > 10 and '406' not in title:  # Valid title
                        break
            
            if not title or '406' in title:
                return None
            
            # Extract main content - updated selectors for current vnexpress structure
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
                    if content and len(content) > 100:  # Valid content
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
    
    def clean_text(self, text: str) -> str:

        if not text:
            return ""
        
        # Remove HTML entities
        text = re.sub(r'&[a-zA-Z0-9#]+;', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', ' ', text)
        
        # Remove email addresses
        text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', ' ', text)
        
        # Remove phone numbers
        text = re.sub(r'(\+84|0)[0-9]{8,10}', ' ', text)
        
        # Remove excessive whitespace and normalize
        text = re.sub(r'\s+', ' ', text)
        text = text.strip()
        
        # Remove lines that are too short (likely navigation/ads)
        lines = text.split('\n')
        cleaned_lines = []
        for line in lines:
            line = line.strip()
            if len(line) > 20 and not re.match(r'^[0-9\s\-\.,:;]+$', line):
                cleaned_lines.append(line)
        
        text = '\n'.join(cleaned_lines)
        
        # Final cleanup
        text = re.sub(r'\n\s*\n', '\n', text)  # Remove empty lines
        text = re.sub(r'[^\w\sàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ\.,!?;:()"\'-]', ' ', text)
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
    
    def is_vietnamese_text(self, text: str) -> Tuple[bool, float]:
        if not text or len(text) < 50:
            return False, 0.0
        
        # Count Vietnamese characters
        vietnamese_chars = len(re.findall(self.vietnamese_patterns[0], text))
        total_alpha_chars = len(re.findall(r'[a-zA-ZàáảãạăắằẳẵặâấầẩẫậèéẻẽẹêếềểễệìíỉĩịòóỏõọôốồổỗộơớờởỡợùúủũụưứừửữựỳýỷỹỵđĐ]', text))
        
        if total_alpha_chars == 0:
            return False, 0.0
        
        vietnamese_char_ratio = vietnamese_chars / total_alpha_chars
        
        # Count Vietnamese words
        vietnamese_words = len(re.findall(self.vietnamese_patterns[1], text, re.IGNORECASE))
        total_words = len(text.split())
        
        vietnamese_word_ratio = vietnamese_words / max(total_words, 1)
        
        # Check for common Vietnamese phrases
        vietnamese_phrases = [
            r'\bviệt nam\b', r'\btheo báo\b', r'\btrong khi\b', r'\bngười dân\b',
            r'\bchính phủ\b', r'\bthành phố\b', r'\bhà nội\b', r'\btphcm\b',
            r'\bngười\b', r'\bviệc\b', r'\bthời gian\b', r'\bkhu vực\b'
        ]
        
        phrase_count = 0
        for phrase in vietnamese_phrases:
            if re.search(phrase, text, re.IGNORECASE):
                phrase_count += 1
        
        phrase_score = min(phrase_count / 4, 1.0)
        
        # Combined score - more lenient
        confidence = (vietnamese_char_ratio * 0.4 + vietnamese_word_ratio * 0.4 + phrase_score * 0.2)
        
        # Lower threshold for acceptance
        return confidence > 0.15, confidence
    
    def count_words(self, text: str) -> int:

        if not text:
            return 0
        
        # Split by whitespace and count non-empty elements
        words = [word for word in text.split() if word.strip()]
        return len(words)
    
    def scrape_url(self, url: str) -> Optional[Dict]:

        soup = self.fetch_url(url)
        if not soup:
            return None
        
        # Extract content
        article_data = self.extract_article_content(soup, url)
        if not article_data:
            return None
        
        # Clean title and content
        title = self.clean_text(article_data['title'])
        content = self.clean_text(article_data['content'])
        
        # Combine title and content
        full_text = f"{title}. {content}".strip()
        
        # Validate Vietnamese content
        is_vietnamese, confidence = self.is_vietnamese_text(full_text)
        if not is_vietnamese:
            print(f"Skipping non-Vietnamese content: {url} (confidence: {confidence:.2f})")
            return None
        
        # Check word count
        word_count = self.count_words(full_text)
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
    
    def find_article_urls(self, category_url: str) -> List[str]:

        soup = self.fetch_url(category_url)
        if not soup:
            return []
        
        article_urls = set()
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            
            if href.startswith('/'):
                href = urljoin(category_url, href)
            
            if ('vnexpress.net' in href and href.endswith('.html')):
                article_urls.add(href)

        
        return list(article_urls)
    
    def scrape_urls_from_file(self, input_file: str, output_file: str, max_categories: Optional[int] = None):
        # Read category URLs
        with open(input_file, 'r', encoding='utf-8') as f:
            category_urls = [line.strip() for line in f if line.strip()]
        
        if max_categories:
            category_urls = category_urls[:max_categories]
        
        
        # Collect all article URLs
        all_article_urls = []
        for category_url in tqdm(category_urls, desc="Finding articles"):
            try:
                article_urls = self.find_article_urls(category_url)
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
                        print(f"✓ Scraped: {entry['title'][:50]}... ({self.count_words(entry['text'])} words)")
                    
                    # Be respectful to the server
                    time.sleep(self.delay)
                    
                except Exception as e:
                    print(f"Error processing {url}: {e}")
                    continue
            
            print(f"\nCompleted! Successfully scraped {successful_count} articles to {output_file}")

