import json
import pandas as pd
import requests
import time
import logging
import os
import random
import re
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Force logging to always print to console
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s:%(message)s')
logger = logging.getLogger(__name__)

print('--- Script started ---')

def classify_domain(domain, company_name='', description=''):
    """
    Enhanced domain classification that focuses on business activities rather than company names
    Uses contextual analysis to determine actual business domain
    """
   
    domain = (domain or '').lower()
    company_name = (company_name or '').lower()
    description = (description or '').lower()
    
    
    primary_text = description
    secondary_text = f"{domain} {company_name}"
    
    
    industry_categories = {
       
        'Cloud Services': {
            'primary': ['cloud computing', 'cloud infrastructure', 'cloud platform', 'aws services', 'azure services', 'cloud migration', 'cloud hosting', 'saas platform', 'iaas provider', 'paas solutions'],
            'secondary': ['cloud', 'aws', 'azure', 'gcp', 'hosting', 'infrastructure'],
            'context': ['deploy', 'scalable', 'servers', 'computing']
        },
        'Software Development': {
            'primary': ['software development', 'application development', 'custom software', 'software solutions', 'mobile app development', 'web development', 'software engineering'],
            'secondary': ['software', 'development', 'programming', 'coding', 'applications'],
            'context': ['build', 'create', 'develop', 'engineer', 'solutions']
        },
        'IT Services': {
            'primary': ['it services', 'it support', 'it consulting', 'managed it services', 'technical support', 'it infrastructure', 'network services', 'system administration'],
            'secondary': ['it service', 'tech support', 'helpdesk', 'managed service', 'network'],
            'context': ['support', 'maintain', 'manage', 'technical', 'systems']
        },
        'Cybersecurity': {
            'primary': ['cybersecurity services', 'information security', 'security consulting', 'penetration testing', 'security audits', 'data protection', 'network security'],
            'secondary': ['cybersecurity', 'security', 'cyber', 'protection', 'firewall'],
            'context': ['protect', 'secure', 'threat', 'vulnerability', 'compliance']
        },
        'AI & Machine Learning': {
            'primary': ['artificial intelligence', 'machine learning solutions', 'ai development', 'deep learning', 'neural networks', 'ai consulting', 'ml services'],
            'secondary': ['ai', 'machine learning', 'artificial intelligence', 'ml', 'neural'],
            'context': ['intelligent', 'automated', 'predictive', 'analytics', 'algorithms']
        },
        'Data Analytics': {
            'primary': ['data analytics', 'business intelligence', 'data science', 'big data solutions', 'data visualization', 'analytics consulting'],
            'secondary': ['analytics', 'data', 'big data', 'business intelligence', 'bi'],
            'context': ['analyze', 'insights', 'reporting', 'dashboard', 'metrics']
        },
        
       
        'FinTech': {
            'primary': ['financial technology', 'fintech solutions', 'digital payments', 'payment processing', 'digital banking', 'financial software', 'blockchain finance'],
            'secondary': ['fintech', 'payment', 'digital payment', 'financial tech'],
            'context': ['transactions', 'banking', 'financial', 'money', 'wallet']
        },
        'Financial Services': {
            'primary': ['financial services', 'investment services', 'wealth management', 'financial planning', 'asset management', 'financial consulting'],
            'secondary': ['financial', 'finance', 'investment', 'wealth management'],
            'context': ['invest', 'portfolio', 'assets', 'financial planning', 'advisory']
        },
        'Banking': {
            'primary': ['banking services', 'commercial banking', 'retail banking', 'private banking', 'investment banking'],
            'secondary': ['banking', 'bank', 'loans', 'credit'],
            'context': ['lending', 'deposits', 'accounts', 'financial institution']
        },
        'Insurance': {
            'primary': ['insurance services', 'insurance brokerage', 'risk management', 'insurance consulting', 'claims management'],
            'secondary': ['insurance', 'policy', 'coverage', 'claims'],
            'context': ['protect', 'coverage', 'risk', 'premiums', 'underwriting']
        },
        
        
        'Real Estate': {
            'primary': ['real estate services', 'property management', 'real estate development', 'property sales', 'commercial real estate', 'residential real estate', 'property investment'],
            'secondary': ['real estate', 'property', 'realty', 'properties'],
            'context': ['buy', 'sell', 'lease', 'rent', 'development', 'buildings']
        },
        'Property Management': {
            'primary': ['property management services', 'facility management', 'building management', 'asset management', 'property maintenance'],
            'secondary': ['property management', 'facility', 'building'],
            'context': ['manage', 'maintain', 'tenants', 'leasing', 'operations']
        },
        'Construction': {
            'primary': ['construction services', 'building construction', 'civil engineering', 'construction management', 'general contracting'],
            'secondary': ['construction', 'building', 'contracting', 'engineering'],
            'context': ['build', 'construct', 'infrastructure', 'projects', 'contractor']
        },
        
       
        'Healthcare Services': {
            'primary': ['healthcare services', 'medical services', 'patient care', 'clinical services', 'health consulting'],
            'secondary': ['healthcare', 'medical', 'health', 'clinical'],
            'context': ['patients', 'treatment', 'care', 'medical', 'health']
        },
        'HealthTech': {
            'primary': ['health technology', 'medical technology', 'digital health', 'telemedicine', 'health software'],
            'secondary': ['healthtech', 'medtech', 'digital health'],
            'context': ['medical', 'patients', 'clinical', 'healthcare', 'digital']
        },
        'Pharmaceutical': {
            'primary': ['pharmaceutical services', 'drug development', 'pharmaceutical manufacturing', 'clinical research'],
            'secondary': ['pharmaceutical', 'pharma', 'drugs', 'medicine'],
            'context': ['research', 'development', 'clinical', 'therapeutic', 'treatments']
        },
        
        
        'Digital Marketing': {
            'primary': ['digital marketing services', 'online marketing', 'seo services', 'social media marketing', 'content marketing', 'digital advertising'],
            'secondary': ['digital marketing', 'marketing', 'seo', 'social media'],
            'context': ['campaigns', 'advertising', 'promote', 'brand', 'online']
        },
        'Advertising': {
            'primary': ['advertising services', 'advertising agency', 'creative advertising', 'media buying', 'brand advertising'],
            'secondary': ['advertising', 'ads', 'marketing', 'creative'],
            'context': ['campaigns', 'creative', 'brand', 'media', 'promotion']
        },
        'Public Relations': {
            'primary': ['public relations', 'pr services', 'communications', 'media relations', 'crisis communications'],
            'secondary': ['public relations', 'pr', 'communications', 'media'],
            'context': ['reputation', 'communications', 'media', 'messaging', 'publicity']
        },
        
       
        'E-commerce': {
            'primary': ['e-commerce services', 'online retail', 'e-commerce platform', 'online marketplace', 'digital commerce'],
            'secondary': ['ecommerce', 'e-commerce', 'online store', 'retail'],
            'context': ['online', 'selling', 'marketplace', 'shopping', 'digital']
        },
        'Retail': {
            'primary': ['retail services', 'retail operations', 'consumer goods', 'retail management'],
            'secondary': ['retail', 'store', 'shopping', 'consumer'],
            'context': ['customers', 'sales', 'products', 'shopping', 'goods']
        },
        
        
        'Consulting': {
            'primary': ['consulting services', 'business consulting', 'management consulting', 'strategic consulting', 'advisory services'],
            'secondary': ['consulting', 'consultancy', 'advisory', 'consulting'],
            'context': ['advice', 'strategy', 'solutions', 'expertise', 'guidance']
        },
        'Legal Services': {
            'primary': ['legal services', 'law firm', 'legal consulting', 'litigation services', 'corporate law'],
            'secondary': ['legal', 'law', 'attorney', 'lawyer'],
            'context': ['legal', 'law', 'litigation', 'contracts', 'compliance']
        },
        'Accounting': {
            'primary': ['accounting services', 'financial accounting', 'tax services', 'bookkeeping', 'audit services'],
            'secondary': ['accounting', 'tax', 'bookkeeping', 'audit'],
            'context': ['financial', 'taxes', 'books', 'compliance', 'reporting']
        },
        
       
        'Manufacturing': {
            'primary': ['manufacturing services', 'industrial manufacturing', 'production services', 'contract manufacturing'],
            'secondary': ['manufacturing', 'production', 'industrial', 'factory'],
            'context': ['produce', 'manufacture', 'assembly', 'industrial', 'products']
        },
        'Logistics': {
            'primary': ['logistics services', 'supply chain', 'transportation', 'shipping services', 'warehousing'],
            'secondary': ['logistics', 'supply chain', 'shipping', 'transport'],
            'context': ['deliver', 'transport', 'warehouse', 'distribution', 'supply']
        },
        
       
        'Education': {
            'primary': ['educational services', 'training services', 'e-learning', 'corporate training', 'educational technology'],
            'secondary': ['education', 'training', 'learning', 'teaching'],
            'context': ['learn', 'teach', 'students', 'courses', 'knowledge']
        },
        'EdTech': {
            'primary': ['educational technology', 'e-learning platform', 'online education', 'learning management'],
            'secondary': ['edtech', 'e-learning', 'educational tech'],
            'context': ['learning', 'education', 'students', 'online', 'platform']
        }
    }
    
    # Enhanced scoring algorithm
    def calculate_industry_score(industry_data, text_primary, text_secondary):
        score = 0
        matches = []
        
        # Primary indicators (business activities) - High weight
        for indicator in industry_data['primary']:
            if indicator in text_primary:
                score += 10  # High score for business activity match
                matches.append(f"Primary: {indicator}")
                
                # Bonus for multiple word phrases
                if len(indicator.split()) > 1:
                    score += 5
        
        # Secondary indicators - Medium weight
        for indicator in industry_data['secondary']:
            if indicator in text_primary:
                score += 5  # Medium score for description match
                matches.append(f"Secondary: {indicator}")
            elif indicator in text_secondary:
                score += 2  # Lower score for name/domain match
                matches.append(f"Name: {indicator}")
        
        # Context validation - Bonus points
        context_matches = 0
        for context in industry_data['context']:
            if context in text_primary:
                context_matches += 1
                matches.append(f"Context: {context}")
        
        # Context bonus (validates the industry match)
        if context_matches > 0:
            score += context_matches * 3
        
        # Penalty for name-only matches without business context
        name_only_matches = sum(1 for match in matches if match.startswith("Name:"))
        business_matches = sum(1 for match in matches if match.startswith("Primary:"))
        
        if name_only_matches > 0 and business_matches == 0:
            score = max(0, score - 5)  # Reduce score for name-only matches
        
        return score, matches
    
    # Calculate scores for all industries
    industry_scores = {}
    for industry, data in industry_categories.items():
        score, matches = calculate_industry_score(data, primary_text, secondary_text)
        if score > 0:
            industry_scores[industry] = {
                'score': score,
                'matches': matches,
                'confidence': min(100, score * 5)  # Convert to percentage
            }
    
    # Find best match with minimum threshold
    if industry_scores:
        best_industry = max(industry_scores.items(), key=lambda x: x[1]['score'])
        industry_name, industry_info = best_industry
        
        # Only return classification if confidence is high enough
        if industry_info['score'] >= 8:  # Minimum threshold for classification
            logger.debug(f"Classified as {industry_name} (score: {industry_info['score']}, matches: {industry_info['matches']})")
            return industry_name
    
    
    general_categories = {
        'Technology': ['tech', 'digital', 'software', 'computer', 'it', 'automation', 'innovation'],
        'Business Services': ['services', 'solutions', 'consulting', 'management', 'business'],
        'Finance': ['financial', 'money', 'capital', 'investment', 'banking', 'insurance'],
        'Healthcare': ['health', 'medical', 'care', 'wellness', 'clinical', 'patient'],
        'Manufacturing': ['manufacturing', 'production', 'industrial', 'factory', 'assembly'],
        'Retail': ['retail', 'store', 'shop', 'consumer', 'sales', 'merchandise']
    }
    
    for category, keywords in general_categories.items():
        category_score = sum(3 if kw in primary_text else 1 if kw in secondary_text else 0 for kw in keywords)
        if category_score >= 5:
            logger.debug(f"General classification: {category} (score: {category_score})")
            return category
    
    logger.debug("No classification found - returning 'Other'")
    return 'Other'



def scrape_companies_google(query, max_results=10):
    """
    Scrape companies using Google search for LinkedIn company pages
    """
    companies = []
    try:
        from googlesearch import search
        # Search for LinkedIn company pages
        search_query = f'site:linkedin.com/company {query}'
        logger.info(f"Searching Google for: {search_query}")
        urls = []
        # Use only supported arguments for googlesearch version
        for url in search(search_query, num_results=max_results * 3):
            if 'linkedin.com/company' in url and len(urls) < max_results * 2:
                urls.append(url)
        logger.info(f"Found {len(urls)} LinkedIn company URLs")
        for i, url in enumerate(urls[:max_results]):
            companies.append({'companyLinkedinUrl': url})
    except Exception as e:
        logger.error(f"Error in Google search: {e}")
        # Fallback: Use hardcoded LinkedIn company URLs for testing Selenium
        urls = [
            "https://uk.linkedin.com/company/microsoft",
            "https://uk.linkedin.com/company/google",
            "https://uk.linkedin.com/company/amazon"
        ]
        logger.warning(f"Using fallback LinkedIn URLs: {urls[:max_results]}")
        for url in urls[:max_results]:
            companies.append({'companyLinkedinUrl': url})
    return companies

def filter_by_criteria(companies, founded_years=None, country=None, size=None):
    """
    Filter companies based on specified criteria
    """
    filtered_companies = []
    
    for company in companies:
        # Check founded year criteria
        if founded_years:
            company_founded = company.get('founded', '')
            if company_founded:
                try:
                    founded_year = int(re.search(r'\d{4}', str(company_founded)).group())
                    if str(founded_year) not in [str(year) for year in founded_years]:
                        continue
                except:
                    pass
        
        # Check country criteria
        if country and country.lower() != 'all countries':
            company_location = company.get('location', '').lower()
            if country.lower() not in company_location:
                continue
        
        # Check size criteria
        if size and size != 'Any':
            company_size = company.get('size', '')
            if size not in company_size:
                continue
        
        filtered_companies.append(company)
    
    return filtered_companies

def extract_contact_info(website_url, company_name):
    """
    Extract contact information from company website
    """
    contact_info = {'email': '', 'phone': '', 'contact_person': ''}
    
    if not website_url:
        return contact_info
    
    try:
        # Clean and validate URL
        if not website_url.startswith(('http://', 'https://')):
            website_url = 'https://' + website_url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Try to find contact page first
        contact_urls = [
            website_url,
            urljoin(website_url, '/contact'),
            urljoin(website_url, '/contact-us'),
            urljoin(website_url, '/about'),
            urljoin(website_url, '/about-us')
        ]
        
        for url in contact_urls:
            try:
                response = requests.get(url, headers=headers, timeout=10)
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract emails
                    email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
                    emails = re.findall(email_pattern, response.text, re.IGNORECASE)
                    
                    # Filter out common non-contact emails
                    excluded_emails = ['noreply@', 'no-reply@', 'donotreply@']
                    valid_emails = [email for email in emails if not any(excluded in email.lower() for excluded in excluded_emails)]
                    
                    if valid_emails:
                        # Prefer contact, info, or hello emails
                        priority_emails = [email for email in valid_emails if any(word in email.lower() for word in ['contact', 'info', 'hello', 'support'])]
                        contact_info['email'] = priority_emails[0] if priority_emails else valid_emails[0]
                        break
                
            except Exception as e:
                logger.debug(f"Error extracting from {url}: {e}")
                continue
    
    except Exception as e:
        logger.debug(f"Error extracting contact info: {e}")
    
    return contact_info

def scrape_linkedin_company_page(url, user_agent='Mozilla/5.0', timeout=20):
    """
    Scrape a LinkedIn company page using a robust, undetectable headless Selenium setup.
    """
    logging.info(f"[Selenium] Starting undetectable headless browser for {url}")
    options = Options()
    options.add_argument('--headless=new')  # Use the new, more undetectable headless mode
    options.add_argument('--disable-gpu')
    options.add_argument("--window-size=1920,1080")
    options.add_argument(f'user-agent={user_agent}')
    options.add_argument('--no-sandbox')
    options.add_argument('--disable-dev-shm-usage')

    # Anti-detection measures
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=options)
        # Further hide automation by executing a CDP command
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {
            'source': "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        })
    except Exception as e:
        logging.error("ChromeDriver not found or not working. Please install and add to PATH.")
        return {'error': 'ChromeDriver not found or not working. Please install and add to PATH.'}
    
    driver.set_page_load_timeout(timeout)
    try:
        driver.get(url)
        logging.info("[Selenium] Page loaded")
        # --- Optional: Automate login if needed ---
        # if 'login' in driver.current_url:
        #     logging.warning('Login required. Automating login...')
        #     # TODO: Fill in your LinkedIn credentials here (store securely!)
        #     username = 'your_email'
        #     password = 'your_password'
        #     driver.find_element(By.ID, 'username').send_keys(username)
        #     driver.find_element(By.ID, 'password').send_keys(password)
        #     driver.find_element(By.XPATH, '//button[@type="submit"]').click()
        #     time.sleep(5)
        #     driver.get(url)
        #     logging.info('Logged in and retried page.')
        # --- End login block ---
        # Wait for company name
        name = ''
        try:
            name_elem = WebDriverWait(driver, timeout).until(
                EC.presence_of_element_located((By.TAG_NAME, 'h1'))
            )
            name = name_elem.text.strip()
            logging.info(f"[Selenium] Company name: {name}")
        except Exception:
            logging.warning("[Selenium] Company name not found")
        # Description
        desc = ''
        try:
            desc_elem = driver.find_element(By.XPATH, '//meta[@name="description"]')
            desc = desc_elem.get_attribute('content').strip() if desc_elem else ''
            logging.info(f"[Selenium] Description: {desc[:60]}")
        except Exception:
            logging.warning("[Selenium] Description not found")
        # Domain from URL
        domain = url.split('/')[4] if len(url.split('/')) > 4 else ''
        # Website
        website = ''
        try:
            website_links = driver.find_elements(By.XPATH, '//a[contains(@href, "http") and not(contains(@href, "linkedin.com"))]')
            for a in website_links:
                if 'website' in a.text.lower():
                    website = a.get_attribute('href')
                    break
            logging.info(f"[Selenium] Website: {website}")
        except Exception:
            logging.warning("[Selenium] Website not found")
        # Company size
        size = ''
        try:
            size_elem = driver.find_element(By.XPATH, '//*[contains(text(), "employees")]')
            size = size_elem.text.strip()
            logging.info(f"[Selenium] Size: {size}")
        except Exception:
            logging.warning("[Selenium] Size not found")
        # Location
        location = ''
        try:
            location_elem = driver.find_element(By.XPATH, '//*[contains(text(), "Headquarter") or contains(text(), "headquarter")]')
            location = location_elem.text.strip()
            logging.info(f"[Selenium] Location: {location}")
        except Exception:
            logging.warning("[Selenium] Location not found")
        # Founded year
        founded = ''
        try:
            founded_elem = driver.find_element(By.XPATH, '//*[contains(text(), "Founded")]')
            founded = founded_elem.text.strip()
            logging.info(f"[Selenium] Founded: {founded}")
        except Exception:
            logging.warning("[Selenium] Founded year not found")
        # Use improved domain classification with multiple data points
        domain_class = classify_domain(domain, name, desc)
        # Random sleep to mimic human behavior
        sleep_time = random.uniform(2, 4)
        logging.info(f"[Selenium] Sleeping for {sleep_time:.2f} seconds to mimic human behavior.")
        time.sleep(sleep_time)
        # Return result
        if not name:
            return {'error': 'Company name not found. LinkedIn may have blocked access or page structure changed.'}
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
        logging.error(f"[Selenium] Error scraping {url}: {e}")
        return {'error': str(e)}
    finally:
        driver.quit()

def run_scraper(
    keywords=None,
    founded_years=None,
    country=None,
    size=None,
    max_results=10,
    sleep_time=1.0,
    user_agent='Mozilla/5.0',
    timeout=10,
    config_path='scraper_config.json',
    output_csv='lead1.csv',
    search_func=None
):
    logger.info(f"Starting scraper with keywords: {keywords}")
    search_query = f"{keywords}"
    if country and country.lower() != 'all countries':
        search_query += f" {country}"
    logger.info("Step 1: Scraping companies from Google...")
    companies = []
    if search_func is not None:
        companies = search_func(search_query)
    else:
        companies = scrape_companies_google(search_query, max_results)
    if not companies:
        logger.warning("No companies found from Google search")
        return pd.DataFrame()
    logger.info(f"Found {len(companies)} companies from Google")
    # BYPASS FILTERING: Use all found companies for Selenium scraping
    filtered_companies = companies
    logger.info(f"Proceeding with {len(filtered_companies)} companies (filtering bypassed)")
    logger.info("Step 3: Extracting contact information...")
    results = []
    for i, company in enumerate(filtered_companies):
        logger.info(f"Processing company {i+1}/{len(filtered_companies)}: {company.get('companyLinkedinUrl')}")
        scraped = scrape_linkedin_company_page(company.get('companyLinkedinUrl'), user_agent=user_agent, timeout=timeout)
        if scraped and not scraped.get('error'):
            company.update(scraped)
        else:
            logger.warning(f"Selenium scraping failed: {scraped.get('error') if scraped else 'Unknown error'}")
        if company.get('website'):
            contact_info = extract_contact_info(company['website'], company.get('name', ''))
            company.update(contact_info)
        time.sleep(sleep_time)
        results.append(company)
    df = pd.DataFrame(results)
    required_columns = [
        'name', 'description', 'website', 'companyLinkedinUrl', 'domain', 'domain_class',
        'size', 'location', 'founded', 'email', 'contact_email', 'phone', 'contact_person'
    ]
    for col in required_columns:
        if col not in df.columns:
            df[col] = ''
    if output_csv:
        df.to_csv(output_csv, index=False)
        logger.info(f"Results saved to {output_csv}")
    logger.info(f"Scraping completed successfully. Found {len(df)} companies.")
    return df

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='LinkedIn Company Scraper')
    parser.add_argument('--keywords', type=str, default=None, help='Keywords for search')
    parser.add_argument('--founded_years', type=str, default=None, help='Comma-separated years')
    parser.add_argument('--country', type=str, default=None, help='Country')
    parser.add_argument('--size', type=str, default=None, help='Company size')
    parser.add_argument('--config_path', type=str, default='scraper_config.json', help='Config file path')
    parser.add_argument('--max_results', type=int, default=10, help='Max LinkedIn results')
    parser.add_argument('--user_agent', type=str, default='Mozilla/5.0', help='User agent')
    parser.add_argument('--timeout', type=int, default=10, help='Request timeout')
    parser.add_argument('--output_csv', type=str, default='lead1.csv', help='Output CSV file')
    parser.add_argument('--sleep_time', type=float, default=1.0, help='Sleep time between requests (seconds)')
    args = parser.parse_args()
    founded_years = args.founded_years.split(',') if args.founded_years else None
    print(f"Running scraper with keywords={args.keywords}, country={args.country}, max_results={args.max_results}")
    df = run_scraper(
        keywords=args.keywords,
        founded_years=founded_years,
        country=args.country,
        size=args.size,
        max_results=args.max_results,
        user_agent=args.user_agent,
        timeout=args.timeout,
        sleep_time=args.sleep_time
    )
    print(f"Scraped {len(df)} companies and saved to {args.output_csv}")
    print(df if not df.empty else 'No data scraped or an error occurred.')
    print('--- Script finished ---')