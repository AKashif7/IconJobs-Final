# IconJobs — Micro Job Matchmaking Web Application

**Final Year Project | University of Westminster**
Student: Abdur Rehman Kashif (W1986281) | Supervisor: David Huang

## Setup Instructions

### 1. Install Dependencies
```
pip install -r requirements.txt
```

### 2. Apply Migrations
```
python manage.py migrate
```

### 3. Create Demo Data (users + sample jobs)
```
python setup_demo.py
```

### 4. Run the Development Server
```
python manage.py runserver
```
Open: http://127.0.0.1:8000

---

## Login Credentials

| Account | Username | Password |
|---------|----------|----------|
| Admin (superuser) | admin | admin123 |
| Demo Employer | employer1 | demo1234 |
| Demo Job Seeker | seeker1 | demo1234 |

Admin panel: http://127.0.0.1:8000/admin/

---

## Project Structure

```
iconjobs/
├── accounts/       — User registration, login, profiles, ratings
├── jobs/           — Job postings, applications, search, save
├── chat/           — Internal messaging (unlocked after acceptance)
├── templates/      — All HTML templates
├── manage.py
├── requirements.txt
└── setup_demo.py   — Demo data creation script
```

## Recruitment Workflow

1. Employer posts a job
2. Job seeker applies (sends profile + CV + message)
3. Employer reviews applicants — sees name, rating, jobs completed, CV
4. Employer can: Accept / Shortlist / Reject
5. On Accept → internal chat auto-opens, contact details revealed
6. They discuss arrival time, address, clothing via chat
7. Employer marks job as Complete
8. Employer leaves a star rating for the worker
