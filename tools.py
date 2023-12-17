from os.path import join, dirname
from aiogram.types import InlineKeyboardButton
from dotenv import load_dotenv
from pymongo import MongoClient
import os
import constants
import random


def get_from_env(key):
    dotenv_path = join(dirname(__file__), '.env')
    load_dotenv(dotenv_path)
    return os.environ.get(key)


def get_categories_buttons():
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
    btn_number_of_questions_list = []
    for number in constants.number_of_questions:
        BTN_NUMBER_OF_QUESTIONS = InlineKeyboardButton(
            str(number), callback_data=f"number_of_questions + :{number}")
        btn_number_of_questions_list.append(BTN_NUMBER_OF_QUESTIONS)
    return btn_number_of_questions_list


def get_difficulties_buttons(InlineKeyboardMarkup):
    for difficulty in constants.difficulties:
        BTN_DIFFICULTY = InlineKeyboardButton(
            difficulty, callback_data=f"difficulty + :{difficulty}")
        InlineKeyboardMarkup.add(BTN_DIFFICULTY)
    return InlineKeyboardMarkup


def get_answers_buttons(question, InlineKeyboardMarkup):
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
