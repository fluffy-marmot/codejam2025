import json
import logging
import re
from datetime import datetime, timedelta, UTC
from pathlib import Path
from urllib import parse, request

# api access point
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
HORIZONS_DATA_DIR = "horizons"

# set logging config here, since this is a standalone script
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


def horizons_query(query_params: dict, save_to: Path | None = None) -> str | None:
    """Generate Horizons API call.

    Generate a Horizons API call using the given query parameters and either save it to the
    specified Path, or return the response as a string if no Path given.
    """
    try:
        # the default format, so we don't need to include this in every call
        if "format" not in query_params:
            query_params["format"] = "text"

        url = f"{HORIZONS_URL}?{parse.urlencode(query_params)}"
        log.info("Horizons query from %s", url)

        bin_response = request.urlopen(url).read()  # noqa: S310
        text_response = bin_response.decode()
        log.info("Received response of %s bytes", len(bin_response))

        if save_to:
            with Path.open(save_to, "w") as f:
                f.write(text_response)
        else:
            return text_response
    except Exception as e:
        log.exception("horizons_query raising %s", type(e).__name__)
        raise


if __name__ == "__main__":
    # create dir for horizons API data if it doesn't already exist
    script_path = Path(__file__).resolve().parent
    horizons_path = script_path / HORIZONS_DATA_DIR
    if not horizons_path.exists():
        Path.mkdir(horizons_path, parents=True, exist_ok=True)

    with Path.open(horizons_path / "template.json") as f:
        template = json.load(f)

    """
    This is a special query that returns info of major bodies ("MB") in the solar system,
    useful for knowing the IDs of planets, moons etc. that horizons refers to things as internally.
    """
    horizons_query(
        query_params={
            "COMMAND": "MB",
            "OBJ_DATA": "YES",
            "MAKE_EPHEM": "NO",
        },
        save_to=horizons_path / "majorbody.txt",
    )

    for planet in template:
        id = planet["id"]
        name = planet["name"]

        now = datetime.now(UTC)
        today = now.strftime("%Y-%m-%d")  # format as "yyyy-mm-dd" which API expects
        tomorrow = (now + timedelta(days=1)).strftime("%Y-%m-%d")

        """
        This query type returns kind of a messy info dump on physical characteristics of a planet;
        we probably don't need most of this, but some stuff may be useful like radius of each planet
        to decide how big to draw them? will create files like "599-Earth-info.txt" in horizons/ dir.
        """
        horizons_query(
            query_params={
                "COMMAND": str(id),
                "OBJ_DATA": "YES",  # just give some random info dump about physical characters
                "MAKE_EPHEM": "NO",  # no position predictions
            },
            save_to=horizons_path / f"{id}-{name}-info.txt",
        )

        """
        This is used to get coordinates, can be given a small stepsize to get many snapshots of coordinates
        but for now we only need a single one, using today's date. The return is a big text dump with a lot of
        random text info attached, using regex to extract the X and Y coordinates. I think if we ignore Z
        coordinate, it should be basically be a projection along ecliptic plane which is a good enough
        representation of planet positions for a simple game.
        """
        pos_response = horizons_query(
            query_params={
                "COMMAND": str(id),
                "OBJ_DATA": "NO",  # we already got the OBJ_DATA info in a separate query
                "MAKE_EPHEM": "YES",  # use this to get position vectors
                "EPHEM_TYPE": "VECTORS",
                "CENTER": "@10",  # 10 is the API's id for sun, so the coordinate system is sun-centered
                "START_TIME": today,  # american date format
                "STOP_TIME": tomorrow,
                "STEP_SIZE": "2d",  # gap of 1d between start, stop and 2d step should return single result?
            },
            save_to=None,
        )

        # TODO: should probably add error checking for the re searches and horizons queries
        # looking for patterns like "X =-2367823E+10" or "Y = 27178E-02" since the API returns coordinates
        # in scientific notation
        planet["x"] = float(re.search(r"X =\s*(-?[\d\.]+E[\+-]\d\d)", pos_response).group(1))
        planet["y"] = float(re.search(r"Y =\s*(-?[\d\.]+E[\+-]\d\d)", pos_response).group(1))

    with Path.open(horizons_path / "planets.json", "w") as f:
        json.dump(template, f, indent=4)
