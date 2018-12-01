import secrets
import getpass
import os
import hashlib
from appdirs import user_data_dir
from permon import config

data_dir = user_data_dir('permon', 'bminixhofer')
secret_path = os.path.join(data_dir, 'SECRET_KEY')


def get_secret_key():
    """
    Get the secret key. This key is created once and stays the same afterwards.
    """
    os.makedirs(data_dir, exist_ok=True)

    if os.path.exists(secret_path):
        return open(secret_path).read()
    else:
        token = secrets.token_hex()
        with open(secret_path, 'w') as f:
            f.write(token)

        return token


def encrypt_password(password):
    """Deterministically encrypt a password."""
    return hashlib.sha256(password.encode('utf-8')).hexdigest()


def prompt_password():
    """Prompt the user to set a password."""
    passwords_match = False
    while not passwords_match:
        password = encrypt_password(getpass.getpass('Enter Password: '))
        verify_password = encrypt_password(
            getpass.getpass('Verify Password: '))

        if password == verify_password:
            passwords_match = True
        else:
            print('Passwords do not match.')

    config.set_config({
        'password': password
    })
