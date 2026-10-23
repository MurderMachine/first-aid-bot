import os
import asyncio
from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    ReplyKeyboardMarkup,
    KeyboardButton
)

# Токен бота @ProtoCross_bot
BOT_TOKEN = "8796370805:AAFBgH9CshXDKX5RFWtYhindlNyzJaiA2lQ"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# База вопросов по протоколам домедицинской помощи ЗШР ТЧХУ (Версия 3)
QUIZ_QUESTIONS = [
    {
        "question": "Сколько времени нужно непрерывно удерживать прямое давление на рану после тампонирования?",
        "options": [
            "Сразу накладывать повязку",
            "Не менее 1 минуты",
            "Не менее 3 минут",
            "Около 10 минут"
        ],
        "correct_option_id": 2,
        "explanation": "Согласно обновленному протоколу (CoTCCC / Stop the Bleed), прямое ручное давление после тампонирования удерживается не менее 3 минут для формирования сгустка."
    },
    {
        "question": "Какой приоритетный метод закрытия открытой раны грудной клетки (пневмоторакс)?",
        "options": [
            "Герметизация пленкой с 3 сторон",
            "Вентильная окклюзионная наклейка (chest seal)",
            "Тугое тампонирование раны",
            "Давящая марлевая повязка"
        ],
        "correct_option_id": 1,
        "explanation": "Метод заклейки «с 3 сторон» исключен; приоритетом является окклюзионная наклейка с клапаном (chest seal)."
    },
    {
        "question": "С чего начинается СЛР у детей и младенцев по актуальному протоколу?",
        "options": [
            "С 30 компрессий грудной клетки",
            "С 5 начальных спасательных вдохов",
            "С немедленного разряда дефибриллятора",
            "С 2 глубоких вдохов"
        ],
        "correct_option_id": 1,
        "explanation": "По протоколам ERC PLS реанимация у детей начинается с 5 начальных спасательных вдохов, так как остановка сердца чаще всего имеет гипоксическую природу."
    },
    {
        "question": "Каково главное действие при тепловом ударе при наличии условий?",
        "options": [
            "Немедленно начать транспортировку",
            "Погрузить пострадавшего в прохладную/холодную воду («cool first, transport second»)",
            "Дать горячий чай",
            "Положить лед прямо на кожу"
        ],
        "correct_option_id": 1,
        "explanation": "При истинном тепловом ударе действует принцип «сначала охлади, потом транспортируй» — приоритетно погружение в воду по шею."
    },
    {
        "question": "Рекомендуется ли вызывать рвоту при остром отравлении неизвестным веществом?",
        "options": [
            "Да, обязательно и немедленно",
            "Да, если прошло менее 30 минут",
            "Нет, вызывать рвоту категорически запрещено",
            "Только если вещество не имеет запаха"
        ],
        "correct_option_id": 2,
        "explanation": "Вызов рвоты запрещен протоколами (IFRC/ANZCOR) из-за риска повторного химического ожога пищевода и аспирации рвотных масс."
    },
    {
        "question": "Какова дозировка аспирина (ацетилсалициловой кислоты) при подозрении на сердечный приступ?",
        "options": [
            "50–75 мг проглотить целиком",
            "160–325 мг разжевать и проглотить",
            "500–1000 мг растворить в воде",
            "Аспирин давать запрещено"
        ],
        "correct_option_id": 1,
        "explanation": "По протоколу в сознании при отсутствии аллергии дают разжевать и проглотить 160–325 мг нерастворимой таблетки аспирина."
    },
    {
        "question": "Что делать, если при сортировке START пострадавший способен самостоятельно ходить?",
        "options": [
            "Присвоить категорию «Зеленый» и вывести в безопасное место",
            "Присвоить категорию «Желтый» и положить на носилки",
            "Оставить на месте и ждать скорую",
            "Начать проводить CABC прямо на месте"
        ],
        "correct_option_id": 0,
        "explanation": "По алгоритму START все ходячие пострадавшие сразу получают категорию «зеленый» (легкие) и направляются в безопасное место."
    },
    {
        "question": "Какова роль длинной транспортировочной доски по обновленному протоколу (виборочная иммобилизация)?",
        "options": [
            "Средство длительной фиксации до приезда скорой",
            "Средство переноски/экстракции, а не длительного удержания",
            "Применяется только при переломах ног",
            "Запрещена к использованию в любых случаях"
        ],
        "correct_option_id": 1,
        "explanation": "Длинная доска — средство переноски/эвакуации. Длительное нахождение на ней вызывает пролежни и ухудшает вентиляцию легких."
    }
]

# Хранилище прогресса {user_id: индекс_вопроса}
user_state = {}

def get_main_keyboard():
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="Следующий вопрос ➡️")],
            [KeyboardButton(text="Начать заново 🔄")]
        ],
        resize_keyboard=True
    )

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_state[message.from_user.id] = 0
    await message.answer(
        "👋 Привет! Добро пожаловать в тренажер по протоколам домедицинской помощи (ЗШР ТЧХУ).\n\n"
        "Формат викторины: после выбора варианта Telegram покажет правильный ответ и пояснение из актуального протокола.\n\n"
        "Нажмите кнопку ниже, чтобы начать тест.",
        reply_markup=get_main_keyboard()
    )

@dp.message(F.text.in_(["Следующий вопрос ➡️", "Начать заново 🔄", "/quiz"]))
async def send_quiz(message: Message):
    user_id = message.from_user.id
    
    if message.text == "Начать заново 🔄":
        user_state[user_id] = 0

    idx = user_state.get(user_id, 0)

    if idx >= len(QUIZ_QUESTIONS):
        await message.answer(
            "🎉 Тест завершен! Вы ответили на все доступные вопросы.\n\n"
            "Чтобы пройти тренировку еще раз, нажмите «Начать заново 🔄».",
            reply_markup=get_main_keyboard()
        )
        return

    q = QUIZ_QUESTIONS[idx]
    
    await bot.send_poll(
        chat_id=message.chat.id,
        question=q["question"],
        options=q["options"],
        type="quiz",
        correct_option_id=q["correct_option_id"],
        explanation=q["explanation"],
        is_anonymous=False
    )
    
    user_state[user_id] = idx + 1

# Фейковый веб-сервер, чтобы Render не закрывал процесс по таймауту порта
async def handle_ping(request):
    return web.Response(text="Bot is running!")

async def start_web_server():
    app = web.Application()
    app.router.add_get("/", handle_ping)
    app.router.add_get("/healthz", handle_ping)
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"Web server started on port {port}")

async def main():
    print("Бот @ProtoCross_bot успешно запущен...")
    # Запускаем параллельно веб-сервер для Render и polling бота
    await asyncio.gather(
        start_web_server(),
        dp.start_polling(bot)
    )

if __name__ == "__main__":
    asyncio.run(main())
