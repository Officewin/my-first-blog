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

On your first visit each day, choose **Beginner** or **Advanced** words. The app
will draw ten random words from the selected list, but the daily submission
limit remains ten regardless of level.

Each user receives ten practice words per day.  The application records every
submission in SQLite so the daily quota and history persist even after logging
out or switching browsers.  Make sure migrations have been applied so the
`DailyPractice`, `DailySubmission`, and `PronunciationHistory` tables exist.
