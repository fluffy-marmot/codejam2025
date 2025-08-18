import json
from pathlib import Path

from flask import Flask, render_template

""" 
using a flask backend to serve a very simple html file containing a canvas that we draw on using
very various pyscript scripts. We can send the planets_info variable along with the render_template
request so that it will be accessible in the index.html template and afterwards the pyscript scripts
"""
app = Flask(__name__)

base_dir = Path(__file__).resolve().parent
static_dir = base_dir / "static"
sprite_dir = static_dir / "sprites"
audio_dir = static_dir / "audio"

# contains various information and game data about planets
with Path.open(base_dir / "horizons_data" / "planets.json", encoding='utf-8') as f:
    planets_info = json.load(f)

# create a list of available sprite files
sprite_list = [sprite_file.stem for sprite_file in sprite_dir.iterdir() if sprite_file.is_file()]

# create a list of available audio files
audio_list = [audio_file.name for audio_file in audio_dir.iterdir()]

with Path.open(static_dir / "lore.txt") as f:
    lore = f.read()

with Path.open(static_dir / "credits.txt") as f:
    credits = f.read()

@app.route("/")
def index():
    return render_template(
        "index.html", 
        planets_info=planets_info, 
        sprite_list=sprite_list, 
        audio_list=audio_list,
        lore=lore,
        credits=credits
    )

if __name__ == "__main__":
    app.run(debug=True)
