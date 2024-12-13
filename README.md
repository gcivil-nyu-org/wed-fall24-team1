# NYC Public Service Finder

### main
[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/wed-fall24-team1.svg?branch=main)](https://app.travis-ci.com/gcivil-nyu-org/wed-fall24-team1/branches)
[![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/wed-fall24-team1/badge.png?branch=main)](https://coveralls.io/github/gcivil-nyu-org/wed-fall24-team1?branch=main)


### develop
[![Build Status](https://app.travis-ci.com/gcivil-nyu-org/wed-fall24-team1.svg?branch=develop)](https://app.travis-ci.com/github/gcivil-nyu-org/wed-fall24-team1/branches)
[![Coverage Status](https://coveralls.io/repos/github/gcivil-nyu-org/wed-fall24-team1/badge.png?branch=develop)](https://coveralls.io/github/gcivil-nyu-org/wed-fall24-team1?branch=develop)


**NYC Public Service Finder** is a full-stack Django web application designed to help NYC residents locate, filter, and engage with a variety of public services. The platform consolidates essential services like shelters, food pantries, mental health centers, and restrooms into one convenient interface. Beyond location-based search and filtering, it includes user accounts, service providers’ dashboards, announcements, user reviews, a forum for community discussions, and moderation functionalities.

---

## Key Features

### For Service Seekers
- **Search and Filter Services:**  
  Find services by category, keyword, radius from your location, or rating.

- **Distance and Rating Sorting:**  
  Sort results to prioritize proximity or quality (ratings).

- **Interactive Map:**  
  Visualize services on a live map with direction links and bookmark them for future reference.

- **User Reviews & Ratings:**  
  Submit and view reviews for services, enhancing transparency and trust.

- **Bookmarks & Profile:**  
  Save favorite services, view your reviews, manage your profile image, and more.

### For Service Providers
- **Service Listing Management:**  
  Create, edit, and deactivate services. Submitted services await admin approval.

- **Announcements:**  
  Broadcast timely messages (e.g., special events, temporary closures) to users who have bookmarked your services.

- **Respond to Reviews:**  
  Address user feedback directly, improve your service’s reputation, and provide additional information.

### Community Interaction
- **Forum Discussions:**  
  Engage in community discussions organized by categories, comment on posts, and get notified about replies.

- **Flag Inappropriate Content:**  
  Users can flag forum posts, comments, or reviews they find inappropriate. Admins review these flags and take action to maintain a safe environment.

### Moderation & Admin
- **Content Moderation:**  
  Admins can review flagged content, dismiss or revoke it, and ensure a positive, respectful community environment.

- **Approval Workflow:**  
  System administrators approve or reject new service listings.

- **Analytics & Dashboards:**  
  Service providers can access dashboards featuring bookmarks over time, reviews, average ratings, distribution by category, and more.

---

## Technology Stack

- **Backend:** Django (Python)
- **Databases:**  
  - **Primary (Relational):** Supabase (PostgreSQL) for user accounts, forums, and relational data  
  - **NoSQL (Key-Value Store):** Amazon DynamoDB for services, reviews, and bookmarks
- **Frontend:** HTML5, CSS3, JavaScript (with Tailwind CSS)
- **Storage:** Amazon S3 for user and service images
- **Geocoding:** Nominatim / Geopy for address-to-coordinate conversions
- **CI/CD:** Travis CI for continuous integration and deployment
- **Version Control:** Git & GitHub
- **Authentication:** Django’s built-in auth plus Django Allauth for social login (e.g., Google OAuth2)

---

## Project Structure

```
wed-fall24-team1/
├── accounts/ # User auth, registration, social login, password reset 
├── forum/ # Discussion forum (categories, posts, comments, notifications)
├── home/ # Main landing page, service listing, bookmarks, reviews, DynamoDB integration 
├── moderation/ # Flagging and moderation of user-generated content 
├── public_service_finder/ # Core Django project settings, URLs 
├── services/ # Service providers’ dashboards, CRUD for services, announcements, analytics 
├── static/ # Static files (CSS, JS, images) 
├── templates/ # HTML templates (global and per-app) 
├── manage.py # Django management script 
└── requirements.txt # Python dependencies
```

---

## Prerequisites and Setup

### Prerequisites
- **Python 3.x**
- **pip**
- **virtualenv** (recommended)
- **Supabase (Postgres)**: A running Supabase PostgreSQL instance for relational data
- **AWS Account** with IAM permissions for DynamoDB & S3
- **AWS CLI** configured locally

### Environment Variables
Create a `.env` file or export as environment variables:
- `DJANGO_SECRET_KEY`
- `GEOCODING_API_KEY`
- `SUPABASE_DB_NAME`, `SUPABASE_DB_USER`, `SUPABASE_DB_PASSWORD`, `SUPABASE_DB_HOST`, `SUPABASE_DB_PORT`
- `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_REGION`
- `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`

### Installation Steps

1. **Clone the Repository:**
```bash
git clone [your-repo-url]
cd wed-fall24-team1
```

2. **Create and Activate a Virtual Environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install Dependencies:**
```bash
pip install -r requirements.txt
```

4. **Configure AWS CLI & Credentials:**
```bash
aws configure
```

Provide your AWS keys, region, and output format.

5. **Set Environment Variables:**
```bash
export DJANGO_SECRET_KEY='your_secret_key'
export AWS_ACCESS_KEY_ID='your_access_key'
export AWS_SECRET_ACCESS_KEY='your_secret_key'
export AWS_DEFAULT_REGION='your_region'
# ... add others as needed
```

6. **Run Migrations:**
```bash
python manage.py migrate
```

7. **Run the Development Server:**
```bash
python manage.py runserver
```

Access the app at: http://localhost:8000

## Database Configuration

### Supabase (Postgres)
Your main relational data store for users, forum posts, flags, etc. Ensure the `DATABASES` setting in `public_service_finder/settings.py` is configured with your Supabase credentials.

### Amazon DynamoDB
- **Tables:** `services`, `reviews`, `bookmark`
- **Data:**  
  - `services`: Stores service info (category, coordinates, rating, status)  
  - `reviews`: Holds user reviews tied to services  
  - `bookmark`: Tracks user bookmarks to services
- Grant DynamoDB read/write permissions to the AWS credentials used.

### Amazon S3
Stores images (profile pics, service images). Set `AWS_STORAGE_BUCKET_NAME` and related S3 settings.

---

## Testing

```bash
python manage.py test
```

CI via Travis and coverage reports via Coveralls are integrated. Check badges above for build and coverage status.

---

## Additional Features

- **User Authentication & Social Login:**  
  Standard username/password plus Google OAuth2 support, password resets, and custom user model.

- **Forums & Notifications:**  
  Community discussions with categories, posts, comments, and profanity filtering. Users receive notifications for replies, approvals, announcements, etc.

- **Flagging & Moderation:**
  Users can flag content. Admins have a dedicated workflow to handle flagged items, ensuring a respectful platform.

- **Provider Dashboards & Analytics:**
  Analyze metrics like bookmarks over time, reviews, rating distribution, and category distribution for continuous service improvement.

- **Announcements:**
  Service providers can post announcements to inform users about changes, events, or temporary closures. Users with the service bookmarked receive notifications.

---

## Contributing

```bash
git checkout -b feature/new-feature
git add .
git commit -m "Add new feature"
```

Open an issue first for large changes.

---

## Team Members

- Omer Basar (Product Owner)
- Aakash Shankar
- Shubham Garg
- Deepjyot Singh Kapoor
- Kartikey Sharma

---

## License

Specify your license in a `LICENSE` file (e.g., MIT).

---

**NYC Public Service Finder** connects communities with essential public services, fostering transparency, engagement, and trust. Explore services, join discussions, and support your neighborhood today!

---

**Made with** :heart: **, powered by** :zap: **Django, and driven by** :rocket: **community spirit.**
