from flask import Flask, render_template
import pandas as pd
import os

app = Flask(__name__)
CSV_PATH = os.path.join("data", "warsaw_highschools_2024.csv")

@app.route("/")
def index():
    df = pd.read_csv(CSV_PATH)
    data = df.to_dict(orient="records")
    return render_template("index.html", data=data)

if __name__ == "__main__":
    app.run(debug=True)