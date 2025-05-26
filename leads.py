import json
import pandas as pd
import requests
import time
import logging
import os
from bs4 import BeautifulSoup
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def classify_domain(domain, company_name='', description=''):
    """
    Classify a company domain into specific business categories
    Uses multiple data points: domain name, company name, and description
    """
    # Ensure we're working with lowercase strings
    domain = (domain or '').lower()
    company_name = (company_name or '').lower()
    description = (description or '').lower()
    
    # Combined text for better classification
    combined_text = f"{domain} {company_name} {description}"
    
    # Define specific industry categories with their keywords
    industry_categories = {
        # IT & Tech Services
        'Cloud Services': ['cloud', 'aws', 'azure', 'gcp', 'hosting', 'iaas', 'paas', 'saas'],
        'IT Services': ['it service', 'tech support', 'helpdesk', 'managed service', 'infrastructure', 'network', 'system'],
        'Software Development': ['software', 'development', 'programming', 'code', 'developer', 'app development'],
        'Digital Transformation': ['digital transformation', 'digitization', 'digital strategy', 'digital solution'],
        'Cybersecurity': ['cyber', 'security', 'threat', 'encryption', 'firewall', 'protection', 'data security'],
        'Data Analytics': ['data', 'analytics', 'big data', 'business intelligence', 'bi', 'data science'],
        'AI & Machine Learning': ['ai', 'machine learning', 'artificial intelligence', 'ml', 'neural', 'nlp', 'deep learning'],
        
        # Finance
        'Financial Services': ['financial', 'finance', 'banking', 'investment', 'wealth management'],
        'FinTech': ['fintech', 'payment', 'transaction', 'digital payment', 'banking tech', 'financial technology'],
        'Investment Banking': ['investment bank', 'capital market', 'ipo', 'merger', 'acquisition'],
        'Insurance': ['insurance', 'policy', 'risk management', 'underwriting', 'claim'],
        
        # Healthcare
        'Healthcare Services': ['healthcare', 'medical', 'health service', 'patient care', 'clinic'],
        'HealthTech': ['healthtech', 'health tech', 'medical technology', 'ehealth', 'health platform'],
        'Pharmaceutical': ['pharma', 'pharmaceutical', 'drug', 'medicine', 'therapeutic'],
        'Biotech': ['biotech', 'biotechnology', 'life science', 'genomic', 'biological'],
        
        # Marketing & Media
        'Digital Marketing': ['digital marketing', 'seo', 'sem', 'content marketing', 'social media marketing'],
        'Advertising': ['advertising', 'ad agency', 'adtech', 'media buying', 'programmatic'],
        'PR & Communications': ['pr', 'public relations', 'communication', 'media relation'],
        'Media & Entertainment': ['media', 'entertainment', 'streaming', 'publishing', 'broadcast'],
        
        # Other Industries
        'E-commerce': ['ecommerce', 'e-commerce', 'online store', 'online retail', 'webshop'],
        'Retail': ['retail', 'store', 'merchant', 'shop', 'consumer goods'],
        'Manufacturing': ['manufacturing', 'production', 'factory', 'industrial', 'assembly'],
        'Consulting': ['consulting', 'consultancy', 'advisor', 'business consultant'],
        'Education': ['education', 'learning', 'school', 'university', 'training', 'edtech'],
        'Real Estate': ['real estate', 'property', 'realty', 'building', 'construction', 'proptech'],
        'Legal Services': ['legal', 'law firm', 'attorney', 'lawyer', 'legal service'],
        'Transportation & Logistics': ['transport', 'logistics', 'shipping', 'delivery', 'supply chain'],
        'Energy': ['energy', 'power', 'utility', 'electricity', 'renewable', 'oil', 'gas'],
        'Telecom': ['telecom', 'telecommunication', 'cellular', 'network provider', 'mobile carrier']
    }
    
    # Calculate relevance scores for each industry
    scores = {}
    for industry, keywords in industry_categories.items():
        # Count how many keywords from this industry appear in the text
        industry_score = 0
        for keyword in keywords:
            if keyword in combined_text:
                industry_score += 1
                
                # Add bonus points for exact matches in name or domain
                if keyword in domain or keyword in company_name:
                    industry_score += 2
                    
                # Add bonus for phrases (keywords with spaces)
                if ' ' in keyword and keyword in combined_text:
                    industry_score += 3
        
        if industry_score > 0:
            scores[industry] = industry_score
    
    # If no industry matched, try to determine a general category
    if not scores:
        # General categories as fallback
        general_categories = {
            'Technology': ['tech', 'software', 'digital', 'comp', 'it', 'app', 'online', 'computer', 'technology', 'systems'],
            'Financial Services': ['finance', 'bank', 'invest', 'capital', 'financial', 'insurance', 'asset', 'money'],
            'Healthcare': ['health', 'med', 'care', 'doctor', 'hospital', 'clinic', 'therapy', 'wellness', 'patient'],
            'Professional Services': ['service', 'solution', 'consulting', 'professional', 'management', 'advisor']
        }
        
        for category, keywords in general_categories.items():
            category_score = sum(1 for kw in keywords if kw in combined_text)
            if category_score > 0:
                scores[category] = category_score
    
    # Return the industry with the highest score, or Other if none found
    if scores:
        return max(scores, key=scores.get)
    else:
        return 'Other'

def scrape_linkedin_company_page(url, user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36', timeout=10):
    """
    Scrape a LinkedIn company page for company information
    """
    headers = {
        'User-Agent': user_agent,
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
    }
    logger.debug(f"Scraping LinkedIn URL: {url}")
    
    try:
        resp = requests.get(url, headers=headers, timeout=timeout)
        if resp.status_code != 200:
            logger.warning(f"Failed to retrieve {url} - Status code: {resp.status_code}")
            return None
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # Extract company name
        name_elem = soup.find('h1') or soup.find('title')
        name = name_elem.text.strip() if name_elem else ''
        if '|' in name:
            name = name.split('|')[0].strip()
        
        # Extract description from meta tag
        desc_elem = soup.find('meta', {'name': 'description'}) or soup.find('meta', {'property': 'og:description'})
        desc = desc_elem.get('content', '').strip() if desc_elem else ''
        
        # Extract domain from URL
        domain_parts = url.replace('https://', '').replace('http://', '').split('/')
        domain = domain_parts[0] if domain_parts else ''
        if 'linkedin.com' in domain:
            # Extract the actual company identifier
            url_parts = url.split('/')
            if 'company' in url_parts:
                try:
                    company_idx = url_parts.index('company')
                    if company_idx + 1 < len(url_parts):
                        domain = url_parts[company_idx + 1]
                except ValueError:
                    domain = ''
        
        # Try to find website URL
        website = ''
        for a in soup.find_all('a', href=True):
            href = a.get('href', '')
            if ('website' in a.text.lower() or 'visit website' in a.text.lower()) and 'linkedin.com' not in href:
                website = href
                break
        
        # Try to extract company size
        size = ''
        for elem in soup.find_all(['p', 'span', 'div']):
            text = elem.text.lower()
            if 'employees' in text or 'people' in text:
                size = elem.text.strip()
                break
        
        # Try to extract location
        location = ''
        for elem in soup.find_all(['span', 'div']):
            text = elem.text.lower()
            if any(keyword in text for keyword in ['headquarter', 'location', 'based in', 'office']):
                location = elem.text.strip()
                break
        
        # Try to extract founding year
        founded = ''
        for elem in soup.find_all(['p', 'span', 'div']):
            text = elem.text.lower()
            if 'founded' in text or 'established' in text:
                founded = elem.text.strip()
                break
        
        # Use improved domain classification with multiple data points
        domain_class = classify_domain(domain, name, desc)
        
        return {
            'companyLinkedinUrl': url,
            'name': name,
            'description': desc,
            'website': website,
            'domain': domain,
            'domain_class': domain_class,
            'size': size,
            'location': location,
            'founded': founded,
            'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
    except Exception as e:
        logger.error(f"Error scraping {url}: {str(e)}")
        return None

def google_search_linkedin_companies(query, max_results=10):
    """
    Search for LinkedIn company URLs using multiple methods with keyword-based URL construction
    """
    logger.debug(f"Searching for: {query}")
    urls = []
    
    # First try: Google search with proper error handling
    try:
        from googlesearch import search
        search_query = f"{query} site:linkedin.com/company"
        logger.debug(f"Google search query: {search_query}")
        
        for url in search(search_query, num_results=max_results*3, lang='en', safe='off', pause=2):
            if 'linkedin.com/company/' in str(url):
                clean_url = str(url).split('&')[0].split('?')[0]
                if clean_url not in urls:
                    urls.append(clean_url)
                    if len(urls) >= max_results:
                        break
        
        if urls:
            logger.debug(f"Google search found {len(urls)} URLs")
            return urls[:max_results]
            
    except Exception as e:
        logger.warning(f"Google search failed: {str(e)}")
    
    # Second method: Construct likely LinkedIn URLs based on query keywords
    logger.debug("Constructing LinkedIn URLs based on query keywords")
    keywords = query.lower().replace(' companies', '').replace(' company', '').split()
    
    # Industry-specific LinkedIn company patterns
    industry_mappings = {
        'fintech': ['stripe', 'square', 'plaid', 'klarna', 'revolut', 'wise', 'checkout', 'adyen'],
        'ai': ['openai', 'anthropic', 'deepmind', 'scale-ai', 'huggingface', 'stability-ai'],
        'crypto': ['coinbase', 'binance', 'kraken', 'gemini', 'blockchain', 'chainlink'],
        'healthcare': ['tempus', 'flatiron-health', 'veracyte', 'guardant-health', 'moderna'],
        'ecommerce': ['shopify', 'bigcommerce', 'woocommerce', 'magento', 'prestashop'],
        'saas': ['salesforce', 'hubspot', 'zendesk', 'atlassian', 'slack', 'zoom'],
        'edtech': ['coursera', 'udemy', 'khan-academy', 'duolingo', 'skillshare'],
        'logistics': ['fedex', 'ups', 'dhl', 'flexport', 'shippo', 'easypost']
    }
    
    # Find matching companies based on keywords
    for keyword in keywords[:3]:  # Use first 3 keywords
        for industry, companies in industry_mappings.items():
            if keyword in industry or industry in keyword:
                for company in companies[:3]:  # Get 3 companies per match
                    url = f"https://www.linkedin.com/company/{company}"
                    if url not in urls:
                        urls.append(url)
                        if len(urls) >= max_results:
                            return urls
    
    # Third method: Direct keyword-based URL construction
    for keyword in keywords[:max_results]:
        if len(keyword) > 2:  # Skip very short words
            # Try different URL patterns
            patterns = [
                keyword,
                f"{keyword}-inc",
                f"{keyword}-technologies",
                f"{keyword}-solutions",
                f"{keyword}inc",
                f"{keyword}tech"
            ]
            
            for pattern in patterns:
                url = f"https://www.linkedin.com/company/{pattern}"
                if url not in urls:
                    urls.append(url)
                    if len(urls) >= max_results:
                        return urls[:max_results]
    
    logger.debug(f"Constructed {len(urls)} potential LinkedIn URLs")
    return urls[:max_results] if urls else []

def run_scraper(
    keywords=None,
    founded_years=None,
    country=None,
    size=None,
    config_path='scraper_config.json',
    max_results=10,
    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    timeout=10,
    output_csv='lead1.csv',
    sleep_time=1.0,
    search_func=None
):
    """
    Main function to run the LinkedIn company scraper
    """
    # Load config if it exists
    config = {}
    if os.path.exists(config_path):
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
        except Exception as e:
            logger.warning(f"Could not load config: {e}")
    
    # Use provided parameters or defaults from config
    keywords = keywords or config.get('keywords', 'IT services')
    founded_years = founded_years or config.get('founded_years', ['2015'])
    country = country or config.get('country', 'United Kingdom')
    size = size or config.get('size', '51-200')
    
    # Build more targeted search query
    if founded_years and len(founded_years) > 0:
        years_str = " OR ".join(founded_years)
        query = f"{keywords} companies {country} ({years_str}) employees {size}"
    else:
        query = f"{keywords} companies {country} employees {size}"
    
    logger.info(f"Search Query: {query}")
    
    # Get LinkedIn company URLs
    urls = []
    if search_func is not None:
        urls = search_func(query)
    else:
        urls = google_search_linkedin_companies(query, max_results)
    
    # Scrape each company page
    results = []
    for i, url in enumerate(urls):
        logger.info(f"Scraping {i+1}/{len(urls)}: {url}")
        data = scrape_linkedin_company_page(url, user_agent=user_agent, timeout=timeout)
        if data:
            results.append(data)
        
        # Add sleep to avoid rate limiting
        if i < len(urls) - 1:
            logger.debug(f"Sleeping for {sleep_time} seconds")
            time.sleep(sleep_time)
    
    # Create DataFrame from results
    df = pd.DataFrame(results)
    
    # Save to CSV if output path provided and results exist
    if output_csv and not df.empty:
        df.to_csv(output_csv, index=False)
        logger.info(f"Results saved to {output_csv}")
    
    return df

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='LinkedIn Company Scraper')
    parser.add_argument('--keywords', type=str, default=None, help='Keywords for search')
    parser.add_argument('--founded_years', type=str, default=None, help='Comma-separated years')
    parser.add_argument('--country', type=str, default=None, help='Country')
    parser.add_argument('--size', type=str, default=None, help='Company size')
    parser.add_argument('--max_results', type=int, default=10, help='Maximum results')
    
    args = parser.parse_args()
    
    founded_years = None
    if args.founded_years:
        founded_years = [year.strip() for year in args.founded_years.split(',')]
    
    run_scraper(
        keywords=args.keywords,
        founded_years=founded_years,
        country=args.country,
        size=args.size,
        max_results=args.max_results
    )
