import os

from flask import Flask, jsonify, render_template, request

import db
import matching

app = Flask(__name__)
app.config["DATABASE"] = os.path.join(app.root_path, "connectors.db")


@app.route("/")
def home():
    return render_template("index.html")


@app.get("/api/connectors")
def api_list():
    with_drawings = request.args.get("rows") == "1"
    return jsonify(db.list_connectors(app.config["DATABASE"], include_rows=with_drawings))


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


@app.put("/api/connectors/<int:connector_id>")
def api_update(connector_id):
    data = request.get_json(silent=True) or {}
    details = data.get("details") or {}
    try:
        found = db.update_connector(
            app.config["DATABASE"], connector_id,
            name=data.get("name"),
            pins=details.get("pins"),
            gender=details.get("gender", "unknown"),
            industry=details.get("industry", "unknown"),
            rows=data.get("rows"),
        )
    except db.InvalidConnector as problem:
        return jsonify(error=str(problem)), 400
    if not found:
        return jsonify(error="No such connector."), 404
    return jsonify(ok=True)


@app.patch("/api/connectors/<int:connector_id>/reviewed")
def api_reviewed(connector_id):
    data = request.get_json(silent=True) or {}
    if not db.set_reviewed(app.config["DATABASE"], connector_id, bool(data.get("reviewed", True))):
        return jsonify(error="No such connector."), 404
    return jsonify(ok=True)


@app.post("/api/search")
def api_search():
    data = request.get_json(silent=True) or {}
    details = data.get("details") or {}
    pins = details.get("pins")
    gender = details.get("gender", "unknown")
    try:
        db.validate_rows(data.get("rows"))
        db.validate_pins_and_gender(pins, gender)
        matches = matching.search(app.config["DATABASE"], data["rows"], pins, gender, limit=5)
    except db.InvalidConnector as problem:
        return jsonify(error=str(problem)), 400
    for match in matches:  # show every score as a whole percentage
        for key in ("score", "drawing_score", "pin_score", "gender_score"):
            if match[key] is not None:
                match[key] = round(match[key] * 100)
    return jsonify(matches)


@app.delete("/api/connectors/<int:connector_id>")
def api_delete(connector_id):
    if not db.delete_connector(app.config["DATABASE"], connector_id):
        return jsonify(error="No such connector."), 404
    return jsonify(ok=True)


db.init_db(app.config["DATABASE"])

if __name__ == "__main__":
    app.run(debug=True)
