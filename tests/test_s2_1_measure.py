"""Task s2-1's official tests. They run on your pull request."""

from eval import is_right, run, scorecard

GLANZA = {"q": "Do you have Glanza?", "action": "answer", "products": ["OPC 186"]}


def test_a_right_reply_has_the_same_action_and_the_product():
    assert is_right({"action": "answer", "products": ["OPC 186"]}, GLANZA)
    assert not is_right({"action": "ask", "products": ["OPC 186", "OPC 109"]}, GLANZA)
    assert not is_right({"action": "answer", "products": ["OPC 109"]}, GLANZA)


def test_the_scorecard_counts_right_answers_honest_noes_and_confident_mistakes():
    results = [{"want": GLANZA, "reply": {"action": "answer", "products": ["OPC 109"]}, "right": False},
               {"want": {"q": "paint", "action": "refuse", "products": []}, "reply": {"action": "refuse", "products": []}, "right": True}]
    assert scorecard(results) == {"right_percent": 50, "honest_no_percent": 100, "confident_mistakes": 1}


def test_askmate_gets_most_test_questions_right():
    from catalogue import load_catalogue

    assert scorecard(run(products=load_catalogue()))["right_percent"] >= 80, "measured on the 35 products the test set is about"
