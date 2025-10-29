import aiohttp

from models import Media

# class Media(SQLModel, table=True):
#     __tablename__ = "media"

#     mid: int = Field(default=None, primary_key=True, index=True)

#     title: str = Field(sa_column=Column("title", String))
#     year: int = Field(sa_column=Column("year", Integer))
#     description: str = Field(sa_column=Column("description", String))
#     poster_url: str = Field(sa_column=Column("poster_url", String))
#     media_url: str = Field(sa_column=Column("media_url", String))
#     media_type: MediaType = Field(default=MediaType.MOVIE)
#     media_source: MediaSource = Field(default=MediaSource.FILMWEB)

#     # Relationships
#     screening_pools: list["ScreeningVotingPool"] = Relationship(back_populates="media")
#     votes: list["Vote"] = Relationship(back_populates="media")


class CrawlerBase:

    def __init__(self, _session: aiohttp.ClientSession = None):
        if _session is None:
            raise ValueError("An aiohttp ClientSession must be provided.")
        self._session = _session

    async def crawl_media(self, media: Media):
        raise NotImplementedError("This method should be overridden by subclasses.")
