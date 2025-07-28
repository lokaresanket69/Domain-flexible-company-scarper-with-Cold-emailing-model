from groq import Groq
import os
import logging
import re
from typing import List, Dict, Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GroqEmailGenerator:
    """
    Generate personalized emails using the Groq API from "Prabisha Consulting Pvt. Ltd."
    based on scraped company data.
    """
    def __init__(self, api_key: Optional[str] = None):
        # Use provided API key or get from environment variable
        self.api_key = api_key or os.environ.get("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("Groq API key is required. Provide it as an argument or set the GROQ_API_KEY environment variable.")
        try:
            # Initialize Groq client with only the api_key parameter
            self.client = Groq(api_key=self.api_key)
        except Exception as e:
            logger.error(f"Failed to initialize Groq client: {str(e)}")
            raise

    def generate_email(self, company_data: Dict, from_company: str = "Prabisha Consulting Pvt. Ltd.") -> str:
        """
        Generate a personalized email for a single company using Groq.
        """
        if not isinstance(company_data, dict):
            logger.error(f"Invalid company data provided: {company_data}")
            return "Error: Invalid company data format."

        # Extract relevant details from the company data
        company_name = company_data.get('name', 'your company')
        description = company_data.get('description', 'your business')
        website = company_data.get('website', 'your website')

        # Create a detailed prompt for Groq
        prompt = f"""
        Subject: Collaboration Inquiry from {from_company}

        Dear {company_name} Team,

        I am writing to you from {from_company}, a consulting firm specializing in helping businesses like yours achieve excellence. After reviewing your work and your website ({website}), I was impressed by your focus on {description}.

        Generate a personalized email that includes the following:
        1. A brief, compelling introduction to {from_company}.
        2. A sentence that shows we have researched {company_name} by referencing their description.
        3. A clear value proposition tailored to their business.
        4. A call to action for a brief introductory call.

        Keep the tone professional, concise, and engaging. The email should be no more than 150 words.
        """

        try:
            chat_completion = self.client.chat.completions.create(
                messages=[{"role": "user", "content": prompt}],
                model="llama3-8b-8192",  # Or another suitable model
            )
            generated_email = chat_completion.choices[0].message.content
            return generated_email
        except Exception as e:
            logger.error(f"Error generating email with Groq: {e}")
            return f"Error: Could not generate email. Details: {e}"

    def generate_bulk_emails(self, companies_data: List[Dict], from_company: str = "Prabisha Consulting Pvt. Ltd.") -> List[str]:
        """
        Generate personalized emails for a list of companies.
        """
        return [self.generate_email(company, from_company) for company in companies_data]

if __name__ == '__main__':
    # --- Example Usage ---
    # Make sure to set your GROQ_API_KEY in your environment variables,
    # or pass it directly to the GroqEmailGenerator.
    # e.g., export GROQ_API_KEY='your-api-key'

    try:
        email_generator = GroqEmailGenerator()
        
        # Example company data (replace with your scraped data)
        sample_company = {
            'name': 'Innovate Inc.',
            'description': 'cutting-edge AI solutions for the healthcare industry',
            'website': 'https://innovateinc.com'
        }
        
        # Generate a single email
        personalized_email = email_generator.generate_email(sample_company)
        
        print("--- Generated Personalized Email ---")
        print(personalized_email)
        print("---------------------------------")
        
    except ValueError as e:
        print(e)
    except Exception as e:
        print(f"An unexpected error occurred: {e}") 