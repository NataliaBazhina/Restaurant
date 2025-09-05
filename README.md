# Сайт для бронирования столиков в ресторане "Family"

Веб-приложение для онлайн-бронирования столиков в ресторане с системой управления бронированиями и пользовательским личным кабинетом.

## Основные возможности

### Для гостей
- Бронирование столиков с выбором даты, времени и количества гостей
- Просмотр схем залов с доступными столиками
- Личный кабинет с историей бронирований
- Обратная связь с администрацией
- Информация о ресторане и услугах

### Для администраторов
-  Управление бронированиями через админ-панель
- Просмотр статистики и занятости столиков
- Управление пользователями
- Управление залами и столиками
- Обработка обратной связи от клиентов
- Подтверждение бронирования по почте.

## Технологический стек

### Backend
- **Python 3.11**
- **Django 4.2**
- **PostgreSQL**
- **Celery** 
- **Redis** 

### Frontend
- **HTML5/CSS3**  
- **Bootstrap 5** 
- **JavaScript** 


### Инфраструктура
- **Docker** - контейнеризация
- **Docker Compose** - оркестрация контейнеров
- **Nginx** - веб-сервер
- **Gunicorn** - WSGI-сервер

## Установка и запуск

### Предварительные требования
- Docker и Docker Compose
- Python 3.11+ (для разработки)

### Запуск через Docker (рекомендуется для продакшена)

1. Клонируйте репозиторий:

git@github.com:NataliaBazhina/Restaurant.git

cd restaurant

2. Создайте файл .env.docker на основе .env.example:

3. Запустите приложение:

docker compose --env-file .env.docker up -d --build

4. Приложение будет доступно по адресу: http://localhost:8000

### Запуск локально (рекомендуется для разработки)

1. Убедитесь, что установлены:

    Python 3.12,
    PostgreSQL,
    Redis
2. Настройте базу данных:

bash

sudo service postgresql start

createdb restaurant

3. Запустите Redis:
redis-server
4. Создайте и активируйте виртуальное окружение:

python -m venv venv
source venv/bin/activate  # Linux/Mac

venv\Scripts\activate     # Windows

5. Установите зависимости:

pip install -r requirements.txt
6. Настройте переменные окружения:

cp .env .env.
7. Примените миграции:

python manage.py migrate
8. Создайте суперпользователя:

python manage.py csu
9. Запустите сервер:

python manage.py runserver
10. Запустите Celery:

celery -A config worker --beat --loglevel=info
11.    Приложение будет доступно по адресу: http://localhost:8000
12. Разработка

Для разработки рекомендуется использовать локальный режим с .env файлом. 
Для тестирования продакшен-среды используйте Docker с .env.docker.

Для Docker (.env.docker)

DB_HOST=db
EMAIL_BACKEND=django.core.mail.backends.smtp.EmailBackend

Для локальной разработки (.env)

DB_HOST=localhost
EMAIL_BACKEND=django.core.mail.backends.console.EmailBackend