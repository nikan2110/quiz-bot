from os.path import join, dirname
from aiogram.types import InlineKeyboardButton
from dotenv import load_dotenv
from pymongo import MongoClient
import os
import constants
import random


def get_from_env(key):
    """
    Retrieves a value from the environment variables based on the given key.

    Args:
    key (str): The key for the environment variable.

    Returns:
    str: The value of the environment variable corresponding to the provided key.
    """
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)


def get_categories_buttons():
    """
    Generates a list of InlineKeyboardButtons for different categories.

    Each button is associated with a category from the database. The buttons are used
    in a Telegram bot to allow users to select a category.

    Returns:
    list: A list of InlineKeyboardButton objects, each representing a category.
    """
    btn_categories_list = []
    collection_name = db["Categories_English"]
    for category in collection_name.find():
        category_id = category["id"]
        category_name = category["name"]
        BTN_CATEGORY = InlineKeyboardButton(
            category_name, callback_data=f"category_number + :{category_id}")
        btn_categories_list.append(BTN_CATEGORY)
    return btn_categories_list


def get_number_of_questions_buttons():
    """
    Creates a list of InlineKeyboardButtons for selecting the number of questions.

    The buttons are used in a Telegram bot to allow users to choose how many questions
    they want to answer in a quiz.

    Returns:
    list: A list of InlineKeyboardButton objects for different question quantities.
    """
    btn_number_of_questions_list = []
    for number in constants.number_of_questions:
        BTN_NUMBER_OF_QUESTIONS = InlineKeyboardButton(
            str(number), callback_data=f"number_of_questions + :{number}")
        btn_number_of_questions_list.append(BTN_NUMBER_OF_QUESTIONS)
    return btn_number_of_questions_list


def get_difficulties_buttons(InlineKeyboardMarkup):
    """
     Adds difficulty level buttons to an InlineKeyboardMarkup object.

     Args:
     InlineKeyboardMarkup (InlineKeyboardMarkup): The markup to which the difficulty buttons will be added.

     Returns:
     InlineKeyboardMarkup: The updated InlineKeyboardMarkup object with difficulty buttons.
     """
    for difficulty in constants.difficulties:
        BTN_DIFFICULTY = InlineKeyboardButton(
            difficulty, callback_data=f"difficulty + :{difficulty}")
        InlineKeyboardMarkup.add(BTN_DIFFICULTY)
    return InlineKeyboardMarkup


def get_answers_buttons(question, InlineKeyboardMarkup):
    """
    Adds answer option buttons to an InlineKeyboardMarkup object for a given question.

    Args:
    question (dict): A dictionary containing the question and its answer options.
    InlineKeyboardMarkup (InlineKeyboardMarkup): The markup to which the answer buttons will be added.

    Returns:
    InlineKeyboardMarkup: The updated InlineKeyboardMarkup object with answer option buttons.
    """
    answers = list(question.values())
    random.shuffle(answers)
    for answer in answers:
        BTN_ANSWER = InlineKeyboardButton(
            answer, callback_data=f"answer + %$%{answer}")
        InlineKeyboardMarkup.add(BTN_ANSWER)
    return InlineKeyboardMarkup


# initialize data base
CONNECTION_STRING = get_from_env("MONGO_CONNECTION")  # credentials from mongo db atlas
client = MongoClient(CONNECTION_STRING)
db = client['QuizBot']  # choose database, in my case 'QuizBot'
user_collection = db["Users"]  # choose collection, in my case 'Users'
