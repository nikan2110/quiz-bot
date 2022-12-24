import requests
import constants
import logging
import html

# Configure logging
logging.basicConfig(level=logging.INFO)


# example - https://opentdb.com/api.php?amount=10&category=18&difficulty=easy&type=multiple
def get_questions(amount: int, category_id: int, difficulty: str):
    logging.info('received params for request: amount - %s, difficulty - %s, category_id - %s', amount, difficulty, category_id)
    parameters = {
        "amount": amount,
        "category": category_id,
        "difficulty": difficulty.split(" ")[0],
        "type": "multiple"
    }
    response = requests.get(
        constants.BASE_URL_QUIZ, params=parameters)
    response.raise_for_status()
    data = response.json()["results"]
    questions_list = []
    for questions_from_API in data:
        new_question = {}
        new_question["question"] = html.unescape(questions_from_API["question"])
        new_question["correct_answer"] = html.unescape(questions_from_API["correct_answer"])
        new_question["incorrect_answer_1"] = html.unescape(questions_from_API["incorrect_answers"][0])
        new_question["incorrect_answer_2"] = html.unescape(questions_from_API["incorrect_answers"][1])
        new_question["incorrect_answer_3"] = html.unescape(questions_from_API["incorrect_answers"][2])
        questions_list.append(new_question)
    return questions_list


def get_quote():
    response = requests.get(constants.BASE_URL_KANYE)
    response.raise_for_status()
    data = response.json()['quote']
    return data

