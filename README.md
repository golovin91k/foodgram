# FOODGRAM
![example workflow](https://github.com/golovin91k/foodgram/workflows/Main%20Foodgram%20workflow/badge.svg)

## Описание проекта
Foodgram - интернет-сайт, позволяющий пользователям создавать и обмениваться рецептами.
Ссылка на запущенный проект - https://foodgram-g91k.zapto.org/

## Технологии проекта
В проекте используются следующие технологии:
- Python
- Javascript
- CSS
- HTML
- Django
- Django REST framework
- Docker
- Nginx

## Инструкция по запуску проекта 

### Запуск проекта на локальном сервере:
1. скопируйте себе на локальный диск настоящий репозиторий
2. перейдите в корневую папку проекта и выполните команду:
```
docker compose up --build 
```
3. далее выполните следующие команды для сборки статики бэкенда:
```
docker compose exec backend python manage.py makemigrations
docker compose exec backend python manage.py migrate
docker compose exec backend python manage.py collectstatic
docker compose exec backend cp -r /app/collected_static/. /backend_static/static/ 
```
Проект должен быть запущен и доступен по адресу:
```
http://localhost:8000/
```

### Запуск проекта на удаленном сервере (под Linux):
1. установите на сервере Docker и Docker compose:
```
sudo apt update
sudo apt install curl
curl -fSL https://get.docker.com -o get-docker.sh
sudo sh ./get-docker.sh
sudo apt install docker-compose-plugin 
```
2. Создайте на удаленном сервере папку /foodgram и в неё скопируйте следующие файлы из корневой папки проекта: </br>
docker-compose.production.yml</br>
nginx.conf</br>

3. В папке /foodgram создайте файл .env со следующим содержанием (пример заполнения):
```
POSTGRES_DB=foodgram 
POSTGRES_USER=foodgram_user
POSTGRES_PASSWORD=foodgram_password
DB_NAME=foodgram
DB_HOST=db
DB_PORT=5432
SECRET_KEY = 'django-insecure-re1*....'
ALLOWED_HOSTS = '158.160.73.244 127.0.0.1 localhost foodgram-g91k.zapto.org'
```

4. На удаленном сервере перейдите в созданную папку /foodgram и выполните следующие команды:
```
sudo docker compose -f docker-compose.production.yml up -d 
sudo docker compose -f docker-compose.production.yml exec backend python manage.py migrate
sudo docker compose -f docker-compose.production.yml exec backend python manage.py collectstatic
sudo docker compose -f docker-compose.production.yml exec backend cp -r /app/collected_static/. /backend_static/static/
```
4. Настройте конфиг nginx на сервере, добавив в него следующие строки:
```
server {
    server_name ваш домен;

    location / {
        proxy_set_header Host localhost;
        proxy_pass http://127.0.0.1:8000;
    }
```
5. Проверьте настройки конфига на отсутствие ошибок и перезагрузите nginx:
```
sudo nginx -t 
sudo service nginx reload 
```
6. Проект должен быть запущен на Вашем удаленном сервере.


Автор проекта - Головин Кирилл golovin91k@gmail.com