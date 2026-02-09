import sqlite3 as sql, time, functools
from typing import Dict, Any, Optional

class Bulletin:
    def __init__(self, id: int):
        """
        Initialize a Bulletin object given a row ID.
        """
        with sql.connect("myop.db") as c:
            c.row_factory = sql.Row
            cur = c.cursor()
            cur.execute("SELECT * FROM bulletins WHERE id = ?;", (id,))
            bulletin = cur.fetchone()
            if bulletin is None:
                raise ReferenceError("Bulletin does not exist")
            expires = bulletin["expires"]
            if expires is not None and int(expires) <= int(time.time()):
                cur.execute("DELETE FROM bulletins WHERE id = ?", (id,))
                c.commit()
                raise ReferenceError("Bulletin has expired")
        self.id = bulletin["id"]
        self.origin = bulletin["origin"]
        self.timestamp = bulletin["timestamp"]
        self.title = bulletin["title"]
        self.body = bulletin["body"]
        self.expires = bulletin["expires"]
        self._deleted = False
        return None

    def isntdeleted(func):
        """
        Wrapper to ensure property self._deleted is not true before executing a function on a row that doesn't exist.
        ONLY WORKS ON INSTANCE METHODS,
        NOT CLASS OR STATIC METHODS.
        """
        @functools.wraps(func)
        def wrapper(self, *args, **kwargs):
            if getattr(self, "_deleted", False):
                raise ReferenceError("Bulletin was deleted")
            return func(self, *args, **kwargs)
        return wrapper
    
    @isntdeleted
    def edit(self, **kwargs):
        allowed_columns = (
                "title",
                "body",
                "origin",
                "timestamp",
                "timestampstr",
                "expires"
                )
        columns = []
        values = []
        for key, value in kwargs.items():
            if key not in allowed_columns:
                raise ValueError(f"Key {key} not allowed")
            columns.append(f"{key} = ?")
            values.append(value)

        if not columns: return self
        sqlstmt = f"""
        UPDATE bulletins
        SET {", ".join(columns)}
        WHERE id = ?"""
        values.append(self.id)
        with sql.connect("myop.db") as c:
            cur = c.cursor()
            cur.execute(sqlstmt, values)
            c.commit()
        return Bulletin(self.id)

    @isntdeleted
    def delete(self):
        """
        Deletes the object.
        Object properties are still accessible.
        """
        with sql.connect("myop.db") as c:
            cur = c.cursor()
            cur.execute("DELETE FROM bulletins WHERE id = ?", (self.id,))
            c.commit()
        self._deleted = True
        return self

    @isntdeleted
    def to_dict(self):
        return {
                "origin": self.origin,
                "title": self.title,
                "body": self.body,
                "timestamp": self.timestamp,
                "expires": self.expires,
                "id": self.id
                }

    @classmethod
    def new_bulletin(cls, title: str, origin: str, expiresin: int, body: str=""):
        """
        Given the parameters of a bulletin, add a new bulletin to the table.
        Returns a Bulletin object.
        Note: expiresin is an integer in minutes.
        """
        timestamp = time.time()
        expires = time.time() + (60*int(expiresin))
        with sql.connect("myop.db") as c:
            cur = c.cursor()
            cur.execute("INSERT INTO bulletins (title, body, origin, timestamp, expires) VALUES (?,?,?,?,?)",
                        (title,
                         body,
                         origin,
                         timestamp,
                         expires)
                        )
            c.commit()
            return cls(cur.lastrowid)

    @classmethod
    def from_row(cls, row: sql.Row):
        obj = cls.__new__(cls)
        obj._load_from_row(row)
        obj._deleted = False
        return obj

    def _load_from_row(self, row: sql.Row):
        self.origin = row["origin"]
        self.title = row["title"]
        self.body = row["body"]
        self.timestamp = int(row["timestamp"])
        self.expires = int(row["expires"]) if row["expires"] is not None else None
        self.id = int(row["id"])

    @classmethod
    def purge_expired(cls, now: Optional[int] = None):
        if now is None:
            now = int(time.time())
        with sql.connect("myop.db") as c:
            cur = c.cursor()
            cur.execute(
                "DELETE FROM bulletins WHERE expires IS NOT NULL AND expires <= ?;",
                (now,),
            )
            c.commit()
            return cur.rowcount

    @classmethod
    def get_all_bulletins(cls):
        cls.purge_expired()
        with sql.connect("myop.db") as c:
            c.row_factory = sql.Row
            cur = c.cursor()
            cur.execute("SELECT * FROM bulletins ORDER BY timestamp DESC;")
            bulletins = [cls.from_row(row) for row in cur.fetchall()]
            return bulletins

    @classmethod
    def filter_user(cls, user: str):
        cls.purge_expired()
        bulletins = []
        with sql.connect("myop.db") as c:
            c.row_factory = sql.Row
            cur = c.cursor()
            cur.execute("SELECT * FROM bulletins WHERE origin = ?", (user,))
            for row in cur.fetchall():
                bulletins.append(Bulletin(row["id"]))
            return bulletins
