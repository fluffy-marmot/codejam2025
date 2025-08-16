import logging
from pathlib import Path
from urllib import parse, request

from .exceptions import HorizonsAPIError, ParsingError
from .models import MajorBody, ObjectData, TimePeriod, VectorData
from .parsers import MajorBodyTableParser, ObjectDataParser, VectorDataParser

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

__all__ = ("HorizonsClient",)


class HorizonsClient:
    """A client for the JPL Horizons API."""

    BASE_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
    TIME_FORMAT = "%Y-%m-%d"

    def _request(self, params: dict, save_to: Path | None = None) -> str:
        """Make a request to the Horizons API and return the result string."""
        params["format"] = "text"
        url = f"{self.BASE_URL}?{parse.urlencode(params)}"
        logger.info("Horizons query from %s", url)

        try:
            with request.urlopen(url) as response:  # noqa: S310
                data = response.read().decode()

            if save_to:
                with Path.open(save_to, "w") as f:
                    f.write(data)

        except Exception as e:
            logger.exception("Horizon query raising %s", type(e).__name__)
            msg = f"Failed to retrieve data from Horizons API: {e}"
            raise HorizonsAPIError(msg) from e

        return data

    def get_major_bodies(self, save_to: Path | None = None) -> list[MajorBody]:
        """Get a list of major bodies.

        Arguments:
            save_to (Path | None): Optional path to save the raw response data.

        Returns:
            list[MajorBody]: A list of major bodies.

        """
        result_text = self._request(
            {
                "COMMAND": "MB",
                "OBJ_DATA": "YES",
                "MAKE_EPHEM": "NO",
            },
            save_to=save_to,
        )
        return MajorBodyTableParser().parse(result_text)

    def get_object_data(self, object_id: int, *, small_body: bool = False, save_to: Path | None = None) -> ObjectData:
        """Get physical data for a specific body.

        Arguments:
            object_id (int): The ID of the object.
            small_body (bool): Whether the object is a small body.
            save_to (Path | None): Optional path to save the raw response data.

        Returns:
            ObjectData: The physical data for the object.

        """
        result_text = self._request(
            {
                "COMMAND": str(object_id) + (";" if small_body else ""),
                "OBJ_DATA": "YES",
                "MAKE_EPHEM": "NO",
            },
            save_to=save_to,
        )

        return ObjectDataParser().parse(result_text)

    def get_vectors(
        self, object_id: int, time_options: TimePeriod, center: int = 10, save_to: Path | None = None
    ) -> VectorData:
        """Get positional vectors for a specific body.

        Arguments:
            object_id (int): The ID of the object.
            time_options (TimePeriod): The time period for the ephemeris.
            center (int): The object id for center for the ephemeris. Default 10 for the sun.
            save_to (Path | None): Optional path to save the raw response data.

        Returns:
            VectorData: The positional vectors for the object.

        """
        result_text = self._request(
            {
                "COMMAND": str(object_id),
                "OBJ_DATA": "NO",
                "MAKE_EPHEM": "YES",
                "EPHEM_TYPE": "VECTORS",
                "CENTER": f"@{center}",
                "START_TIME": time_options.start.strftime(self.TIME_FORMAT),
                "STOP_TIME": time_options.end.strftime(self.TIME_FORMAT),
                "STEP_SIZE": time_options.step,
            },
            save_to=save_to,
        )

        vector_data = VectorDataParser().parse(result_text)
        if vector_data is None:
            msg = "Failed to find all vector components in the text."
            logger.warning(msg)
            raise ParsingError(msg)
        return vector_data
