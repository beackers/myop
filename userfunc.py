import sqlite3
from werkzeug.security import generate_password_hash

class User:
    def __init__(self, callsign: str=None, id: int=None):
        self._deleted = False
        try:
            assert callsign or id
        except AssertionError:
            raise SyntaxError("Must initialize a user with either an id or a callsign, 0 given")
        try:
            with sqlite3.connect("myop.db") as c:
                c.row_factory = sqlite3.Row
                cur = c.cursor()
                if callsign:
                    cur.execute("SELECT * FROM users WHERE callsign = ?;", (callsign,))
                if id:
                    cur.execute("SELECT * FROM users WHERE id = ?;", (id,))
                row = cur.fetchone()
            assert row
        except AssertionError:
            raise AssertionError(f"User {callsign or id} doesn't exist but should")
        self.id = row["id"]
        self.name = row["name"]
        self.pwdhash = row["pwdhash"]
        self.callsign = row["callsign"]
        if row["permissions"] == 0:
            self.permissions = False
        elif row["permissions"] == 1:
            self.permissions = True
        else:
            self.permissions = None
        self.active = bool(row["active"])
        return None


    def delete(self):
        with sqlite3.connect("myop.db") as c:
            c.row_factory = sqlite3.Row
            cur = c.cursor()
            cur.execute("DELETE FROM users WHERE id = ?", (self.id,))
            c.commit()
        self._deleted = True
        return

    def edit(self, **kwargs):
        with sqlite3.connect("myop.db") as c:
            c.row_factory = sqlite3.Row
            cur = c.cursor()
            attr = []
            for key in kwargs.keys():
                attr.append(f"{key} = '{kwargs[key]}'")
            attr = ", ".join(attr)
            cur.execute(
                    f"UPDATE users SET {attr} WHERE id = ?",
                    (self.id,)
                    )
            c.commit()
            self.__init__(id=self.id)

def new_user(callsign: str, name: str=None, permissions: int=0, active: int=0, pwd: str=None):
    with sqlite3.connect("myop.db") as c:
        c.row_factory = sqlite3.Row
        cur = c.cursor()
        if pwd:
            pwd = generate_password_hash(pwd)
        print(callsign, name, permissions, active, pwd)
        cur.execute("""
        INSERT INTO users (callsign, name, permissions, pwdhash, active) VALUES (?,?,?,?,?);
        """,
                    (callsign, name, permissions, pwd, active)
                    )
        c.commit()
    return User(callsign)

