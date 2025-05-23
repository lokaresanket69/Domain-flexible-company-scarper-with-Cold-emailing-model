import re
import logging
import pandas as pd
from collections import Counter

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def extract_keywords(text, min_word_length=3, max_keywords=10):
    """
    Extract relevant keywords from text using simple text processing
    """
    if not text or not isinstance(text, str):
        return ''
    
    # Clean text: remove special characters and convert to lowercase
    cleaned_text = re.sub(r'[^\w\s]', ' ', text.lower())
    
    # Split into words and filter
    words = cleaned_text.split()
    
    # Common stop words to exclude
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
        'by', 'is', 'are', 'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had',
        'do', 'does', 'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
        'can', 'shall', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it',
        'we', 'they', 'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our',
        'their', 'what', 'which', 'who', 'when', 'where', 'why', 'how', 'all', 'any',
        'both', 'each', 'few', 'more', 'most', 'other', 'some', 'such', 'no', 'nor',
        'not', 'only', 'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now',
        'linkedin', 'followers', 'company', 'companies'
    }
    
    # Filter words: remove stop words, short words, and numbers
    filtered_words = [
        word for word in words 
        if len(word) >= min_word_length 
        and word not in stop_words 
        and not word.isdigit()
        and word.isalpha()
    ]
    
    # Count word frequency and get top keywords
    word_freq = Counter(filtered_words)
    top_keywords = [word for word, _ in word_freq.most_common(max_keywords)]
    
    return ', '.join(top_keywords)

def extract_technologies(text):
    """
    Extract technology-related keywords from text
    """
    if not text or not isinstance(text, str):
        return ''
    
    # Common technology keywords to look for
    tech_keywords = {
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'deep learning',
        'cloud', 'aws', 'azure', 'gcp', 'kubernetes', 'docker',
        'python', 'java', 'javascript', 'react', 'angular', 'vue',
        'blockchain', 'cryptocurrency', 'fintech', 'api', 'saas',
        'mobile', 'ios', 'android', 'app', 'web', 'frontend', 'backend',
        'data', 'analytics', 'big data', 'database', 'sql', 'nosql',
        'cybersecurity', 'security', 'encryption', 'firewall'
    }
    
    text_lower = text.lower()
    found_technologies = []
    
    for tech in tech_keywords:
        if tech in text_lower:
            found_technologies.append(tech)
    
    return ', '.join(found_technologies[:5])  # Limit to top 5

def analyze_sentiment(text):
    """
    Simple sentiment analysis based on keyword presence
    """
    if not text or not isinstance(text, str):
        return 'neutral'
    
    text_lower = text.lower()
    
    # Positive indicators
    positive_words = [
        'innovative', 'leading', 'growth', 'successful', 'excellent', 'outstanding',
        'best', 'top', 'premier', 'award', 'winning', 'solution', 'cutting-edge',
        'advanced', 'transform', 'optimize', 'improve', 'enhance', 'efficient'
    ]
    
    # Negative indicators
    negative_words = [
        'challenge', 'problem', 'difficult', 'struggle', 'crisis', 'decline',
        'reduce', 'cut', 'layoff', 'downsize', 'bankruptcy', 'loss', 'fail'
    ]
    
    positive_count = sum(1 for word in positive_words if word in text_lower)
    negative_count = sum(1 for word in negative_words if word in text_lower)
    
    if positive_count > negative_count:
        return 'positive'
    elif negative_count > positive_count:
        return 'negative'
    else:
        return 'neutral'

def process_descriptions(df):
    """
    Process DataFrame with company descriptions to add NLP features
    """
    if df.empty:
        return df
    
    logger.info("Processing descriptions with NLP...")
    
    # Ensure description column exists
    if 'description' not in df.columns:
        df['description'] = ''
    
    # Apply NLP processing
    df['keywords'] = df['description'].apply(extract_keywords)
    df['technologies'] = df['description'].apply(extract_technologies)
    df['sentiment'] = df['description'].apply(analyze_sentiment)
    df['description_length'] = df['description'].apply(lambda x: len(str(x)) if x else 0)
    
    logger.info("NLP processing completed")
    return df

def get_analytics_summary(df):
    """
    Generate analytics summary from processed data
    """
    if df.empty:
        return {}
    
    summary = {
        'total_companies': len(df),
        'sentiment_distribution': df['sentiment'].value_counts().to_dict() if 'sentiment' in df.columns else {},
        'domain_class_distribution': df['domain_class'].value_counts().to_dict() if 'domain_class' in df.columns else {},
        'avg_description_length': df['description_length'].mean() if 'description_length' in df.columns else 0,
        'top_keywords': [],
        'top_technologies': []
    }
    
    # Extract top keywords across all companies
    if 'keywords' in df.columns:
        all_keywords = []
        for keywords_str in df['keywords'].dropna():
            all_keywords.extend([k.strip() for k in str(keywords_str).split(',') if k.strip()])
        if all_keywords:
            keyword_freq = Counter(all_keywords)
            summary['top_keywords'] = [k for k, _ in keyword_freq.most_common(10)]
    
    # Extract top technologies across all companies
    if 'technologies' in df.columns:
        all_technologies = []
        for tech_str in df['technologies'].dropna():
            all_technologies.extend([t.strip() for t in str(tech_str).split(',') if t.strip()])
        if all_technologies:
            tech_freq = Counter(all_technologies)
            summary['top_technologies'] = [t for t, _ in tech_freq.most_common(10)]
    
    return summary
