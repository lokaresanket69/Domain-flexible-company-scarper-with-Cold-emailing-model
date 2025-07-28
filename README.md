# LinkedIn Scraper with Groq AI Email Generation

A Flask-based web application that scrapes LinkedIn company data and generates personalized emails using Groq AI.

## Features

- Scrape LinkedIn company information
- Generate personalized emails using Groq AI
- Send emails via cPanel webmail
- User-friendly web interface
- Docker support for easy deployment

## Prerequisites

- Python 3.11+
- Docker (for containerized deployment)
- Groq API key
- LinkedIn account (for scraping)

## Local Development Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd linkedin-scraper
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   - Copy `.env.example` to `.env`
   - Update the values in `.env` with your configuration

5. Initialize the database:
   ```bash
   flask db upgrade
   ```

6. Run the development server:
   ```bash
   flask run
   ```

## Docker Setup

1. Build the Docker image:
   ```bash
   docker build -t linkedin-scraper .
   ```

2. Run the container:
   ```bash
   docker run -d --name linkedin-scraper -p 5000:5000 --env-file .env linkedin-scraper
   ```

## Deployment

### Render.com

1. Create a new Web Service on Render
2. Connect your GitHub/GitLab repository
3. Select "Docker" as the environment
4. Set the Dockerfile path to `./Dockerfile`
5. Add the required environment variables from `.env.example`
6. Deploy!

## Environment Variables

See `.env.example` for all available environment variables.

## Project Structure

```
.
├── app/                      # Application package
│   ├── __init__.py          # Application factory
│   ├── models.py            # Database models
│   ├── routes.py            # Application routes
│   └── static/              # Static files (CSS, JS, images)
│   └── templates/           # HTML templates
├── utils/
│   ├── groq_email_generator.py  # Groq AI email generation
│   └── web_scraper.py       # Web scraping utilities
├── tests/                   # Test files
├── .env.example             # Example environment variables
├── .gitignore               # Git ignore file
├── Dockerfile               # Docker configuration
├── README.md                # This file
├── requirements.txt         # Python dependencies
└── wsgi.py                 # WSGI entry point
```

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Flask for the web framework
- Groq for the AI email generation
- Selenium for web scraping
- Render for deployment hosting
