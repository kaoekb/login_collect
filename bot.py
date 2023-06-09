import telebot
from config import Token_MDB, Token_tg 
from pymongo import MongoClient

bot = telebot.TeleBot(Token_tg)

class DataBase:
	def __init__(self):
		cluster = MongoClient(Token_MDB)

		self.db = cluster["Users_school_21"]
		self.login = self.db["login"]

	def get_user(self, chat_id):
		user = self.login.find_one({"chat_id": chat_id})

		if user is not None:
			return user

		user = {
			"chat_id": chat_id,
			"login_school": [],
			"login_tg": [],
            "user_id": [],
		}

		self.login.insert_one(user)

		return user

	def set_user(self, chat_id, update):
		self.login.update_one({"chat_id": chat_id}, {"$set": update})

db = DataBase()

def find_login(login): # Проверка, есть ли такой логин в БД
    query = {"$or": [{"login_school": login}, {"login_tg": login}]}
    result = db.login.find_one(query)
    if result is None:
        return None
    else:
        return result["login_school"], result["login_tg"]


@bot.message_handler(commands=['start'])
def handle_start(message):
    # Получаем id пользователя
    user_id = message.from_user.id
    # Проверяем, есть ли пользователь в базе данных
    if db.login.find_one({"user_id": user_id}) is not None:
        # Если пользователь уже есть в базе данных, переходим в функцию callback
            bot.register_next_step_handler(message, callback)
            bot.send_message(message.chat.id, 'Введи школьный или телеграм ник (без @) интересующего тебя пира.')

    else:
        # Если пользователь новый, отправляем сообщение с просьбой ввести школьный ник
        bot.send_message(message.chat.id, f'Привет, {message.from_user.first_name}, введи свой школьный ник')
        bot.register_next_step_handler(message, hi)


def hi(message):
    # Получаем логин пользователя в нижнем регистре
    login_school = message.text.lower()
    # Получаем логин пользователя в Telegram в нижнем регистре
    login_tg = message.from_user.username.lower() if message.from_user.username is not None else None
    user_id = message.from_user.id
    # Проверяем, есть ли логин в Telegram
    if login_tg is None:
        # Если логина нет, отправляем сообщение с просьбой создать логин
        bot.send_message(message.chat.id, 'Для использования бота необходимо создать логин (имя пользователя) в настройках Telegram, это не сложно.')
    else:
        # Если логин есть, добавляем логины в базу данных
        db.login.insert_one({"login_school": login_school, "login_tg": login_tg, "user_id": user_id})
        bot.send_message(message.chat.id, 'Введи школьный или телеграм ник (без @) интересующего тебя пира.')
    bot.register_next_step_handler(message, callback)


@bot.message_handler(content_types=['text'])
def callback(message):
    login = message.text.lower()
    result = find_login(login)
    if result is None:
        bot.send_message(message.chat.id, "Логин не найден")
        bot.send_message(message.chat.id, 'Введи школьный или телеграм ник (без @) интересующего тебя пира.')

    else:
        text = f"Login school: {result[0].capitalize()}, login tg: @{result[1].capitalize()}"
        bot.send_message(message.chat.id, text)
        bot.send_message(message.chat.id, 'Введи школьный или телеграм ник интересующего тебя пира.')


bot.polling()