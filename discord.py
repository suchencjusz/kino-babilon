from dotenv import load_dotenv
import os

load_dotenv()

from fastapi_discord import DiscordOAuthClient
from fastapi_discord.exceptions import ClientSessionNotInitialized


discord = DiscordOAuthClient(
    client_id=os.getenv("DISCORD_CLIENT_ID"),
    client_secret=os.getenv("DISCORD_CLIENT_SECRET"),
    redirect_uri=os.getenv("DISCORD_REDIRECT_URI"),
    scopes=["identify"],
)
