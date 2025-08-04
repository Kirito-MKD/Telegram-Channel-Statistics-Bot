import telebot
from telebot.async_telebot import AsyncTeleBot
from telebot.async_telebot import types
import asyncio
import os
from tools import save_file, read_file, buttons_admins, create_user_menu,\
    get_delay_in_seconds, get_subscribers, chanel, me, keys, get_users_from_db, add_user, remove_user,\
    get_real_count_of_sub, get_full_user_from_db, reset_full, add_to_statistic,\
    get_time, update_statistic, get_unsub_days, match
from telethon import TelegramClient
from database import connection_table
from myLogs import Mylogs
from exel import Exel
from random import choice
from myAdmins import MyAdmins

API_bot = "Your api"

bot = AsyncTeleBot(API_bot)

active_user = []
time_message = ""
user_login = "Your login"
user_password = "Your password"

user_bot_thread = None
user_time_data = []

user_bot = None

bool_get_login = False
bool_get_password = False

database = connection_table("channel.db")

session_name = "Current-session"
logs = Mylogs(session_name)
Admins = MyAdmins(logs, bot)

"""authorization"""
@bot.message_handler(commands=["start"])
async def start(message):
    await bot.send_message(message.chat.id, "Я ваш помощник по вашему каналу, чтобы начать введите /login")


@bot.message_handler(commands=["login"])
async def login(message):
    if await Admins.is_active_admin(message.chat.id , mute_mode=True):
        markup = create_user_menu(buttons_admins)
        await bot.send_message(message.chat.id , "Вы уже прошли авторизацию" , reply_markup=markup)
        return None

    global bool_get_login
    bool_get_login = True

    await bot.send_message(message.chat.id, "Введите логин:")

@bot.message_handler(func=lambda message: message.text and bool_get_login)
async def get_login(message):
    global bool_get_login , bool_get_password

    if message.text != user_login:
        bool_get_login = False
        await bot.send_message(message.chat.id, "Неверный логин!\nПопробуйте еще раз!\n/login")
        return None

    bool_get_login = False
    bool_get_password = True

    await bot.send_message(message.chat.id, "Введите пароль")

@bot.message_handler(func=lambda message: message.text and bool_get_password)
async def get_password(message):
    global bool_get_password

    if message.text != user_password:
        await bot.send_message(message.chat.id, "Неверный пороль!\nПопробуйте еще раз.\n /login")
        bool_get_password = False
        return None

    bool_get_password = False
    Admins.register_admin(message.from_user.id)
    markup = create_user_menu(buttons_admins)
    await bot.send_message(message.chat.id , "Вы успешно авторизовались" , reply_markup=markup)


"""Edit sub message"""


bool_edit_sub_m = False
bool_edit_unsub_m = False
bool_get_number_to_del_sub = False

@bot.message_handler(func=lambda message: message.text == buttons_admins[2])
async def add_sub_message(message):

    if not await Admins.is_active_admin(message.from_user.id):
        await bot.send_message(message.chat.id, "Вы не авторизовались введите /login")
        return None

    global time_message, bool_edit_sub_m
    bool_edit_sub_m = True
    time_message = ""
    await bot.send_message(message.chat.id, "Отправьте новое сообщение")

@bot.message_handler(func=lambda message: bool_edit_sub_m)
async def get_sub_message(message):
    global time_message, bool_edit_sub_m
    bool_edit_sub_m = False
    time_message = message.text
    markup = types.InlineKeyboardMarkup().add(
        *[
            telebot.types.InlineKeyboardButton(text="Отмена" , callback_data="cancel"),
            telebot.types.InlineKeyboardButton(text="Сохранить", callback_data="save_sub")
        ]
    )

    await bot.send_message(message.chat.id , "Ваше новое сообщение:\n" + message.text.replace(
        "|name|" , message.from_user.first_name if message.chat.first_name else "") , parse_mode="HTML" ,
                           reply_markup=markup)


@bot.callback_query_handler(func=lambda callback: callback.data == "save_sub")
async def save_sub_message(call):
    data = read_file("messages.json")
    global time_message

    data["sub_message"].append(time_message)
    time_message = ""

    tryies = 0
    while not save_file("messages.json", data) and tryies < 4:
        tryies += 1

    if tryies == 4:
        await bot.send_message(call.message.chat.id, "Сообщение не сохранено")

    await bot.send_message(call.message.chat.id, "Сообщение сохранено")
@bot.message_handler(func=lambda message: message.text == buttons_admins[3])
async def delete_sub_message(user_message):

    if not await Admins.is_active_admin(user_message.from_user.id):
        await bot.send_message(user_message.chat.id , "Вы не авторизовались введите /login")
        return None

    messages = read_file("messages.json")["sub_message"]

    if len(messages) < 1:
        await bot.send_message(user_message.chat.id, "У вас нет сообщений")
        return None

    await bot.send_message(user_message.chat.id, 'У вас есть следующие сообщение для подписчиков: ')
    for i in range(len(messages)):
        await bot.send_message(user_message.chat.id, f"{i+1}) {messages[i].replace('|name|', user_message.from_user.first_name if match(user_message.from_user.first_name) else '')}", parse_mode="HTML")
    await bot.send_message(user_message.chat.id, "Выберите номер для удаления", parse_mode="HTML")

    global bool_get_number_to_del_sub
    bool_get_number_to_del_sub = True

@bot.message_handler(func=lambda message: message.text and bool_get_number_to_del_sub)
async def get_number_to_del_sub_message(user_message):
    messages = read_file("messages.json")
    global bool_get_number_to_del_sub
    bool_get_number_to_del_sub = False

    if not user_message.text.isdigit():
        await bot.send_message(user_message.chat.id, "Вы ввели не числовое значение\nНачните заново")
        return None
    if int(user_message.text) > len(messages["sub_message"]):
        await bot.send_message(user_message.chat.id, "У вас нет столько сообщений\nНачните заново")
        return None

    markup = types.InlineKeyboardMarkup().add(
        *[
            telebot.types.InlineKeyboardButton(text="Отмена" , callback_data="cancel") ,
            telebot.types.InlineKeyboardButton(text="Удалить" ,
                                               callback_data=f"del_sub_{user_message.text}")
        ]
    )

    await bot.send_message(user_message.chat.id,
                     "Вы хотите удалить следующие сообщение:\n"
                     + messages["sub_message"][int(user_message.text)-1],
                     parse_mode="HTML",
                     reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("del_sub"))
async def del_sub_message(call):
    messages = read_file("messages.json")

    try:
        del messages["sub_message"][int(call.data.split("_")[-1])-1]
        save_file("messages.json", messages)
        await bot.send_message(call.message.chat.id, "Сообщение удалено")
    except:
        await bot.send_message(call.message.chat.id, "Сообщение не удалено")

"""Edit unsub message"""

@bot.message_handler(func=lambda message: message.text == buttons_admins[4])
async def change_unsub_message(message):

    if not await Admins.is_active_admin(message.from_user.id):
        await bot.send_message(message.chat.id, "Вы не авторизовались введите /login")
        return None

    global time_message, bool_edit_unsub_m
    bool_edit_unsub_m = True
    time_message = ""
    await bot.send_message(message.chat.id, "Отправьте новое сообщение")
@bot.message_handler(func=lambda message: bool_edit_unsub_m)
async def get_unsub_message(message):
    global time_message, bool_edit_unsub_m
    bool_edit_unsub_m = False
    time_message = message.text
    markup = telebot.types.InlineKeyboardMarkup().add(
        *[
            types.InlineKeyboardButton(text="Отмена" , callback_data="cancel"),
            types.InlineKeyboardButton(text="Сохранить", callback_data="save_unsub")
        ]
    )

    await bot.send_message(message.chat.id, "Ваше новое сообщение:\n" + message.text.replace(
        "|name|", message.from_user.first_name if message.from_user.first_name else ""), parse_mode="HTML", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "save_unsub")
async def save_unsub_message(call):
    data = read_file("messages.json")
    global time_message

    data["unsub_message"] = time_message
    time_message = ""

    tryies = 0
    while not save_file("messages.json", data) and tryies < 4:
        tryies += 1

    if tryies == 4:
        await bot.send_message(call.message.chat.id, "Сообщение не сохранено")

    await bot.send_message(call.message.chat.id, "Сообщение сохранено")



"""User bot"""


time_user_data = []
flag = False
bool_get_user_bot_data = False
bool_get_code = False
my_thread = False
app = None
sCode = None
bot_subscribers = 0
bot_unsubscribers = 0
active_bot = False
unsub_sending = True

@bot.message_handler(func=lambda message: message.text == buttons_admins[5])
async def user_bot(message):

    if not await Admins.is_active_admin(message.from_user.id):
        await bot.send_message(message.chat.id, "Вы не авторизовались введите /login")
        return None

    if not os.path.exists(session_name + ".session"):
        markup = telebot.types.InlineKeyboardMarkup().add(
            *[
                types.InlineKeyboardButton(text="Отмена" , callback_data="cancel") ,
                types.InlineKeyboardButton(text="Добавить" , callback_data="add_bot")
            ]
        )
        await bot.send_message(message.chat.id , "У вас нет активого бота. Хотите добавить?" , reply_markup=markup)

    elif not app and os.path.exists(session_name + ".session"):
        markup = telebot.types.InlineKeyboardMarkup().add(
            *[
                types.InlineKeyboardButton(text="Отмена" , callback_data="cancel") ,
                types.InlineKeyboardButton(text="Изменить" , callback_data="add_bot_o")
            ]
        )
        markup.add(types.InlineKeyboardButton(text="Активировать" , callback_data="activate"))
        await bot.send_message(message.chat.id , "Имеется неактивный бот." , reply_markup=markup)
    else:
        markup = telebot.types.InlineKeyboardMarkup().add(
            *[
                types.InlineKeyboardButton(text="Отмена" , callback_data="cancel") ,
                types.InlineKeyboardButton(text="Изменить" , callback_data="add_bot_o")
            ]
        )
        markup.add(types.InlineKeyboardButton(text="Выключить" , callback_data="disable"))
        await bot.send_message(message.chat.id , "У вас есть активный бот. Изменить его?" , reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "activate")
async def active_bot(call):
    global bool_get_user_bot_data
    bool_get_user_bot_data = False
    await get_code(call.message, True)

@bot.callback_query_handler(func=lambda call: call.data == "disable")
async def disable_user_bot(call):
    global app
    await bot.send_message(call.message.chat.id, "Отключаем бота...")

    if app:
        global active_bot, flag
        active_bot = False
        flag=False

        try:
            await app.disconnect()
        except Exception as err:
            logs.set_error_log(str(err), "disable user bot")

    await asyncio.sleep(10)
    app = None
    await bot.send_message(call.message.chat.id , "Бот отключен")

@bot.callback_query_handler(func=lambda call: call.data.startswith("add_bot"))
async def add_bot(call):
    global bool_get_user_bot_data, app
    bool_get_user_bot_data = True

    if call.data[-1] == "o":

        global flag, flag_session, active_bot
        flag = False
        active_bot = False

        await bot.send_message(call.message.chat.id, "Подождите 10 секунд\nОтключаем старого бота")
        await asyncio.sleep(10)

        if app:
            try:
                await app.disconnect()
            except Exception as err:
                pass

        try:
            if os.path.exists(session_name+".session"):
                os.remove(session_name+".session")
        except Exception as err:
            logs.set_error_log(str(err), "delete session")

    time_user_data.clear()
    await bot.send_message(call.message.chat.id , "Введите данные юзер бота как:" \
                                                  "\n<u>api_id;api_hash;телефон </u>\n" \
                                                  "Формат телефона <i>+79225551234</i>" , parse_mode="HTML")

@bot.message_handler(func=lambda message: bool_get_user_bot_data)
async def get_data_user_bot(message):
    try:
        api_id, api_hash,phone = message.text.split(";")
        time_user_data.extend([api_id, api_hash, phone])
    except Exception as err:
        logs.set_error_log("Not critical " + str(err), "get_data_from_user")
        await bot.send_message(message.chat.id, "Неккоректный ввод")
        return None

    global bool_get_user_bot_data , app , bool_get_code, sCode, flag
    bool_get_user_bot_data = False
    app = None
    try:
        app = TelegramClient(session=session_name , api_id=api_id , api_hash=api_hash)
        await app.connect()
        await app.send_code_request(phone)
    except Exception as err:
        if str(err) == "database is locked":

            if app:

                try:
                    asyncio.get_event_loop().stop()
                except Exception as err1:
                    logs.set_error_log(str(err1), "get_data_from_user_bot:1")

                try:
                    await app.disconnect()
                except Exception as err2:
                    logs.set_error_log(str(err2), "get_data_from_user_bot:2")
        await bot.send_message(message.chat.id, "Ошибка\nпопробуйте еще раз")
        flag = False
        return None

    bool_get_code = True
    await bot.send_message(message.chat.id, "Введите код, отправленный на аккаунт юзер бота")

@bot.message_handler(func=lambda message: bool_get_code)
async def get_code(message=None, active_mode = False, message_mode=True):
    global app, sCode, my_thread, flag, bool_get_code
    bool_get_code = False

    if message_mode:
        code = str(message.text)

    try:
        if active_mode and not flag:
            data = read_file("user-bot.json")
            api_id = data["api_id"]
            api_hash = data["api_hash"]
            phone = data["phone"]
            user_time_data.clear()
            user_time_data.extend([api_id, api_hash, phone])
            app = TelegramClient(session_name, api_hash=api_hash, api_id=api_id)
            await app.start()
        elif flag:
            await bot.send_message(message.chat.id , "Бот уже активирован\n")
            return None
        else:
            api_id , api_hash , phone = time_user_data
            await app.sign_in(phone, code)
            data = {
                "api_id": api_id ,
                "api_hash": api_hash ,
                "phone": phone
            }
            save_file("user-bot.json" , data)
    except Exception as err:
        if str(err) == "database is locked":
            logs.set_error_log("Not critical" + str(err), "get_code")
            await bot.send_message(message.chat.id , "Бот уже активирован\n")
            return None
        else:
            await bot.send_message(message.chat.id , "Ошибка\n" + str(err))
            await app.disconnect()
            logs.set_error_log(str(err) , "get_code")
            app = None
            return None

    global active_bot

    if message_mode:
        await bot.send_message(message.chat.id, "Готово")
    else:
        await Admins.notify_active_admins("Юзер-бот был перезапущен.Ошибка произошла на сервере\n")

    # Start the background thread
    try:
        await get_real_count_of_sub(app)

    except Exception as err1:
        global active_bot
        active_bot = True
        logs.set_error_log(str(err1) , "get_code1")
        await Admins.notify_active_admins("Ошибка\nСкорее всего вы не добавили пользователя как администратора\n"
                                                "Попробуйте еще раз")
        return None

    app.parse_mode = "html"
    flag = True
    await asyncio.sleep(30)
    old_members = get_users_from_db(database)
    new_ones = await get_subscribers(app, Admins)  # new subs
    if "err" in new_ones.keys():
        app.disconnect()
        app = None
        flag = False
        await Admins.notify_active_admins("Юзер бот отключен\nДобавьте бота как админа\n"
                                          "После чего включите юзер-бота")
        return None
    if len(new_ones.keys()) - len(old_members.keys()) >= 10:
        for user_id in new_ones.keys():
            if user_id not in old_members.keys():
                first_name = new_ones[user_id][0]
                add_user(database , user_id , first_name , logs)
                logs.set_error_log("Add user ", "first_name")
    try:
        global unsub_sending
        last_send_gift_message = ""

        # start monitor users
        while flag:
            old_members = get_users_from_db(database) # old subs
            new_ones = await get_subscribers(app, Admins) # new subs
            if "err" in new_ones.keys():
                await Admins.notify_active_admins("Юзер бот отключен\nДобавьте бота как админа\n"
                                            "После включите юзер-бота")
                app.disconnect()
                app = None
                flag = False
                break

            if len(new_ones.keys()) - len(old_members.keys()) >= 20:
                logs.set_error_log("Too many difference beetwen real sub and new_ones", "get_code:sending_block")
                for user_id in new_ones.keys():
                    first_name = new_ones[user_id][0]
                    if user_id not in old_members.keys():
                        add_user(database , user_id , first_name , logs)
                        logs.set_error_log("Add to db" , first_name)
                new_ones.clear()
                old_members.clear()

                continue

            messages = read_file("messages.json")  # text for sending

            #get people who join
            for user_id in new_ones.keys():
                if user_id not in old_members.keys():
                    await asyncio.sleep(get_delay_in_seconds())

                    gift_message = choice(messages["sub_message"])
                    while len(messages["sub_message"]) > 1 and gift_message == last_send_gift_message: # get random gift message for new ones
                        gift_message = choice(messages["sub_message"])

                    last_send_gift_message = gift_message
                    first_name = ""
                    try:
                        first_name = new_ones[user_id][0]
                        add_user(database , user_id , first_name , logs)
                        global bot_subscribers
                        bot_subscribers += 1
                        add_to_statistic(database , get_time() , first_name , new_ones[user_id][1] ,
                                         new_ones[user_id][2] , "подписался" , user_id , " ", logs)
                        await app.send_message(user_id, gift_message.replace("|name|", first_name.title() if first_name and  match(first_name) else ""))
                        logs.set_sending_log(user_id, first_name, True)

                    except Exception as err:
                        logs.set_error_log(str(err), "sending to new people " + str(user_id) + " " + first_name if first_name else "")

            leave_message = messages["unsub_message"]
            #get people who leave
            for user_id in old_members.keys():
                if user_id not in new_ones.keys():
                    global bot_unsubscribers
                    bot_unsubscribers += 1
                    first_name = old_members[user_id]
                    remove_user(database, user_id, logs)
                    update_statistic(database, user_id, first_name, logs)
                    if unsub_sending:
                        await asyncio.sleep(get_delay_in_seconds())

                        try:
                            await app.send_message(user_id, leave_message.replace("|name|", first_name.title() if first_name and  match(first_name) else ""))
                            logs.set_sending_log(user_id , first_name , False)
                        except Exception as err:
                            logs.set_error_log(str(err), "Unsub send " + first_name + " " + str(user_id))


            new_ones.clear()
            old_members.clear()


            await asyncio.sleep(300)

    except Exception as err:
        logs.set_error_log(str(err), "sending_code after while 1")

#todo !!!
    try:
        asyncio.get_event_loop().stop()
    except Exception as err:
        logs.set_error_log(str(err), "sending_code after while 2")

    try:
        await app.disconnect()
    except Exception as err:
        logs.set_error_log(str(err) , "sending_code after while 3")


    try:
        if os.path.exists(session_name+".session"):
            os.remove(session_name+".session")
    except Exception as err:
        logs.set_error_log(str(err) , "sending_code afer while 3")

    app = None

    await Admins.notify_active_admins("Юзер бот был остановлен")



@bot.message_handler(func=lambda message: message.text == buttons_admins[7])
async def check_work_bot(message):
    if app:
        try:
            await app.send_message(me, "Привет от бота.\nБот работает")
            await bot.send_message(message.chat.id , "Вам должно прийти сообщение от юзера бота")
        except:
            await bot.send_message(message.chat.id, "Юзер бот не активирован или не работает")
    else:
        await bot.send_message(message.chat.id, "Юзер бот не активирован или не работает")


@bot.message_handler(func=lambda message: message.text == buttons_admins[6])
async def get_status_unsub_sending(message):
    global unsub_sending
    answer = "Рассылка отписавшимся "

    if unsub_sending:
        button = types.InlineKeyboardButton(text="Отключить рассылку" , callback_data="change_status_unsub")
        answer += "<u>включена</u>"
    else:
        button = types.InlineKeyboardButton(text="Включить рассылку" , callback_data="change_status_unsub")
        answer += "<u>выключена</u>"

    markup = types.InlineKeyboardMarkup().add(
        *[
            types.InlineKeyboardButton(text="Назад" , callback_data="cancel"),
            button,
        ]
    )
    await bot.send_message(message.chat.id, answer, reply_markup=markup, parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "change_status_unsub")
async def disable_unsub_sending(call):
    global unsub_sending

    if unsub_sending:
        unsub_sending = False
        await bot.send_message(call.message.chat.id, "Рассылка выключена\nИзменения вступят в силу через пару минут")
    else:
        unsub_sending = True
        await bot.send_message(call.message.chat.id , "Рассылка включена\nИзменения вступят в силу через пару минут")


@bot.message_handler(func=lambda message: message.text == buttons_admins[0])
async def get_statistic(message):
    global bot_subscribers, bot_unsubscribers
    markup = telebot.types.InlineKeyboardMarkup().add(
        *[
            types.InlineKeyboardButton(text="Обнулить статистику" , callback_data="del") ,
        ]
    )
    await bot.send_message(message.chat.id, f"🆕людей подписалось:<u>{bot_subscribers}</u>\n"
                                            f"➖людей отписалось: <u>{bot_unsubscribers}</u>",
                     reply_markup=markup,
                     parse_mode="HTML")


@bot.callback_query_handler(func=lambda call: call.data == "del")
async def del_statistic(call):
    global bot_subscribers, bot_unsubscribers
    await bot.send_message(call.message.chat.id, "Статистика была сброшена")
    bot_subscribers = 0
    bot_unsubscribers = 0


@bot.message_handler(func=lambda message: message.text == buttons_admins[1])
async def get_full_statistic(message):
    markup = telebot.types.InlineKeyboardMarkup(row_width=2).add(
        *[
            types.InlineKeyboardButton(text="Exel", callback_data="post_exel"),
            types.InlineKeyboardButton(text="Сообщение" , callback_data="post_message"),
            types.InlineKeyboardButton(text="Обнулить статистику" , callback_data="reset_full") ,
        ]
    )

    markup.add(types.InlineKeyboardButton(text="Отмена" , callback_data="cancel"))

    await bot.send_message(message.chat.id, "Выбирите exel, если хотите получить exel таблицу\n"
                                            "Выберите сообщение, если хотите получить статистику в боте.", reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data == "post_message")
async def get_full_statistic_in_message(call):
    users = get_full_user_from_db(database, logs)
    answer = "Дата подписки|имя пользователя|ник в тг|телефон|дней был подписан\n\n"

    for user in users:
        answer += user[0] + " " + user[1] + " " + user[2] + " " + user[3]  + " "
        if user[4] == "отписался":
            answer += str(get_unsub_days(user[0], user[6])) + " дня(дней)" + " сейчас отписан" + " "+ "\n\n"
        else:
            answer += user[4] + " " + "\n\n"
    if not users:
        await bot.send_message(call.message.chat.id, "Нет взаимодействий")
        return None

    await bot.send_message(call.message.chat.id, answer)

@bot.callback_query_handler(func=lambda call: call.data == "post_exel")
async def get_full_statistic_exel(call):
    users = get_full_user_from_db(database, logs)
    file = Exel().build(users)
    await bot.send_message(call.message.chat.id, "Вот ваша статистика")
    doc = open(file, 'rb')
    await bot.send_document(call.message.chat.id, document=doc)

@bot.callback_query_handler(func=lambda call: call.data == "reset_full")
async def reset_full_statistic(call):
    reset_full(database, logs)
    await bot.send_message(call.message.chat.id, "Готово")


"""Help info"""

@bot.message_handler(func=lambda message: message.text == buttons_admins[8])
async def text_style(message):
    answer = """
Для красивого оформления текста можно использовать следующие приемы
    \|name\| \- чтобы вставить имя человека, если есть доступ
    \<b\>**Жирный текст**\</b\>
    \<i\>_Наклонный текст_\</i\>
    \<u\>__Подчёркнутый текст__\</u\>
    \<tg\-spoiler\>||Спрятанный текст||\</tg\-spoiler\>
    \<a href\=https://kwork\.ru/user/simply\_kirill\>[ссылка](https://kwork.ru/user/simply_kirill)\</a\>
    
Для быстрого копирования
    \<b\>\</b\>
    \<i\>\</i\>
    \<u\>\</u\>
    \<tg\-spoiler\>\</tg\-spoiler\>
    \<a href\='ссылка'\>\</a\>
    
    """
    await bot.send_message(message.chat.id, answer, parse_mode="Markdownv2")


@bot.message_handler(func=lambda message: message.text == buttons_admins[9])
async def user_bot_instruction(message):
    answer = """
    Для изменения юзер бота, сначала вам нужно будет активировать на сайте (https://my.telegram.org/auth) следуя инструкциям по фотографиям(5 шагов) ниже. Затем вам нужна будет ввести поочередно в бот следующие данные 
!!!<u>У акканту должна быть отключена двоенная верификация(two-step verification)</u>
        *Телефон
        *api_id
        *api_hash
Затем на аккаунт юзер бота придет, код, который нужно будет передать боту, после чего юзер бот будет активирован. Не забудьте добавить юзер бота в канал в качестве администратора!
    """
    await bot.send_message(message.chat.id, answer, parse_mode="HTML")
    await bot.send_photo(message.chat.id, open('instruction/step1.jpg', 'rb'))
    await bot.send_photo(message.chat.id, open('instruction/step2.jpg', 'rb'))
    await bot.send_photo(message.chat.id , open('instruction/step3.jpg' , 'rb'))
    await bot.send_photo(message.chat.id , open('instruction/step4.jpg' , 'rb'))
    await bot.send_photo(message.chat.id , open('instruction/step5.jpg' , 'rb'))


@bot.message_handler(commands=["get_users"])
async def get_number_of_sub(message):
    sub = await get_subscribers(app)
    real_sub = await get_real_count_of_sub(app)
    await bot.send_message(message.chat.id, f"У вас подписчиков: {len(sub.keys())}:{real_sub}")


@bot.message_handler(commands=["logs"])
async def get_logs(message):
    await bot.send_message(message.chat.id, "Логи")
    await bot.send_document(message.chat.id , logs.get_sending_logs())
    await bot.send_document(message.chat.id , logs.get_error_logs())

@bot.message_handler(commands=["clear_logs"])
async def clear_logs(message):
    logs.clear_logs()
    await bot.send_message(message.chat.id, "Готово")

@bot.message_handler(commands=["enable_logs"])
async def enable_logs(message):
    logs.enable_logs()
    await bot.send_message(message.chat.id, "Готово")

@bot.message_handler(commands=["disable_logs"])
async def enable_logs(message):
    logs.disable_logs()
    await bot.send_message(message.chat.id, "Готово")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
async def cancel(call):
    global bool_get_user_bot_data, bool_edit_unsub_m, bool_edit_sub_m
    bool_edit_sub_m = False
    bool_edit_unsub_m = False
    bool_get_user_bot_data = False
    await bot.send_message(call.message.chat.id , "Действие было отменено")


async def start_bot():

    if os.path.exists("./Current-session.session"):
        await asyncio.gather(bot.polling(request_timeout=90) , get_code(None, True, False))
    else:
        await bot.polling(request_timeout=90)


asyncio.run(start_bot())
