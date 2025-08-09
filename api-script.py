import logging
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

    """
    this is a special query that returns info of major bodies ("MB") in the solar system,
    useful for knowing the IDs of planets, moons etc. that horizons refers to things as internally
    """
    horizons_query(
        query_params={
            "COMMAND": "MB",
            "OBJ_DATA": "YES",
            "MAKE_EPHEM": "NO",
        },
        save_to=horizons_path / "majorbody.txt",
    )
