import requests
import constants
import logging
import html

# Configure logging
logging.basicConfig(level=logging.INFO)


# example - https://opentdb.com/api.php?amount=10&category=18&difficulty=easy&type=multiple
def get_questions(amount: int, category_id: int, difficulty: str):
    """
    Fetches a list of questions from an external API based on specified parameters.

    Args:
    amount (int): The number of questions to fetch.
    category_id (int): The identifier for the category of questions.
    difficulty (str): The difficulty level of the questions (e.g., "easy", "medium", "hard").

    Returns:
    list: A list of dictionaries, each representing a question and its associated answers.
    """
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
    """
    Fetches a random quote from an external API.

    Returns:
    str: A string containing the quote.
    """
    response = requests.get(constants.BASE_URL_KANYE)
    response.raise_for_status()
    data = response.json()['quote']
    return data

