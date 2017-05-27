# SweetfxDB

Code for sfx.thelazy.net

To set up:

1. First, install python 2.x
2. (Optional)create virtualenv and 
3. run "pip install -r reqs.txt" to install required packages
4. run "python manage.py syncdb --migrate --noinput" -> sets up an sqlite database
5. run "python manage.py createsuperuser" -> sets up superuser
6. run "python manage.py runserver" -> starts a test server on localhost:8000
