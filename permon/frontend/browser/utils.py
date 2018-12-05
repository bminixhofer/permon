import flask_login


# simple user model, we only need one user
class User(flask_login.UserMixin):
    def __init__(self, user_id):
        self.id = user_id
        self.name = 'user'
        self.password_hash = self.name + '_secret'

    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password_hash)
