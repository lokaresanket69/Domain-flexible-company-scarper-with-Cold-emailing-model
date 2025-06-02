import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import logging
from typing import Dict, List, Optional
import re

logger = logging.getLogger(__name__)

class CPanelEmailSender:
    """
    Send personalized emails through cPanel webmail using SMTP
    """
    
    def __init__(self, smtp_server: str, smtp_port: int, email: str, password: str):
        self.smtp_server = smtp_server
        self.smtp_port = smtp_port
        self.email = email
        self.password = password
        self.sender_name = "Prabisha Consulting"
        
    def test_connection(self) -> bool:
        """Test SMTP connection to cPanel"""
        try:
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                logger.info("SMTP connection successful")
                return True
        except Exception as e:
            logger.error(f"SMTP connection failed: {e}")
            return False
    
    def parse_generated_email(self, generated_email: str) -> Dict[str, str]:
        """
        Parse the generated email to extract subject and body
        """
        lines = generated_email.strip().split('\n')
        subject = ""
        body_lines = []
        body_started = False
        
        for line in lines:
            line = line.strip()
            if line.startswith('Subject:'):
                subject = line.replace('Subject:', '').strip()
            elif line.startswith('Dear') or body_started:
                body_started = True
                body_lines.append(line)
            elif line and not line.startswith('Email:') and body_started:
                body_lines.append(line)
        
        # Clean up the body
        body = '\n'.join(body_lines).strip()
        
        # Default subject if not found
        if not subject:
            subject = "Partnership Opportunity - Digital Transformation Services"
        
        return {
            'subject': subject,
            'body': body
        }
    
    def send_email(self, recipient_email: str, generated_email: str, company_name: str = "") -> bool:
        """
        Send a single personalized email
        """
        try:
            # Parse the generated email
            email_parts = self.parse_generated_email(generated_email)
            
            # Create message
            message = MIMEMultipart("alternative")
            message["Subject"] = email_parts['subject']
            message["From"] = f"{self.sender_name} <{self.email}>"
            message["To"] = recipient_email
            
            # Create the email body
            text_body = email_parts['body']
            
            # Add HTML version for better formatting
            html_body = f"""
            <html>
              <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                {email_parts['body'].replace(chr(10), '<br>')}
                <br><br>
                <div style="border-top: 1px solid #eee; padding-top: 10px; margin-top: 20px;">
                  <small style="color: #666;">
                    Best regards,<br>
                    {self.sender_name} Team<br>
                    <a href="mailto:{self.email}">{self.email}</a>
                  </small>
                </div>
              </body>
            </html>
            """
            
            # Add both text and HTML parts
            part1 = MIMEText(text_body, "plain")
            part2 = MIMEText(html_body, "html")
            
            message.attach(part1)
            message.attach(part2)
            
            # Send the email
            context = ssl.create_default_context()
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email, self.password)
                server.sendmail(self.email, recipient_email, message.as_string())
                
            logger.info(f"Email sent successfully to {recipient_email} ({company_name})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            return False
    
    def send_bulk_emails(self, email_data: List[Dict], delay_seconds: float = 5.0) -> Dict[str, int]:
        """
        Send emails to multiple recipients with delay between sends
        """
        sent_count = 0
        failed_count = 0
        results = []
        
        for i, data in enumerate(email_data):
            company_name = data.get('company', '')
            recipient_email = data.get('email') or data.get('contact_email', '')
            generated_email = data.get('generated_email', '')
            
            if not recipient_email:
                logger.warning(f"No email address for {company_name}, skipping")
                failed_count += 1
                continue
                
            if not generated_email or generated_email.startswith('Error'):
                logger.warning(f"No valid generated email for {company_name}, skipping")
                failed_count += 1
                continue
            
            logger.info(f"Sending email to {company_name} ({recipient_email}) - {i+1}/{len(email_data)}")
            
            success = self.send_email(recipient_email, generated_email, company_name)
            
            results.append({
                'company': company_name,
                'email': recipient_email,
                'status': 'sent' if success else 'failed'
            })
            
            if success:
                sent_count += 1
            else:
                failed_count += 1
            
            # Add delay between emails to avoid being flagged as spam
            if i < len(email_data) - 1 and delay_seconds > 0:
                import time
                time.sleep(delay_seconds)
        
        return {
            'sent': sent_count,
            'failed': failed_count,
            'total': len(email_data),
            'results': results
        }
    
    def validate_email_address(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None