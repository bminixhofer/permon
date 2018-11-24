import secrets
import getpass
import os
import hashlib
from appdirs import user_data_dir
from permon import config

secret_path = os.path.join(user_data_dir('permon', 'bminixhofer'),
                           'SECRET_KEY')


def get_secret_key():
    if os.path.exists(secret_path):
        return open(secret_path).read()
    else:
        token = secrets.token_hex()
        with open(secret_path, 'w') as f:
            f.write(token)

        return token


def prompt_password():
    passwords_match = False
    while not passwords_match:
        password = hashlib.sha256(
            getpass.getpass('Enter Password: ').encode('utf-8')
        ).hexdigest()
        verify_password = hashlib.sha256(
            getpass.getpass('Verify Password: ').encode('utf-8')
        ).hexdigest()
        if password == verify_password:
            passwords_match = True
        else:
            print('Passwords do not match.')

    config.set_config({
        'password': password
    })
