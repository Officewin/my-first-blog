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
