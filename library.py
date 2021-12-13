import requests
from tkinter import messagebox
from tkinter import ttk
from tkinter import *
import tkinter as tk

server_url = "http://localhost:8000/"
token = ""

databaseName = 'dataBase.db'
who = 0
currentUserID = 0
currentTable = 0
root = tk.Tk()
root.title("Читальный зал")
root.geometry("1600x500")
root.resizable(False, False)

# region tables
frame = ttk.Treeview(root)
frame.place(relx=0.15, rely=0.05, relwidth=0.36, relheight=0.89)
frame2 = ttk.Treeview(root)
frame2.place(relx=0.62, rely=0.05, relwidth=0.36, relheight=0.89)
frame["columns"] = ("ID", "Название", "Автор", "Год издания", "Кол-во")
frame.column("#0", width=0, stretch=tk.NO)
frame.column("ID", width=40, stretch=tk.NO)
frame.column("Название", width=200, stretch=tk.NO)
frame.column("Автор", width=200, stretch=tk.NO)
frame.column("Год издания", width=80, stretch=tk.NO)
frame.column("Кол-во", width=50, stretch=tk.NO)

frame.heading("ID", text="ID", anchor=tk.W)
frame.heading("Название", text="Название", anchor=tk.W)
frame.heading("Автор", text="Автор", anchor=tk.W)
frame.heading("Год издания", text="Год издания", anchor=tk.W)
frame.heading("Кол-во", text="Кол-во", anchor=tk.W)

frame2["columns"] = ("ID", "Название", "Автор", "Год издания", "Идентификатор")
frame2.column("#0", width=0, stretch=tk.NO)
frame2.column("ID", width=40, stretch=tk.NO)
frame2.column("Название", width=200, stretch=tk.NO)
frame2.column("Автор", width=150, stretch=tk.NO)
frame2.column("Год издания", width=80, stretch=tk.NO)
frame2.column("Идентификатор", width=100, stretch=tk.NO)

frame2.heading("ID", text="ID", anchor=tk.W)
frame2.heading("Название", text="Название", anchor=tk.W)
frame2.heading("Автор", text="Автор", anchor=tk.W)
frame2.heading("Год издания", text="Год издания", anchor=tk.W)
frame2.heading("Идентификатор", text="Идентификатор", anchor=tk.W)


# endregion
def fill_LibTable():
    try:
        frame.delete(*frame.get_children())
        books = requests.get(f"{server_url}all").json()["res"]
        for i in books:
            frame.insert('', 'end', values=i)
    except Exception as e:
        print(e)


def fill_on_hand_table():
    global currentTable
    try:
        if currentUserID != -999:
            currentTable = 0
            button_take.configure(state='normal')
            button_give.configure(state='normal')
            frame2.heading("Идентификатор", text="Идентификатор", anchor=tk.W)
            button_sortCount2.configure(text='Идентификатору')
            frame2.delete(*frame2.get_children())
            books = requests.get(f"{server_url}user_books/{currentUserID}",
                                 headers={"Authorization": f"Bearer {token}"}).json()
            for i in books:
                frame2.insert('', 'end', values=i)
    except Exception as e:
        print(e)


def fill_middle_time():
    global currentTable
    try:
        currentTable = 1
        button_take.configure(state='disabled')
        button_give.configure(state='disabled')
        frame2.heading("Идентификатор", text="Среднее время", anchor=tk.W)
        button_sortCount2.configure(text='Времени')
        frame2.delete(*frame2.get_children())
        books = requests.get(f"{server_url}fill/middle_time").json()["res"]
        for i in books:
            frame2.insert('', 'end', values=i)
    except Exception as e:
        print(e)


def fill_frequency():
    global currentTable
    try:
        currentTable = 2
        button_take.configure(state='disabled')
        button_give.configure(state='disabled')
        frame2.heading("Идентификатор", text="Частота выдачи", anchor=tk.W)
        button_sortCount2.configure(text='Частоте')
        frame2.delete(*frame2.get_children())
        books = requests.get(f"{server_url}fill/frequency").json()["res"]
        for i in books:
            frame2.insert('', 'end', values=i)
    except Exception as e:
        print(e)


def sort_frame(byWhat):
    try:
        frame.delete(*frame.get_children())
        books = requests.get(f"{server_url}sort/{byWhat}").json()["res"]
        for i in books:
            frame.insert('', 'end', values=i)
    except Exception as e:
        print(e)


def sort_frame2(byWhat):
    try:
        frame2.delete(*frame2.get_children())
        books = requests.get(f"{server_url}sort2/{byWhat}/{currentUserID}/{currentTable}",
                             headers={"Authorization": f"Bearer {token}"}).json()["res"]
        if not books:
            return
        for i in books:
            frame2.insert('', 'end', values=i)
    except Exception as e:
        print(e)


def add_book():
    try:
        if len(entry_title.get()) != 0 and len(entry_author.get()) != 0 and \
                len(entry_year.get()) != 0 and len(entry_count.get()) != 0:
            data = [0, entry_title.get(), entry_author.get(), entry_year.get(), entry_count.get()]
            if not data[3].isdigit():
                messagebox.showerror("TypeError", "Год издания должен быть указан числом")
                return
            if not data[4].isdigit():
                messagebox.showerror("TypeError", "Кол-во экземпляров должно быть указано числом")
                return
            response = requests.post(f"{server_url}book", json={"data": data})
            if response.status_code == 200:
                data[0] = response.json()["res"]
            frame.insert('', 'end', values=data)
        else:
            messagebox.showerror("Ошибка ввода", "Все поля должны быть заполнены")
    except Exception as e:
        print(e)


def del_book():
    try:
        i = frame.selection()[0]
        book = str(frame.item(i).values()).split()
        frame.delete(i)
        book_id = book[2][1:-1]
        requests.delete(f"{server_url}book/{book_id}").json()
    except IndexError:
        messagebox.showerror('Ошибка', 'Вы не выбрали книгу')


def replace_book(table):
    try:
        if table == "Library":
            button_take.configure(state='normal')
            button_give.configure(state='normal')
            i = frame.selection()[0]
            book = frame.item(i).values()
            book = str(book).split()
            book_id = book[2][1:-1]
            response = requests.get(f"{server_url}take?book_id={book_id}&user={currentUserID}").json()
            if response["res"] > 1:
                frame.item(i, values=requests.get(f"{server_url}book/{book_id}").json())
                frame2.insert('', 'end', values=requests.get(f"{server_url}on_hand?book_id={book_id}").json()["res"])
            else:
                frame2.insert('', 'end', values=requests.get(f"{server_url}on_hand?book_id={book_id}").json()["res"])
                frame.delete(i)
        elif table == "NotInLibrary":
            i = frame2.selection()[0]
            book = frame2.item(i).values()
            book = str(book).split()
            book_id = book[2][1:-1]
            user_id = book[len(book) - 3][:-2]
            requests.get(f"{server_url}return?book_id={book_id}&user={user_id}")
            frame2.delete(i)
            fill_LibTable()
        else:
            print('Где-то закралась ошибочка')
    except IndexError:
        messagebox.showerror('Ошибка', 'Вы не выбрали книгу')


def add_count(count):
    try:
        i = frame.selection()[0]
        book = str(frame.item(i).values()).split()
        book_id = book[2][1:-1]
        requests.patch(f"{server_url}book/{book_id}?count={count}").json()
        fill_LibTable()
    except IndexError:
        messagebox.showerror('Ошибка', 'Вы не выбрали книгу')


def all_disabled():
    button_middle.configure(state='disabled')
    button_add.configure(state='disabled')
    button_del.configure(state='disabled')
    button_take.configure(state='disabled')
    button_give.configure(state='disabled')
    button_plusOne.configure(state='disabled')
    button_plusTwo.configure(state='disabled')
    button_plusFive.configure(state='disabled')
    button_plusTen.configure(state='disabled')
    button_plusFT.configure(state='disabled')
    button_plusTwenty.configure(state='disabled')
    button_sortID.configure(state='disabled')
    button_sortID2.configure(state='disabled')
    button_sortName.configure(state='disabled')
    button_sortName2.configure(state='disabled')
    button_sortAuthor.configure(state='disabled')
    button_sortAuthor2.configure(state='disabled')
    button_sortYear.configure(state='disabled')
    button_sortYear2.configure(state='disabled')
    button_sortCount.configure(state='disabled')
    button_sortCount2.configure(state='disabled')
    button_frequency.configure(state='disabled')


def login():
    global who, token, currentUserID
    all_disabled()
    if len(entry_userId.get()) != 0 and len(entry_pass.get()) != 0:
        permissions = requests.get(f"{server_url}auth?login={entry_userId.get()}&password={entry_pass.get()}").json()
        token = permissions["token"]
        permissions = permissions["res"]
        if permissions:
            if permissions == "1":
                button_middle.configure(state='normal')
                button_add.configure(state='normal')
                button_del.configure(state='normal')
                button_take.configure(state='normal')
                button_give.configure(state='normal')
                button_plusOne.configure(state='normal')
                button_plusTwo.configure(state='normal')
                button_plusFive.configure(state='normal')
                button_plusTen.configure(state='normal')
                button_plusFT.configure(state='normal')
                button_plusTwenty.configure(state='normal')
                button_frequency.configure(state='normal')
                button_onHand.configure(state='normal')
                button_download.configure(state='normal')
            else:
                button_take.configure(state='normal')
                button_give.configure(state='normal')
            who = int(permissions)
        elif not permissions:
            messagebox.showerror('error', 'Неверный пароль')
            return
        else:
            messagebox.showerror('error', 'Пользователь не найден')
    else:
        messagebox.showerror('error', 'Заполните необходимые поля')
        return
    if len(entry_userId.get()) != 0:
        currentUserID = entry_userId.get()
    fill_on_hand_table()
    entry_userId.delete(0, 'end')
    entry_pass.delete(0, 'end')
    button_sortID.configure(state='normal')
    button_sortID2.configure(state='normal')
    button_sortName.configure(state='normal')
    button_sortName2.configure(state='normal')
    button_sortAuthor.configure(state='normal')
    button_sortAuthor2.configure(state='normal')
    button_sortYear.configure(state='normal')
    button_sortYear2.configure(state='normal')
    button_sortCount.configure(state='normal')
    button_sortCount2.configure(state='normal')
    button_exit.configure(state='normal')
    button_enter.configure(state='disabled')
    button_reg.configure(state='disabled')


def download():
    from json import dump
    books = requests.get(f"{server_url}download/{currentUserID}/{currentTable}",
                         headers={"Authorization": f"Bearer {token}"}).json()
    print(books)
    with open("otchet.json", "w") as file:
        dump(books, file, indent=2)


def reg():
    if len(entry_userId.get()) != 0 and len(entry_pass.get()) != 0:
        response = requests.post(f"{server_url}register", json={"login": entry_userId.get(),
                                                                "password": entry_pass.get()})
        if response.status_code == 200:
            messagebox.showinfo('Успех', 'Регистрация прошла успешно')
            login()
        elif response.status_code == 403:
            messagebox.showerror("Ошибка", "Неверный пароль")
        else:
            messagebox.showerror("Ошибка", "Неизвестная ошибка")
    else:
        messagebox.showerror('Ошибка', 'Необходимо указать логин и пароль для регистрации')


def Exit():
    global who, currentUserID
    who = 0
    currentUserID = -999
    all_disabled()
    button_enter.configure(state='normal')
    button_reg.configure(state='normal')
    button_exit.configure(state="disabled")
    frame2.delete(*frame2.get_children())


# region UI создание графического интерфейса
l_frame = LabelFrame(root, relief=FLAT)
l_frame.place(relx=0.025, rely=0.85, relwidth=0.12, relheight=0.14)

button_add = tk.Button(root, text="Добавить", bg='#BDBDBD', command=lambda: add_book(), state='disabled')
button_add.place(relx=0.045, rely=0.34, relwidth=0.1, relheight=0.05)
button_del = tk.Button(root, text="Удалить", bg='#BDBDBD', command=lambda: del_book(), state='disabled')
button_del.place(relx=0.045, rely=0.40, relwidth=0.1, relheight=0.05)
button_give = tk.Button(root, text="->Взять книгу->", bg='#BDBDBD', command=lambda: replace_book("Library"),
                        state='disabled')
button_give.place(relx=0.515, rely=0.05, relwidth=0.1, relheight=0.05)
button_take = tk.Button(root, text="<-Вернуть книгу<-", bg='#BDBDBD', command=lambda: replace_book("NotInLibrary"),
                        state='disabled')
button_take.place(relx=0.515, rely=0.11, relwidth=0.1, relheight=0.05)
button_middle = tk.Button(root, text="Среднее время на руках", bg='#BDBDBD', command=lambda: fill_middle_time(),
                          state='disabled')
button_middle.place(relx=0.515, rely=0.27, relwidth=0.1, relheight=0.05)
button_frequency = tk.Button(root, text="Частота выдачи", bg='#BDBDBD', command=lambda: fill_frequency(),
                             state='disabled')
button_frequency.place(relx=0.515, rely=0.33, relwidth=0.1, relheight=0.05)
button_onHand = tk.Button(root, text="Список книг на руках", bg='#BDBDBD', command=lambda: fill_on_hand_table(),
                          state='disabled')
button_onHand.place(relx=0.515, rely=0.39, relwidth=0.1, relheight=0.05)
button_download = tk.Button(root, text="Скачать отчет", bg='#BDBDBD', command=lambda: download(),
                            state='disabled')
button_download.place(relx=0.515, rely=0.45, relwidth=0.1, relheight=0.05)

button_sortID = tk.Button(root, text="ID", bg='#BDBDBD', command=lambda: sort_frame("ID"), state='disabled')
button_sortID.place(relx=0.22, rely=0.945, relwidth=0.03, relheight=0.05)
button_sortName = tk.Button(root, text="Названию", bg='#BDBDBD', command=lambda: sort_frame("Name"), state='disabled')
button_sortName.place(relx=0.255, rely=0.945, relwidth=0.05, relheight=0.05)
button_sortAuthor = tk.Button(root, text="Автору", bg='#BDBDBD', command=lambda: sort_frame("Author"), state='disabled')
button_sortAuthor.place(relx=0.31, rely=0.945, relwidth=0.05, relheight=0.05)
button_sortYear = tk.Button(root, text="Году", bg='#BDBDBD', command=lambda: sort_frame("Year"), state='disabled')
button_sortYear.place(relx=0.365, rely=0.945, relwidth=0.05, relheight=0.05)
button_sortCount = tk.Button(root, text="Количеству", bg='#BDBDBD', command=lambda: sort_frame("Count"),
                             state='disabled')
button_sortCount.place(relx=0.42, rely=0.945, relwidth=0.05, relheight=0.05)
button_sortID2 = tk.Button(root, text="ID", bg='#BDBDBD', command=lambda: sort_frame2("ID"), state='disabled')
button_sortID2.place(relx=0.693, rely=0.945, relwidth=0.03, relheight=0.05)
button_sortName2 = tk.Button(root, text="Названию", bg='#BDBDBD', command=lambda: sort_frame2("Name"), state='disabled')
button_sortName2.place(relx=0.728, rely=0.945, relwidth=0.05, relheight=0.05)
button_sortAuthor2 = tk.Button(root, text="Автору", bg='#BDBDBD', command=lambda: sort_frame2("Author"),
                               state='disabled')
button_sortAuthor2.place(relx=0.783, rely=0.945, relwidth=0.05, relheight=0.05)
button_sortYear2 = tk.Button(root, text="Году", bg='#BDBDBD', command=lambda: sort_frame2("Year"), state='disabled')
button_sortYear2.place(relx=0.838, rely=0.945, relwidth=0.05, relheight=0.05)
button_sortCount2 = tk.Button(root, text="Идентификатору", bg='#BDBDBD', command=lambda: sort_frame2("takeID"),
                              state='disabled')
button_sortCount2.place(relx=0.893, rely=0.945, relwidth=0.06, relheight=0.05)
button_plusOne = tk.Button(root, text="+1", bg='#BDBDBD', command=lambda: add_count(1), state='disabled')
button_plusOne.place(relx=0.515, rely=0.6, relwidth=0.03, relheight=0.05)
button_plusTwo = tk.Button(root, text="+2", bg='#BDBDBD', command=lambda: add_count(2), state='disabled')
button_plusTwo.place(relx=0.55, rely=0.6, relwidth=0.03, relheight=0.05)
button_plusFive = tk.Button(root, text="+5", bg='#BDBDBD', command=lambda: add_count(5), state='disabled')
button_plusFive.place(relx=0.585, rely=0.6, relwidth=0.03, relheight=0.05)
button_plusTen = tk.Button(root, text="-1", bg='#BDBDBD', command=lambda: add_count(-1), state='disabled')
button_plusTen.place(relx=0.515, rely=0.665, relwidth=0.03, relheight=0.05)
button_plusFT = tk.Button(root, text="-2", bg='#BDBDBD', command=lambda: add_count(-2), state='disabled')
button_plusFT.place(relx=0.55, rely=0.665, relwidth=0.03, relheight=0.05)
button_plusTwenty = tk.Button(root, text="-5", bg='#BDBDBD', command=lambda: add_count(-5), state='disabled')
button_plusTwenty.place(relx=0.585, rely=0.665, relwidth=0.03, relheight=0.05)
button_refresh = tk.Button(root, text="Обновить БД", bg='#BDBDBD', command=lambda: (fill_LibTable(),
                                                                                    fill_on_hand_table()),
                           state='normal')
button_refresh.place(relx=0.515, rely=0.8, relwidth=0.1, relheight=0.05)

entry_title = tk.Entry(root, font=12)
entry_title.place(relx=0.045, rely=0.05, relwidth=0.1, relheight=0.05)
entry_author = tk.Entry(root, font=12)
entry_author.place(relx=0.045, rely=0.12, relwidth=0.1, relheight=0.05)
entry_year = tk.Entry(root, font=12)
entry_year.place(relx=0.045, rely=0.19, relwidth=0.1, relheight=0.05)
entry_count = tk.Entry(root, font=12)
entry_count.place(relx=0.045, rely=0.26, relwidth=0.1, relheight=0.05)

label_title = tk.Label(root, font=12, text="Назв:", fg='black')
label_title.place(relx=0.01, rely=0.05)
label_author = tk.Label(root, font=12, text="Автор:", fg='black')
label_author.place(relx=0.005, rely=0.12)
label_year = tk.Label(root, font=12, text="Год:", fg='black')
label_year.place(relx=0.015, rely=0.19)
label_count = tk.Label(root, font=12, text="Кол-во:", fg='black')
label_count.place(relx=0.005, rely=0.26)
label_sort = tk.Label(root, font=12, text="Сортировка по:", fg='black')
label_sort.place(relx=0.148, rely=0.945)
label_sort2 = tk.Label(root, font=12, text="Сортировка по:", fg='black')
label_sort2.place(relx=0.62, rely=0.945)
label_fill = tk.Label(root, font=12, text="Изменение количества", fg='black')
label_fill.place(relx=0.514, rely=0.55, relwidth=0.106, relheight=0.05)
label_func = tk.Label(root, font=12, text="Формирование отчетов", fg='black')
label_func.place(relx=0.513, rely=0.22, relwidth=0.106, relheight=0.05)

label_func = tk.Label(root, font=12, text="Авторизация", fg='black')
label_func.place(relx=0.048, rely=0.67)
entry_userId = tk.Entry(root, font=12)
entry_userId.place(relx=0.027, rely=0.72, relwidth=0.1, relheight=0.05)
entry_pass = tk.Entry(root, font=12, show="*")
entry_pass.place(relx=0.027, rely=0.78, relwidth=0.1, relheight=0.05)
button_enter = tk.Button(l_frame, text="Вход", bg='#BDBDBD', command=lambda: login())
button_enter.place(relx=0, rely=-0.1, relwidth=0.41, relheight=0.5)
button_reg = tk.Button(l_frame, text="Регистрация", bg='#BDBDBD', command=lambda: reg())
button_reg.place(relx=0, rely=0.46, relwidth=0.85, relheight=0.4)
button_exit = tk.Button(l_frame, text="Выход", bg='#BDBDBD', command=lambda: Exit(), state='disabled')
button_exit.place(relx=0.44, rely=-0.1, relwidth=0.41, relheight=0.5)

fill_LibTable()
# endregion
if __name__ == "__main__":
    root.mainloop()
