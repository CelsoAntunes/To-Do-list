
# My To-Do-list

This is a Django application running in Docker with a PostgreSQL database. The project is containerized using Docker and Docker Compose, and it can be easily set up and run with minimal configuration.

## Prerequisites

Make sure you have the following installed on your machine:

- [Docker](https://docs.docker.com/get-docker/)
- [Docker Compose](https://docs.docker.com/compose/install/)

## How to Run the Project

### 1. Clone the Repository

First, clone the project repository to your local machine:

```bash
git clone https://github.com/CelsoAntunes/To-Do-list.git
cd To-Do-list
```

### 2. Build and Run the Containers -- You can pull the image already generated from Docker hub using: 

```bash
docker pull antunesc/firstproject-django:latest
```

After this you can just start the containers following the next lines. If you rather build the image yourself, just follow from here on.

To build and start the containers for the Django app and PostgreSQL database, run:

```bash
docker-compose up -d
```

This command will:

- Build the Django application image (if it’s not built yet).
- Download the official PostgreSQL 14 image (if not available locally).
- Start both the Django app and the PostgreSQL database in the background.

### Optional: If you want to build the image yourself, before you "run docker-compose up -d", run:
```bash
docker-compose up --build
```

### 3. Access the Application

Once the containers are running, you can access the Django app by opening your browser and going to:

```
http://localhost:8000
```

### 4. Stopping the App

To stop the containers, run:

```bash
docker-compose down
```

This will stop and remove the containers, but the data will persist because the database is stored in a Docker volume.

- The PostgreSQL image will be pulled automatically as it is the official `postgres:14` image.

## Troubleshooting

- **Ports already in use**: If you get an error about port 8000 or 5432 already being in use, make sure there are no other services running on those ports, or change the ports in the `docker-compose.yml` file.

- **Dependencies**: If you encounter errors related to missing dependencies, make sure that the `requirements.txt` file is correctly configured, and that the Dockerfile installs all the necessary libraries.

## Additional Notes

- The Django app is set up to connect to the PostgreSQL database automatically via Docker Compose.
- Data in the PostgreSQL container is persisted between restarts due to the volume configuration in the `docker-compose.yml` file.
- This project uses the official PostgreSQL 14 Docker image, so no need to push it to Docker Hub.

## Contributing

Feel free to fork the repository, create a new branch, make your changes, and submit a pull request.
In case you want to run the already structured automated tests, run:

```bash
python manage.py test
```

## Docker Compose Example Configuration

If you want to change the ports or any other configuration, here's an example of how the `docker-compose.yml` file looks:

```yaml
version: '3.8'

services:
  db:
    image: postgres:14
    container_name: user_postgres
    restart: always
    environment:
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
      POSTGRES_DB: userdb
    volumes:
      - user_db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    networks:
      - app_network

  django:
    build: .
    container_name: user_django
    restart: always
    depends_on:
      - db
    environment:
      DB_NAME: userdb
      DB_USER: user
      DB_PASSWORD: password
      DB_HOST: db
      DB_PORT: 5432
    ports:
      - "8000:8000"
    networks:
      - app_network
    volumes:
      - .:/app

volumes:
  user_db_data:

networks:
  app_network:
    driver: bridge
```
