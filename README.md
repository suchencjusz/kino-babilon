# Kino Babilon

[https://kino.kranus.pro/](https://kino.kranus.pro/)

# Instalacja

`docker-compose.yml`

## master - teoretycznie działający branch
```yaml
volumes:
  kino-db-volume:
    driver: local

services:
  kino-babilon-backend:
    image: suchencjusz/kino-babilon-backend:latest
    container_name: kino-babilon-backend
    ports:
      - "8008:8008"
    volumes:
      - kino-db-volume:/app/data
    env_file:
      - .env
```

wszystko jest w docker-compose.yml w repo


https://discord.com/developers/applications -> jakas aplikacja -> OAuth2 -> wypełnić .env
`.env`
```env
DISCORD_CLIENT_ID=1431635250605199520
DISCORD_CLIENT_SECRET=
DISCORD_REDIRECT_URI=http://127.0.0.1:8008/auth/callback
FRONTEND_REDIRECT_URL=http://127.0.0.1:8008
DATABASE_URL=sqlite:///./data/database.db
FRONTEND_REDIRECT_URL=http://127.0.0.1:8008/auth/getuser
FIRST_ADMIN_DISCORD_ID=
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

Dokumentacja API: http://localhost:8008/docs
