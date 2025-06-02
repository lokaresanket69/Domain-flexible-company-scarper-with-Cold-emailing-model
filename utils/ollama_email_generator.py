import subprocess
import json
import logging
import pandas as pd
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class OllamaEmailGenerator:
    """
    Generate personalized emails using Ollama models based on scraped company data
    """
    
    def __init__(self, model_name='mistral'):
        self.model_name = model_name
        self.company_name = "Prabisha Consulting"
        
    def check_ollama_availability(self) -> bool:
        """Check if Ollama is available and running"""
        try:
            # Try to ping ollama service first
            result = subprocess.run(['which', 'ollama'], capture_output=True, timeout=5)
            if result.returncode != 0:
                return False
            
            # Then check if it can list models
            result = subprocess.run(['ollama', 'list'], capture_output=True, timeout=10)
            return result.returncode == 0
        except FileNotFoundError:
            logger.error("Ollama command not found. Please install Ollama first.")
            return False
        except Exception as e:
            logger.error(f"Ollama not available: {e}")
            return False
    
    def generate_email_for_company(self, company_data: Dict) -> str:
        """
        Generate a personalized email for a single company
        """
        company = company_data.get('name', '').strip()
        description = company_data.get('description', '').strip()
        industry = company_data.get('domain_class', '').strip()
        size = company_data.get('size', '').strip()
        location = company_data.get('location', '').strip()
        region = company_data.get('region', '').strip()
        
        prompt = f"""
You are an AI sales assistant from {self.company_name}.

Write a friendly and personalized cold outreach email to the company below, explaining how we can help them with automation, AI-driven efficiency, or digital transformation services.

Make the email clear, concise, and relevant to their business description. Avoid sounding too generic.

Company Name: {company}
Industry: {industry}
Company Size: {size}
Location: {location}
Region: {region}
What They Do: {description}

Write a professional email that:
1. Has a compelling subject line
2. Shows you've researched their company
3. Explains how our services can benefit their specific industry
4. Includes a clear call to action
5. Keeps it under 200 words

Email Format:
Subject: [Subject Line]

Dear [Company] Team,

[Email Body]

Best regards,
{self.company_name} Team

Email:
"""

        try:
            result = subprocess.run(
                ['ollama', 'run', self.model_name],
                input=prompt.encode('utf-8'),
                capture_output=True,
                timeout=60
            )
            
            if result.returncode == 0:
                output = result.stdout.decode('utf-8', errors='ignore').strip()
                return output
            else:
                error_msg = result.stderr.decode('utf-8', errors='ignore')
                logger.error(f"Ollama error: {error_msg}")
                return f"Error generating email: {error_msg}"
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout generating email for {company}")
            return "Error: Email generation timed out"
        except Exception as e:
            logger.error(f"Error generating email for {company}: {e}")
            return f"Error: {str(e)}"
    
    def generate_emails_for_companies(self, companies_data: List[Dict], delay_seconds: float = 2.0) -> List[Dict]:
        """
        Generate emails for multiple companies with optional delay between requests
        """
        results = []
        
        for i, company_data in enumerate(companies_data):
            company_name = company_data.get('name', f'Company {i+1}')
            logger.info(f"Generating email for {company_name} ({i+1}/{len(companies_data)})")
            
            generated_email = self.generate_email_for_company(company_data)
            
            result = {
                'company_id': company_data.get('id'),
                'company': company_name,
                'description': company_data.get('description', ''),
                'email': company_data.get('email', ''),
                'contact_email': company_data.get('contact_email', ''),
                'generated_email': generated_email,
                'generation_status': 'success' if not generated_email.startswith('Error') else 'error'
            }
            
            results.append(result)
            
            # Add delay between requests to avoid overwhelming the system
            if i < len(companies_data) - 1 and delay_seconds > 0:
                import time
                time.sleep(delay_seconds)
        
        return results
    
    def save_generated_emails_to_csv(self, results: List[Dict], output_file: str = 'generated_emails.csv') -> str:
        """
        Save generated emails to CSV file
        """
        try:
            df = pd.DataFrame(results)
            df.to_csv(output_file, index=False)
            logger.info(f"Generated emails saved to {output_file}")
            return output_file
        except Exception as e:
            logger.error(f"Error saving emails to CSV: {e}")
            raise
    
    def get_companies_without_emails(self, companies_data: List[Dict]) -> List[Dict]:
        """
        Filter companies that don't have generated emails yet
        """
        return [company for company in companies_data 
                if not company.get('generated_email') or company.get('generated_email', '').strip() == '']