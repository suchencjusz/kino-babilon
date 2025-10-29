from unittest.mock import AsyncMock

import aiohttp
import pytest

from logic.crawler import CrawlerBase

pytest_plugins = ("pytest_asyncio",)


@pytest.mark.asyncio
async def test_crawl_movie():
    """Testuje, czy CrawlerBase można poprawnie zainicjować z sesją."""

    mock_session = AsyncMock(spec=aiohttp.ClientSession)
    crawler = CrawlerBase(_session=mock_session)

    assert crawler._session is mock_session
