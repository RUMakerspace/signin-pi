from flask_bcrypt import Bcrypt
from flask_login import UserMixin
from tinydb import TinyDB, where

## User container class
class Users:
    __DB = None
    __BC = None

    # Initialize the TinyDB
    def __init__(self, path, app):
        self.__DB = TinyDB(path)
        self.__BC = Bcrypt(app)

        # The makerspace user shouldn't ever have the password changed.
        # This also ensures there's always a user to get in if running on a new system for the first time.
        # TODO: On install, you should create a new user.
        self.__DB.upsert(
            {
                "username": "Rutgers",
                "password_hash": self.__BC.generate_password_hash("Makerspace").decode(
                    "utf-8"
                ),
            },
            where("username") == "Rutgers",
        )

    # Add a user if they do not exist
    def add_user(self, username, password):
        if not self.__DB.search(where("username") == username):
            self.__DB.insert(
                {
                    "username": username,
                    "password_hash": self.__BC.generate_password_hash(password),
                }
            )

    # Find a user and generate its User object
    def find_user(self, username):
        users = self.__DB.search(where("username") == username)
        if users:
            user = users[0]
            return self.User(user["username"], user["password_hash"])

    def remove_user(self, username):
        self.__DB.remove(where("username") == username)

    def try_login_user(self, username, password):
        user = None
        users = self.__DB.search(where("username") == username)

        if users:
            user = users[0]

        if user and self.__BC.check_password_hash(user["password_hash"], password):
            return self.User(user["username"], user["password_hash"])
        else:
            return None

    ## Flask User Model
    class User(UserMixin):
        def __init__(self, u, pw_h):
            self.id = u
            self.password_hash = pw_h

        def __repr__(self):
            return f"{self.id}: {self.password_hash}"
