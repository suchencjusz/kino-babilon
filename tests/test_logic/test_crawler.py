import pytest

from logic.crawler import CrawlerBase
from models import Media, MediaSource, SelectionMode, MediaType

pytest_plugins = ('pytest_asyncio',)

@pytest.mark.asyncio
async def test_crawl_movie():
    crawler = CrawlerBase()

    media = Media(
        title="Test Movie",
        year=2023,
        description="A test movie description.",
        poster_url="https://example.com/poster.jpg",
        media_url="https://www.filmweb.pl/film/Test-Movie-2023-12345678",
        media_type=MediaType.MOVIE,
        media_source=MediaSource.FILMWEB,
    )

    with pytest.raises(NotImplementedError):
        await crawler.crawl_media(media)

        
