import json
from telebot import types
import asyncio
import datetime
from database import database
from random import randint
from telethon.tl.functions.channels import GetParticipantsRequest
from telethon.tl.types import ChannelParticipantsSearch
from telethon import functions
from telethon import TelegramClient
#import telethon.errors.rpc_error_list.ChatAdminRequiredError

buttons_admins = [
   "0Статистика",
   "1Получить подробную статистику",
   "2Добавить сообщение для новых\n подписчиков",
    "3Удалить сообщение для новых подписчиков",
   "4Изменить сообщение для отписавшихся",
   "5Изменить/активировать юзер аккаунт",
   "6Отключить/активировать рассылку отписавшимся",
    "7Проверить работу бота",
    "8Примеры оформления текста",
    "9Инструкция по юзер-ботам",
]

keys = ['A' , 'B' , 'C' , 'D' , 'E' , 'F' , 'G' , 'H' , 'I' , 'J' , 'K' , 'L' , 'M' , 'N' , 'O' , 'P' , 'Q' ,
            'R' , 'S' , 'T' , 'U' ,
            'V' , 'W' , 'X' , 'Y' , 'Z'
            'А', 'Б', 'В', 'Г', 'Д', 'Е', 'Ё', 'Ж', 'З', 'И', 'Й', 'К', 'Л', 'М', 'Н', 'О',
            'П', 'Р', 'С', 'Т', 'У', 'Ф', 'Х', 'Ц', 'Ч', 'Ш', 'Щ', 'Ъ', 'Ы', 'Ь', 'Э', 'Ю', 'Я']

chanel= "@Test_chanel_bot12"
me = "me"

def match(text, alphabet=set('абвгдеёжзийклмнопрстуфхцчшщъыьэюя')):
    return not alphabet.isdisjoint(text.lower())


def get_time(str_mode: bool = True) -> str or datetime.datetime:
    utc_time = datetime.datetime.utcnow()
    tz_modifier = datetime.timedelta(hours=3)
    tz_time = utc_time + tz_modifier
    if str_mode:
        return tz_time.strftime("%Y-%m-%d %H:%M:%S")

    return tz_time
def read_file(file_name: str) -> dict:

    try:
        with open(file_name, "r", encoding="utf-8") as file:
            with open(file_name) as file:
                data = json.load(file)

            return data
    except Exception as _:
        return {}


def save_file(file_name: str, data:dict) -> bool:
    try:
        with open(file_name, "w", encoding="utf-8") as file:
            json.dump(data, file)

    except Exception as err:
        return False

    return True


def create_user_menu(messages: list) -> "types.ReplyKeyboardMarkup":
    """Создает клавиатуру (которая располагается под полем ввода сообщений пользователя) с кнопками"""
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)  # создания клавиатуры для ответов

    for text in messages:
        button = types.KeyboardButton(text)
        keyboard.add(button)

    return keyboard


async def get_subscribers(app, Admins) -> dict:
    prey = {}
    if app and await app.is_user_authorized():

        try:
            for key in keys:
                offset = 0
                participants = await app(GetParticipantsRequest(
                    chanel , ChannelParticipantsSearch(key) , offset , limit=200 , hash=0))
                for user in participants.users:
                    if user.id not in prey.keys():
                        prey[user.id] = [user.first_name if user.first_name else "",user.username if user.username else "",user.phone if user.phone else ""]

        except Exception as err:
            if err.code == 400:
                await Admins.notify_active_admins("Ошибка\nСкорее всего вы не добавили пользователя как администратора\n"
                                              "Попробуйте еще раз")
                return {"err":400}
            return {}
    return prey


def get_users_from_db(database) -> dict:
    users = {}
    for user in database.get_all("subscribers"):
        users[user[0]] = user[1]

    return users


def get_full_user_from_db(database, logs) -> list["date", "first_name", "nickname", "phone", "sub/usnub"]:
    """user[0]-date user[1]-first_name user[2]-username user[3]-phone user[4]-type(sub/unsub)"""
    users = []

    try:
        for user in database.get_all("statistic"):
            users.append([user[0], user[1], user[2], user[3], user[4], user[5], user[6]])
    except Exception as err:
        logs.set_error_log(str(err) , "get statistic from db")

    return users


def reset_full(database, logs):
    try:
        database.delete_all("statistic")
    except Exception as err:
        logs.set_error_log(str(err) , "reset statistic")

def add_user(database, id, first_name, logs):

    try:
        database.add_new_items([id , first_name] , "id, first_name" , "subscribers")
    except Exception as err:
        logs.set_error_log(str(err) , "add user to Db")
        return False

    return True

def add_to_statistic(database:database, date, first_name, nickname, phone, type, id, leave_date="", logs=""):
    database.delete_item(f"id={id}" , "statistic")
    try:
        database.add_new_items([date , first_name, nickname, phone, type, id, leave_date] , "date, first_name, user_name, phone,type,id,leave_date", "statistic")
    except Exception as err:
        if logs:
            logs.set_error_log(str(err) , "add user to Db")
        return False

    return True

def remove_user(database, id, logs):
    try:
        database.delete_item(f"id={id}", "subscribers")
    except Exception as err:
        logs.set_error_log(str(err), "remove user from db")
        return False
    return True


async def get_real_count_of_sub(app) -> int:
    channel_connect = await app.get_entity(chanel)
    result = await app(functions.channels.GetFullChannelRequest(channel_connect))
    sub = result.full_chat.participants_count
    return sub

def get_delay_in_seconds() -> int:
    return randint(900, 1500)

def get_unsub_days(date_join: str, date_leave: str) -> int:
    date_join = datetime.datetime.strptime(date_join, "%Y-%m-%d %H:%M:%S")
    date_leave = datetime.datetime.strptime(date_leave , "%Y-%m-%d %H:%M:%S")
    return date_leave.day - date_join.day


def update_statistic(database, user_id, first_name, logs):
    try:
        user = database.get_certain(f"id={user_id}" , "statistic")
        if user and user[0]:
            time = user[0][0]
            first_name = user[0][1]
            nickname = user[0][2]
            phone = user[0][3]
        else:
            add_to_statistic(database , get_time(), first_name , " " ,
                             "", "отписался" , user_id , get_time() , logs)
            return None


        database.delete_item(f"id={user_id}" , "statistic")
        add_to_statistic(database , time , first_name , nickname,
                         phone , "отписался" , user_id, get_time(), logs)
    except Exception as err:
        logs.set_error_log(str(err), "error in update statistic")
