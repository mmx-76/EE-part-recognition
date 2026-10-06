from flask import Flask

app = Flask(__name__)


@app.route("/")
def home():
    return "<h1>Connector Finder</h1><p>Hello! The app is running.</p>"


if __name__ == "__main__":
    app.run(debug=True)
