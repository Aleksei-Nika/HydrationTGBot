from dotenv import load_dotenv
from os import getenv
import logging
from aiogram import Bot, Dispatcher, Router, F
from aiogram.filters import Command


load_dotenv()
TELEGRAM_BOT_TOKEN = getenv("TELEGRAM_BOT_TOKEN")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

bot = Bot(token=TELEGRAM_BOT_TOKEN)

dp = Dispatcher()

router = Router()
dp.include_router(router)

@router.message()