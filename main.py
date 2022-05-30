from bot_keyboards.client_kb import kb_client
import logging
from aiogram import Bot, Dispatcher, executor, types
import asyncio
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from utility import load_data, dump_data
import requests
import aioschedule
from colorama import Fore
import os
from dotenv import load_dotenv

load_dotenv()

os.getenv('API_TOKEN')
API_TOKEN = os.getenv('API_TOKEN')
# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot,storage=storage)


class SetEvent(StatesGroup):
    waiting_for_currency= State()
    waiting_for_period = State()
    finishing_up = State()

@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    """
    This handler will be called when user sends `/start` or `/help` command
    """
    await message.reply("Hi!\nI'm Exchange Bot!\n", reply_markup=kb_client)

@dp.message_handler(commands=['CurrencyRete'])
async def add_currency(message: types.Message):
    """
    This handler will be called when user sends '/CurrencyRete' command
    """
    await message.answer("Please enter currency from and currency to(ex.: usd,eur)")

@dp.message_handler(commands=['cencelSchedule'])
async def add_period(message: types.Message):
    """
    This handler will be called when user sends '/cencelSchedule' command, and it cencel the schedule
    """
    buttons = [
        types.InlineKeyboardButton(text="Cencel", callback_data="cencel"),
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await message.answer(text="Please confirm", reply_markup=keyboard)



@dp.callback_query_handler(text="cencel")
async def confirm(message: types.Message):
    """
    Confirm button
    """
    await scheduler(loop = False)
    await message.answer("Schedule was cenceled")


@dp.message_handler(commands=['addSchedule'])
async def add_period(message: types.Message):
    """
    This handler will be called when user sends '/addSchedule' command
    Create new schedule
    """
    keyboard = types.InlineKeyboardMarkup()
    buttons = [
        types.InlineKeyboardButton(text="Add currency", callback_data="add_schedule_currency")
    ]
    keyboard.add(*buttons)
    await message.answer("Lets create your schedule", reply_markup=keyboard)

@dp.callback_query_handler(text="add_schedule_currency")
async def add_schedule_curency(call: types.CallbackQuery):
    """
    Add schedule currency
    """
    await SetEvent.waiting_for_currency.set()
    await call.message.answer(text="Please enter currency from and currency to(ex.: usd,eur)")
    await call.answer()


@dp.message_handler(state=SetEvent.waiting_for_currency, content_types=types.ContentTypes.TEXT)
async def get_schedule_name(message: types.Message, state: FSMContext):
    """
    Here we add data about currency
    """
    user_data = message.text.split(',')
    currency_from = user_data[0]
    currency_to = user_data[1]
    formated_currency = "{0}_{1}".format(currency_from, currency_to)
  
    await state.update_data(currency=formated_currency) #add currency
    await message.answer(text="Please enter how often you want to get information (enter in minutes)")
    await SetEvent.next()


@dp.message_handler(state=SetEvent.waiting_for_period, content_types=types.ContentTypes.TEXT)
async def get_schedule_time(message: types.Message, state: FSMContext):
    """
    Write info about time period for our schedule
    """
    await state.update_data(period=int(message.text))
    buttons = [
        types.InlineKeyboardButton(text="Confirm", callback_data="create_event"),
        types.InlineKeyboardButton(text="Cancel", callback_data="forget"),
    ]
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(*buttons)
    await message.answer(text="Please confirm event creation:", reply_markup=keyboard)
    await SetEvent.next()



@dp.callback_query_handler(text="create_event", state=SetEvent.finishing_up)
async def create_schedule(call: types.CallbackQuery, state: FSMContext):
    """
    Here we create schedule
    """
    currency = await state.get_data()

    await state.finish()
    await state.reset_state()

    for file in os.listdir("users"): #if we do not have file for this user
         if not file.startswith(str(call.from_user.id)):
            load_data(call.from_user.id) #create new file

    user_data = load_data(call.from_user.id) #get info from json file

    entry =  {
        "records": user_data[-1]["records"] + 1, 
        "user_id": call.from_user.id, 
        "exchange_currency": currency['currency'], 
        "period": currency['period'], 
        "username": call.from_user.username
        }
    user_data.append(entry)

    dump_data(user_data)
    asyncio.create_task(scheduler(currency = currency['currency'], minutes = currency['period'], user_id = call.from_user.id))
    print(Fore.GREEN, call.from_user.username + " have created new schedule")
    await call.answer()
   


@dp.message_handler()
async def get_currency(message: types.Message):
    """
    Call this function when we want to an exchange rate instantly
    """
    try:
        user_data = message.text.split(',')
        currency_from = user_data[0]
        currency_to = user_data[1]
        user_id = message.from_user.id
        await get_data(currency_from, currency_to, user_id)
    except:
        print(Fore.RED, "Incorrect currency")
        await message.answer(text="You enter incorrect currency")


async def get_data(currency_from, currency_to, user_id):
    """
    Here we get data from requests
    """
    data_for_request = "{0}_{1}".format(currency_from, currency_to)
    r = requests.get('https://coinpay.org.ua/api/v1/exchange_rate')
    request_data = r.json().get('rates')
    for pairs in request_data:
        pair = pairs.get('pair')
        if data_for_request.upper() == pair:
            answer = 'One {0} cost {1} {2}'.format(currency_from, pairs.get('price'), currency_to)
            await bot.send_message(user_id, answer)


async def scheduler(**kwargs):
    """
    Function for create a schedule
    """
    n=1
    try:
        if kwargs['loop'] == False:
            n=0
            aioschedule.clear()
    except:
        pass
    try:
        data = kwargs['currency'].split('_')
        currency_from = data[0]
        currency_to = data[1]
        aioschedule.every(kwargs['minutes']).seconds.do(lambda: get_data(currency_from, currency_to, kwargs['user_id']))
        print(Fore.GREEN, "Schedule was create for user({0}) with period {1} minutes".format(kwargs['user_id'], kwargs['minutes']))
        while n:
            await aioschedule.run_pending()
            await asyncio.sleep(1)
    except:
        pass

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)

