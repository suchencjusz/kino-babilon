# Kino Babilon

tu cos bedzie

# Instalacja

`docker-compose.yml`

## master - teoretycznie działający branch
```yaml
services:
  kino-babilon-backend:
    image: suchencjusz/kino-babilon-backend:latest
    container_name: kino-babilon-backend
    ports:
      - "8000:8000"
    volumes:
      - ./:/app
      - ./kino_babilon.db:/app/kino_babilon.db
    env_file:
      - .env
```

## dev - voodoo
```yaml
services:
  kino-babilon-backend:
    image: suchencjusz/kino-babilon-backend:dev
    container_name: kino-babilon-backend-dev
    ports:
      - "8008:8000"
    volumes:
      - ./:/app
      - ./kino_babilon_dev.db:/app/kino_babilon.db
    env_file:
      - .env
```


https://discord.com/developers/applications -> jakas aplikacja -> OAuth2 -> wypełnić .env
`.env`
```env
DISCORD_CLIENT_ID=
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=http://localhost:8000/auth/callback
```

# Deweloperka

`Linux`
```bash
git clone https://github.com/suchencjusz/kino-babilon
cd kino-babilon
git checkout dev
python3 -m venv venv
source ./venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
```

Dokumentacja API: http://localhost:8000/docs