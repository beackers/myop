import sqlite3, functools
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
        self.permissions = int(row["permissions"])
        self.active = bool(row["active"])
        return None


    def _load_from_row(self, row: sqlite3.Row):
        self.id = row["id"]
        self.callsign = row["callsign"]
        self.pwdhash = row["pwdhash"]
        self.name = row["name"]
        self.active = bool(row["active"])
        self.permissions = int(row["permissions"])

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
            attr = [ f"{key} = ?"
                    for key in kwargs.keys()
                    if key != "pwdhash"
                    ]
            values = tuple( value
                      for key, value in kwargs.items()
                      if key != "pwdhash"
                      )
            if "pwdhash" in kwargs.keys():
                attr.append("pwdhash = ?")
                values = values + (generate_password_hash(kwargs["pwdhash"]),)
            values = values + (self.id,)
            attr = ", ".join(attr)
            cur.execute(
                    f"UPDATE users SET {attr} WHERE id = ?",
                    values
                    )
            c.commit()
            return self.__init__(id=self.id)

    def set_new_password(self, newpwd: str):
        newpwd = generate_password_hash(newpwd)
        with sqlite3.connect("myop.db") as c:
            cur = c.cursor()
            cur.execute("UPDATE users SET pwdhash = ? WHERE id = ?;", (newpwd, self.id))
            c.commit()
        return User(id=self.id)

    @classmethod
    def new_user(cls, callsign: str, name: str=None, permissions: int=0, active: int=0, pwd: str=None):
        with sqlite3.connect("myop.db") as c:
            c.row_factory = sqlite3.Row
            cur = c.cursor()
            if pwd:
                pwd = generate_password_hash(pwd)
            cur.execute("""
            INSERT INTO users (callsign, name, permissions, pwdhash, active) VALUES (?,?,?,?,?);
            """,
                        (callsign, name, permissions, pwd, active)
                        )
            c.commit()
        return cls(callsign)

    @classmethod
    def get_all_users(cls):
        with sqlite3.connect("myop.db") as c:
            c.row_factory = sqlite3.Row
            cur = c.cursor()
            cur.execute("SELECT * FROM users ORDER BY id ASC")
            return [ cls.from_row(row) for row in cur.fetchall() ]

    @classmethod
    def from_row(cls, row: sqlite3.Row):
        obj = cls.__new__(cls)
        obj._load_from_row(row)
        obj._deleted = False
        return obj
