# Nurox

Nurox is a Flask-based community platform that combines user accounts, social interaction, problem sharing, stories, group communication, subscriptions, and AI-powered assistance. It provides authentication with OTP verification, profiles, posts and problems, group chat, chatbot support using Google Generative AI, notifications, and an administrative dashboard with subscription management.

---

## Overview

Nurox enables users to register, verify their accounts, share problems and stories, interact within groups, chat, and explore content by sectors. It supports premium subscription plans, profile management, password updates, admin control, and email functionality for verification and notifications.

The platform includes:

* Full user authentication and account lifecycle
* Email-based OTP verification
* Problem and story submission and browsing
* Group creation, administration, and chat
* AI chatbot assistance
* Subscription system with multiple plans
* Admin dashboard for moderation and user oversight
* SEO and legal pages
* Notifications and system alerts
* Structured templates and modern UI

---

## Features

* User Registration, Login, Logout
* OTP-based Account Verification
* Profile editing and password updates
* Submit and view problems
* Submit and view stories
* Comments and interactions features implemented in templates
* Group creation and management
* Group chat with admin controls
* AI chatbot using Google Generative AI
* Subscription purchase and approval workflow
* Subscription status dashboard
* Admin login and control panel
* User management and content moderation routes
* Email notifications via Flask-Mail
* Session handling with persistent storage
* Static media support and UI assets
* Terms & Conditions, Privacy Policy, Contact, and About pages

---

## Tech Stack

**Backend**

* Flask
* Flask-SQLAlchemy
* Flask-Login
* Flask-Bcrypt
* Flask-Mail
* Flask-Session
* Flask-Migrate
* psycopg2 (PostgreSQL)

**AI**

* Google Generative AI (`google-generativeai`)

**Frontend**

* Jinja2 templates
* HTML / CSS / JS
* Static assets

Dependencies are listed in `requirements.txt`.

---

## Project Structure

```
Nurox/
│
├── app.py                     # Main application
├── app.txt                    # Database reference info
├── requirements.txt           # Dependencies
├── ads.txt
│
├── static/
│   ├── images/                # Subscription images and UI graphics
│   ├── logo2.png
│   ├── notification_sound.mp3
│   └── error.png
│
└── templates/                 # Full web UI pages
    ├── base.html
    ├── home.html
    ├── login.html
    ├── register.html
    ├── verify_account.html
    ├── profile.html
    ├── user_profile.html
    ├── submit_problem.html
    ├── problems.html
    ├── problem_details.html
    ├── posts.html
    ├── story_feed.html
    ├── story_detail.html
    ├── groups/
    ├── subscription.html
    ├── subscription_status.html
    ├── admin_dashboard.html
    ├── users_list.html
    ├── contact.html
    ├── privacy_policy.html
    └── terms_conditions.html
```

---

## Installation

1. Extract or clone the project.
2. Ensure Python is installed.
3. Install required dependencies:

```
pip install -r requirements.txt
```

---

## Configuration

### Database

PostgreSQL and SQLite references are included. Update the database URI in `app.py`:

```
app.config['SQLALCHEMY_DATABASE_URI'] = 'YOUR_DATABASE_URL'
```

A reference file `app.txt` includes example database connection strings.

### Session

Persistent sessions are configured using SQLAlchemy-backed Flask-Session.

### Secret Key

Set a secure secret key inside `app.py`.

### Email

Flask-Mail is used for OTP and notifications. Configure SMTP credentials in the app configuration.

### Google Generative AI

Configure your API key:

```
genai.configure(api_key="YOUR_GOOGLE_GENAI_KEY")
```

---

## Running the Application

Run the Flask application:

```
python app.py
```

Then open in your browser:

```
http://localhost:5000
```

---

## Usage

* Register a new account
* Verify with OTP
* Login and update your profile
* Post problems and stories
* Join and interact in groups
* Use chatbot support
* Manage or purchase subscriptions
* Admins can log in to the admin panel to manage system content and users

---

## Routes (Highlights)

* `/` – Home
* `/register`, `/login`, `/logout`
* `/send_otp`, `/validate_otp`
* `/profile`, `/edit_profile`, `/change_password`
* `/submit_problem`, `/problems`
* `/stories`
* `/create_group`, `/group/<id>`
* `/chatbot`
* `/subscribe`, `/subscription/status`
* `/admin_login`, `/admin_dashboard`
* SEO / legal pages included

---

## Notes

* Email configuration is required for OTP and verification workflows.
* Database must be properly configured to enable persistence.
* Subscription images and assets are included in static resources.
* Session lifetime is configured for extended user retention.

---

## Troubleshooting

* Ensure all dependencies are installed.
* Verify database connectivity.
* Confirm valid email SMTP settings.
* Ensure Google Generative AI API credentials are working.
* Check server logs for runtime errors.
* Create necessary directories if file handling is enabled.

---

## License

This repository does not include a license file.
