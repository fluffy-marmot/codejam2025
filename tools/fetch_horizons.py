import json
import logging
from datetime import UTC, datetime, timedelta
from pathlib import Path

from horizons_api import HorizonsClient, TimePeriod

# api access point
HORIZONS_URL = "https://ssd.jpl.nasa.gov/api/horizons.api"
HORIZONS_DATA_DIR = "horizons_data"

SUN_ID = 10

# set logging config here, since this is a standalone script
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

if __name__ == "__main__":
    client = HorizonsClient()
    # create dir for horizons API data if it doesn't already exist
    working_dir = Path.cwd()
    horizons_path = working_dir / HORIZONS_DATA_DIR
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
        id: int = planet["id"]
        name: str = planet["name"]
        time_period = TimePeriod(start=today, end=tomorrow)

        object = client.get_object_data(id)

        if id == SUN_ID:
            continue  # skip sun since we don't need its position

        pos_response = client.get_vectors(id, time_period)
        planet["info"] = object.text

    with Path.open(horizons_path / "planets.json", "w") as f:
        json.dump(template, f, indent=4)
