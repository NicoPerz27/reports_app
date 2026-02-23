
# S-21-S Reporting System

A simplified, responsive web application for managing congregation field service reports.

## Setup

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Apply Migrations**
   ```bash
   python manage.py migrate
   ```

3. **Create Admin User**
   ```bash
   python manage.py createsuperuser
   ```

4. **Run Server**
   ```bash
   python manage.py runserver
   ```

## Apps
- **accounts**: Custom user model.
- **organization**: Groups and Publishers.
- **reports**: Monthly reports and service years.
- **public_access**: Secure self-reporting links.
