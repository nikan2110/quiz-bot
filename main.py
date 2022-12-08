import logging
import inline_keyboard
import tools
import constants
import API
import os
from pymongo import MongoClient
from aiogram import Bot, Dispatcher, executor, types, utils
from aiogram.utils.executor import start_webhook

# Credentials
API_TOKEN = tools.get_from_env("TELEGRAM_API_TOKEN")
HEROKU_APP_NAME=tools.get_from_env("HEROKU_APP_NAME")

# webhook settings
WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'

# webserver settings
WEBAPP_HOST = '0.0.0.0'
WEBAPP_PORT = int(os.getenv('PORT'))

# Question for user
QUESTIONS = {}

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize bot and dispatcher and DB
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)


@dp.message_handler(commands=['start', 'help'])
async def send_welcome(message: types.Message):
    chat_id = message.from_user.id
    logging.info('start button pushed. received chat_id: %s', chat_id)
    if tools.user_collection.find_one(filter={"id": chat_id}) is None:
        tools.user_collection.insert_one({"id": chat_id, "user_name": "", "number_of_questions": 0,
                                         "difficulty": "", "count_correct_answers": 0, "category_id": ""})
    await message.answer(text=constants.GREETING_TEXT,
                         reply_markup=inline_keyboard.PLAY)


@dp.callback_query_handler(text='play')
async def register_user(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    user = tools.user_collection.find_one(filter={"id": chat_id})
    logging.info('received user_name after play button: %s', user["user_name"])
    if user["user_name"] == "":
        await bot.send_message(chat_id=chat_id, text=constants.TAKE_USER_NAME_TEXT)
    else:
        user_name = user["user_name"]
        tools.user_collection.update_one(filter={"id": chat_id}, update={
                                         "$set": {"count_correct_answers": 0}})
        await bot.send_message(chat_id=chat_id, text=f"Welcome back {user_name}. Do you want to continue?", reply_markup=inline_keyboard.CONTINUE)


@dp.callback_query_handler(text='cancel')
async def cancel(callback_query: types.CallbackQuery):
    await bot.send_message(chat_id=callback_query.from_user.id, text=constants.GOODBYE_TEXT)


@dp.message_handler()
async def register(message: types.Message):
    key_word = message.text.split(":")[0].lower()
    if key_word.startswith("name"):
        user_name = message.text.split(":")[1].title().strip()
        chat_id = message.from_user.id
        tools.user_collection.update_one(filter={"id": chat_id}, update={
                                                  "$set": {"user_name": user_name}})
        logging.info('received user_name after registration: %s', user_name)
        await message.answer(text=f"Hello, {user_name}! Nice to meet you! ")
        await message.answer(text=constants.NUMBER_OF_QUESTIONS_TEXT,  reply_markup=inline_keyboard.QUESTIONS)
    else:
        await message.answer(text="Press play to start new quiz",  reply_markup=inline_keyboard.PLAY)


@dp.callback_query_handler(text_startswith="continue")
async def user_exist(callback_query: types.CallbackQuery):
    await bot.send_message(chat_id=callback_query.from_user.id, text=constants.NUMBER_OF_QUESTIONS_TEXT,  reply_markup=inline_keyboard.QUESTIONS)


@dp.callback_query_handler(text_startswith="question")
async def questions(callback_query: types.CallbackQuery):
    number_of_questions = callback_query.data.split(":")[1]
    chat_id = callback_query.from_user.id
    logging.info('received number of questions: %s', number_of_questions)
    tools.user_collection.update_one(filter={"id": chat_id}, update={
                                              "$set": {"number_of_questions": number_of_questions}})
    await bot.send_message(chat_id=chat_id, text=constants.CATEGORY_TEXT,  reply_markup=inline_keyboard.CATEGORIES)


@dp.callback_query_handler(text_startswith="category")
async def categories(callback_query: types.CallbackQuery):
    category_id = callback_query.data.split(":")[1]
    chat_id = callback_query.from_user.id
    logging.info('received category id: %s', category_id)
    tools.user_collection.update_one(filter={"id": chat_id}, update={
                                              "$set": {"category_id": category_id}})
    await bot.send_message(chat_id=chat_id, text=constants.DIFFICULTY_TEXT,  reply_markup=inline_keyboard.DIFFICULTIES)


@dp.callback_query_handler(text_startswith="difficulty")
async def difficulty_and_first_question(callback_query: types.CallbackQuery):
    difficulty = callback_query.data.split(":")[1]
    chat_id = callback_query.from_user.id
    logging.info('received difficulty: %s', difficulty)
    tools.user_collection.find_one_and_update(filter={"id": chat_id}, update={
                                              "$set": {"difficulty": difficulty}})
    global QUESTIONS
    current_user = tools.user_collection.find_one(filter={"id": chat_id})
    amount = current_user["number_of_questions"]
    category = current_user["category_id"]
    difficulty = current_user["difficulty"]
    list_of_questions = API.get_questions(amount, category, difficulty)
    QUESTIONS[chat_id] = list_of_questions
    logging.info('quantity of user questions: %s', len(QUESTIONS.get(chat_id)))
    if len(QUESTIONS.get(chat_id)) != 0:
        current_question = QUESTIONS.get(chat_id)[0]
        question_text = current_question["question"]
        del current_question["question"]
        await bot.send_message(chat_id=chat_id, text=question_text,  reply_markup=inline_keyboard.create_answers_buttons(current_question))


@dp.callback_query_handler(text_startswith="answer")
async def check_answer(callback_query: types.CallbackQuery):
    user_answer = callback_query.data.split("%$%")[1]
    chat_id = callback_query.from_user.id
    current_question = QUESTIONS.get(chat_id)[0]
    right_answer = current_question["correct_answer"]
    message_text = ""
    if user_answer == right_answer:
        count = tools.user_collection.find_one(filter={"id": chat_id})[
            "count_correct_answers"]
        count += 1
        tools.user_collection.find_one_and_update(filter={"id": chat_id}, update={
                                                  "$set": {"count_correct_answers": count}})
        message_text = constants.RIGHT_ANSWER
    else:
        message_text = constants.WRONG_ANSWER
    await bot.send_message(chat_id=callback_query.from_user.id, text=message_text + right_answer, reply_markup=inline_keyboard.NEXT)


@dp.callback_query_handler(text_startswith="next")
async def next_answer(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    global QUESTIONS
    QUESTIONS.get(chat_id).pop(0)
    logging.info('quantity of user questions: %s', len(QUESTIONS.get(chat_id)))
    if len(QUESTIONS.get(chat_id)) != 0:
        global CURRENT_QUESTION
        current_question = QUESTIONS.get(chat_id)[0]
        question_text = current_question["question"]
        del current_question["question"]
        await bot.send_message(chat_id=chat_id, text=question_text,  reply_markup=inline_keyboard.create_answers_buttons(current_question))
    else:
        current_user = tools.user_collection.find_one(filter={"id": chat_id})
        user_name = current_user["user_name"]
        count_correct_answers = current_user["count_correct_answers"]
        number_of_questions = current_user["number_of_questions"]
        congrats_text = f"Congratulations 🥳 {user_name} you answered {count_correct_answers} of {number_of_questions} questions correctly 😱! \n Do you want to play again? Just click play 👇 And let's go!"
        await bot.send_message(chat_id=chat_id, text=congrats_text,  reply_markup=inline_keyboard.PLAY)


@dp.callback_query_handler(text_startswith="friend")
async def call_a_friend(callback_query: types.CallbackQuery):
    logging.info('somebody asked kanye west')
    quote = API.get_quote()
    await bot.send_photo(chat_id=callback_query.from_user.id, photo=constants.IMAGE_URL)
    await bot.send_message(chat_id=callback_query.from_user.id, text=f"Kanye: {quote}")

async def on_startup(dp: Dispatcher):
    await bot.set_webhook(WEBHOOK_URL)


async def on_shutdown(dp: Dispatcher):
    await bot.delete_webhook()


if __name__ == '__main__':
    start_webhook(
        dispatcher=dp,
        webhook_path=WEBHOOK_PATH,
        skip_updates=True,
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        host=WEBAPP_HOST,
        port=WEBAPP_PORT,
    )
