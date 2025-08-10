from flask import Flask, render_template
import json
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)

with Path.open(BASE_DIR / "horizons" / "planets.json") as f:
    planets_info = json.load(f)

@app.route("/")
def index():
    return render_template("index.html", planets_info=planets_info)

if __name__ == "__main__":
    app.run(debug=True)