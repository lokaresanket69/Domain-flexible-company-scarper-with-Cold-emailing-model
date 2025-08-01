import json
import os
import logging
import traceback
from flask import render_template, request, jsonify, send_file, redirect, url_for, flash, session
import pandas as pd
from leads import run_scraper
from utils.nlp_processor import process_descriptions
from utils.groq_email_generator import GroqEmailGenerator
from utils.cpanel_email_sender import CPanelEmailSender
from models import Company
from db import db
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def register_routes(app, db):
    """Register all application routes"""
    
    @app.route('/')
    def index():
        # Read default config
        config = {}
        if os.path.exists('scraper_config.json'):
            try:
                with open('scraper_config.json', 'r') as f:
                    config = json.load(f)
            except Exception as e:
                logger.warning(f"Could not load config: {e}")
        
        # Check if CSV exists to pass to template
        csv_exists = os.path.exists('lead1.csv')
        
        return render_template('index.html', config=config, csv_exists=csv_exists)

    @app.route('/scrape', methods=['POST'])
    def scrape():
        """Handle company scraping requests and return JSON."""
        try:
            keywords = request.form.get('keywords', 'IT services')
            founded_years_str = request.form.get('founded_years', '')
            founded_years = [year.strip() for year in founded_years_str.split(',')] if founded_years_str else []
            country = request.form.get('country', 'United Kingdom')
            size = request.form.get('size', '51-200')
            max_results = int(request.form.get('max_results', 10))
            sleep_time = float(request.form.get('sleep_time', 1.0))
            
            results_df = run_scraper(
                keywords=keywords,
                founded_years=founded_years,
                country=country,
                size=size,
                max_results=max_results,
                sleep_time=sleep_time
            )
            
            if not results_df.empty:
                results_df = process_descriptions(results_df)
                
                companies_saved = 0
                for _, row in results_df.iterrows():
                    try:
                        company_data = row.to_dict()
                        existing_company = Company.query.filter_by(linkedin_url=company_data.get('companyLinkedinUrl')).first()
                        if existing_company:
                            for key, value in company_data.items():
                                if hasattr(existing_company, key):
                                    setattr(existing_company, key, value)
                        else:
                            new_company = Company.from_dict(company_data)
                            db.session.add(new_company)
                        db.session.commit()
                        companies_saved += 1
                    except Exception as e:
                        logger.error(f"Error saving company to database: {e}")
                        db.session.rollback()
                
                # Store results in session to display on another page
                session['scraping_results'] = results_df.to_dict('records')
                
                return jsonify({
                    'success': True,
                    'message': f'Successfully scraped {companies_saved} companies.',
                    'redirect_url': url_for('show_results')
                })
            else:
                return jsonify({'success': False, 'error': 'No results found.'}), 404
                
        except Exception as e:
            logger.error(f"Error during scraping: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'success': False, 'error': str(e)}), 500

    @app.route('/results')
    def show_results():
        """Display scraping results stored in the session."""
        results = session.pop('scraping_results', [])
        if not results:
            flash("No scraping results to display.", "warning")
            return redirect(url_for('index'))
        return render_template('results.html', results=results)

    @app.route('/download')
    def download():
        try:
            # Create a CSV string from the DataFrame
            if os.path.exists('lead1.csv'):
                return send_file('lead1.csv', as_attachment=True, download_name='linkedin_companies.csv')
            else:
                flash("No data available to download. Please run a scrape first.", "warning")
                return redirect(url_for('index'))
        except Exception as e:
            flash(f"Error downloading file: {str(e)}", "danger")
            return redirect(url_for('index'))

    @app.route('/companies')
    def view_companies():
        try:
            # Get companies from database
            companies = Company.query.order_by(Company.scraped_at.desc()).all()
            company_list = [company.to_dict() for company in companies]
            
            # Pass to template for display
            return render_template('companies.html', companies=company_list)
        except Exception as e:
            logger.error(f"Error viewing companies: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f"Error retrieving companies: {str(e)}", "danger")
            return redirect(url_for('index'))

    @app.route('/api/scrape', methods=['POST'])
    def api_scrape():
        try:
            body = request.get_json()
            keywords = body.get('keywords', 'IT services')
            founded_years = body.get('founded_years', ['2015'])
            country = body.get('country', 'United Kingdom')
            size = body.get('size', '51-200')
            max_results = body.get('max_results', 10)
            
            # Run the scraper
            df = run_scraper(
                keywords=keywords, 
                founded_years=founded_years, 
                country=country, 
                size=size,
                max_results=max_results
            )
            
            # Process with NLP
            df = process_descriptions(df)
            
            # Save to CSV
            df.to_csv('lead1.csv', index=False)
            
            # Save to database
            for _, row in df.iterrows():
                try:
                    company_data = row.to_dict()
                    existing_company = Company.query.filter_by(linkedin_url=company_data.get('companyLinkedinUrl')).first()
                    
                    if existing_company:
                        # Update existing company
                        for key, value in company_data.items():
                            if key == 'companyLinkedinUrl':
                                continue
                            if hasattr(existing_company, key):
                                setattr(existing_company, key, value)
                        db.session.commit()
                    else:
                        # Create new company record
                        new_company = Company.from_dict(company_data)
                        db.session.add(new_company)
                        db.session.commit()
                except Exception as e:
                    logger.error(f"Error saving company to database: {str(e)}")
                    db.session.rollback()
            
            # Return as CSV string
            csv_str = df.to_csv(index=False)
            return {
                "statusCode": 200,
                "headers": {"Content-Type": "text/csv"},
                "body": csv_str
            }
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            logger.error(traceback.format_exc())
            return {
                "statusCode": 500,
                "body": json.dumps({"error": str(e)})
            }

    @app.route('/api/companies', methods=['GET'])
    def api_companies():
        try:
            companies = Company.query.all()
            company_list = [company.to_dict() for company in companies]
            return jsonify({
                "statusCode": 200,
                "data": company_list,
                "count": len(company_list)
            })
        except Exception as e:
            logger.error(f"API error: {str(e)}")
            return jsonify({
                "statusCode": 500,
                "error": str(e)
            }), 500

    @app.route('/health')
    def health_check():
        """Health check endpoint for monitoring"""
        try:
            # Test database connection
            db.session.execute('SELECT 1')
            return jsonify({
                "status": "healthy",
                "database": "connected",
                "version": "1.0.0"
            })
        except Exception as e:
            return jsonify({
                "status": "unhealthy",
                "database": "disconnected",
                "error": str(e)
            }), 500

    @app.route('/generate-emails', methods=['POST'])
    def generate_emails():
        """Generate personalized emails using Groq for scraped companies"""
        try:
            data = request.get_json()
            model_name = data.get('model_name', 'llama3-8b-8192')
            companies = data.get('companies', [])
            
            if not companies:
                return jsonify({'error': 'No companies provided for email generation'}), 400
            
            # Get Groq API key from environment variables
            groq_api_key = os.environ.get("GROQ_API_KEY")
            if not groq_api_key:
                return jsonify({
                    'error': 'Groq API key not found. Please set the GROQ_API_KEY environment variable.'
                }), 500
                
            # Initialize Groq email generator
            email_generator = GroqEmailGenerator(api_key=groq_api_key)
            
            # Generate emails
            generated_emails = []
            for company in companies:
                # Generate email
                email_content = email_generator.generate_email(company, from_company="Prabisha Consulting Pvt. Ltd.")
                
                # Update company data with generated email
                company['generated_email'] = email_content
                
                # Save updated company to database
                db_company = Company.query.get(company['id'])
                if db_company:
                    db_company.generated_email = email_content
                    db.session.commit()
                
                generated_emails.append(company)
            
            return jsonify({
                'message': f'Successfully generated emails for {len(generated_emails)} companies',
                'companies': generated_emails
            })
        except Exception as e:
            logger.error(f"Error generating emails with Groq: {e}")
            logger.error(traceback.format_exc())
            return jsonify({'error': str(e)}), 500
    
    @app.route('/send_emails', methods=['POST'])
    def send_emails():
        """Send generated emails via cPanel webmail"""
        try:
            # Get cPanel email configuration
            smtp_server = request.form.get('smtp_server')
            smtp_port = int(request.form.get('smtp_port', 587))
            email_address = request.form.get('email_address')
            email_password = request.form.get('email_password')
            company_ids = request.form.getlist('company_ids')
            
            if not all([smtp_server, email_address, email_password]):
                return jsonify({
                    'error': 'SMTP server, email address, and password are required for sending emails',
                    'success': False
                }), 400
            
            # Initialize email sender
            email_sender = CPanelEmailSender(smtp_server, smtp_port, email_address, email_password)
            
            # Test connection first
            if not email_sender.test_connection():
                return jsonify({
                    'error': 'Failed to connect to SMTP server. Please check your credentials.',
                    'success': False
                }), 400
            
            # Get companies with generated emails
            if company_ids:
                companies = Company.query.filter(
                    Company.id.in_(company_ids),
                    Company.generated_email.isnot(None),
                    Company.email_sent == False
                ).all()
            else:
                companies = Company.query.filter(
                    Company.generated_email.isnot(None),
                    Company.email_sent == False
                ).all()
            
            if not companies:
                return jsonify({
                    'message': 'No companies found with generated emails ready to send',
                    'success': True,
                    'sent_count': 0
                })
            
            # Prepare email data
            email_data = []
            for company in companies:
                if company.email or company.contact_email:
                    email_data.append({
                        'company': company.name,
                        'email': company.email or company.contact_email,
                        'generated_email': company.generated_email,
                        'company_id': company.id
                    })
            
            # Send emails
            results = email_sender.send_bulk_emails(email_data)
            
            # Update database with sent status
            for result_item in results['results']:
                if result_item['status'] == 'sent':
                    company = Company.query.filter_by(name=result_item['company']).first()
                    if company:
                        company.email_sent = True
                        company.email_sent_at = datetime.now()
                        db.session.commit()
            
            return jsonify({
                'message': f'Email sending completed. Sent: {results["sent"]}, Failed: {results["failed"]}',
                'success': True,
                'sent_count': results['sent'],
                'failed_count': results['failed'],
                'total_count': results['total'],
                'results': results['results']
            })
            
        except Exception as e:
            logger.error(f"Error sending emails: {str(e)}")
            return jsonify({
                'error': f'Email sending failed: {str(e)}',
                'success': False
            }), 500
    
    @app.route('/email_dashboard')
    def email_dashboard():
        """Dashboard for managing email generation and sending"""
        try:
            # Get companies with and without emails
            companies_with_emails = Company.query.filter(Company.generated_email.isnot(None)).count()
            companies_without_emails = Company.query.filter(Company.generated_email.is_(None)).count()
            emails_sent = Company.query.filter(Company.email_sent == True).count()
            
            # Get recent companies
            recent_companies = Company.query.order_by(Company.scraped_at.desc()).limit(10).all()
            company_list = [company.to_dict() for company in recent_companies]
            
            stats = {
                'total_companies': Company.query.count(),
                'companies_with_emails': companies_with_emails,
                'companies_without_emails': companies_without_emails,
                'emails_sent': emails_sent
            }
            
            return render_template('email_dashboard.html', stats=stats, companies=company_list)
            
        except Exception as e:
            logger.error(f"Error loading email dashboard: {str(e)}")
            flash(f"Error loading dashboard: {str(e)}", "danger")
            return redirect(url_for('index'))

    @app.route('/get-email/<int:company_id>', methods=['GET'])
    def get_email(company_id):
        """[DEBUG] Fetch the generated email content for a specific company."""
        print(f"--- DEBUG: /get-email route hit for company ID: {company_id} ---")
        try:
            # For debugging, we bypass the database and return a test email.
            return jsonify({
                'success': True,
                'email_content': f"This is a test email for Company ID: {company_id}. If you see this, the route is working."
            })
        except Exception as e:
            print(f"--- DEBUG: Error in /get-email route: {e} ---")
            return jsonify({'success': False, 'error': 'A server error occurred.'}), 500

    return app
