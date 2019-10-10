# SweetfxDB

Code for sfx.thelazy.net

To set up:

1. docker-compose up --build
2. visit http://<dockerhost>:8124/
3. To create admin user: docker-compose exec sweetfx python manage.py createsuperuser
4. To reset stored data and db: docker-compose down -v