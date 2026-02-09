from flask import Flask, render_template, jsonify, request, session, abort, redirect, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_socketio import SocketIO, send, emit
import secrets, time, socket, hashlib, json, logging, sqlite3, functools, re
import userfunc, bullfunc


# -------- SETUP -------- #

# App + WebSocket
app = Flask(__name__.split(".")[0])
app.config["SECRET_KEY"] = secrets.token_hex(16)
websocket = SocketIO(app)



# Little bit of color never hurt anybody :)
def coloredText(text, code):
    return f"\033[{code}m{text}\033[0m"

ansiescapere = re.compile(r"\x1B\[[0-?]*[ -/]*[@-~]")
class AnsiEscapeFormatter(logging.Formatter):
    def format(self, record):
        msg = super().format(record)
        return ansiescapere.sub("", msg)

# Logging
def startLogger():

    log = logging.getLogger(__name__)
    log.setLevel("INFO")
    if not log.handlers:
        handler = logging.FileHandler("static/app.log", encoding="utf-8")
        streamHandler = logging.StreamHandler()
        fmt = "{asctime} [{levelname}]: \n{message}"
        formatter = logging.Formatter(fmt, style="{")
        escapedformatter = AnsiEscapeFormatter(fmt, style="{")
        handler.setFormatter(escapedformatter)
        streamHandler.setFormatter(formatter)
        log.addHandler(handler)
        log.addHandler(streamHandler)
    return log

log = startLogger()
log.info("System check starting.")
log.info(coloredText("Secret key generated!", "34"))
logging.getLogger("werkzeug").setLevel(logging.ERROR)
app.logger.setLevel(logging.WARNING)


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
                log.info("Bootstrap admin is accessing page")
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
    app.config["BOOTSTRAP_ADMIN"] = {
            "callsign": "BOOTSTRAP_ADMIN",
            "pwdhash": generate_password_hash("bootstrapbill"),
            "active": 1,
            "permissions": 1,
            "name": None
            }
else:
    app.config["BOOTSTRAP_ADMIN"] = None



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

@app.errorhandler(500)
def err500(e):
    return f"{str(e)}\n{e.name}\n{e.description}", e.code

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
    bulletins = bullfunc.Bulletin.get_all_bulletins()
    bulletins = [ b.to_dict() for b in bulletins ]
    return render_template("control.html", csrf=session["csrf"], users=users, bulletins=bulletins)

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
    new = userfunc.User.new_user(
            callsign = newuser["callsign"].lower(),
            name = newuser["name"],
            active = 1,
            permissions = newuser["permissions"],
            pwd = newuser["password"]
            )
    if new.permissions > 0 and admin_exists() and app.config.get("BOOTSTRAP_ADMIN") is not None:
        app.config["BOOTSTRAP_ADMIN"] = None
        session.clear()
        return redirect("/login", 301)
    log.info(f"New user added! \nCallsign: {newuser['callsign']}")
    return redirect("/control", 301)


@app.route("/control/user/<int:id>", methods=["GET", "POST", "DELETE"])
@logged_in(1)
@needs_csrf
def view_or_edit_user(id: int):
    try: user = userfunc.User(id=id)
    except Exception as e:
        print(e)
        return e, 500
    if request.method == "GET":
        return render_template("view_user.html", csrf=session["csrf"], user=user)
    elif request.method == "DELETE":
        if user.permissions >= 1 and admin_exists() == 1:
            log.critical("Last active admin was almost deleted!")
            return "cannot delete last admin", 409
        if request.headers.get("csrf") != session["csrf"]:
            return "CSRF token didn't match", 403
        user.delete()
        return jsonify({"status": 200}), 200
    elif request.method == "POST":
        f = dict(request.get_json())
        if session["csrf"] != f["csrf"]: return "CSRF token doesn't match. Try reloading.", 409
        f["active"] = bool(int(f.get("active") or 0))
        f["permissions"] = int(f.get("permissions") or 0)
        if f["active"] == 0 and user.permissions == 1 and admin_exists() == 1:
            log.critical("Nearly deactivated last admin!")
            return "cannot deactivate last admin", 409
        if user.permissions == 1 and admin_exists() == 1 and f["permissions"] < 1:
            log.critical("Nearly locked all users out of control panel!")
            return "cannot change last admin to normal user", 409
        editable_fields = ["callsign", "name", "active", "permissions"]
        old = user.to_dict()
        diff = {
                k: f[k]
                for k in editable_fields
                if k in f and f[k] != old[k]
                }
        if not diff and f["pwdhash"] is None:
            return "No changes were submitted", 301
        if diff:
            try: user.edit(**diff)
            except Exception as e:
                log.exception(e)
                return str(e), 500
        if f["pwdhash"] is not None:
            user.set_new_password(f["pwdhash"])
            log.info(f"{coloredText(user.callsign, 36)}'s password was changed by {coloredText(session['user'], 31)}")
        return "Changes saved", 200


# --------- LOGIN ---------- #

@app.route("/login", methods=["GET", "POST", "DELETE"])
@needs_csrf
def login():
    if request.method == "GET":
        return render_template("login.html", csrf=session["csrf"], loggedinas=session.get("user"))

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
        if app.config.get("BOOTSTRAP_ADMIN") and u["username"] == app.config["BOOTSTRAP_ADMIN"]["callsign"] and not admin_exists():
            if check_password_hash(app.config["BOOTSTRAP_ADMIN"]["pwdhash"], u["password"]):
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
            flash("That callsign doesn't exist.\nIf it should, contact an admin.")
            return redirect('/login', code=301)
        if user.pwdhash and (check_password_hash(user.pwdhash, u["password"])):
            session["user"] = user.callsign
            return redirect("/", code=301)
        elif not user.pwdhash:
            session["user"] = user.callsign
            return redirect("/", code=301)
        else:
            log.info("someone attempted login with a wrong password")
            flash("That password didn't match, can you try that again?")
            return redirect('/login', code=301)

    elif request.method == "DELETE":
        session.clear()
        return jsonify({"status": 200})




# ======== Bulletins ======== #

@app.route("/bulletins", methods=['GET', "POST"])
@logged_in()
@needs_csrf
def bulletins():
    with open("static/config.json", "r") as f:
        config = json.load(f)
        if not config.get("services").get("bulletins"): return render_template("disabled.html"), 403
    if request.method == "GET":
        return render_template("bulletins.html", csrf=session["csrf"])
    elif request.method == "POST":
        newbull = request.form
        if not newbull.get("csrf") or newbull["csrf"] != session["csrf"]:
            abort(409, "CSRF token didn't match. Try reloading.")
        bullfunc.Bulletin.new_bulletin(
                origin = session["user"],
                title = newbull["title"],
                body = newbull.get("body"),
                expiresin = newbull["expiresin"]
                )
        return render_template("bulletins.html", csrf=session["csrf"], origin=session["user"])



@app.route("/bulletins/all", methods=["GET", "DELETE"])
@logged_in()
@needs_csrf
def allbulletins():
    if request.method == "GET":
        bulletins = bullfunc.Bulletin.get_all_bulletins()
        bulletins = [ b.to_dict() for b in bulletins ]
        return jsonify({
            "bulletins": bulletins,
            "status": 200
            })
    elif request.method == "DELETE":
        j = request.get_json()
        if j.get("csrf") != session["csrf"]:
            return "CSRF token didn't match", 409
        bulletins = bullfunc.Bulletin.get_all_bulletins()
        for b in bulletins:
            try: b.delete()
            except Exception as e:
                log.info(f"Failed to delete bulletin with ID {b.id}\n{e}")
                return f"Couldn't delete bulletin {b.id}", 500
        return jsonify({
            "status": 200
            })

@app.route("/bulletins/<int:id>", methods=["GET", "UPDATE", "DELETE"])
@logged_in()
@needs_csrf
def onebulletin(id: int):
    try:
        bulletin = bullfunc.Bulletin(id)
    except ReferenceError:
        abort(404, "Bulletin not found.")
    if request.method == "GET":
        return render_template("view_bulletin.html", bulletin=bulletin)
    elif request.method == "UPDATE":
        j = request.get_json()
        og = bulletin.to_dict()
        acceptable_fields = { "title", "origin", "body" }
        diff = {
                k: j[k]
                for k in acceptable_fields
                if k in j and j[k] != og[k]
                }
        if not diff: return "No changes were submitted", 304
        try: bulletin.edit(**diff)
        except Exception as e:
            log.error(f"/bulletins/{id}: error in editing bulletin {bulletin.id}\n{e}")
            return e, 500
        return "Accepted and edited", 200
    elif request.method == "DELETE":
        bulletin.delete()
        return "Successfully deleted post", 200



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
        print(f"New Message: {data.get('msg', ' ')}\nFrom station: {data.get('username')}")
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
