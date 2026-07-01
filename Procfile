web: python manage.py migrate --run-syncdb && python manage.py auto_setup && gunicorn fibertruck.wsgi:application --bind 0.0.0.0:$PORT
