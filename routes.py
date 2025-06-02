import json
import os
import logging
import traceback
from flask import render_template, request, jsonify, send_file, redirect, url_for, flash
import pandas as pd
from leads import run_scraper
from utils.nlp_processor import process_descriptions
from utils.ollama_email_generator import OllamaEmailGenerator
from utils.cpanel_email_sender import CPanelEmailSender
from models import Company
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
        try:
            keywords = request.form.get('keywords', 'IT services')
            founded_years = request.form.get('founded_years', '2015')
            founded_years = [year.strip() for year in founded_years.split(',')]
            country = request.form.get('country', 'United Kingdom')
            region = request.form.get('region', 'All Regions')  # New region parameter
            size = request.form.get('size', '51-200')
            max_results = int(request.form.get('max_results', 10))
            sleep_time = float(request.form.get('sleep_time', 1.0))
            
            logger.debug(f"Scraping with parameters: keywords={keywords}, years={founded_years}, country={country}, size={size}")
            
            # Run the scraper
            results_df = run_scraper(
                keywords=keywords,
                founded_years=founded_years,
                country=country,
                size=size,
                max_results=max_results,
                sleep_time=sleep_time
            )
            
            # Process descriptions with NLP
            if not results_df.empty:
                results_df = process_descriptions(results_df)
                results_df.to_csv('lead1.csv', index=False)
                
                # Save to database
                companies_saved = 0
                for _, row in results_df.iterrows():
                    try:
                        # Convert row to dict and create Company object
                        company_data = row.to_dict()
                        
                        # Check if company already exists (by LinkedIn URL)
                        existing_company = Company.query.filter_by(linkedin_url=company_data.get('companyLinkedinUrl')).first()
                        
                        if existing_company:
                            # Update existing company
                            for key, value in company_data.items():
                                if key == 'companyLinkedinUrl':
                                    continue  # Skip the URL as it's already set
                                if hasattr(existing_company, key):
                                    setattr(existing_company, key, value)
                            db.session.commit()
                        else:
                            # Create new company record
                            new_company = Company.from_dict(company_data)
                            db.session.add(new_company)
                            db.session.commit()
                        
                        companies_saved += 1
                    except Exception as e:
                        logger.error(f"Error saving company to database: {str(e)}")
                        db.session.rollback()
                
                flash(f"Scraping completed successfully! Saved {companies_saved} companies to database.", "success")
                return render_template('results.html', results=results_df.to_dict('records'))
            else:
                flash("No results found. Try adjusting your search parameters.", "warning")
                return redirect(url_for('index'))
                
        except Exception as e:
            logger.error(f"Error during scraping: {str(e)}")
            logger.error(traceback.format_exc())
            flash(f"An error occurred: {str(e)}", "danger")
            return redirect(url_for('index'))

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

    @app.route('/generate_emails', methods=['POST'])
    def generate_emails():
        """Generate personalized emails using Ollama for scraped companies"""
        try:
            # Get parameters
            model_name = request.form.get('model_name', 'mistral')
            company_ids = request.form.getlist('company_ids')
            
            # Initialize Ollama email generator
            email_generator = OllamaEmailGenerator(model_name=model_name)
            
            # Check if Ollama is available
            if not email_generator.check_ollama_availability():
                return jsonify({
                    'error': 'Ollama is not available. Please ensure Ollama is installed and running.',
                    'success': False
                }), 400
            
            # Get companies from database
            if company_ids:
                companies = Company.query.filter(Company.id.in_(company_ids)).all()
            else:
                companies = Company.query.filter(Company.generated_email.is_(None)).all()
            
            if not companies:
                return jsonify({
                    'message': 'No companies found for email generation',
                    'success': True,
                    'generated_count': 0
                })
            
            # Convert to list of dictionaries
            companies_data = [company.to_dict() for company in companies]
            
            # Generate emails
            results = email_generator.generate_emails_for_companies(companies_data)
            
            # Update database with generated emails
            for result in results:
                if result.get('company_id'):
                    company = Company.query.get(result['company_id'])
                    if company:
                        company.generated_email = result['generated_email']
                        db.session.commit()
            
            # Save results to CSV
            output_file = email_generator.save_generated_emails_to_csv(results)
            
            return jsonify({
                'message': f'Generated emails for {len(results)} companies',
                'success': True,
                'generated_count': len(results),
                'output_file': output_file,
                'results': results
            })
            
        except Exception as e:
            logger.error(f"Error generating emails: {str(e)}")
            return jsonify({
                'error': f'Email generation failed: {str(e)}',
                'success': False
            }), 500
    
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

    return app
