web: rm -f db.sqlite3 && python manage.py migrate && python manage.py auto_setup && gunicorn fibertruck.wsgi:application --bind 0.0.0.0:$PORT
