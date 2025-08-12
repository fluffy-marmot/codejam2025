import json
from pathlib import Path

from flask import Flask, render_template

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)

"""
planets.json contains some various data about the planets
"""
with Path.open(BASE_DIR / "horizons_data" / "planets.json") as f:
    planets_info = json.load(f)

""" 
using a flask backend to serve a very simple html file containing a canvas that we draw on using
very various pyscript scripts. We can send the planets_info variable along with the render_template
request so that it will be accessible in the index.html template and afterwards the pyscript scripts
"""

@app.route("/")
def index():
    return render_template("index.html", planets_info=planets_info)

if __name__ == "__main__":
    app.run(debug=True)