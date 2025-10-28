# Kino Babilon

tu cos bedzie

# Instalacja

`docker-compose.yml`

## master - teoretycznie działający branch
```
services:
  kino_babilon_backend:
    image: suchencjusz/kino_babilon_backend:master
    container_name: kino_babilon_backend
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
      - ./kino_babilon.db:/app/kino_babilon.db
    env_file:
      - .env
```

## dev - voodoo
```
services:
  kino_babilon_backend:
    image: suchencjusz/kino_babilon_backend:dev
    container_name: kino_babilon_backend
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
      - ./kino_babilon_dev.db:/app/kino_babilon.db
    env_file:
      - .env
```


https://discord.com/developers/applications -> jakas aplikacja -> OAuth2 -> wypełnić .env
`.env`
```
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback
```

# Deweloperka

`Linux`
```
git clone https://github.com/suchencjusz/kino-babilon
cd kino-babilon
git checkout -b dev
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
```

no i se odpalasz po uvicorn tak jak w Dockerfile
