class UserLogin():
    def fromDB(self, user_id, db):
        self.__user = db.getUser(user_id)
        return self

    def create(self, user):
        self.__user = user
        return self

    def is_auth(self):
        return True

    def is_active(self):
        return True

    def is_anon(self):
        return False

    def get_id(self):
        return str(self.__user['id'])

    def get_login(self):
        return str(self.__user['name'] + ' ' + self.__user['surname'])
