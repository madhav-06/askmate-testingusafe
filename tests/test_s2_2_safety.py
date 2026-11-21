"""Task s2-2's official tests. They run on your pull request."""

from safety import is_safe, prices_in

FACTS = [{"code": "OPC 186", "name": "Glanza", "price": "₹12,400"}]


def test_every_way_of_writing_a_price_is_found():
    assert prices_in("₹12,400 or Rs 9,900 or Rs.1250") == [12400, 9900, 1250]
    assert prices_in("no price here") == []


def test_a_made_up_price_or_product_is_not_safe():
    assert is_safe("We have the Glanza (OPC 186) for ₹12,400.", FACTS)
    assert not is_safe("The Glanza is ₹9,999 today.", FACTS)
    assert not is_safe("Try the Glanza Gold (OPC 999).", FACTS)
