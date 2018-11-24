import flask_login


# simple user model, we only need one user
class User(flask_login.UserMixin):
    def __init__(self, id):
        self.id = id
        self.name = 'user'
        self.password_hash = self.name + '_secret'

    def __repr__(self):
        return "%d/%s/%s" % (self.id, self.name, self.password_hash)
