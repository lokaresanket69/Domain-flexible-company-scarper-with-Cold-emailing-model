from app import db
from datetime import datetime

class Company(db.Model):
    """Enhanced model for storing LinkedIn company data with new classification fields"""
    __tablename__ = 'companies'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    website = db.Column(db.String(255))
    linkedin_url = db.Column(db.String(255), unique=True)
    domain = db.Column(db.String(100))
    domain_class = db.Column(db.String(50))
    size = db.Column(db.String(100))
    location = db.Column(db.Text)
    region = db.Column(db.String(100))  # New field for region filtering
    founded = db.Column(db.Text)
    keywords = db.Column(db.Text)
    technologies = db.Column(db.Text)
    sentiment = db.Column(db.String(20))
    description_length = db.Column(db.Integer)
    
    # NEW ENHANCED FIELDS
    business_activities = db.Column(db.Text)  # Extracted business activities
    company_maturity = db.Column(db.String(20))  # startup, growth, established
    classification_confidence = db.Column(db.Integer)  # Classification confidence score
    industry_tags = db.Column(db.Text)  # Multiple industry tags
    
    # Email and contact fields
    email = db.Column(db.String(255))
    contact_email = db.Column(db.String(255))
    phone = db.Column(db.String(100))
    contact_person = db.Column(db.String(255))
    
    # Email generation tracking
    generated_email = db.Column(db.Text)
    email_sent = db.Column(db.Boolean, default=False)
    email_sent_at = db.Column(db.DateTime)
    scraped_at = db.Column(db.DateTime, default=datetime.now)
    
    def __repr__(self):
        return f'<Company {self.name}>'
    
    def to_dict(self):
        """Convert Company object to dictionary with enhanced fields"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'website': self.website,
            'companyLinkedinUrl': self.linkedin_url,
            'domain': self.domain,
            'domain_class': self.domain_class,
            'size': self.size,
            'location': self.location,
            'region': self.region,
            'founded': self.founded,
            'keywords': self.keywords,
            'technologies': self.technologies,
            'sentiment': self.sentiment,
            'description_length': self.description_length,
            'business_activities': self.business_activities,
            'company_maturity': self.company_maturity,
            'classification_confidence': self.classification_confidence,
            'industry_tags': self.industry_tags,
            'email': self.email,
            'contact_email': self.contact_email,
            'phone': self.phone,
            'contact_person': self.contact_person,
            'generated_email': self.generated_email,
            'email_sent': self.email_sent,
            'email_sent_at': self.email_sent_at.strftime('%Y-%m-%d %H:%M:%S') if self.email_sent_at else None,
            'scraped_at': self.scraped_at.strftime('%Y-%m-%d %H:%M:%S') if self.scraped_at else None
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create Company object from dictionary with enhanced fields"""
        return cls(
            name=data.get('name', ''),
            description=data.get('description', ''),
            website=data.get('website', ''),
            linkedin_url=data.get('companyLinkedinUrl', ''),
            domain=data.get('domain', ''),
            domain_class=data.get('domain_class', ''),
            size=data.get('size', ''),
            location=data.get('location', ''),
            region=data.get('region', ''),
            founded=data.get('founded', ''),
            keywords=data.get('keywords', ''),
            technologies=data.get('technologies', ''),
            sentiment=data.get('sentiment', ''),
            description_length=data.get('description_length', 0),
            business_activities=data.get('business_activities', ''),
            company_maturity=data.get('company_maturity', ''),
            classification_confidence=data.get('classification_confidence', 0),
            industry_tags=data.get('industry_tags', ''),
            email=data.get('email', ''),
            contact_email=data.get('contact_email', ''),
            phone=data.get('phone', ''),
            contact_person=data.get('contact_person', ''),
            scraped_at=datetime.now()
        )

    def get_primary_email(self):
        """Get the primary email address for this company"""
        return self.contact_email or self.email or ''
    
    def has_contact_info(self):
        """Check if company has any contact information"""
        return bool(self.email or self.contact_email or self.phone)
    
    def get_display_location(self):
        """Get formatted location for display"""
        if self.region and self.location:
            return f"{self.region}, {self.location}"
        return self.location or self.region or 'Unknown'
    
    def get_age_years(self):
        """Calculate company age in years"""
        if not self.founded:
            return None
        
        try:
            founded_year = int(self.founded)
            current_year = datetime.now().year
            return current_year - founded_year
        except (ValueError, TypeError):
            return None
    
    def is_startup(self):
        """Check if company is considered a startup (less than 5 years old)"""
        age = self.get_age_years()
        return age is not None and age < 5
    
    def get_confidence_level(self):
        """Get confidence level as text"""
        if not self.classification_confidence:
            return 'Unknown'
        
        confidence = self.classification_confidence
        if confidence >= 80:
            return 'High'
        elif confidence >= 60:
            return 'Medium'
        elif confidence >= 40:
            return 'Low'
        else:
            return 'Very Low'
    
    def update_from_dict(self, data):
        """Update company fields from dictionary"""
        updatable_fields = [
            'name', 'description', 'website', 'domain', 'domain_class',
            'size', 'location', 'region', 'founded', 'keywords', 'technologies',
            'sentiment', 'description_length', 'business_activities',
            'company_maturity', 'classification_confidence', 'industry_tags',
            'email', 'contact_email', 'phone', 'contact_person'
        ]
        
        for field in updatable_fields:
            if field in data and hasattr(self, field):
                setattr(self, field, data[field])