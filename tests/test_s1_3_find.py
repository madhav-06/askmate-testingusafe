"""Ticket s1-3's official tests. They run on your pull request."""

from catalogue import load_catalogue
from search import find, meaning, words

PRODUCTS = load_catalogue()


def test_words_are_clean_and_sizes_are_joined():
    assert words("18 by 14 Basin?") == ["18x14", "basin"]


def test_a_customer_word_becomes_the_list_word():
    assert meaning("commode") == "toilet"


def test_a_name_finds_one_product():
    assert find("Do you have Glanza?", PRODUCTS) == ["OPC 186"]


def test_the_best_matches_win_cheapest_first():
    assert find("18 by 14 basin", PRODUCTS) == ["WBSN 277", "WBSN 278"]


def test_nothing_matching_gives_nothing():
    assert find("Do you sell tiles?", PRODUCTS) == []
