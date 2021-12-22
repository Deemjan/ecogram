# Команды alembic

alembic init -t async migrations Для инициализации

alembic revision --autogenerate -m "{message}" для коммита

alembic upgrade head для миграции

alembic history

alembic downgrade -1

alembic downgrade {rev_number}

# Команды docker

docker context create remote --docker "host=ssh://root@host"

docker context ls

docker-compose up -d --build

docker-compose --context remote up -d

# Чтобы развернуть контейнер

На винде: установить docker desktop https://www.docker.com/products/docker-desktop

ввести команду docker-compose up -d --build

Подождать пока запустятся контейнеры

Перейти на http://localhost:8008/docs чтобы убедиться что все работает (тут же можно покидать запросы)

Чтобы вырубить контейнеры, ввести команду docker-compose down -v