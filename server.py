from datetime import datetime

from fastapi import FastAPI, Request, Depends
from fastapi_jwt_auth import AuthJWT
from fastapi_jwt_auth.exceptions import AuthJWTException
from fastapi.responses import JSONResponse
from typing import List
from pydantic import BaseModel
from bcrypt import hashpw, gensalt, checkpw
import sqlite3


app = FastAPI()
db_name = 'dataBase.db'


def create_tables(connect, cursor):
    cursor.execute('CREATE TABLE IF NOT EXISTS Library(ID INTEGER,'
                   'Name TEXT,'
                   'Author TEXT,'
                   'Year INTEGER,'
                   'Count INTEGER,'
                   'OnHandsCount INTEGER,'
                   'CountTakes INTEGER,'
                   'AllTime INTEGER,'
                   'middle_time TEXT,'
                   'frequency TEXT,'
                   'add_time TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS NotInLibrary(ID INTEGER,'
                   'Name TEXT,'
                   'Author TEXT,'
                   'Year INTEGER,'
                   'takeID INTEGER,'
                   'timeTake TEXT,'
                   'takerID TEXT)')
    cursor.execute('CREATE TABLE IF NOT EXISTS Users(login TEXT,'
                   'password TEXT,'
                   'type TEXT)')
    connect.commit()


class JWTSettings(BaseModel):
    authjwt_secret_key: str = "SECRET"


@AuthJWT.load_config
def get_config():
    return JWTSettings()


@app.exception_handler(AuthJWTException)
def authjwt_exception_handler(request: Request, exc: AuthJWTException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message}
    )


class UserData(BaseModel):
    login: str
    password: str


class AddBook(BaseModel):
    data: List


def get_max_takes(cursor):
    try:
        cursor.execute("SELECT MAX(takeID) FROM NotInLibrary")
        max_id = int(cursor.fetchall()[0][0])
        max_id += 1
        return max_id
    except TypeError:
        return 1


def get_max_in_lib(cursor):
    try:
        cursor.execute("SELECT MAX(ID) FROM Library")
        max_id = int(cursor.fetchall()[0][0])
        max_id += 1
        return max_id
    except TypeError:
        return 1


@app.get("/all")
def get_all_books():
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    create_tables(connect, cursor)
    cursor.execute("SELECT ID,Name,Author,Year,Count FROM Library WHERE Count>0 ORDER BY ID")
    books = cursor.fetchall()
    return {"res": books}


@app.get("/auth")
async def user_auth(login: str, password: str, Authorize: AuthJWT = Depends()):
    try:
        connect = sqlite3.connect(db_name)
        cursor = connect.cursor()
        cursor.execute(f"SELECT password, type FROM Users WHERE login='{login}'")
        res = cursor.fetchall()
        if checkpw(password.encode("utf-8"), res[0][0].encode("utf-8"), ):
            return {"res": res[0][1], "token": Authorize.create_refresh_token(res[0][1])}
        else:
            return JSONResponse({"res": False}, status_code=403)
    except IndexError as e:
        return JSONResponse({"res": None}, status_code=500)


@app.post("/register")
async def user_register(data: UserData):
    try:
        connect = sqlite3.connect(db_name)
        cursor = connect.cursor()
        cursor.execute(f"SELECT login FROM Users WHERE login='{data.login}'")
        try:
            user = cursor.fetchall()[0][0]
            return JSONResponse({"res": "User exists"}, status_code=409)
        except IndexError:
            password = str(hashpw(data.password.encode("utf-8"), gensalt()))[2:-1]
            cursor.execute(f"INSERT INTO Users VALUES('{data.login}', '{password}', 0)")
            connect.commit()
            return {"res": True}
    except IndexError:
        return JSONResponse({"res": "Something went wrong"}, status_code=500)


def set_frequency(book_id: int, connect, cursor):
    try:
        cursor.execute(f"SELECT CountTakes, add_time FROM Library WHERE ID={book_id}")
        res = cursor.fetchall()
        takes = res[0][0]
        time = res[0][1]
        date_format = '%y-%m-%d'
        time = datetime.strptime(time, date_format)
        now = datetime.strptime(datetime.now().strftime('%y-%m-%d'), date_format)
        res = now - time
        res = int(res.days)
        freq = str(round(takes / (res + 1), 2))
        freq += " takes/days"
        cursor.execute(f"UPDATE Library SET frequency='{freq}' WHERE ID={book_id}")
        connect.commit()
    except Exception as e:
        print(e)


def set_middleTime(book_id: int, connect, cursor):
    try:
        cursor.execute(f"SELECT AllTime,CountTakes FROM Library WHERE ID={book_id}")
        res = cursor.fetchall()
        time = res[0][0]
        takes = res[0][1]
        if takes == 0:
            cursor.execute(f"UPDATE Library SET middle_time='0' WHERE ID={book_id}")
            connect.commit()
            return
        middle = time / takes
        last_num = str(middle)[len(str(middle)) - 1]
        if middle == 1 or last_num == '1':
            day = ' день'
        elif 5 > middle > 1 or last_num == '2' or last_num == '2' or last_num == '2':
            day = ' дня'
        else:
            day = ' дней'
        cursor.execute(f"UPDATE Library SET middle_time='{str(round(time / takes, 2)) + day}' WHERE ID={book_id}")
        connect.commit()
    except Exception as e:
        print(e)


@app.get("/return")
async def return_book(book_id: int, user: int):
    try:
        connect = sqlite3.connect(db_name)
        cursor = connect.cursor()
        cursor.execute(f"SELECT timeTake FROM NotInLibrary WHERE takeID={user}")
        time = cursor.fetchall()[0][0]
        date_format = '%y-%m-%d'
        time = datetime.strptime(time, date_format)
        now = datetime.strptime(datetime.now().strftime('%y-%m-%d'), date_format)
        res = now - time
        res = int(res.days)
        cursor.execute(f"UPDATE Library SET Count=Count+1, OnHandsCount=OnHandsCount-1, AllTime=AllTime+{res} "
                       f"WHERE ID={book_id}")
        cursor.execute(f"DELETE FROM NotInLibrary WHERE ID={book_id} AND TakeID={user}")
        connect.commit()
        set_frequency(book_id, connect, cursor)
        set_middleTime(book_id, connect, cursor)
        return True
    except Exception as e:
        print(e)
        return None


@app.get("/take")
async def take_book(book_id: int, user: str):
    try:
        connect = sqlite3.connect(db_name)
        cursor = connect.cursor()
        cursor.execute(f"SELECT Count FROM Library WHERE ID={book_id}")
        count = int(cursor.fetchall()[0][0])
        if count > 0:
            cursor.execute(f"UPDATE Library SET Count=Count-1, OnHandsCount=OnHandsCount+1, CountTakes=CountTakes+1 "
                           f"WHERE ID={book_id}")
            cursor.execute(f"SELECT ID, Name, Author, Year FROM Library WHERE ID={book_id}")
            data = cursor.fetchall()[0]
            cursor.execute("INSERT INTO NotInLibrary VALUES (?,?,?,?,{0},'{1}','{2}')"
                           .format(get_max_takes(cursor), datetime.now().strftime('%y-%m-%d'), user), data)
            connect.commit()
            return {"res": count}
        else:
            cursor.execute(f"UPDATE Library SET Count=0 WHERE ID={book_id}")
            connect.commit()
            return {"res": count}
    except Exception as e:
        print(e)
        return {"res": None}


@app.get("/on_hand")
async def get_book_onHand(book_id: int):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    cursor.execute(f"SELECT MAX(takeID) FROM NotInLibrary WHERE ID={book_id}")
    max_id = cursor.fetchall()[0][0]
    cursor.execute(f"SELECT ID,Name,Author,Year,takeID FROM NotInLibrary WHERE takeID={max_id}")
    book = cursor.fetchall()[0]
    return {"res": book}


@app.get("/book/{book_id}")
async def get_book(book_id: int):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    cursor.execute(f"SELECT ID,Name,Author,Year,Count FROM Library WHERE ID={book_id}")
    book = cursor.fetchall()[0]
    return book


@app.delete("/book/{book_id}")
async def delete_book(book_id: int):
    try:
        connect = sqlite3.connect(db_name)
        cursor = connect.cursor()
        cursor.execute(f"DELETE FROM library WHERE ID={book_id}")
        connect.commit()
    except Exception as e:
        print(e)


@app.patch("/book/{book_id}")
async def add_books_count(book_id: int, count: int):
    try:
        connect = sqlite3.connect(db_name)
        cursor = connect.cursor()
        cursor.execute(f"UPDATE Library SET Count=Count+{count} WHERE ID={book_id}")
        connect.commit()
    except Exception as e:
        print(e)


@app.post("/book")
async def add_book(data: AddBook):
    try:
        data = data.data
        connect = sqlite3.connect(db_name)
        cursor = connect.cursor()
        data[0] = get_max_in_lib(cursor)
        cursor.execute("INSERT INTO library VALUES (?,?,?,?,?,0,0,0,'0','0','{0}')"
                       .format(datetime.now().strftime('%y-%m-%d')), data)
        connect.commit()
        return {"res": data[0]}
    except Exception as e:
        print(e)


@app.get("/fill/{column}")
def fill_table(column: str):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    cursor.execute(f"SELECT ID, Name, Author, Year, {column} FROM Library ORDER BY ID")
    return {"res": cursor.fetchall()}


@app.get("/sort/{column}")
async def sort1(column: str):
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    cursor.execute(f"SELECT ID,Name,Author,Year,Count FROM Library WHERE Count>0 ORDER BY {column}")
    return {"res": cursor.fetchall()}


@app.get("/sort2/{column}/{user_id}/{table}")
async def sort2(column: str, user_id: str, table: int, Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()
    permissions = int(Authorize.get_jwt_subject())
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    if table == 0:
        if permissions == 1:
            cursor.execute(f"SELECT ID,Name,Author,Year,takeID FROM NotInLibrary ORDER BY {column}")
        else:
            cursor.execute(f"SELECT ID,Name,Author,Year,takeID FROM NotInLibrary WHERE takerID='{user_id}' "
                           f"ORDER BY {column}")
    elif table == 1:
        if column == "takeID":
            column = "middle_time"
        if permissions == 1:
            cursor.execute(f"SELECT ID,Name,Author,Year,middle_time FROM Library ORDER BY {column}")
        else:
            return {"res": False}
    else:
        if column == "takeID":
            column = "frequency"
        if permissions == 1:
            cursor.execute(f"SELECT ID,Name,Author,Year,frequency FROM Library ORDER BY {column}")
        else:
            return {"res": False}
    return {"res": cursor.fetchall()}


@app.get("/download/{user_id}/{table}")
async def download(user_id: str, table: int, Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()
    permissions = int(Authorize.get_jwt_subject())
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    result = []
    if table == 0:
        if permissions == 1:
            cursor.execute(f"SELECT ID,Name,Author,Year,takerID FROM NotInLibrary ORDER BY ID")
            for i in cursor.fetchall():
                result.append({"id": i[0], "name": i[1], "author": i[2], "year": i[3], "take_id": i[4]})
        else:
            return {"res": False}
    elif table == 1:
        if permissions == 1:
            cursor.execute(f"SELECT ID,Name,Author,Year,middle_time FROM Library ORDER BY ID")
            for i in cursor.fetchall():
                result.append({"id": i[0], "name": i[1], "author": i[2], "year": i[3], "middle_time": i[4]})
        else:
            return {"res": False}
    else:
        if permissions == 1:
            cursor.execute(f"SELECT ID,Name,Author,Year,frequency FROM Library ORDER BY ID")
            for i in cursor.fetchall():
                result.append({"id": i[0], "name": i[1], "author": i[2], "year": i[3], "frequency": i[4]})
        else:
            return {"res": False}
    return result


@app.get("/user_books/{user_id}")
async def get_user_books(user_id: str, Authorize: AuthJWT = Depends()):
    Authorize.jwt_refresh_token_required()
    permissions = int(Authorize.get_jwt_subject())
    connect = sqlite3.connect(db_name)
    cursor = connect.cursor()
    if permissions == 1:
        cursor.execute("SELECT ID, Name, Author, Year, takeID FROM NotInLibrary ORDER BY ID")
    else:
        cursor.execute(f"SELECT ID, Name, Author, Year, takeID FROM NotInLibrary WHERE takerID='{user_id}' ORDER BY ID")
    res = cursor.fetchall()
    return res
