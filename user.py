from db import Database
import uuid
from werkzeug.security import generate_password_hash, check_password_hash
import re


class User:
    PASSWORD_PATTERN = r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
    email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'

    @staticmethod
    def add_user(username, email, password):
        user_id = str(uuid.uuid4())  # Generate a random UUID
        hashed_password = generate_password_hash(password)
        Database.insert("users", ["id", "username", "email", "password"], [user_id, username, email, hashed_password])

    @staticmethod
    def email_exists(email):
        result = Database.select("users", ["email"], "email = ?", (email,))
        return result is not None

    @staticmethod
    def check_user(email, password):
        user = Database.select("users", ["id", "username", "email", "password"], "email = ?", (email,))
        if user and check_password_hash(user[3], password):
            return user
        return None

    @staticmethod
    def get_user_by_id(user_id):
        return Database.select("users", ["id", "username", "email", "password"], "id = ?", (user_id,))

    @staticmethod
    def is_valid_password(password):
        return bool(re.match(User.PASSWORD_PATTERN, password))

    @staticmethod
    def is_valid_email(email):
        return bool(re.match(User.email_pattern, email))