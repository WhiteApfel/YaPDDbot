import logging
import requests
from aiogram import Bot, types
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.dispatcher import Dispatcher
from aiogram.utils.executor import start_webhook
import random
import re
import pymongo
import time
import string

API_TOKEN = '211412442:NJjdfsdfbsbjhb#Bjh3bjhb#HJV3ghhg3'
PDD_TOKEN = "UCTKVTCYFVV43JCANEDBLEUFT6BFPCCRQATIWFOHKDAB76JPO64Q"
EXAMPLE_MAILBOX = "topolya@imgay.design"
RE_SHORT = r"[\w\d]{1,3}@imgay\.design"
RE_NORMAL = r"[\w\d]{4,32}@imgay\.design"
CONTACT_USERNAME = "whiteapfel"
BLAGODAROCKA = f'\n\nPS. Сервера и домен стоят деняков, которые оплачиваются из собственных средств. Буду безмерно рад, ' \
			   f'если поддержишь рубликом. <a href="https://rocketbank.ru/whiteapfel">Рокет</a>\n\n' \
			   f'PPS. Почту обслуживает Яндекс и я к ней не имею никакого доступа, только создаю и передаю тебе стартовый пароль'


# webhook settings
WEBHOOK_HOST = f'https://any.host.tld'
WEBHOOK_PATH = f'/{API_TOKEN}'  # Или любой другой нужный путь
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
# webserver settings
WEBAPP_HOST = '0.0.0.0'  # or ip
WEBAPP_PORT = 32123
# DB settings
DB = pymongo.MongoClient("mongodb://user:password@127.0.0.1:2717/")

logging.basicConfig(level=logging.CRITICAL)

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
dp.middleware.setup(LoggingMiddleware())


def gen_tmplt(what: str):
	if what == "sorry":
		return random.choice(['Извини', 'Прости', 'Пожалуйста, прости', 'Прости, пожалуйста', 'Мне жаль',
								'Мне безумно жаль',  'Мне правда жаль', 'Упс', 'Увы'])
	if what == "name":
		return random.choice(['солнышко', 'зайка', 'котенька', 'лися'])
	if what == "where":
		return random.choice(['я работаю', 'я это делаю', 'я делаю это', 'это делается', 'могу это сделать'])
	if what == "how":
		return random.choice(['только ', 'исключительно ', 'нигде больше, кроме как ', ''])
	if what == "pm":
		return random.choice(['личных сообщениях', 'ЛС', 'личке', 'PM', 'DM'])


@dp.message_handler(commands=['reg_gaymail', "start", "help"])
async def gaymail_reg(message: types.Message):
	if message.chat.type == "private":
		await message.answer(
			f"Я тут почтовые ящички регистрирую на домене <code>{EXAMPLE_MAILBOX.split('@')[-1]}</code>\n\n"
			f"Просто отправь мне почтовый ящик, который хочешь получить, в формате <code>{EXAMPLE_MAILBOX}</code>. Он "
			f"обязательно должен оканчиваться на\xa0<code>@{EXAMPLE_MAILBOX.split('@')[-1]}</code>.",
			parse_mode="HTML")
	else:
		await message.reply(f"{gen_tmplt('sorry')}, {gen_tmplt('name')}, но {gen_tmplt('where')} "
						f"{gen_tmplt('how')}в {gen_tmplt('pm')}")


@dp.message_handler(lambda m: re.match(RE_SHORT, m.text.lower()))
async def gaymail_email_short(message: types.Message):
	await message.reply(f'{gen_tmplt("sorry")}, меньше 4 символов нельзя, такие правила. '
		f'И что ты мне сделаешь? Я в другом городе!\n\nМожешь написать @{CONTACT_USERNAME}, тебе постараются помочь')


@dp.message_handler(lambda m: re.match(RE_NORMAL, m.text.lower()))
async def gaymail_email_normal(message: types.Message):
	if message.from_user.id not in DB.WAEmail.accounts.distinct("user_id"):
		pw = "".join([random.choice(string.ascii_letters+string.digits) for _ in range(15)])
		ul = message.text.lower().split("@")[0]
		if ul not in DB.WAEmail.accounts.distinct("login"):
			un = message.from_user.username if message.from_user.username else message.from_user.first_name
			DB.WAEmail.accounts.save({"login": ul, "password": pw, "user_id": message.from_user.id, "username": str(un),
											"protected": False, "time": int(time.time()), "status": "wait"})
			await message.reply(f'Понял, принял. Скоро напишу тебе о решении по {ul}@{EXAMPLE_MAILBOX.split("@")[-1]} 😉'
								f'{BLAGODAROCKA}',
					parse_mode="HTML")
			keyboard = types.InlineKeyboardMarkup()
			keyboard.add(
				types.InlineKeyboardButton(text="Ну нет", callback_data=f"gaymail|no|{ul}|{message.from_user.id}"),
				types.InlineKeyboardButton(text="Окей!", callback_data=f"gaymail|yes|{ul}|{message.from_user.id}")
			)
			await bot.send_message(248733366, f'Тут хотят зарегистрировать ящичек.\n\nЛогин: {ul}\nПользователь: @{un} -'
										f' {message.from_user.id}', reply_markup=keyboard)
		else:
			await message.reply(f"Увы, но этот почтовый ящик я уже кому-то отдал.\n\nЕсли он тебе очень нужен, напиши в "
							f"личные сообщения @{CONTACT_USERNAME}")
	else:
		await message.reply(f"Мне жаль, но на тебя уже заводили ящик, а я больше одного не могу выдать 😞\n\nЕсли уверен, "
						f"что это ошибочка, напиши в личные сообщения @{CONTACT_USERNAME}")


@dp.callback_query_handler(lambda call: call.data.split("|")[0] == "gaymail")
async def gaymail_callback_base(call: types.CallbackQuery):
	act = call.data.split("|")[1]
	user_info = DB.WAEmail.accounts.find({"user_id": int(call.data.split("|")[3])})[0]
	if act == "yes":
		r = requests.post("https://pddimp.yandex.ru/api2/admin/email/add",
						data={"domain": EXAMPLE_MAILBOX.split('@')[-1], "login": user_info["login"], "password": user_info["password"]},
						headers={"PddToken": PDD_TOKEN}).json()
		if r["success"] == "ok":
			keyboard = types.InlineKeyboardMarkup()
			keyboard.add(
				types.InlineKeyboardButton(text="🔐 Получить пароль",
					callback_data=f'gaymailpsswd|{user_info["user_id"]}')
			)
			await bot.send_message(user_info["user_id"],
							f'<b>Успех! Создано 🎉</b>\n\n'
							f''
							f'Ящик {user_info["login"]}@{EXAMPLE_MAILBOX.split("@")[-1]} теперь твой.\n\n'
							f''
							f'Можешь использовать Яндекс.Почту или настроить свой почтовый клиент:\n\n'
							f''
							f'~~ ~~ ~~ ~~ ~~ ~~ ~~\n'
							f'<b>IMAP</b>\n'
							f'Сервер: <code>imap.yandex.ru</code>\n'
							f'Соединение: <code>SSL</code>\n'
							f'Порт: <code>993</code>\n\n'
							f''
							f'<b>SMTP</b>\n'
							f'Сервер: <code>smtp.yandex.ru</code>\n'
							f'Соединение: <code>SSL</code>\n'
							f'Порт: <code>465</code>\n'
							f'~~ ~~ ~~ ~~ ~~ ~~ ~~\n\n'
							f''
							f'<b>Логин</b>: <code>{user_info["login"]}@{EXAMPLE_MAILBOX.split("@")[-1]}</code>\n\n'
							f''
							f'Чтобы получить стартовый пароль, нажми на кнопку снизу. '
							f'Рекомендую сразу после получения зайти на https://mail.yandex.ru и сменить его.',
							disable_web_page_preview=True, parse_mode="HTML", reply_markup=keyboard)
			DB.WAEmail.accounts.update({"user_id": user_info["user_id"]},
											{"$set": {"status": "OK", "time": int(time.time())}})
			await bot.answer_callback_query(callback_query_id=call.id, text="Успешно отправлено!")
			await bot.edit_message_text(
				f'<b>Успех! Создано!</b>\n\n'
				f'{user_info["login"]}@{EXAMPLE_MAILBOX.split("@")[-1]} теперь у @{user_info["username"]}',
				chat_id=call.message.chat.id, message_id=call.message.message_id, parse_mode="HTML")
		else:
			await bot.send_message(248733366, f"Тут ошибка:\n\n{str(r)}")
	else:
		DB.WAEmail.accounts.remove({"user_id": user_info["user_id"]})
		await bot.send_message(user_info["user_id"],
				f'Мне жаль, твоя заявка на {user_info["login"]}@{EXAMPLE_MAILBOX.split("@")[-1]} отклонена.\n\n'
				f'Если тебе очень хочется этот почтовый ящик, можешь написать @{CONTACT_USERNAME}')
		await bot.delete_message(call.message.chat.id, call.message.message_id)
		await bot.answer_callback_query(callback_query_id=call.id, text="Удалено и уничтожено")


@dp.callback_query_handler(lambda call: call.data.split("|")[0] == "gaymailpsswd")
async def gaymail_callback_password(call: types.CallbackQuery):
	user_info = DB.WAEmail.accounts.find({"user_id": int(call.data.split("|")[1])})[0]
	start_message = "Кто-то говорил, что уже изменил пароль. Новый я не знаю, но...\n\nСтартовый" if user_info[
		"protected"] else "Пароль"
	finish_message = "Если всё же ещё стоит этот, измени его" if user_info["protected"] else "Измени его"
	psswd_message = "Пароль точно изменён" if user_info["protected"] else "Пароль изменён"
	keyboard = types.InlineKeyboardMarkup()
	keyboard.add(
		types.InlineKeyboardButton(text=f"🔐 {psswd_message}", callback_data=f'gaymailpsswdprotected|{user_info["user_id"]}')
	)
	await bot.send_message(chat_id=call.message.chat.id,
					text=f'{start_message}: <code>{user_info["password"]}</code>\n\n{finish_message}, '
						f'используя <a href="https://mail.yandex.ru">Яндекс.Почту</a>.',
					parse_mode="HTML", disable_web_page_preview=True, reply_markup=keyboard)
	await bot.answer_callback_query(callback_query_id=call.id)


@dp.callback_query_handler(lambda call: call.data.split("|")[0] == "gaymailpsswdprotected")
async def gaymail_callback_passwordprotected(call: types.CallbackQuery):
	DB.WAEmail.accounts.update({"user_id": int(call.data.split("|")[1])}, {"$set": {"protected": True}})
	await bot.delete_message(call.message.chat.id, call.message.message_id)


@dp.message_handler(commands=["ping"])
async def echo(message: types.Message):
	await bot.send_message(message.chat.id, "/pong")


async def on_startup(dp):
	await bot.set_webhook(WEBHOOK_URL)


# insert code here to run it after start


async def on_shutdown(dp):
	logging.warning('Shutting down..')

	# insert code here to run it before shutdown

	# Remove webhook (not acceptable in some cases)
	await bot.delete_webhook()

	# Close DB connection (if used)
	await dp.storage.close()
	await dp.storage.wait_closed()

	logging.warning('Bye!')


if __name__ == '__main__':
	start_webhook(
		dispatcher=dp,
		webhook_path=WEBHOOK_PATH,
		on_startup=on_startup,
		on_shutdown=on_shutdown,
		skip_updates=True,
		host=WEBAPP_HOST,
		port=WEBAPP_PORT
	)
