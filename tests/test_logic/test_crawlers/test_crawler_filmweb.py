import pytest
import json

from unittest.mock import AsyncMock, patch

from logic.crawlers.crawler_filmweb import CrawlerFilmweb
from models import Media, MediaSource, MediaType

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_crawl_filmweb_media_none_media():
    """Testuje, czy przekazanie None jako media zwraca None."""

    crawler = CrawlerFilmweb()
    result = await crawler.crawl_media(None)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_filmweb_media_no_mid():
    """Testuje, czy media bez ID (mid) zwraca None."""

    crawler = CrawlerFilmweb()
    media = Media(url="https://www.filmweb.pl/film/Zielona+granica-2023-10034732")
    result = await crawler.crawl_media(media)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_filmweb_media_no_url():
    """Testuje, czy media bez URL zwraca None."""

    crawler = CrawlerFilmweb()
    media = Media(mid=1)
    result = await crawler.crawl_media(media)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_filmweb_media_invalid_url():
    """Testuje, czy media z URL-em nie z filmweb.pl zwraca None."""

    crawler = CrawlerFilmweb()
    media = Media(mid=1, url="https://www.imdb.com/title/tt27627798/")
    result = await crawler.crawl_media(media)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_filmweb_media_invalid_source():
    """Testuje, czy media z nieobsługiwanym źródłem zwraca None."""
    crawler = CrawlerFilmweb()
    media = Media(
        mid=1,
        url="https://www.filmweb.pl/film/Zielona+granica-2023-10034732",
        media_source=MediaSource.IMDB,
    )
    result = await crawler.crawl_media(media)
    assert result is None


@pytest.mark.asyncio
@patch("aiohttp.ClientSession.get", new_callable=AsyncMock)
async def test_crawl_filmweb_media_success_with_mock_api(mock_get):
    """
    Testuje logikę parsowania odpowiedzi z API Filmwebu,
    używając zamockowanego zapytania sieciowego.
    """
    crawler = CrawlerFilmweb()

    fake_filmweb_api_str = """
    {"id":10078589,"title":"Sirât","originalTitle":"Sirât","year":2025,"type":"film","subType":"film_cinema","posterPath":"/85/89/10078589/8196392.2.jpg"}
    """
    fake_filmweb_api_json = json.loads(fake_filmweb_api_str)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = fake_filmweb_api_json
    mock_get.return_value.__aenter__.return_value = mock_response

    media_input = Media(
        mid=10078589,
        url="https://www.filmweb.pl/film/Sir%C3%A2t-2025-10078589",
        media_source=MediaSource.FILMWEB,
    )

    result = await crawler.crawl_media(media_input)

    assert result is not None
    assert result.mid == 10078589
    assert result.title == "Sirât"
    assert result.year == 2025
    assert result.poster_url == "https://fwcdn.pl/fpo/85/89/10078589/8196392.2.jpg"
    assert result.media_type == MediaType.MOVIE
    assert result.media_source == MediaSource.FILMWEB