from dotenv import load_dotenv
from os import getenv
import logging
import asyncio
from aiogram.dispatcher.event.bases import SkipHandler
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton


load_dotenv()
TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

dp = Dispatcher()

router = Router()
dp.include_router(router)

# Словарь для хранения данных привязаных к пользователям (ключ - ПОЛЬЗОВАТЕЛЬ: значение ДАННЫЕ)
DATA = {}

def register_user(user_id: int, date_message: str, data: dict = DATA) -> dict:
    '''Функция ленивой условной регистрации пользователя.
    Создает и (или) возвращает структуру для хранения данный пользователя.
    Структура данных о пользователе это словарь с ключем 'date' со значением даты последнего выпитого стакана и
    ключем 'water' со значением количество выпитой воды в эту дату'''
    return data.setdefault(user_id, {'date': date_message, 'water': 0})

def func_add_water(user: dict, date_message: str, water: int = 250) -> dict:
    '''Функция добаляет объема выпитой воды к общим данным. Так же функция проверяет дату последнего выпитого стакан воды,
    в случае если дата отличается от даты сообщения вызова этой функции, то учёт выпитой воды происходит заново.
    На параметры функция:
    - user - получает структуру данных (dict) пользователя;
    - date_message - дату сообщения о выпитой воде (дата сообщения обрабатывающаяся хендлером add_water);
    - water - количество выпитой воды (по умолчанию устоновленно 250 мл);
    Обработка. Функция сопоставляет дату последнего выпитого стакана (user['date']) и дату сообщения (параметр функции date_massage),
    при их совпадении счетчик воды (user['water']) увеличивается на количество выпитой воды (параметр функции water).
    При их различии в счетчик воды (user['water']) устанавливается значения выпитой воды (параметр функции water)
    и в дату последнего выпитого стакана (user['date']) устанавливается параметр date_massage.
    Функция возвращает словарь user"
    учитывает добавляет к учету выпитую воду сегодня'''
    if user['date'] == date_message:
        user['water'] += water
    else:
        user['date'] = date_message
        user['water'] = water
    return user

def func_statistics(user: dict, date_message: str) -> int:
    '''Функция возврата количества выпитой воды за сегодня (дата сообщения вызывающего функцию).'''
    return user['water'] if user['date'] == date_message else 0

def func_reset(user: dict, date_message: str) -> dict:
    '''Функция сбразывает количество выпитой воды за сегодня (дата сообщения вызывающего функцию).'''
    user['date'] = date_message
    user['water'] = 0
    return user

def check_user(user_id: int, data: dict = DATA) -> bool:
    '''функция для проверки регистрации пользователя'''
    return True if data.get(user_id) is not None else False

def check_user_exception(user_id: int, data: dict = DATA):
    '''Функция вызывает исключение SkipHandler если пользователь не зарегистрирован.
    Функция использыется для передачи сообщения в обработку другим хендлерам.'''
    if not check_user(user_id):
        raise SkipHandler
    return data[user_id]

@router.message(Command('start'))
async def cmd_start(message: Message):
    '''Хендлер регистрирует пользователя и отображает для него клавиатуру'''
    user_id = message.from_user.id
    if check_user(user_id):
        text = 'Привет👋, сколько ты уже выпил воды сегодня?😉'
    else:
        register_user(user_id, message.date.date().isoformat())
        text = 'Привет👋, я помогу тебе отследить дневную норму потребления воды\nФиксируй каждый выпитый стакан, и мы узнаем, сколько воды ты потребляешь!'
    await message.answer(
        text=text,
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[
                [KeyboardButton(text='🥤 Выпил стакан (250 мл)', style='primary')],
                [KeyboardButton(text='📊 Мой прогресс'),
                 KeyboardButton(text='🔄 Сброс')]
            ],
            is_persistent=True,
            resize_keyboard=True
        )
    )

@router.message(F.text == '🥤 Выпил стакан (250 мл)')
async def add_water(message: Message):
    '''Хендлер регистрирует пользователя, учитывает выпитый стакан воды и возвращает общий объём и выпитой воды за сегодня'''
    user_id = message.from_user.id
    user = register_user(user_id, message.date.date().isoformat())
    DATA[user_id] = func_add_water(user, message.date.date().isoformat())
    await message.answer(
        text=f'Записано! Итого: {DATA[user_id]["water"]} мл'
    )

@router.message(F.text == '📊 Мой прогресс')
async def statistics(message: Message):
    '''Хендлер проверяет регистрацию пользователя и возвращает зарегистрированному пользователю, объем выпитой воды за сегодня'''
    user_id = message.from_user.id
    user = check_user_exception(user_id)
    water = func_statistics(user, message.date.date().isoformat())
    text = f'Сегодня выпито {water} мл.\n'
    if water == 0:
        text = f'{text}Ну выпей хоть стаканчик😢'
    elif 250 <= water <= 1000:
        text = f'{text}Давай попьём ещё водички😊'
    elif 1000 < water < 1750:
        text = f'{text}Более половины суточной нормы уже выпита🤗'
    elif water >= 1750:
        text = f'{text}Последний стакан и норма будет сделана👍'
    elif water == 2000:
        text = f'{text}Суточная норма потреблена ровно!👌'
    elif water > 2000:
        text = f'{text}Суточная норма воды потреблена! Поздравляю!🥳'
    await message.answer(text=text)

@router.message(F.text == '🔄 Сброс')
async def reset(message: Message):
    '''Хендлер проверяет регистрация пользователя и сбрасывает объем выпитой воды за сегодня'''
    user_id = message.from_user.id
    user = check_user_exception(user_id)
    DATA[user_id] = func_reset(user, message.date.date().isoformat())
    await message.answer(text='Счётчик выпитой воды обнулён')

@router.message()
async def fallback(message: Message):
    '''Хендлер проверяет регистрацию пользователя, предлагает зарегистрироваться, если пользователь этого не сделал,
    и выбрать команду на клавишах'''
    if check_user(message.from_user.id):
        text = 'Настало время попить водички? 😁\nИспользуй клавиши для отправки команд😉'
    else:
        text = 'Кажется, мы не знакомы😀?\nОтправь /start для начала работы🤓'
    await message.answer(
        text=text
    )

async def main():
    logger = logging.getLogger(__name__)
    logger.info('Бот готов к работе')
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())