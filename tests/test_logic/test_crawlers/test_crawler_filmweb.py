import json
from unittest.mock import AsyncMock, patch  # Upewnij się, że masz AsyncMock

import aiohttp
import pytest

from logic.crawlers.crawler_filmweb import CrawlerFilmweb
from models import Media, MediaSource, MediaType

pytest_plugins = ("pytest_asyncio",)


@pytest.fixture
async def mock_session():
    """Pytest fixture to provide a mocked aiohttp _session."""

    return AsyncMock(spec=aiohttp.ClientSession)


@pytest.mark.asyncio
async def test_crawl_filmweb_media_none_media(mock_session):
    """Testuje, czy przekazanie None jako media zwraca None."""

    crawler = CrawlerFilmweb(_session=mock_session)
    result = await crawler.crawl_media(None)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_filmweb_media_no_mid(mock_session):
    """Testuje, czy media bez ID (mid) zwraca None."""

    crawler = CrawlerFilmweb(_session=mock_session)
    media = Media(url="https://www.filmweb.pl/film/Zielona+granica-2023-10034732")
    result = await crawler.crawl_media(media)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_filmweb_media_no_url(mock_session):
    """Testuje, czy media bez URL zwraca None."""

    crawler = CrawlerFilmweb(_session=mock_session)
    media = Media(mid=1)
    result = await crawler.crawl_media(media)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_filmweb_media_invalid_url(mock_session):
    """Testuje, czy media z URL-em nie z filmweb.pl zwraca None."""

    crawler = CrawlerFilmweb(_session=mock_session)
    media = Media(mid=1, url="https://www.imdb.com/title/tt27627798/")
    result = await crawler.crawl_media(media)

    assert result is None


@pytest.mark.asyncio
async def test_crawl_filmweb_media_invalid_source(mock_session):
    """Testuje, czy media z nieobsługiwanym źródłem zwraca None."""

    crawler = CrawlerFilmweb(_session=mock_session)
    media = Media(
        mid=1,
        url="https://www.filmweb.pl/film/Zielona+granica-2023-10034732",
        media_source=MediaSource.IMDB,
    )
    result = await crawler.crawl_media(media)

    assert result is None


@pytest.mark.asyncio
@patch("logic.crawlers.crawler_filmweb.aiohttp.ClientSession")
async def test_crawl_filmweb_media_success_with_mock_api(MockClientSession):
    """
    Testuje logikę parsowania odpowiedzi z API Filmwebu,
    używając zamockowanego zapytania sieciowego.
    """

    fake_filmweb_api_str = """
    {"id":10078589,"title":"Sirât","originalTitle":"Sirât","year":2025,"type":"film","subType":"film_cinema","posterPath":"/85/89/10078589/8196392.2.jpg"}
    """
    fake_filmweb_api_json = json.loads(fake_filmweb_api_str)

    mock_response = AsyncMock()
    mock_response.status = 200
    mock_response.json.return_value = fake_filmweb_api_json

    mock_context_manager = AsyncMock()
    mock_context_manager.__aenter__.return_value = mock_response
    mock_context_manager.__aexit__.return_value = None

    mock_session = MockClientSession.return_value
    mock_session.get.return_value = mock_context_manager

    crawler = CrawlerFilmweb(_session=MockClientSession.return_value)

    media_input = Media(
        mid=10078589,
        url="https://www.filmweb.pl/film/Sir%C3%A2t-2025-10078589",
        media_source=MediaSource.FILMWEB,
        media_type=MediaType.MOVIE,
    )

    result = await crawler.crawl_media(media_input)

    mock_session.get.assert_called_once_with(
        "https://www.filmweb.pl/api/v1/title/10078589/info"
    )

    assert result is not None
    assert result.mid == 10078589
    assert result.title == "Sirât"
    assert result.year == 2025
    assert result.poster_url == "https://fwcdn.pl/fpo/85/89/10078589/8196392.2.jpg"
    assert result.media_type == MediaType.MOVIE
    assert result.media_source == MediaSource.FILMWEB
