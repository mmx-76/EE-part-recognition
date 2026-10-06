import os

from flask import Flask, jsonify, render_template, request

import db

app = Flask(__name__)
app.config["DATABASE"] = os.path.join(app.root_path, "connectors.db")


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/connectors")
def api_list():
    return jsonify(db.list_connectors(app.config["DATABASE"]))


@app.get("/api/connectors/<int:connector_id>")
def api_get(connector_id):
    connector = db.get_connector(app.config["DATABASE"], connector_id)
    if connector is None:
        return jsonify(error="No such connector."), 404
    return jsonify(connector)


@app.post("/api/connectors")
def api_add():
    data = request.get_json(silent=True) or {}
    details = data.get("details") or {}
    try:
        new_id = db.add_connector(
            app.config["DATABASE"],
            name=data.get("name"),
            pins=details.get("pins"),
            gender=details.get("gender", "unknown"),
            industry=details.get("industry", "unknown"),
            rows=data.get("rows"),
        )
    except db.InvalidConnector as problem:
        return jsonify(error=str(problem)), 400
    return jsonify(id=new_id), 201


@app.delete("/api/connectors/<int:connector_id>")
def api_delete(connector_id):
    if not db.delete_connector(app.config["DATABASE"], connector_id):
        return jsonify(error="No such connector."), 404
    return jsonify(ok=True)


db.init_db(app.config["DATABASE"])

if __name__ == "__main__":
    app.run(debug=True)
