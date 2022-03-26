# Команды alembic

alembic init -t async migrations Для инициализации

alembic revision --autogenerate -m "{message}" для коммита

alembic upgrade head для миграции

alembic history

alembic downgrade -1

alembic downgrade {rev_number}

# Чтобы развернуть контейнер

На винде: установить docker desktop https://www.docker.com/products/docker-desktop

ввести команду docker-compose up -d --build

Подождать пока запустятся контейнеры

Перейти на http://localhost/docs чтобы убедиться что все работает (тут же можно покидать запросы)

Чтобы остановить контейнеры, ввести команду docker-compose down -v