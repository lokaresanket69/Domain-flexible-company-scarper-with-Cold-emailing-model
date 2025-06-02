import re
import logging
import pandas as pd
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_business_activities(text):
    """
    Extract business activities and services from company descriptions
    """
    if not text or not isinstance(text, str):
        return ''
    
    text_lower = text.lower()
    
    # Business activity patterns
    activity_patterns = [
        r'we (provide|offer|deliver|specialize in|focus on) ([^.]+)',
        r'our services include ([^.]+)',
        r'(providing|offering|delivering) ([^.]+)',
        r'we are (a|an) ([^.]+) (company|firm|organization)',
        r'specializing in ([^.]+)',
        r'expert(s)? in ([^.]+)',
        r'solutions for ([^.]+)',
        r'we help (companies|businesses|organizations) ([^.]+)',
        r'our expertise in ([^.]+)',
        r'leading provider of ([^.]+)'
    ]
    
    activities = []
    for pattern in activity_patterns:
        matches = re.findall(pattern, text_lower)
        for match in matches:
            if isinstance(match, tuple):
                activity = ' '.join(match).strip()
            else:
                activity = match.strip()
            if len(activity) > 5 and len(activity) < 100:  # Filter reasonable length
                activities.append(activity)
    
    return '; '.join(activities[:3])  # Top 3 activities

def extract_keywords(text, min_word_length=3, max_keywords=10):
    """
    Enhanced keyword extraction focusing on business-relevant terms
    """
    if not text or not isinstance(text, str):
        return ''
    
    # Clean text: remove special characters and convert to lowercase
    cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words and filter
    words = cleaned_text.split()
    
    # Enhanced stop words including common company terms
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'shall', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our',
        'their', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'any',
        'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now',
        'linkedin', 'followers', 'company', 'companies', 'inc', 'ltd', 'llc', 'corp',
        'corporation', 'limited', 'group', 'international', 'global', 'worldwide'
    }
    
    # Business-relevant terms get priority
    business_priority_terms = {
        'services', 'solutions', 'consulting', 'technology', 'software', 'development',
        'management', 'digital', 'platform', 'analytics', 'innovation', 'automation',
        'strategy', 'optimization', 'intelligence', 'integration', 'implementation',
        'enterprise', 'professional', 'advanced', 'custom', 'specialist', 'expertise'
    }
    
    # Filter words: remove stop words, short words, and numbers
    filtered_words = []
    for word in words:
        if (len(word) >= min_word_length 
            and word not in stop_words 
            and not word.isdigit()
            and word.isalpha()):
            
            # Give priority to business-relevant terms
            if word in business_priority_terms:
                filtered_words.extend([word] * 2)  # Double weight
            else:
                filtered_words.append(word)
    
    # Count word frequency and get top keywords
    word_freq = Counter(filtered_words)
    top_keywords = [word for word, _ in word_freq.most_common(max_keywords)]
    
    return ', '.join(top_keywords)

def extract_technologies(text):
    """
    Enhanced technology extraction with broader coverage
    """
    if not text or not isinstance(text, str):
        return ''
    
    # Comprehensive technology keywords
    tech_categories = {
        'Programming Languages': ['python', 'java', 'javascript', 'c++', 'c#', 'php', 'ruby', 'go', 'rust', 'swift', 'kotlin', 'scala'],
        'Web Technologies': ['react', 'angular', 'vue', 'nodejs', 'html', 'css', 'bootstrap', 'jquery', 'typescript', 'webpack'],
        'Cloud Platforms': ['aws', 'azure', 'gcp', 'google cloud', 'cloud', 'kubernetes', 'docker', 'serverless', 'lambda'],
        'Databases': ['sql', 'mysql', 'postgresql', 'mongodb', 'oracle', 'redis', 'elasticsearch', 'cassandra', 'dynamodb'],
        'AI/ML': ['ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning', 'tensorflow', 'pytorch', 'nlp', 'computer vision'],
        'Mobile': ['mobile', 'ios', 'android', 'app', 'mobile app', 'flutter', 'react native', 'xamarin', 'cordova'],
        'Business Tech': ['crm', 'erp', 'saas', 'api', 'blockchain', 'iot', 'automation', 'salesforce', 'sap', 'oracle'],
        'Security': ['cybersecurity', 'security', 'encryption', 'firewall', 'penetration testing', 'ssl', 'authentication'],
        'Analytics': ['analytics', 'big data', 'data science', 'business intelligence', 'tableau', 'power bi', 'looker', 'qlik'],
        'DevOps': ['devops', 'ci/cd', 'jenkins', 'git', 'github', 'gitlab', 'terraform', 'ansible'],
        'E-commerce': ['shopify', 'magento', 'woocommerce', 'prestashop', 'bigcommerce', 'stripe', 'paypal']
    }
    
    text_lower = text.lower()
    found_technologies = []
    
    for category, techs in tech_categories.items():
        for tech in techs:
            if tech in text_lower:
                found_technologies.append(tech)
    
    # Remove duplicates and limit
    unique_techs = list(dict.fromkeys(found_technologies))
    return ', '.join(unique_techs[:8])  # Top 8 technologies

def analyze_sentiment(text):
    """
    Enhanced sentiment analysis with business context
    """
    if not text or not isinstance(text, str):
        return 'neutral'
    
    text_lower = text.lower()
    
    # Business-focused positive indicators
    positive_words = [
        'innovative', 'leading', 'growth', 'successful', 'excellent', 'outstanding',
        'best', 'top', 'premier', 'award', 'winning', 'solution', 'cutting-edge',
        'advanced', 'transform', 'optimize', 'improve', 'enhance', 'efficient',
        'expert', 'specialized', 'proven', 'trusted', 'reliable', 'quality',
        'comprehensive', 'scalable', 'robust', 'strategic', 'innovative',
        'world-class', 'industry-leading', 'state-of-the-art', 'breakthrough',
        'revolutionary', 'pioneering', 'acclaimed', 'renowned', 'prestigious'
    ]
    
    # Business-focused negative indicators
    negative_words = [
        'challenge', 'problem', 'difficult', 'struggle', 'crisis', 'decline',
        'reduce', 'cut', 'layoff', 'downsize', 'bankruptcy', 'loss', 'fail',
        'outdated', 'limited', 'basic', 'minimal', 'poor', 'weak',
        'struggling', 'failing', 'problematic', 'issues', 'concerns'
    ]
    
    # Count with context weighting
    positive_count = 0
    negative_count = 0
    
    for word in positive_words:
        if word in text_lower:
            positive_count += 1
            # Extra weight for business achievement terms
            if word in ['award', 'winning', 'leading', 'expert', 'proven', 'world-class']:
                positive_count += 1
    
    for word in negative_words:
        if word in text_lower:
            negative_count += 1
    
    # Determine sentiment with threshold
    total_indicators = positive_count + negative_count
    if total_indicators == 0:
        return 'neutral'
    
    positive_ratio = positive_count / total_indicators
    
    if positive_ratio >= 0.7:
        return 'positive'
    elif positive_ratio <= 0.3:
        return 'negative'
    else:
        return 'neutral'

def analyze_company_maturity(text, founded_year=None):
    """
    Analyze company maturity based on description language and founding year
    """
    if not text:
        return 'unknown'
    
    text_lower = text.lower()
    
    # Enhanced maturity indicators
    startup_indicators = [
        'startup', 'founded', 'new', 'emerging', 'innovative', 'disruptive',
        'young company', 'fast-growing', 'early stage', 'seed funding',
        'venture capital', 'series a', 'series b'
    ]
    
    established_indicators = [
        'established', 'leading', 'years of experience', 'decades', 'proven track record',
        'industry leader', 'market leader', 'fortune 500', 'public company',
        'global presence', 'worldwide', 'international', 'heritage', 'legacy'
    ]
    
    growth_indicators = [
        'growing', 'expanding', 'scaling', 'growth', 'rapidly expanding',
        'market expansion', 'new markets', 'acquisition', 'merger'
    ]
    
    # Score different indicators
    startup_score = sum(2 if indicator in text_lower else 0 for indicator in startup_indicators)
    established_score = sum(2 if indicator in text_lower else 0 for indicator in established_indicators)
    growth_score = sum(1 if indicator in text_lower else 0 for indicator in growth_indicators)
    
    # Factor in founding year if available
    if founded_year:
        try:
            year = int(founded_year)
            current_year = 2024
            age = current_year - year
            
            if age < 3:
                startup_score += 3
            elif age < 7:
                startup_score += 1
                growth_score += 2
            elif age < 15:
                growth_score += 2
            else:
                established_score += 3
        except (ValueError, TypeError):
            pass
    
    # Determine maturity level
    max_score = max(startup_score, established_score, growth_score)
    
    if max_score == 0:
        return 'unknown'
    elif startup_score == max_score:
        return 'startup'
    elif established_score == max_score:
        return 'established'
    else:
        return 'growth'

def extract_company_size_category(size_text):
    """
    Categorize company size into standard buckets
    """
    if not size_text:
        return 'Unknown'
    
    size_lower = size_text.lower()
    
    # Extract numbers from size text
    numbers = re.findall(r'\d+', size_text)
    
    if numbers:
        # Take the first number as approximate size
        size_num = int(numbers[0])
        
        if size_num < 10:
            return 'Micro (1-10)'
        elif size_num < 50:
            return 'Small (11-50)'
        elif size_num < 200:
            return 'Medium (51-200)'
        elif size_num < 1000:
            return 'Large (201-1000)'
        else:
            return 'Enterprise (1000+)'
    
    # Fallback to text analysis
    if any(word in size_lower for word in ['micro', 'very small']):
        return 'Micro (1-10)'
    elif any(word in size_lower for word in ['small', 'startup']):
        return 'Small (11-50)'
    elif any(word in size_lower for word in ['medium', 'mid-size']):
        return 'Medium (51-200)'
    elif any(word in size_lower for word in ['large', 'big']):
        return 'Large (201-1000)'
    elif any(word in size_lower for word in ['enterprise', 'corporate', 'multinational']):
        return 'Enterprise (1000+)'
    
    return 'Unknown'

def process_descriptions(df):
    """
    Enhanced description processing with comprehensive NLP features
    """
    if df.empty:
        return df
    
    logger.info("Processing descriptions with enhanced NLP...")
    
    # Ensure description column exists
    if 'description' not in df.columns:
        df['description'] = ''
    
    # Apply enhanced NLP processing
    df['business_activities'] = df['description'].apply(extract_business_activities)
    df['keywords'] = df['description'].apply(extract_keywords)
    df['technologies'] = df['description'].apply(extract_technologies)
    df['sentiment'] = df['description'].apply(analyze_sentiment)
    df['description_length'] = df['description'].apply(lambda x: len(str(x)) if x else 0)
    df['company_maturity'] = df.apply(lambda row: analyze_company_maturity(row.get('description', ''), row.get('founded', '')), axis=1)
    
    # Enhanced size categorization
    if 'size' in df.columns:
        df['size_category'] = df['size'].apply(extract_company_size_category)
    
    # Add word count and readability metrics
    df['word_count'] = df['description'].apply(lambda x: len(str(x).split()) if x else 0)
    df['sentence_count'] = df['description'].apply(lambda x: len(re.split(r'[.!?]+', str(x))) if x else 0)
    df['avg_words_per_sentence'] = df.apply(lambda row: row['word_count'] / max(row['sentence_count'], 1), axis=1)
    
    logger.info("Enhanced NLP processing completed")
    return df

def get_enhanced_analytics_summary(df):
    """
    Generate comprehensive analytics summary from processed data
    """
    if df.empty:
        return {}
    
    summary = {
        'total_companies': len(df),
        'sentiment_distribution': df['sentiment'].value_counts().to_dict() if 'sentiment' in df.columns else {},
        'domain_class_distribution': df['domain_class'].value_counts().to_dict() if 'domain_class' in df.columns else {},
        'maturity_distribution': df['company_maturity'].value_counts().to_dict() if 'company_maturity' in df.columns else {},
        'size_distribution': df['size_category'].value_counts().to_dict() if 'size_category' in df.columns else {},
        'avg_description_length': df['description_length'].mean() if 'description_length' in df.columns else 0,
        'avg_word_count': df['word_count'].mean() if 'word_count' in df.columns else 0,
        'companies_with_websites': len(df[df['website'].notna() & (df['website'] != '')]) if 'website' in df.columns else 0,
        'companies_with_contact_info': len(df[(df['email'].notna() & (df['email'] != '')) | (df['phone'].notna() & (df['phone'] != ''))]) if 'email' in df.columns else 0,
        'top_keywords': [],
        'top_technologies': [],
        'top_business_activities': [],
        'location_distribution': {},
        'founded_year_distribution': {}
    }
    
    # Extract top keywords across all companies
    if 'keywords' in df.columns:
        all_keywords = []
        for keywords_str in df['keywords'].dropna():
            all_keywords.extend([k.strip() for k in str(keywords_str).split(',') if k.strip()])
        if all_keywords:
            keyword_freq = Counter(all_keywords)
            summary['top_keywords'] = [{'keyword': k, 'count': v} for k, v in keyword_freq.most_common(10)]
    
    # Extract top technologies
    if 'technologies' in df.columns:
        all_technologies = []
        for tech_str in df['technologies'].dropna():
            all_technologies.extend([t.strip() for t in str(tech_str).split(',') if t.strip()])
        if all_technologies:
            tech_freq = Counter(all_technologies)
            summary['top_technologies'] = [{'tech': t, 'count': c} for t, c in tech_freq.most_common(10)]
    
    # Extract top business activities
    if 'business_activities' in df.columns:
        all_activities = []
        for activity_str in df['business_activities'].dropna():
            all_activities.extend([a.strip() for a in str(activity_str).split(';') if a.strip()])
        if all_activities:
            activity_freq = Counter(all_activities)
            summary['top_business_activities'] = [{'activity': a, 'count': c} for a, c in activity_freq.most_common(5)]
    
    # Location distribution
    if 'location' in df.columns:
        locations = df['location'].dropna()
        location_freq = Counter(locations)
        summary['location_distribution'] = dict(location_freq.most_common(10))
    
    # Founded year distribution
    if 'founded' in df.columns:
        founded_years = df['founded'].dropna()
        year_freq = Counter(founded_years)
        summary['founded_year_distribution'] = dict(year_freq.most_common(10))
    
    return summary

# Keep the original functions for backward compatibility
def get_analytics_summary(df):
    """Original analytics summary function - kept for compatibility"""
    return get_enhanced_analytics_summary(df)