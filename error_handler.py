from functools import wraps
from flask import jsonify


def handle_errors(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            print(f"Error encountered: {str(e)}")
            return jsonify(error=str(e)), 500
    return wrapper
