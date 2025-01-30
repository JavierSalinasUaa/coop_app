from functools import wraps
from flask import redirect, request, session, url_for, flash
from flask_login import current_user

def role_required(required_role=[]):
    def wrapper(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            rol_usuario = session.get('role')
            if not current_user.is_authenticated or rol_usuario not in required_role:
                flash("No tienes permiso para acceder a esta página.", "error")
                # Redirige a la página anterior o a la página de inicio si no se encuentra referrer
                return redirect(request.referrer or '/')
            return f(*args, **kwargs)
        return decorated_function
    return wrapper