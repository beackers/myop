from flask import Flask, render_template, jsonify, request, session, abort, redirect
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, send, emit
import secrets, time, socket, hashlib, json, logging, sqlite3, functools


# -------- SETUP -------- #

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
        fmt = "{asctime} [{levelname}]: \n{message}"
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

except:
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

# Check if logged in decorator
def logged_in(route):
    @functools.wraps(route)
    def wrapper_logged_in(*args, **kwargs):
        # for now just worry about the decorator
        with sqlite3.connect("myop.db") as c:
            cur = c.cursor()
            if session.get("user"):
                cur.execute("SELECT * FROM users WHERE callsign=?", (session.get("username")))
                if not session.get("username") in cur.fetchall():
                    log.debug("user redirected to login")
                    return redirect("/login")
                else:
                    log.debug("user passed")
                    return route(*args, **kwargs)
            else:
                log.info("user passed without login")
                return route(*args, **kwargs)
    return wrapper_logged_in

# csrf checking
def needs_csrf(route):
    @functools.wraps(route)
    def wrapper_csrf(*args, **kwargs):
        if "csrf" in session:
            return route(*args, **kwargs)
        else:
            session["csrf"] = secrets.token_hex(16)
            return route(*args, **kwargs)
    return wrapper_csrf


# ------------ APP ------------- #

# Misc. routes
@app.route("/")
@logged_in
def main():
    with open("static/config.json", "r") as f:
        title = json.load(f)["title"]
    return render_template("main.html", title=title)

@app.route("/log")
@logged_in
def showlog():
    with open("static/app.log", "r") as log:
        return log.read().encode("utf-8"), 200


# ======== Control Panel ======== #

@app.route("/control", methods=['GET'])
@logged_in
@needs_csrf
def control():
    return render_template("control.html", csrf=session["csrf"])

@app.route("/controlapi", methods=['GET', 'POST'])
@logged_in
def controlapi():
    if request.method == "GET":
        with open('static/config.json', "r") as file:
            data = json.load(file)
            log.debug(f"Sending Current Config File:\n{data}")
            return jsonify(data), 200
    elif request.method == "POST":
        data = request.form
        if not data.get("csrf"): abort(403)
        if not data.get("csrf") == session["csrf"]: abort(403)
        new = {
                "title": data.get("title"),
                "services": {
                    "chat": data.get("chat") is not None,
                    "bulletins": data.get("bulletins") is not None
                    }
                }
        with open("static/config.json", "w") as file:
            json.dump(new, file)
            log.info("config rewritten!")
            return redirect('/control', code=301)



# The actual login page
# Pro tip: no @logged_in (for obvious reasons)
@app.route("/login", methods=["GET", "POST"])
@needs_csrf
def login():
    if request.method == "GET":
        return render_template("login.html", username=session.get("username") or "", csrf=session["csrf"])
    elif request.method == "POST":
        u = request.form
        if ("csrf" or "username" or "password")not in u: abort(403)
        if session["csrf"] != u["csrf"]: abort(403)
        log.debug("login form passed basic qualifications")
        with sqlite3.connect("myop.db") as c:
            cur = c.cursor()
            c.row_factory = sqlite3.Row
            cur.execute("SELECT callsign, pwdhash FROM users WHERE (callsign = ?)", (u["username"].lower(),))
            row = cur.fetchone()
            if row is None:
                log.warning(f"someone tried to log in, but username didn't exist\nusername: {u["username"]}")
                abort(403)
            if (row) and (check_password_hash(row["pwdhash"], u["password"])):
                session["user"] = row["callsign"]
                log.info("user logged in!")
                return redirect("/", code=301)
            else:
                log.warning(f"someone failed a login!\nusername: {u["username"]}")
                abort(403)
    elif request.method == "DELETE":
        session["user"] = None
        return redirect("/login", code=301)




# ======== Bulletins ======== #

@app.route("/bulletins", methods=['GET'])
@logged_in
@needs_csrf
def bulletins():
    with open("static/config.json", "r") as f:
        config = json.load(f)
        if not config.get("services").get("bulletins"): return render_template("disabled.html"), 403
    return render_template("bulletins.html", csrf=session["csrf"], uname="None")

@app.route("/bulletinsapi", methods=["GET"])
@logged_in
def bulletinsapiget():
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
            "expires": bulletin[5]
        })
    return jsonify(data), 200

@app.route("/bulletinsapi", methods=["POST"])
@logged_in
def bulletinsapipost():
    posted = request.form.get("csrf")
    stored = session.get("csrf")
    if not posted or posted != stored:
        abort(403)
    bulletin = request.form
    log.debug(f"{bulletin=}")
    if not isinstance(bulletin, dict):
        abort(403)
    if ("title" and "expires" and "origin") not in bulletin: abort(403)
    log.debug("bulletin passed basic qualifications")
    with sqlite3.connect("myop.db") as c:
        cur = c.cursor()
        cur.execute(
                "INSERT INTO bulletins (origin, title, body, timestamp, expires) VALUES (?,?,?,?,?)",
                (bulletin.get("origin"), bulletin.get("title"), bulletin.get("body"), bulletin.get("timestamp"), bulletin.get("expires"))
                )
        c.commit()
    log.debug("Changes commited")
    return redirect("/bulletins"), 301

@app.route("/bulletinsapi", methods=['DELETE'])
@logged_in
def bulletinsapidelete():
    with sqlite3.connect("myop.db") as c:
        cur = c.cursor()
        cur.execute("DELETE FROM bulletins;")
        c.commit()
    return jsonify({"status": 200})



# ======== Chat Stuff ========== #

@app.route("/chat", methods=['GET'])
@logged_in
def chat():
    with open("static/config.json", "r") as f:
        config = json.load(f)
        if not config.get("services").get("chat"): return render_template("disabled.html"), 403
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
        log.error("Something happened!", exc_info=1)
        pass

