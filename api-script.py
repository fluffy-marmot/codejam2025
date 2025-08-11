import json
import logging
import re
from datetime import UTC, datetime, timedelta
from pathlib import Path

from horizons_api import HorizonsClient, TimePeriod

# api access point
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
HORIZONS_DATA_DIR = "horizons_data"

# set logging config here, since this is a standalone script
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

if __name__ == "__main__":
    client = HorizonsClient()
    # create dir for horizons API data if it doesn't already exist
    script_path = Path(__file__).resolve().parent
    horizons_path = script_path / HORIZONS_DATA_DIR
    if not horizons_path.exists():
        Path.mkdir(horizons_path, parents=True, exist_ok=True)

    with Path.open(horizons_path / "planets.json") as f:
        template = json.load(f)

    """
    This is a special query that returns info of major bodies ("MB") in the solar system,
    useful for knowing the IDs of planets, moons etc. that horizons refers to things as internally.
    """
    major_bodies = client.get_major_bodies(save_to=horizons_path / "major_bodies.txt")

    today = datetime.now(tz=UTC)
    tomorrow = today + timedelta(days=1)

    for planet in template:
        id = planet["id"]
        name = planet["name"]

        """
        This query type returns kind of a messy info dump on physical characteristics of a planet;
        we probably don't need most of this, but some stuff may be useful like radius of each planet
        to decide how big to draw them? will create files like "599-Earth-info.txt" in horizons/ dir.
        """
        client.get_object_data(id, save_to=horizons_path / f"{id}-{name}-info.txt")

        if id == 10:
            continue  # skip sun since we don't need its position

        """
        This is used to get coordinates, can be given a small stepsize to get many snapshots of coordinates
        but for now we only need a single one, using today's date. The return is a big text dump with a lot of
        random text info attached, using regex to extract the X and Y coordinates. I think if we ignore Z
        coordinate, it should be basically be a projection along ecliptic plane which is a good enough
        representation of planet positions for a simple game.
        """
        time_period = TimePeriod(start=today, end=tomorrow)
        pos_response = client.get_vectors(id, time_period)
        planet["x"] = pos_response.x
        planet["y"] = pos_response.y

    with Path.open(horizons_path / "planets.json", "w") as f:
        json.dump(template, f, indent=4)
