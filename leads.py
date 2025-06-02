import json
import pandas as pd
import requests
import time
import logging
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def classify_domain(domain, company_name='', description=''):
    """
    Enhanced domain classification that focuses on business activities rather than company names
    Uses contextual analysis to determine actual business domain
    """
    # Ensure we're working with lowercase strings
    domain = (domain or '').lower()
    company_name = (company_name or '').lower()
    description = (description or '').lower()
    
    # Prioritize description for classification (main business activity source)
    primary_text = description
    secondary_text = f"{domain} {company_name}"
    
    # Enhanced industry categories with business activity indicators
    industry_categories = {
        # Technology & IT
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
        
        # Finance & FinTech
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
        
        # Real Estate & Property
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
        
        # Healthcare
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
        
        # Marketing & Media
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
        
        # E-commerce & Retail
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
        
        # Professional Services
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
        
        # Manufacturing & Industrial
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
        
        # Education & Training
        'Education': {
            'primary': ['educational services', 'training services', 'e-learning', 'corporate training', 'educational technology'],
            'secondary': ['education', 'training', 'learning', 'teaching'],
            'context': ['learn', 'teach', 'students', 'courses', 'knowledge']
        },
        'EdTech': {
            'primary': ['educational technology', 'e-learning platform', 'online education', 'learning management'],
            'secondary': ['edtech', 'e-learning', 'educational tech'],
            'context': ['learning', 'education', 'students', 'online', 'platform']
        },
        
        # Food & Beverage
        'Food & Beverage': {
            'primary': ['food services', 'restaurant', 'catering', 'food production', 'beverage manufacturing'],
            'secondary': ['food', 'beverage', 'restaurant', 'catering'],
            'context': ['cuisine', 'dining', 'cooking', 'nutrition', 'hospitality']
        },
        
        # Travel & Tourism
        'Travel & Tourism': {
            'primary': ['travel services', 'tourism', 'travel agency', 'hospitality services', 'tour operator'],
            'secondary': ['travel', 'tourism', 'hotel', 'hospitality'],
            'context': ['vacation', 'destination', 'booking', 'accommodation', 'leisure']
        },
        
        # Entertainment & Media
        'Entertainment': {
            'primary': ['entertainment services', 'media production', 'content creation', 'gaming', 'sports entertainment'],
            'secondary': ['entertainment', 'media', 'gaming', 'sports'],
            'context': ['content', 'production', 'creative', 'audience', 'performance']
        },
        
        # Automotive
        'Automotive': {
            'primary': ['automotive services', 'car dealership', 'auto repair', 'automotive manufacturing'],
            'secondary': ['automotive', 'auto', 'vehicle', 'car'],
            'context': ['vehicles', 'driving', 'transportation', 'mobility', 'automotive']
        },
        
        # Energy & Utilities
        'Energy': {
            'primary': ['energy services', 'renewable energy', 'power generation', 'utility services', 'energy consulting'],
            'secondary': ['energy', 'power', 'utility', 'electricity', 'renewable'],
            'context': ['generation', 'distribution', 'sustainable', 'grid', 'consumption']
        },
        
        # Agriculture
        'Agriculture': {
            'primary': ['agricultural services', 'farming', 'crop production', 'livestock', 'agribusiness'],
            'secondary': ['agriculture', 'farming', 'agricultural', 'crop'],
            'context': ['cultivation', 'harvest', 'livestock', 'rural', 'sustainable']
        },
        
        # Telecommunications
        'Telecommunications': {
            'primary': ['telecommunications services', 'telecom', 'network provider', 'communication services'],
            'secondary': ['telecom', 'telecommunications', 'network', 'communication'],
            'context': ['connectivity', 'infrastructure', 'wireless', 'broadband', 'communication']
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
    
    # Fallback to general categories if no specific match
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

def extract_contact_info(company_url, company_name):
    """
    Extract contact information from company website
    """
    contact_info = {'email': '', 'phone': '', 'contact_person': ''}
    
    if not company_url:
        return contact_info
    
    try:
        # Clean and validate URL
        if not company_url.startswith(('http://', 'https://')):
            company_url = 'https://' + company_url
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(company_url, headers=headers, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            text_content = soup.get_text().lower()
            
            # Extract emails
            email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
            emails = re.findall(email_pattern, response.text, re.IGNORECASE)
            
            # Filter out common non-contact emails
            excluded_emails = ['info@', 'contact@', 'support@', 'admin@', 'webmaster@', 'noreply@']
            valid_emails = []
            
            for email in emails:
                email_lower = email.lower()
                if not any(excluded in email_lower for excluded in excluded_emails):
                    valid_emails.append(email)
            
            if valid_emails:
                contact_info['email'] = valid_emails[0]
            elif emails:  # Use any email if no specific contact emails found
                contact_info['email'] = emails[0]
            
            # Extract phone numbers
            phone_patterns = [
                r'\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}',  # US format
                r'\+?44[-.\s]?[0-9]{4}[-.\s]?[0-9]{6}',  # UK format
                r'\+?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,4}[-.\s]?[0-9]{1,9}'  # International
            ]
            
            for pattern in phone_patterns:
                phones = re.findall(pattern, response.text)
                if phones:
                    contact_info['phone'] = phones[0]
                    break
            
            # Try to extract contact person name
            contact_sections = soup.find_all(['div', 'section'], class_=re.compile(r'contact|team|about', re.I))
            for section in contact_sections:
                section_text = section.get_text()
                # Look for patterns like "Contact: John Doe" or "CEO: Jane Smith"
                name_patterns = [
                    r'(?:contact|ceo|founder|director|manager|owner)[:]\s*([A-Z][a-z]+\s+[A-Z][a-z]+)',
                    r'([A-Z][a-z]+\s+[A-Z][a-z]+)(?:\s*[-,]\s*(?:ceo|founder|director|manager|owner))'
                ]
                
                for pattern in name_patterns:
                    matches = re.findall(pattern, section_text, re.IGNORECASE)
                    if matches:
                        contact_info['contact_person'] = matches[0]
                        break
                
                if contact_info['contact_person']:
                    break
        
    except Exception as e:
        logger.debug(f"Error extracting contact info from {company_url}: {e}")
    
    return contact_info

def scrape_companies_google(query, max_results=10):
    """
    Scrape companies using Google search with enhanced data extraction
    """
    companies = []
    
    try:
        from googlesearch import search
        
        # Enhanced search query for LinkedIn company pages
        search_query = f'site:linkedin.com/company {query}'
        
        logger.info(f"Searching Google for: {search_query}")
        
        urls = []
        for url in search(search_query, num_results=max_results * 3, stop=max_results * 3):
            if 'linkedin.com/company' in url and len(urls) < max_results * 2:
                urls.append(url)
        
        logger.info(f"Found {len(urls)} LinkedIn company URLs")
        
        for i, url in enumerate(urls[:max_results]):
            try:
                logger.info(f"Processing company {i+1}/{min(max_results, len(urls))}: {url}")
                
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                
                response = requests.get(url, headers=headers, timeout=15)
                
                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')
                    
                    # Extract company data
                    company_data = {
                        'companyLinkedinUrl': url,
                        'name': '',
                        'description': '',
                        'website': '',
                        'domain': '',
                        'size': '',
                        'location': '',
                        'founded': '',
                        'email': '',
                        'contact_email': '',
                        'phone': '',
                        'contact_person': ''
                    }
                    
                    # Extract company name
                    name_selectors = [
                        'h1.org-top-card-summary__title',
                        'h1[data-test-id="org-name"]',
                        '.org-top-card-summary__title',
                        'h1.t-24'
                    ]
                    
                    for selector in name_selectors:
                        name_elem = soup.select_one(selector)
                        if name_elem:
                            company_data['name'] = name_elem.get_text().strip()
                            break
                    
                    # Extract description
                    desc_selectors = [
                        '.org-top-card-summary__tagline',
                        '.org-about-us-organization-description__text',
                        '[data-test-id="about-us__description"]'
                    ]
                    
                    for selector in desc_selectors:
                        desc_elem = soup.select_one(selector)
                        if desc_elem:
                            company_data['description'] = desc_elem.get_text().strip()
                            break
                    
                    # Extract website
                    website_selectors = [
                        'a[data-test-id="about-us__website"]',
                        '.org-about-us-organization-description__website a'
                    ]
                    
                    for selector in website_selectors:
                        website_elem = soup.select_one(selector)
                        if website_elem:
                            website_url = website_elem.get('href', '')
                            if website_url:
                                # Clean up LinkedIn redirect URLs
                                if 'linkedin.com/redir/redirect' in website_url:
                                    import urllib.parse
                                    parsed = urllib.parse.parse_qs(urllib.parse.urlparse(website_url).query)
                                    if 'url' in parsed:
                                        website_url = parsed['url'][0]
                                
                                company_data['website'] = website_url
                                
                                # Extract domain
                                try:
                                    domain = urlparse(website_url).netloc
                                    company_data['domain'] = domain.replace('www.', '')
                                except:
                                    pass
                                break
                    
                    # Extract company size
                    size_elem = soup.find(string=re.compile(r'\d+.*employees'))
                    if size_elem:
                        company_data['size'] = size_elem.strip()
                    
                    # Extract location
                    location_selectors = [
                        '.org-top-card-summary__headquarter',
                        '[data-test-id="about-us__headquarters"]'
                    ]
                    
                    for selector in location_selectors:
                        location_elem = soup.select_one(selector)
                        if location_elem:
                            company_data['location'] = location_elem.get_text().strip()
                            break
                    
                    # Extract founded year
                    founded_elem = soup.find(string=re.compile(r'Founded.*\d{4}'))
                    if founded_elem:
                        founded_match = re.search(r'\d{4}', founded_elem)
                        if founded_match:
                            company_data['founded'] = founded_match.group()
                    
                    # Enhanced domain classification
                    if company_data['name'] or company_data['description']:
                        domain_class = classify_domain(
                            domain=company_data['domain'],
                            company_name=company_data['name'],
                            description=company_data['description']
                        )
                        company_data['domain_class'] = domain_class
                    
                    # Extract contact information from company website
                    if company_data['website']:
                        contact_info = extract_contact_info(company_data['website'], company_data['name'])
                        company_data.update(contact_info)
                    
                    # Only add if we have meaningful data
                    if company_data['name'] and (company_data['description'] or company_data['website']):
                        companies.append(company_data)
                        logger.info(f"Successfully extracted data for: {company_data['name']}")
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                logger.error(f"Error processing {url}: {e}")
                continue
    
    except Exception as e:
        logger.error(f"Error in Google search: {e}")
    
    return companies

def filter_by_criteria(companies, founded_years=None, country=None, size=None):
    """
    Filter companies based on specified criteria
    """
    filtered_companies = []
    
    for company in companies:
        # Check founded year criteria
        if founded_years:
            company_year = company.get('founded', '')
            if company_year and not any(year in company_year for year in founded_years):
                continue
        
        # Check country criteria
        if country and country.lower() != 'all countries':
            company_location = company.get('location', '').lower()
            if country.lower() not in company_location:
                continue
        
        # Check size criteria
        if size and size != 'All Sizes':
            company_size = company.get('size', '')
            if size not in company_size:
                continue
        
        filtered_companies.append(company)
    
    return filtered_companies

def run_scraper(keywords, founded_years, country, size, max_results=10, sleep_time=1.0):
    """
    Main scraper function with enhanced filtering and data extraction
    """
    logger.info(f"Starting enhanced scrape for keywords: {keywords}")
    logger.info(f"Criteria - Years: {founded_years}, Country: {country}, Size: {size}")
    
    all_companies = []
    
    try:
        # Search for companies
        companies = scrape_companies_google(keywords, max_results)
        
        if companies:
            # Apply filtering criteria
            filtered_companies = filter_by_criteria(
                companies=companies,
                founded_years=founded_years,
                country=country,
                size=size
            )
            
            logger.info(f"Found {len(companies)} companies, {len(filtered_companies)} match criteria")
            
            # Limit to max_results
            final_companies = filtered_companies[:max_results]
            
            all_companies.extend(final_companies)
        
        # Convert to DataFrame
        if all_companies:
            df = pd.DataFrame(all_companies)
            
            # Add timestamp
            df['scraped_at'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            logger.info(f"Enhanced scraping completed. Found {len(df)} companies.")
            return df
        else:
            logger.warning("No companies found matching criteria.")
            return pd.DataFrame()
            
    except Exception as e:
        logger.error(f"Error in run_scraper: {e}")
        return pd.DataFrame()

def export_to_csv(companies_df, filename='linkedin_companies.csv'):
    """
    Export companies data to CSV file
    """
    try:
        companies_df.to_csv(filename, index=False)
        logger.info(f"Data exported to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Error exporting to CSV: {e}")
        return None

def load_from_csv(filename='linkedin_companies.csv'):
    """
    Load companies data from CSV file
    """
    try:
        if os.path.exists(filename):
            df = pd.read_csv(filename)
            logger.info(f"Loaded {len(df)} companies from {filename}")
            return df
        else:
            logger.warning(f"File {filename} not found")
            return pd.DataFrame()
    except Exception as e:
        logger.error(f"Error loading from CSV: {e}")
        return pd.DataFrame()

# Test function
if __name__ == "__main__":
    # Test the enhanced scraper
    test_keywords = "real estate"
    test_years = ["2020", "2021"]
    test_country = "United Kingdom"
    test_size = "51-200"
    
    logger.info("Testing enhanced LinkedIn scraper...")
    
    results = run_scraper(
        keywords=test_keywords,
        founded_years=test_years,
        country=test_country,
        size=test_size,
        max_results=5
    )
    
    if not results.empty:
        print(f"\nFound {len(results)} companies:")
        for _, company in results.iterrows():
            print(f"- {company['name']} ({company['domain_class']})")
            print(f"  Description: {company['description'][:100]}...")
            print(f"  Website: {company['website']}")
            print()
        
        # Export results
        export_to_csv(results, 'test_results.csv')
    else:
        print("No companies found")