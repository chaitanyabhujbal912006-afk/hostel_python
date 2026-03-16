from functools import wraps

from flask import redirect, session


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "admin" not in session:
            return redirect("/")
        return view(*args, **kwargs)

    return wrapped_view
