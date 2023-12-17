from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import tools

BTN_PLAY = InlineKeyboardButton('Play 🥳', callback_data='play')
BTN_CANCEL = InlineKeyboardButton('Cancel ❌', callback_data='cancel')
PLAY = InlineKeyboardMarkup().add(BTN_PLAY, BTN_CANCEL)

BTN_CALL = InlineKeyboardButton('Call a friend ☎', callback_data='friend')
CALL_A_FRIEND = InlineKeyboardMarkup().add(BTN_CALL)

BTN_CONTINUE = InlineKeyboardButton('Continue ', callback_data='continue')
CONTINUE = InlineKeyboardMarkup().add(BTN_CONTINUE)

btn_number_of_questions_list = tools.get_number_of_questions_buttons()
NUMBER_OF_QUESTIONS = InlineKeyboardMarkup().add(*btn_number_of_questions_list)

btn_categories_list = tools.get_categories_buttons()
CATEGORIES = InlineKeyboardMarkup().add(*btn_categories_list)

DIFFICULTIES = InlineKeyboardMarkup()
DIFFICULTIES = tools.get_difficulties_buttons(DIFFICULTIES)


def create_answers_buttons(question):
    """
    Creates an inline keyboard with answer options for a given question.

    This function generates a set of buttons for each answer option in the question,
    and adds special buttons for additional functionalities like 'call a friend' or 'cancel'.

    Args:
    question (dict): A dictionary containing the question and its answer options.

    Returns:
    InlineKeyboardMarkup: An object representing an inline keyboard with answer buttons.
    """
    ANSWERS = InlineKeyboardMarkup()
    ANSWERS = tools.get_answers_buttons(question, ANSWERS)
    return ANSWERS.add(BTN_CALL, BTN_CANCEL)


BTN_NEXT = InlineKeyboardButton('Next ➡', callback_data='next')
NEXT = InlineKeyboardMarkup().add(BTN_NEXT)
