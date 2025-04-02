import sqlite3
from hashlib import sha256
from secrets import token_bytes
from time import time
from settings import Settings

class UsersDBHandler:
    SALT_LENGTH = 8
    PEPPER = b"my_secret_pepper"

    def __init__(self, db_path=Settings.DATABASE_PATH.value) -> None:
        self.db_path = db_path
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS users (
                                    username TEXT UNIQUE NOT NULL PRIMARY KEY,
                                    email TEXT UNIQUE NOT NULL,
                                    password TEXT NOT NULL,
                                    salt TEXT NOT NULL)"""
            )
            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def is_username_exist(self, username):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username=?", (username,))
            return cursor.fetchone() is not None

    def is_email_exist(self, email):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email=?", (email,))
            return cursor.fetchone() is not None

    def get_email(self, username):
        if not self.is_username_exist(username):
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT email FROM users WHERE username=?", (username,))
            email = cursor.fetchone()[0]
            return email

    def get_username(self, email) -> str:
        if not self.is_email_exist(email):
            return None
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT username FROM users WHERE email=?", (email,))
            username = cursor.fetchone()[0]
            return username

    def is_password_ok(self, username, password):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT password, salt FROM users WHERE username=?", (username,)
            )
            stored_password, stored_salt = cursor.fetchone()

            if stored_password:
                hashed_password = sha256(
                    password.encode() + stored_salt + UsersDBHandler.PEPPER
                ).hexdigest()
                return hashed_password == stored_password
            return False

    def save_user(self, username, email, password) -> None:
        salt = token_bytes(UsersDBHandler.SALT_LENGTH)
        hashed_password = sha256(
            password.encode() + salt + UsersDBHandler.PEPPER
        ).hexdigest()
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO users (username, email, password, salt) VALUES (?, ?, ?, ?)",
                (username, email, hashed_password, salt),
            )
            conn.commit()

    def update_user_password(self, username, new_password) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT salt FROM users WHERE username=?", (username,))
            stored_salt = cursor.fetchone()[0]
            hashed_password = sha256(
                new_password.encode() + stored_salt + UsersDBHandler.PEPPER
            ).hexdigest()
            cursor.execute(
                "UPDATE users SET password=? WHERE username=?", (hashed_password, username)
            )
            conn.commit()

    def delete_user(self, username) -> None:
        if self.is_username_exist(username):
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM users WHERE username=?", (username,))
                conn.commit()


class EmailCodeDBHandler:
    TIMEOUT = Settings.EMAIL_CODE_TIMEOUT.value  # 5 minutes

    def __init__(self, db_path=Settings.DATABASE_PATH.value) -> None:
        self.db_path = db_path
        self.create_table()
        self.clean_expired_codes()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS emails (
                                    email TEXT UNIQUE NOT NULL PRIMARY KEY,
                                    timeout FLOAT NOT NULL)"""
            )
            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def is_email_exist(self, email) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM emails WHERE email=?", (email,))
            return cursor.fetchone() is not None

    def is_timeout_passed(self, email) -> bool:
        if not self.is_email_exist(email):
            return True
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT timeout FROM emails WHERE email=?", (email,))
            timeout = cursor.fetchone()[0]
            return time() > timeout

    def save_email(self, email) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO emails (email, timeout) VALUES (?, ?)",
                (email, time() + EmailCodeDBHandler.TIMEOUT),
            )
            conn.commit()

    def delete_email(self, email) -> None:
        if self.is_email_exist(email):
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM emails WHERE email=?", (email,))
                conn.commit()

    def clean_expired_codes(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM emails WHERE timeout < ?", (time(),))
            conn.commit()

    def delete_table(self) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE IF EXISTS emails")
            conn.commit()

class DomainsDBHandler:
    def __init__(self, db_path=Settings.DATABASE_PATH.value) -> None:
        self.db_path = db_path
        self.create_table()

    def create_table(self):
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """CREATE TABLE IF NOT EXISTS domains (
                                    domain TEXT UNIQUE NOT NULL PRIMARY KEY,
                                    username TEXT NOT NULL,
                                    time FLOAT NOT NULL)"""
            )
            conn.commit()

    def get_connection(self):
        return sqlite3.connect(self.db_path)

    def save_domain(self, domain, username) -> None:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT OR REPLACE INTO domains (domain, username, time) VALUES (?, ?, ?)",
                (domain, username, time()),
            )
            conn.commit()

    def is_domain_exist(self, domain) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM domains WHERE domain=?", (domain,))
            return cursor.fetchone() is not None

if __name__ == "__main__":
    # example usage:
    db_test = UsersDBHandler()
    """if not db_test.is_username_exist("user1"):
        db_test.save_user("user1", "user1@example.com", "password123")
    print(db_test.is_username_exist("user1"))
    print(db_test.is_password_ok("user1", "password123"))
    print(db_test.is_password_ok("user1", "pass123"))
    db_test.update_user_password("user1", "newpassword456")
    print(db_test.get_username("user1@example.com"))
    if not db_test.is_username_exist("itamar"):
        db_test.save_user("itamar", "dalalitamar@gmail.com", "dllilo05")
    print(db_test.is_username_exist("itamar"))
    print(db_test.is_email_exist("dalalitamar@gmail.com"))
    print(db_test.get_email("itamar"))
    print(db_test.is_password_ok("itamar", "dllilo05"))"""
    db_test.delete_user("itamar")
    #email_db_test = EmailCodeDBHandler()
    #email_db_test.save_email("dalalitamar@gmail.com")
    # print(email_db_test.is_timeout_passed("dalalitamar@gmail.com"))
    # email_db_test.delete_email("dalalitamar@gmail.com")
    # email_db_test.clean_expired_codes()