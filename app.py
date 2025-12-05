from flask import Flask, render_template, jsonify, request, session, abort, redirect
from flask_socketio import SocketIO, send, emit
import secrets, time, socket, hashlib, json

app = Flask(__name__.split(".")[0])
app.config["SECRET_KEY"] = secrets.token_hex(16)
key = hashlib.sha256(app.config["SECRET_KEY"].encode("utf-8")).hexdigest()
print(f"Secret key generated! Hash: {key}")
websocket = SocketIO(app)

with open("static/bulletins.json", "w") as file:
    data = {
                "bulletins": []
            }
    json.dump(data, file)

@app.route("/")
def main():
    return render_template("main.html")

@app.route("/control")
def control():
    return render_template("login.html")

@app.route("/chat")
def chat():
	return render_template("chat.html")

@app.route("/bulletins", methods=['GET'])
def bulletins():
    with open("static/bulletins.json", "r") as file:
        data = json.load(file)
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return render_template("bulletins.html", csrf=session["csrf"])

@app.route("/bulletinsapi", methods=["GET"])
def bulletinsapi():
    with open("static/bulletins.json", "r") as file:
        data = json.load(file)
    return jsonify(data), 200

@app.route("/bulletinsapi", methods=["POST"])
def bulletinsapipost():
    posted = request.form.get("csrf")
    stored = session.get("csrf")
    if not posted or posted != stored:
        abort(403)
    bulletin = request.form
    # May need to get changed based on how I want this to be formatted.
    # Note to self: potentially use SQLite in future for better data management.
    if not isinstance(bulletin, dict):
        abort(403)
    if "title" not in bulletin: abort(403)
    if "body" not in bulletin: abort(403)
    print(bulletin)
    data = {
            "title": bulletin["title"],
            "body": bulletin["body"],
            "time": time.time(),
            "exp-time": None #bulletin["expires"]
        }
    with open("static/bulletins.json", "r") as file:
        old = json.load(file)
        print(str(old))
    old["bulletins"] = old["bulletins"] + [data]
    print(str(old))
    with open("static/bulletins.json", "w") as file:
        json.dump(old, file)
    return redirect("/bulletins"), 301



@websocket.on("message")
def newMsg(data):
	try:
		print("New Message:" + data.get("msg", " "))
		dataToSend = {
			"timestamp": time.asctime(),
			"username": data.get("username", "unknown"),
			"message": data.get("msg", "<blank>")
		}
		dataType = "message"
	except Exception as e:
		dataToSend = {
			"timestamp": "SYSTEM",
			"username": str(type(e)),
			"message": str(e)
		}
		print("Handled exception in newMsg()")
		dataType = "error"

	finally:
		emit(dataType, dataToSend, broadcast=True)

if __name__ == "__main__":
	try:
		websocket.run(app, host="0.0.0.0", port=5000)
	except Exception as inst:
		emit("error", {
			"timestamp": time.asctime(),
			"title": str(type(inst)),
			"detail": str(e)
		})
		pass

