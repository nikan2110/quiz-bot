import requests
import constants
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)


# https://opentdb.com/api.php?amount=10&category=18&difficulty=easy&type=multiple
def get_questions(amount: int, category_id: int, difficulty: str):
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
    for question_from_API in data:
        new_question = {}
        new_question["question"] = question_from_API["question"].replace("&quot;", "''").replace("&#039;", "'").replace("&amp;", "and")
        new_question["correct_answer"] = question_from_API["correct_answer"].replace("&quot;", "''").replace("&#039;", "'").replace("&amp;", "and")
        new_question["incorrect_answer_1"] = question_from_API["incorrect_answers"][0].replace("&quot;", "''").replace("&#039;", "'").replace("&amp;", "and")
        new_question["incorrect_answer_2"] = question_from_API["incorrect_answers"][1].replace("&quot;", "''").replace("&#039;", "'").replace("&amp;", "and")
        new_question["incorrect_answer_3"] = question_from_API["incorrect_answers"][2].replace("&quot;", "''").replace("&#039;", "'").replace("&amp;", "and")
        questions_list.append(new_question)
    return questions_list


def get_quote():
    response = requests.get(constants.BASE_URL_KANYE)
    response.raise_for_status()
    data = response.json()['quote']
    return data

