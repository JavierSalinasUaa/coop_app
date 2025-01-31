from werkzeug.security import check_password_hash, generate_password_hash
from flask_login import UserMixin


class Usuario(UserMixin):
    def __init__(self, user_id, username, role = None):
        self.id = user_id
        self.username = username
        self.role = role
