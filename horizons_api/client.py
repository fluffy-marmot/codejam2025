import logging
import re
from datetime import datetime
from pathlib import Path
from urllib import parse, request

from .exceptions import HorizonsAPIError
from .models import MajorBody, ObjectData, VectorData
from .parsers import parse_body_table

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

    def get_major_bodies(self) -> list[MajorBody]:
        """Get a list of major bodies.

        Returns:
            list[MajorBody]: A list of major bodies.

        """
        result_text = self._request(
            {
                "COMMAND": "MB",
                "OBJ_DATA": "YES",
                "MAKE_EPHEM": "NO",
            }
        )
        return parse_body_table(result_text)

    def get_object_data(self, object_id: int, *, small_body: bool = False) -> ObjectData:
        """Get physical data for a specific body.

        Arguments:
            object_id (int): The ID of the object.
            small_body (bool): Whether the object is a small body.

        Returns:
            ObjectData: The physical data for the object.

        """
        result_text = self._request(
            {
                "COMMAND": str(object_id) + (";" if small_body else ""),
                "OBJ_DATA": "YES",
                "MAKE_EPHEM": "NO",
            }
        )

        radius_match = re.search(r"Radius \(km\)\s*=\s*([\d\.]+)", result_text)
        radius = float(radius_match.group(1)) if radius_match else None

        return ObjectData(radius=radius)

    def get_vectors(
        self, object_id: int, start_time: datetime, stop_time: datetime, *, step_size: str = "2d", center: int = 10
    ) -> VectorData:
        """Get positional vectors for a specific body.

        Arguments:
            object_id (int): The ID of the object.
            start_time (datetime): The start time for the ephemeris.
            stop_time (datetime): The stop time for the ephemeris.
            step_size (str): The step size for the ephemeris.
            center (int): The object id for center for the ephemeris. Default 10 for the sun.

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
                "START_TIME": start_time.strftime(self.TIME_FORMAT),
                "STOP_TIME": stop_time.strftime(self.TIME_FORMAT),
                "STEP_SIZE": step_size,
            }
        )

        pattern = r"\s*=\s*(-?[\d\.]+E[\+-]\d\d)"
        x_match = re.search("X" + pattern, result_text)
        y_match = re.search("Y" + pattern, result_text)
        z_match = re.search("Z" + pattern, result_text)

        if not x_match or not y_match or not z_match:
            msg = "Could not parse vector data from response."
            raise HorizonsAPIError(msg)

        return VectorData(
            x=float(x_match.group(1)),
            y=float(y_match.group(1)),
            z=float(z_match.group(1)) if z_match else None,
        )
