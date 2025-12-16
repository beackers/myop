from flask import Flask, render_template, jsonify, request, session, abort, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, send, emit
import secrets, time, socket, hashlib, json, logging, sqlite3, functools
import userfunc


# -------- SETUP -------- #

# App + WebSocket
app = Flask(__name__.split(".")[0])
app.config["SECRET_KEY"] = secrets.token_hex(16)
websocket = SocketIO(app)



# Little bit of color never hurt anybody :)
def coloredText(text, code):
    return f"\033[{code}m{text}\033[0m"


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
log.info("System check starting.")
log.info(coloredText("Secret key generated!", "34"))


# Database
with sqlite3.connect("myop.db") as conn:
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            callsign TEXT NOT NULL UNIQUE,
            name TEXT NOT NULL,
            pwdhash TEXT,
            permissions INTEGER NOT NULL DEFAULT 0 CHECK (permissions IN (0,1)),
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
log.info(coloredText("Database is online and ready", "34"))


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
log.info(coloredText("Configuration file is online and ready", "34"))

# Check if logged in decorator
def logged_in(permissions=0):
    def wrapper(route):
        @functools.wraps(route)
        def wrapper_logged_in(*args, **kwargs):
            if session.get("user") == "BOOTSTRAP_ADMIN":
                log.info("Bootstrap admin is accessing page:")
                return route(*args, **kwargs)
            if session.get("user"):
                user = userfunc.User(session["user"])
                if user.active and (user.permissions >= permissions):
                    return route(*args, **kwargs)
                else:
                    log.warning("Someone just tried to access a page, but wasn't active or didn't have permissions")
                    if not user.active:
                        abort(403, "User's account is not active. If it should be, contact an administrator.")
                    elif not user.permissions >= permissions:
                        abort(403, "User's account doesn't have the right permissions. If you should, contact an administrator.")
            else:
                # for not-logged-in people
                flash("please log in before continuing")
                return redirect("/login", code=301)
        return wrapper_logged_in
    return wrapper

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

def admin_exists():
    with sqlite3.connect("myop.db") as c:
        c.row_factory = sqlite3.Row
        cur = c.cursor()
        cur.execute("SELECT * FROM users WHERE permissions = 1;")
        return len(cur.fetchall())


log.info(coloredText("Key functions defined", "34"))

if not admin_exists():
    BOOTSTRAP_ADMIN = {
            "callsign": "BOOTSTRAP_ADMIN",
            "pwdhash": generate_password_hash("bootstrapbill"),
            "active": 1,
            "permissions": 1,
            "name": None
            }
else:
    BOOTSTRAP_ADMIN = None



# ------------ APP ------------- #

# Misc. routes
@app.route("/")
@logged_in()
def main():
    with open("static/config.json", "r") as f:
        title = json.load(f)["title"]
    return render_template("main.html", title=title)

@app.route("/log")
@logged_in()
def showlog():
    with open("static/app.log", "r") as log:
        return log.read().encode("utf-8"), 200

# ======== Control Panel ======== #

@app.route("/control", methods=['GET'])
@logged_in(1)
@needs_csrf
def control():
    with sqlite3.connect("myop.db") as c:
        c.row_factory = sqlite3.Row
        cur = c.cursor()
        cur.execute("SELECT * FROM users ORDER BY name")
        users = cur.fetchall()
    return render_template("control.html", csrf=session["csrf"], users=users)

@app.route("/controlapi", methods=['GET', 'POST'])
@logged_in(1)
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


@app.route("/control/user/add", methods=["GET", "POST"])
@logged_in(1)
@needs_csrf
def add_user():
    if request.method == "GET":
        return render_template("add_user.html", csrf=session["csrf"])
    
    newuser = request.form

    # qualifications
    if "csrf" not in newuser or "callsign" not in newuser or "permissions" not in newuser:
        log.warning("someone tried to add a new user, but forgot basic deets")
        abort(500)
    if newuser["csrf"] != session["csrf"]:
        log.warning("/control/user/add: CSRF didn't match")
        abort(403)

    log.debug("/control/user/add: form passed basic qualifications")
    userfunc.new_user(
            callsign = newuser["callsign"].lower(),
            name = newuser["name"],
            active = 1,
            permissions = newuser["permissions"],
            pwd = newuser["password"]
            )
    if newuser["permissions"] == 1 and admin_exists() and BOOTSTRAP_ADMIN:
        BOOTSTRAP_ADMIN = None
        session.clear()
    log.info(f"New user added! \nCallsign: {newuser["callsign"]}")
    return redirect("/control", 301)


@app.route("/control/user/<int:id>", methods=["GET", "POST", "DELETE"])
@logged_in(1)
@needs_csrf
def view_or_edit_user(id: int):
    try: user = userfunc.User(id=id)
    except Exception as e:
        print(e)
        abort(500)
    if request.method == "GET":
        return render_template("view_user.html", csrf=session["csrf"], user=user)
    elif request.method == "DELETE":
        if user.permissions == 1 and admin_exists() == 1:
            log.critical("Last active admin was almost deleted!")
            abort(409, "cannot delete last admin")
        if request.headers.get("csrf") != session["csrf"]:
            abort(403, "CSRF token didn't match")
        user.delete()
        return jsonify({"status": 200}), 200
    elif request.method == "POST":
        if session["csrf"] != request.form["csrf"]: abort(403)
        f = request.form
        if f.get("active"):
            active = 1
        else:
            active = 0
        if active == 0 and user.permissions == 1 and admin_exists() == 1:
            log.critical("Nearly deactivated last admin!")
            abort(409, "cannot deactivate last admin")
        permissions = int(f.get("permissions"))
        user.edit(
                name=f.get("name"),
                permissions=permissions,
                callsign=f.get("callsign").lower(),
                active=active
                )
        if f.get("password"):
            user.set_new_password(f["password"])
        return redirect("/control", code=301)


# --------- LOGIN ---------- #

@app.route("/login", methods=["GET", "POST", "DELETE"])
@needs_csrf
def login():
    if request.method == "GET":
        return render_template("login.html", username=session.get("username") or "", csrf=session["csrf"], loggedinas=session.get("user"))

    elif request.method == "POST":
        u = request.form
        # check csrf, un exist
        if "csrf"  not in u or "username" not in u:
            log.info("/login: request didn't pass BQ")
            abort(403)
        if session["csrf"] != u["csrf"]:
            log.info("/login: CSRF didn't match")
            abort(403)

        # bootstrap operation
        if BOOTSTRAP_ADMIN and u["username"] == BOOTSTRAP_ADMIN["callsign"] and not admin_exists():
            if check_password_hash(BOOTSTRAP_ADMIN["pwdhash"], u["password"]):
                session["user"] = "BOOTSTRAP_ADMIN"
                return redirect("/control/user/add", 301)
            else:
                log.info("someone just tried to log in as bootstrap admin")
                abort(403)

        # normal user
        try:
            user = userfunc.User(u["username"].lower())
        except:
            log.info("someone tried to log in with a username that doesn't exist")
            abort(400)
        if user.pwdhash and (check_password_hash(user.pwdhash, u["password"])):
            session["user"] = user.callsign
            return redirect("/", code=301)
        elif not user.pwdhash:
            session["user"] = user.callsign
            return redirect("/", code=301)
        else:
            log.info("someone attempted login with a wrong password")
            abort(403)

    elif request.method == "DELETE":
        session.clear()
        return jsonify({"status": 200})




# ======== Bulletins ======== #

@app.route("/bulletins", methods=['GET'])
@logged_in()
@needs_csrf
def bulletins():
    with open("static/config.json", "r") as f:
        config = json.load(f)
        if not config.get("services").get("bulletins"): return render_template("disabled.html"), 403
    return render_template("bulletins.html", csrf=session["csrf"], uname="None")

@app.route("/bulletinsapi", methods=["GET"])
@logged_in()
def bulletinsapiget():
    with sqlite3.connect("myop.db") as c:
        c.row_factory = sqlite3.Row
        cur = c.cursor()
        cur.execute("SELECT * FROM bulletins")
        b = cur.fetchall()
    data = {
            "bulletins": []
            }
    for bulletin in b:
        data["bulletins"].append({
            "origin": bulletin["origin"],
            "title": bulletin["title"],
            "body": bulletin["body"],
            "timestamp": bulletin["timestamp"],
            "expires": bulletin["expires"]
        })
    return jsonify(data), 200

@app.route("/bulletinsapi", methods=["POST"])
@logged_in()
def bulletinsapipost():
    posted = request.form.get("csrf")
    stored = session.get("csrf")
    if not posted or posted != stored:
        abort(403, "CSRF didn't match. Try reloading the page.")
    bulletin = request.form
    if not isinstance(bulletin, dict):
        abort(403, "Bulletin must be in the form of a dictionary. Contact administrators.")
    if "title" not in bulletin or "expires" not in bulletin:
        abort(403, "bulletin must have a title and expiration time. Revise the bulletin.")
    expires = bulletin["expires"]
    expires = (time.time() + (int(expires)*60))*1000
    with sqlite3.connect("myop.db") as c:
        cur = c.cursor()
        cur.execute(
                "INSERT INTO bulletins (origin, title, body, timestamp, expires) VALUES (?,?,?,?,?)",
                (session["user"],
                 bulletin.get("title"),
                 bulletin.get("body"),
                 time.time()*1000,
                 expires)
                )
        c.commit()
    return redirect("/bulletins"), 301

@app.route("/bulletinsapi", methods=['DELETE'])
@logged_in()
def bulletinsapidelete():
    with sqlite3.connect("myop.db") as c:
        cur = c.cursor()
        cur.execute("DELETE FROM bulletins;")
        c.commit()
    return jsonify({"status": 200})



# ======== Chat Stuff ========== #

@app.route("/chat", methods=['GET'])
@logged_in()
def chat():
    with open("static/config.json", "r") as f:
        config = json.load(f)
        if not config.get("services").get("chat"): return render_template("disabled.html"), 403
    return render_template("chat.html", callsign = session["user"])

@websocket.on("message")
def newMsg(data):
    try:
        print(f"New Message: {data.get("msg", " ")}\nFrom station: {data.get("username")}")
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
