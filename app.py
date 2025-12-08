from flask import Flask, render_template, jsonify, request, session, abort, redirect
from flask_socketio import SocketIO, send, emit
import secrets, time, socket, hashlib, json, logging, sqlite3


# App + WebSocket
app = Flask(__name__.split(".")[0])
app.config["SECRET_KEY"] = secrets.token_hex(16)
key = hashlib.sha256(app.config["SECRET_KEY"].encode("utf-8")).hexdigest()
websocket = SocketIO(app)

# Logging
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


# Database
with sqlite3.connect("myop.db") as conn:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            callsign TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            pwdhash TEXT NOT NULL,
            permissions TEXT NOT NULL,
            active INTEGER NOT NULL DEFAULT 0 CHECK (active IN (0,1))
        );
            """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS bulletins (
            id INTEGER PRIMARY KEY,
            origin TEXT NOT NULL,
            title TEXT NOT NULL,
            body TEXT,
            timestamp INTEGER NOT NULL DEFAULT CURRENT_TIMESTAMP,
            expires INTEGER
        )
            """)
    conn.commit()


# Little bit of color never hurt anybody :)
def coloredText(stuff, colorcode):
    return f"\033[{code}m{text}\033[0m"


# Set up files
try:
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



# Misc. routes
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



# ======== Bulletins ======== #

@app.route("/bulletins", methods=['GET'])
def bulletins():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return render_template("bulletins.html", csrf=session["csrf"])

@app.route("/bulletinsapi", methods=["GET"])
def bulletinsapi():
    with sqlite3.connect("myop.db") as c:
        cur = c.cursor()
        cur.execute("SELECT * FROM bulletins")
        b = cur.fetchall()
    data = {
            "bulletins": []
            }
    for bulletin in b:
        data["bulletins"].append({
            "origin": bulletin[1],
            "title": bulletin[2],
            "body": bulletin[3],
            "timestamp": bulletin[4],
            "expires": bulletins[5]
        })
    return jsonify(data), 200

@app.route("/bulletinsapi", methods=["POST"])
def bulletinsapipost():
    posted = request.form.get("csrf")
    stored = session.get("csrf")
    if not posted or posted != stored:
        abort(403)
    bulletin = request.form
    if not isinstance(bulletin, dict):
        abort(403)
    if ("title" and "expires" and "origin") not in bulletin: abort(403)
    with sqlite3.connect("myop.db") as c:
        cur = c.cursor()
        cur.execute(
                "INSERT INTO bulletins (origin, title, body, timestamp, expires) VALUES (?,?,?,?,?)",
                (bulletin["origin"], bulletin["title"], bulletin["body"], bulletin["timestamp"], bulletin["expires"])
                )
        c.commit()
    return redirect("/bulletins"), 301




# ======== Chat Stuff ========== #

@app.route("/chat", methods=['GET'])
def chat():
    return render_template("chat.html")

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

