from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

b1 = KeyboardButton('/CurrencyRete')
b2 = KeyboardButton('/addSchedule')
b3 = KeyboardButton('/cencelSchedule')

kb_client = ReplyKeyboardMarkup()
kb_client.add(b1).add(b2).add(b3)


