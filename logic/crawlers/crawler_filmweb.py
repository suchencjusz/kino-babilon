import logging
import re

import aiohttp  # noqa F401

from logic.crawler import CrawlerBase
from models import Media, MediaSource, MediaType


class CrawlerFilmweb(CrawlerBase):

    async def _crawl_movie(self, media: Media):

        # https://www.filmweb.pl/film/Sir%C3%A2t-2025-10078589

        filmweb_movie_id = None
        match = re.search(r"(\d+)$", media.url)
        if match:
            filmweb_movie_id = match.group(1)
        else:
            logging.warning(
                f"CrawlerFilmweb: Could not extract Filmweb movie ID from URL: {media.url}"
            )
            return None

        movie_info_url = f"https://www.filmweb.pl/api/v1/title/{filmweb_movie_id}/info"
        movie_poster_url: str = "https://vectorified.com/images/no-data-icon-23.png"
        # https://fwcdn.pl/fpo  +  /07/34/734/7899618_1.$.jpg

        try:
            async with self._session.get(movie_info_url) as response:
                if response.status != 200:
                    logging.warning(
                        f"Failed to fetch movie info for Filmweb ID {filmweb_movie_id}: HTTP {response.status}"
                    )
                    return None
                info_data = await response.json()

            media.title = info_data.get("title", media.title)
            media.year = info_data.get("year", media.year)
            media.description = info_data.get("description", media.description)
            media.poster_url = info_data.get("posterPath", None)

            if media.poster_url and media.poster_url.startswith("/"):
                media.poster_url = "https://fwcdn.pl/fpo" + media.poster_url
            else:
                media.poster_url = movie_poster_url

            logging.debug(
                f"Crawled data for Filmweb ID {filmweb_movie_id}: {media.title} ({media.year})"
            )

        except Exception as e:
            logging.warning(
                f"Exception while crawling Filmweb movie ID {filmweb_movie_id}: {e}"
            )
            return None

        return media

    async def _crawl_series(self, media: Media):
        logging.warning("CrawlerFilmweb: Series crawling not implemented yet.")
        return None

    async def crawl_media(self, media: Media):

        if media is None:
            logging.warning("CrawlerFilmweb: Provided media is None")
            return None

        if media.mid is None:
            logging.warning("CrawlerFilmweb: Media ID (mid) is None")
            return None

        if media.url is None:
            logging.warning("CrawlerFilmweb: Media URL is None")
            return None

        if "filmweb.pl" not in media.url:
            logging.warning(
                f"CrawlerFilmweb: Media URL does not belong to Filmweb: {media.url}"
            )
            return None

        if media.media_source == MediaSource.FILMWEB:

            if media.media_type == MediaType.MOVIE:
                return await self._crawl_movie(media)
            elif media.media_type == MediaType.SERIES:
                return await self._crawl_series(media)
        else:
            logging.warning(
                f"CrawlerFilmweb cannot handle media source: {media.media_source}"
            )
            return None

        pass
