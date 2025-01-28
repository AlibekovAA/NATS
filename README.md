docker compose up --build
http://localhost:8000 - для доступа к основному API
http://localhost:8000/docs - для доступа к Swagger UI (документация API)
# Остановить все контейнеры
docker stop $(docker ps -a -q)

# Удалить все контейнеры
docker rm $(docker ps -a -q)

# Удалить все образы
docker rmi $(docker images -q)

# Очистить неиспользуемые ресурсы
docker system prune -a --volumes
