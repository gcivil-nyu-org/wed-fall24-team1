# NYC Public Service Finder

### main
[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/wed-fall24-team1.svg?branch=main)](https://app.travis-ci.com/gcivil-nyu-org/wed-fall24-team1/branches)
[![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/wed-fall24-team1/badge.png?branch=main)](https://coveralls.io/github/gcivil-nyu-org/wed-fall24-team1?branch=main)


### develop
[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/wed-fall24-team1.svg?branch=develop)](https://app.travis-ci.com/github/gcivil-nyu-org/wed-fall24-team1/branches)

[![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/wed-fall24-team1/badge.png?branch=develop)](https://coveralls.io/github/gcivil-nyu-org/wed-fall24-team1?branch=develop)


## Description
A web application built with Django that helps users locate and access public services in New York City. This tool aims to simplify the process of finding essential public services for NYC residents.

## Features
- User account management
- Public service location finder
- Service information directory
- Interactive map interface
- User-friendly search functionality

## Tech Stack
- **Backend Framework:** Django
- **Database:** Amazon DynamoDB
- **Frontend:** HTML, CSS, JavaScript
- **Version Control:** Git
- **CI/CD:** Travis CI

## Installation

### Prerequisites
- Python 3.x
- pip
- virtualenv (recommended)
- AWS account with DynamoDB access
- AWS CLI configured

### Setup Instructions
1. Clone the repository
```bash
git clone [repository-url]
cd wed-fall24-team1
```

2. Create and activate virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows use: venv\Scripts\activate
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Configure AWS credentials
```bash
aws configure
```
Enter your AWS credentials when prompted:
- AWS Access Key ID
- AWS Secret Access Key
- Default region name (e.g., us-east-1)
- Default output format (json recommended)

5. Set up environment variables
```bash
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='your_region'
```

6. Run development server
```bash
python manage.py runserver
```

The application will be available at `http://localhost:8000`

## Project Structure
```
wed-fall24-team1/
├── .github/            # GitHub configuration files
├── accounts/           # User authentication and management
├── db-prep/           # Database preparation scripts
├── home/              # Home page application
├── public_service_finder/  # Main application logic
├── services/          # Service-related functionality
├── static/            # Static files (CSS, JS, images)
├── manage.py          # Django management script
└── requirements.txt   # Project dependencies
```

## Database Configuration
This project uses Amazon DynamoDB as its primary database. The database configuration can be found in the project settings. Make sure you have:

1. Created the necessary DynamoDB tables:
   - Users
   - Services
   - [Other tables as needed]

2. Set up the correct IAM permissions:
   - DynamoDB full access for development
   - Limited read/write access for production

3. Configured the tables with appropriate partition keys and sort keys:
   ```python
   # Example table structure
   {
       'TableName': 'Users',
       'KeySchema': [
           {'AttributeName': 'user_id', 'KeyType': 'HASH'},
           {'AttributeName': 'email', 'KeyType': 'RANGE'}
       ]
   }
   ```

## Testing
```bash
python manage.py test
```

## Contributing
1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## Team Members
- Omer Basar: Product Owner
- Aakash Shankar
- Shubham Garg
- Deepjyot Singh Kapoor
- Kartikey Sharma
