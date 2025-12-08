from flask import Flask, render_template, jsonify, request, session, abort, redirect
from flask_socketio import SocketIO, send, emit
import secrets, time, socket, hashlib, json, logging

app = Flask(__name__.split(".")[0])
app.config["SECRET_KEY"] = secrets.token_hex(16)
key = hashlib.sha256(app.config["SECRET_KEY"].encode("utf-8")).hexdigest()
websocket = SocketIO(app)

def startLogger():
    log = logging.getLogger(__name__)
    log.setLevel("INFO")
    if not log.handlers:
        handler = logging.FileHandler("static/app.log", encoding="utf-8")
        streamHandler = logging.StreamHandler()
        fmt = "{asctime} [{levelname}] -- {message}"
        formatter = logging.Formatter(fmt, style="{")
        handler.setFormatter(formatter)
        streamHandler.setFormatter(formatter)
        log.addHandler(handler)
        log.addHandler(streamHandler)
    return log

log = startLogger()
log.info(f"Secret key generated! Hash: {key}")

# Little bit of color never hurt anybody :)
def coloredText(stuff, colorcode):
    return f"\033[{code}m{text}\033[0m"



try:
    with open("static/bulletins.json", "w") as file:
        data = {
                    "bulletins": []
                }
        json.dump(data, file)

    with open("static/config.json", "r") as file:
        data = json.load(file)
        assert type(data) == dict

except (AssertionError, json.decoder.JSONDecodeError):
    with open("static/config.json", "w") as file:
        data = {
                "title": None,
                "services": {
                    "chat": True,
                    "bulletins": True
                    },
                "files": []
                }
        json.dump(data, file)
    log.exception("Error loading config.json")


@app.route("/")
def main():
    return render_template("main.html")

@app.route("/log")
def log():
    with open("static/app.log", "r") as log:
        return log.read().encode("utf-8"), 200


# ======== Control Panel ======== #
# Can add an admin login page at a later time.

@app.route("/control", methods=['GET'])
def control():
    # check user.logged-in logic, for later
    # return redirect("/login"), 301
    return render_template("control.html")

@app.route("/controlapi", methods=['GET', 'POST'])
def controlapi():
    if request.method == "GET":
        with open('static/config.json', "r") as file:
            return jsonify(json.load(file).encode("utf-8")), 200
    else:
        data = request.form
        new = {
                "title": data["title"],
                "services": data["services"],
                "files": data["files"]
                }
        with open("static/config.json", "w") as file:
            json.dump(data, file)
        log.info("config rewritten!")
        return "rewritten", 200



# The actual login page
# @app.route("/login")
# def login():
#     return render_template("login.html")

@app.route("/chat")
def chat():
    return render_template("chat.html")




# ======== Bulletins ======== #

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
    data = {
            "title": bulletin["title"],
            "body": bulletin["body"],
            "time": time.time(),
            "exp-time": None #bulletin["expires"]
        }
    with open("static/bulletins.json", "r") as file:
        old = json.load(file)
    old["bulletins"] = old["bulletins"] + [data]
    with open("static/bulletins.json", "w") as file:
        json.dump(old, file)
    return redirect("/bulletins"), 301




# ======== Chat Stuff ========== #

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

