# My First Blog

This project includes a pronunciation practice app. After pulling new updates run migrations to create database tables:

```bash
python manage.py migrate
```

Then create a superuser and start the development server:

```bash
python manage.py createsuperuser
python manage.py runserver
```

Log in and visit `/pronounce/` to record audio. Use the History link to view your past scores.

Two additional endpoints provide different difficulty levels:

- `/pronounce-easy/` – common words for beginners.
- `/pronounce-advanced/` – more challenging vocabulary.

Access to these paths is controlled per user.

### Granting access in the admin

Open the Django admin and locate **User App Access**. Create or edit a
`UserAppAccess` entry for the desired account and select which pronunciation
levels (`pronounce_easy` or `pronounce_advanced`) they may use. Users without an
entry only see the default `/pronounce/` route.

Each user receives ten practice words per day.  The application records every
submission in SQLite so the daily quota and history persist even after logging
out or switching browsers.  Make sure migrations have been applied so the
`DailyPractice`, `DailySubmission`, and `PronunciationHistory` tables exist.
