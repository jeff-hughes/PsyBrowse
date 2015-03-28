import os
from django.utils.crypto import get_random_string

def generate_secret_key(path=None):
    if path is None:
        dir = os.path.abspath(os.path.dirname(__file__))
        path = os.path.join(dir, 'secret_key.py')

    chars = 'abcdefghijklmnopqrstuvwxyz0123456789!@#$%^&*(-_=+)'
    key = get_random_string(50, chars)
    text = "SECRET_KEY = '{:s}'\n".format(key)

    with open(path, 'w') as file:
        file.write(text)