import sqlite3


class FDataBase:
    def __init__(self, db):
        self.__db = db
        self.__cur = db.cursor()

    def adduser(self, name, surname, email, age, work, position, password, photo):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email LIKE '{email}'")
            res = self.__cur.fetchone()
            if res:
                print("Пользователь с таким email уже существует")
                return ("Error 1")
            if name == 'admin':
                self.__cur.execute(f"SELECT * FROM users WHERE name LIKE 'admin'")
                res = self.__cur.fetchone()
                if res:
                    print("Не пытайтесь зарегистрировать еще одного админа")
                    return("Error 2")
            if name == 'admin':
                self.__cur.execute("INSERT INTO users VALUES(NULL,?, ?, ?, ?, ?, ?, ?, ?, ?)",
                                   (name, surname, email, age, work, position, password, photo, 'Админ'))
            else:
                self.__cur.execute("INSERT INTO users VALUES(NULL,?, ?, ?, ?, ?, ?, ?, ?, ?)", (name, surname, email, age, work, position, password, photo, 'Пользователь'))
            self.__db.commit()
        except sqlite3.Error as e:
            print("Ошибка добавления пользователя в БД "+str(e))
            return False
        return True

    def getUser(self, userId):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE id = {userId} LIMIT 1")
            res = self.__cur.fetchone()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения пользователя из БД "+str(e))
        return(False, False)

    def getAllUsers(self):
        try:
            self.__cur.execute(f"SELECT * FROM users")
            res = self.__cur.fetchall()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения пользователя из БД "+str(e))
        return []

    def getUserByEmail(self, email):
        try:
            self.__cur.execute(f"SELECT * FROM users WHERE email = '{email}'")
            res = self.__cur.fetchone()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения пользователя из БД "+str(e))
        return(False)

    def updateUser(self, id, name, surname, email, age, work, position):
        try:

            self.__cur.execute(f"UPDATE users SET name = '{name}', surname='{surname}', email='{email}', age='{age}', worked='{work}', post='{position}' WHERE id = '{id}'")
            res = self.__cur.fetchone()
            if res:
                return res
        except sqlite3.Error as e:
            print("Ошибка получения пользователя из БД "+str(e))
        #return(False)
