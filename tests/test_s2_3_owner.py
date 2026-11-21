"""Task s2-3's official tests. They run on your pull request."""

from owner import wants_bargain


def test_bargaining_goes_to_the_owner():
    for q in ("Can I get a discount?", "best price for 10 basins", "bulk order", "any offer?", "your last price?"):
        assert wants_bargain(q), q


def test_a_cheapest_question_is_a_product_question_not_bargaining():
    assert not wants_bargain("the cheapest wall hung toilet")
    assert not wants_bargain("Do you have Glanza?")
