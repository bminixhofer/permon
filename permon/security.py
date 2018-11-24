from appdirs import user_data_dir
import secrets
import os
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
