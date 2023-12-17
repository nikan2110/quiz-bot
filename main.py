import logging
import inline_keyboard
import tools
import constants
import API
import os
import datetime as dt
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram import Bot, Dispatcher, types, executor
from aiogram.utils.executor import start_webhook
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext


# create state for conversation handler when receive user name
class Form(StatesGroup):
    name = State()


# credentials
API_TOKEN = tools.get_from_env("TELEGRAM_API_TOKEN")
# HEROKU_APP_NAME = tools.get_from_env("HEROKU_APP_NAME")
#
# # webhook settings
# WEBHOOK_HOST = f'https://{HEROKU_APP_NAME}.herokuapp.com'
# WEBHOOK_PATH = f'/webhook/{API_TOKEN}'
# WEBHOOK_URL = f'{WEBHOOK_HOST}{WEBHOOK_PATH}'
#
# # webserver settings
# WEBAPP_HOST = '0.0.0.0'
# WEBAPP_PORT = int(os.getenv('PORT'))

# configure logging
logging.basicConfig(format='%(asctime)s : %(message)s ', level=logging.INFO)

# initialize bot and dispatcher and DB
bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


# helper function to avoid code duplication
def create_answers_and_question(current_user):
    current_question = current_user['questions'][0]
    question_text = current_question["question"]
    del current_question[
        "question"]  # we don't need the question, because we don't need create button for it. Just need answers
    response = {
        "question_text": question_text,
        "current_question": current_question
    }
    return response


# command start
@dp.message_handler(commands='start')
async def send_welcome(message: types.Message):
    chat_id = message.from_user.id
    logging.info('start button pushed. received chat_id: %s', chat_id)
    await message.answer(text=constants.GREETING_TEXT, reply_markup=inline_keyboard.PLAY)


# play button
@dp.callback_query_handler(text='play')
async def register_user(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    current_user = tools.user_collection.find_one(filter={"id": chat_id})
    if current_user is None:
        tools.user_collection.insert_one({
            "id": chat_id, "user_name": "",
            "number_of_questions": 0,
            "difficulty": "",
            "count_correct_answers": 0,
            "category_id": ""})
        await Form.name.set()
        await bot.send_message(chat_id=chat_id, text=constants.TAKE_USER_NAME_TEXT)
    else:
        user_name = current_user["user_name"]
        logging.info('received user_name after play button: %s', user_name)
        tools.user_collection.update_one(filter={"id": chat_id}, update={
            "$set": {
                "count_correct_answers": 0,
                "last_game": dt.datetime.now(),
                "questions": ""
            }})
        await bot.send_message(chat_id=chat_id, text=f"Welcome back {user_name}. Do you want to continue?",
                               reply_markup=inline_keyboard.CONTINUE)


# cancel button
@dp.callback_query_handler(text='cancel')
async def cancel(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    tools.user_collection.update_one(filter={"id": chat_id}, update={
        "$set": {"questions": ""}})
    await bot.send_message(chat_id=callback_query.from_user.id, text=constants.GOODBYE_TEXT)


# save user name to database
@dp.message_handler(state=Form.name)
async def register(message: types.Message, state: FSMContext):
    async with state.proxy():
        user_name = message.text.strip()
        if user_name == '/start':
            await message.answer(text="Please, use another name")
            return
        chat_id = message.from_user.id
        tools.user_collection.update_one(filter={"id": chat_id}, update={
            "$set": {
                "user_name": user_name
            }})
        logging.info('received user_name after registration: %s', user_name)
        await state.finish()
        await message.answer(text=f"Hello, {user_name}! Nice to meet you! ")
        await message.answer(text=constants.NUMBER_OF_QUESTIONS_TEXT, reply_markup=inline_keyboard.NUMBER_OF_QUESTIONS)


# user already exist and want to continue the game
@dp.callback_query_handler(text_startswith="continue")
async def user_exist(callback_query: types.CallbackQuery):
    await bot.send_message(chat_id=callback_query.from_user.id, text=constants.NUMBER_OF_QUESTIONS_TEXT,
                           reply_markup=inline_keyboard.NUMBER_OF_QUESTIONS)


# choose number of questions
@dp.callback_query_handler(text_startswith="number")
async def questions(callback_query: types.CallbackQuery):
    number_of_questions = callback_query.data.split(":")[1]
    chat_id = callback_query.from_user.id
    logging.info('received number of questions: %s', number_of_questions)
    tools.user_collection.update_one(filter={"id": chat_id}, update={
        "$set": {
            "number_of_questions": number_of_questions
        }})
    await bot.send_message(chat_id=chat_id, text=constants.CATEGORY_TEXT, reply_markup=inline_keyboard.CATEGORIES)


# choose category
@dp.callback_query_handler(text_startswith="category")
async def categories(callback_query: types.CallbackQuery):
    category_id = callback_query.data.split(":")[1]
    chat_id = callback_query.from_user.id
    logging.info('received category id: %s', category_id)
    tools.user_collection.update_one(filter={"id": chat_id}, update={
        "$set": {
            "category_id": category_id
        }})
    await bot.send_message(chat_id=chat_id, text=constants.DIFFICULTY_TEXT, reply_markup=inline_keyboard.DIFFICULTIES)


# choose difficulty and send first question
@dp.callback_query_handler(text_startswith="difficulty")
async def difficulty_and_first_question(callback_query: types.CallbackQuery):
    difficulty = callback_query.data.split(":")[1]
    chat_id = callback_query.from_user.id
    logging.info('received difficulty: %s', difficulty)
    current_user = tools.user_collection.find_one_and_update(filter={"id": chat_id}, update={
        "$set": {
            "difficulty": difficulty
        }})
    amount = current_user["number_of_questions"]
    category = current_user["category_id"]
    list_of_questions = API.get_questions(amount, category, difficulty)
    tools.user_collection.update_one(filter={"id": chat_id}, update={
        "$set": {
            "questions": list_of_questions
        }})
    current_user = tools.user_collection.find_one(filter={"id": chat_id})
    logging.info('quantity of user questions: %s', len(current_user["questions"]))
    if len(current_user["questions"]) != 0:
        response = create_answers_and_question(current_user)
        await bot.send_message(chat_id=chat_id, text=response['question_text'],
                               reply_markup=inline_keyboard.create_answers_buttons(response['current_question']))
    else:
        await bot.send_message(chat_id=callback_query.from_user.id, text=constants.GREETING_TEXT,
                               reply_markup=inline_keyboard.PLAY)


# receive an answer from user and compare it with the right answer
@dp.callback_query_handler(text_startswith="answer")
async def check_answer(callback_query: types.CallbackQuery):
    user_answer = callback_query.data.split("%$%")[1]
    chat_id = callback_query.from_user.id
    current_user = tools.user_collection.find_one(filter={"id": chat_id})
    if len(current_user["questions"]) != 0:
        current_question = current_user['questions'][0]
        right_answer = current_question["correct_answer"]
        message_text = ""
        if user_answer == right_answer:
            count = current_user["count_correct_answers"]
            count += 1
            tools.user_collection.update_one(filter={"id": chat_id}, update={
                "$set": {
                    "count_correct_answers": count
                }})
            message_text = constants.RIGHT_ANSWER
        else:
            message_text = constants.WRONG_ANSWER
        await bot.send_message(chat_id=callback_query.from_user.id, text=message_text + right_answer,
                               reply_markup=inline_keyboard.NEXT)
    else:
        await bot.send_message(chat_id=callback_query.from_user.id, text=constants.GREETING_TEXT,
                               reply_markup=inline_keyboard.PLAY)


# get a next question
@dp.callback_query_handler(text_startswith="next")
async def next_question(callback_query: types.CallbackQuery):
    chat_id = callback_query.from_user.id
    current_user = tools.user_collection.find_one(filter={"id": chat_id})
    list_of_questions = current_user['questions']
    list_of_questions.pop(0)
    tools.user_collection.update_one(filter={"id": chat_id}, update={
        "$set": {"questions": list_of_questions}})
    current_user = tools.user_collection.find_one(filter={"id": chat_id})
    logging.info('quantity of user questions: %s', len(current_user['questions']))
    if len(current_user['questions']) != 0:
        response = create_answers_and_question(current_user)
        await bot.send_message(chat_id=chat_id, text=response['question_text'],
                               reply_markup=inline_keyboard.create_answers_buttons(response['current_question']))
    else:  # user answered on all questions
        user_name = current_user["user_name"]
        count_correct_answers = current_user["count_correct_answers"]
        number_of_questions = current_user["number_of_questions"]
        congrats_text = f"Congratulations 🥳 {user_name} you answered {count_correct_answers} of {number_of_questions} questions correctly 😱! \n Do you want to play again? Just click play 👇 And let's go!"
        await bot.send_message(chat_id=chat_id, text=congrats_text, reply_markup=inline_keyboard.PLAY)


@dp.callback_query_handler(text_startswith="friend")
async def call_a_friend(callback_query: types.CallbackQuery):
    logging.info('somebody asked kanye west')
    quote = API.get_quote()
    await bot.send_photo(chat_id=callback_query.from_user.id, photo=constants.IMAGE_URL)
    await bot.send_message(chat_id=callback_query.from_user.id, text=f"Kanye: {quote}")


# async def on_startup(dp: Dispatcher):
#     await bot.set_webhook(WEBHOOK_URL)
#
#
# async def on_shutdown(dp: Dispatcher):
#     await bot.delete_webhook()


if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
    # start_webhook(
    #     dispatcher=dp,
    #     webhook_path=WEBHOOK_PATH,
    #     skip_updates=True,
    #     on_startup=on_startup,
    #     on_shutdown=on_shutdown,
    #     host=WEBAPP_HOST,
    #     port=WEBAPP_PORT,
    # )
