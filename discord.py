import os

from dotenv import load_dotenv

if os.path.exists(".env"):
    from dotenv import load_dotenv  # noqa F811

    load_dotenv()

from fastapi_discord import DiscordOAuthClient

discord = DiscordOAuthClient(
    client_id=os.getenv("DISCORD_CLIENT_ID"),
    client_secret=os.getenv("DISCORD_CLIENT_SECRET"),
    redirect_uri=os.getenv("DISCORD_REDIRECT_URI"),
    scopes=["identify"],
)
