#!/usr/bin/env python3
"""
Simple Quick Commerce News Scraper - WORKING VERSION
Just extracts articles with links, full text, and dates
"""

import requests
from bs4 import BeautifulSoup
import feedparser
import time
import argparse
from datetime import datetime, timedelta
import re

class SimpleQComScraper:
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        # Working RSS feeds for Indian news sources
        self.sources = {
            "Business News": [
                "https://economictimes.indiatimes.com/rssfeedsdefault.cms",
                "https://www.business-standard.com/rss/latest.rss",
                "https://www.livemint.com/rss/companies",
                "https://www.financialexpress.com/feed/",
                "https://www.moneycontrol.com/rss/business.xml"
            ],
            "Startup & Tech News": [
                "https://yourstory.com/feed",
                "https://inc42.com/feed/",
                "https://www.medianama.com/feed/",
                "https://entrackr.com/feed/"
            ]
        }
        
        # Quick commerce keywords
        self.keywords = [
            "quick commerce", "q-commerce", "qcommerce", "quick-commerce",
            "blinkit", "zepto", "swiggy instamart", "instamart", 
            "amazon now", "flipkart minutes", "bigbasket now",
            "dunzo", "grofers", "milk basket", "fresh to home",
            "ultra fast delivery", "10 minute delivery", "15 minute delivery",
            "instant delivery", "rapid delivery", "express delivery",
            "dark store", "dark stores", "micro fulfillment",
            "on-demand delivery", "hyperlocal delivery", "last mile delivery",
            "grocery delivery", "instant grocery", "delivery hero",
            "food delivery instant", "medicine delivery instant"
        ]
    
    def extract_full_article(self, url):
        """Extract full article text from URL"""
        try:
            response = self.session.get(url, timeout=15)
            if response.status_code != 200:
                return "Could not fetch article content"
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove unwanted elements
            for element in soup(['script', 'style', 'nav', 'header', 'footer', 
                               'aside', 'advertisement', '.ad', '.ads', 'form', 'button']):
                element.decompose()
            
            # Try to find main content
            content_selectors = [
                'article', '.article-content', '.post-content', '.entry-content',
                '.content', 'main', '.main', '.story', '.article-body',
                '.story-body', '.text-content', '[data-module="ArticleBody"]'
            ]
            
            content = ""
            for selector in content_selectors:
                content_elem = soup.select_one(selector)
                if content_elem:
                    # Get text from paragraphs
                    paragraphs = content_elem.find_all(['p', 'div'])
                    content_parts = []
                    for p in paragraphs:
                        text = p.get_text(separator=' ', strip=True)
                        if len(text) > 50:  # Only substantial paragraphs
                            content_parts.append(text)
                    content = '\n\n'.join(content_parts)
                    break
            
            if not content:
                # Fallback to all paragraphs
                paragraphs = soup.find_all('p')
                content_parts = []
                for p in paragraphs:
                    text = p.get_text(separator=' ', strip=True)
                    if len(text) > 50:
                        content_parts.append(text)
                content = '\n\n'.join(content_parts[:15])  # First 15 good paragraphs
            
            # Clean up the text
            content = self.clean_text(content)
            return content if content else "Content extraction failed"
            
        except Exception as e:
            return f"Error extracting content: {str(e)}"
    
    def clean_text(self, text):
        """Clean and format text"""
        if not text:
            return ""
        
        # Remove extra whitespace
        text = re.sub(r'\n+', '\n', text)
        text = re.sub(r' +', ' ', text)
        
        # Remove common unwanted patterns
        unwanted_patterns = [
            r'(Advertisement|Subscribe|Read More|Continue Reading).*',
            r'Share.*?(Facebook|Twitter|LinkedIn).*',
            r'Follow us on.*',
            r'Also Read:.*',
            r'Related:.*',
            r'Download.*app.*',
            r'Newsletter.*',
            r'Cookie.*policy.*'
        ]
        
        for pattern in unwanted_patterns:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)
        
        return text.strip()
    
    def is_relevant_article(self, title, content):
        """Check if article is about quick commerce"""
        text = (title + " " + content).lower()
        
        # Check for quick commerce keywords
        return any(keyword in text for keyword in self.keywords)
    
    def parse_date(self, date_string):
        """Parse various date formats to standard format"""
        if not date_string:
            return datetime.now().strftime("%d %B %Y")
        
        try:
            # Try different date parsing approaches
            if hasattr(date_string, 'timetuple'):
                # feedparser date object
                return datetime(*date_string.timetuple()[:6]).strftime("%d %B %Y")
            elif isinstance(date_string, str):
                # Try to parse string date
                for fmt in ["%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%Y-%m-%d %H:%M:%S"]:
                    try:
                        return datetime.strptime(date_string, fmt).strftime("%d %B %Y")
                    except ValueError:
                        continue
        except:
            pass
        
        return datetime.now().strftime("%d %B %Y")
    
    def add_google_news_search(self, days_back=7):
        """Add Google News search for quick commerce"""
        articles = []
        
        # Specific search terms for quick commerce news
        search_terms = [
            "Blinkit India quick commerce",
            "Zepto funding India",
            "Swiggy Instamart market share",
            "Amazon Now Mumbai delivery",
            "quick commerce India startup"
        ]
        
        print("Searching Google News for quick commerce developments...")
        
        for term in search_terms[:3]:  # Limit searches
            try:
                # Simple Google News RSS search
                encoded_term = term.replace(" ", "+")
                search_url = f"https://news.google.com/rss/search?q={encoded_term}&hl=en-IN&gl=IN&ceid=IN:en"
                
                response = self.session.get(search_url, timeout=10)
                if response.status_code == 200:
                    feed = feedparser.parse(response.content)
                    
                    for entry in feed.entries[:3]:  # Top 3 results per search
                        # Check date
                        if hasattr(entry, 'published_parsed') and entry.published_parsed:
                            pub_date = datetime(*entry.published_parsed[:6])
                            cutoff_date = datetime.now() - timedelta(days=days_back)
                            if pub_date < cutoff_date:
                                continue
                        
                        # Check relevance
                        if self.is_relevant_article(entry.title, entry.get('summary', '')):
                            print(f"    Found: {entry.title[:60]}...")
                            
                            # Extract full content
                            full_content = self.extract_full_article(entry.link)
                            
                            article = {
                                'title': entry.title,
                                'url': entry.link,
                                'content': full_content,
                                'date': self.parse_date(entry.get('published_parsed')),
                                'source': 'Google News Search',
                                'category': 'Quick Commerce'
                            }
                            
                            articles.append(article)
                            time.sleep(1)  # Rate limiting
                            
            except Exception as e:
                print(f"    Error searching for '{term}': {e}")
        
        return articles
    
    def remove_duplicates(self, articles):
        """Remove duplicate articles based on title similarity"""
        unique_articles = []
        seen_titles = set()
        
        for article in articles:
            # Simple deduplication based on title
            title_key = re.sub(r'[^\w\s]', '', article['title'].lower())
            title_key = ' '.join(title_key.split()[:6])  # First 6 words
            
            if title_key not in seen_titles:
                seen_titles.add(title_key)
                unique_articles.append(article)
        
        return unique_articles
    
    def scrape_rss_feeds(self, days_back=7):
        """Scrape all RSS feeds for articles from specified number of days"""
        articles = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        print(f"Looking for quick commerce articles from the last {days_back} days (since {cutoff_date.strftime('%Y-%m-%d')})")
        
        for category, feeds in self.sources.items():
            print(f"Scraping {category} sources...")
            
            for feed_url in feeds:
                try:
                    print(f"  - {feed_url}")
                    response = self.session.get(feed_url, timeout=15)
                    
                    if response.status_code == 200:
                        feed = feedparser.parse(response.content)
                        
                        for entry in feed.entries[:25]:  # Check more articles
                            # Check if article is within specified timeframe
                            if hasattr(entry, 'published_parsed') and entry.published_parsed:
                                pub_date = datetime(*entry.published_parsed[:6])
                                if pub_date < cutoff_date:
                                    continue
                            
                            # Check relevance for quick commerce
                            if self.is_relevant_article(entry.title, entry.get('summary', '')):
                                
                                # Extract full article content
                                print(f"    Extracting: {entry.title[:60]}...")
                                full_content = self.extract_full_article(entry.link)
                                
                                # Only keep articles with substantial content (more than just error messages)
                                if (len(full_content) > 200 and 
                                    not full_content.startswith("Content extraction failed") and 
                                    not full_content.startswith("Error extracting content") and
                                    not full_content.startswith("Could not fetch")):
                                    
                                    # Parse publication date
                                    pub_date = self.parse_date(entry.get('published_parsed'))
                                    
                                    article = {
                                        'title': entry.title,
                                        'url': entry.link,
                                        'content': full_content,
                                        'date': pub_date,
                                        'source': feed_url,
                                        'category': 'Quick Commerce'
                                    }
                                    
                                    articles.append(article)
                                    time.sleep(2)  # More polite rate limiting
                                else:
                                    print(f"    Skipped: Content too short or extraction failed")
                                
                except Exception as e:
                    print(f"    Error scraping {feed_url}: {e}")
        
        # REMOVE Google News search completely since it doesn't work
        print("Skipping Google News search (redirect URLs don't work for content extraction)")
        
        # Remove duplicates
        articles = self.remove_duplicates(articles)
        
        return articles
    
    def generate_company_summary(self, articles):
        """Generate a summary of companies mentioned"""
        
        # Key companies to track
        qcom_companies = [
            "Blinkit", "Zepto", "Swiggy", "Instamart", "Amazon Now", "Flipkart Minutes",
            "Dunzo", "Grofers", "BigBasket", "Milk Basket", "Fresh To Home",
            "Delivery Hero", "Zomato", "Eternal", "Myntra Rapid"
        ]
        
        mentioned_companies = set()
        
        for article in articles:
            text = (article['title'] + " " + article['content']).lower()
            
            for company in qcom_companies:
                if company.lower() in text:
                    mentioned_companies.add(company)
        
        summary = "\n## Companies Mentioned This Period\n\n"
        
        if mentioned_companies:
            summary += f"**Quick Commerce Companies:** {', '.join(sorted(mentioned_companies))}\n\n"
        else:
            summary += "No major quick commerce companies specifically mentioned.\n\n"
        
        return summary
    
    def generate_simple_report(self, articles, days_back):
        """Generate text report"""
        if not articles:
            return f"No quick commerce articles found for the last {days_back} days."
        
        period_text = f"last {days_back} day{'s' if days_back != 1 else ''}"
        report = f"""QUICK COMMERCE INDUSTRY NEWS REPORT
==================================================
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Timeframe: {period_text.title()}
Total articles: {len(articles)}

"""
        
        for i, article in enumerate(articles, 1):
            report += f"""
================================================================================
ARTICLE {i}
================================================================================

TITLE: {article['title']}

SOURCE: {article.get('source', 'Unknown')}

URL: {article['url']}

PUBLISHED: {article['date']}

FULL CONTENT:
----------------------------------------
{article['content']}
----------------------------------------

"""
        
        # Add company summary
        report += self.generate_company_summary(articles)
        
        return report
    
    def save_report(self, report, days_back=7):
        """Save report to file"""
        timeframe_label = f"{days_back}days"
        filename = f"quick_commerce_news_{timeframe_label}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(report)
            print(f"Report saved to: {filename}")
            return filename
        except Exception as e:
            print(f"Error saving report: {e}")
            return None
    
    def run_scraper(self, days_back=7):
        """Main scraping function"""
        print("Starting quick commerce news scraping...")
        print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Looking for articles from the last {days_back} days")
        
        # Scrape articles
        articles = self.scrape_rss_feeds(days_back)
        
        if not articles:
            print(f"No relevant quick commerce articles found for the last {days_back} days.")
            return
        
        print(f"Found {len(articles)} relevant articles with full content")
        
        # Generate report
        report = self.generate_simple_report(articles, days_back)
        
        # Save report
        filename = self.save_report(report, days_back)
        
        print("Scraping complete!")
        if filename:
            print(f"Open {filename} to view the results")

def main():
    parser = argparse.ArgumentParser(description='Simple Quick Commerce News Scraper')
    parser.add_argument('--days', type=int, help='Number of days to look back (1-30)', default=7)
    
    args = parser.parse_args()
    
    # Create scraper instance
    scraper = SimpleQComScraper()
    
    if args.days and 1 <= args.days <= 30:
        # Use command line specified days
        scraper.run_scraper(args.days)
    else:
        # Use default 7 days
        scraper.run_scraper(7)

if __name__ == "__main__":
    main()
