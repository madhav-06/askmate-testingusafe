"""Ticket s1-2's official tests. They run on your pull request."""

from catalogue import clean_code, clean_price, load_catalogue


def test_every_way_of_writing_a_price_gives_the_same_number():
    assert [clean_price(p) for p in ["₹ 11,500", "Rs. 11500/-", "11500", "₹11,500.00", "Rs 11500"]] == [11500] * 5


def test_every_way_of_writing_a_code_gives_the_same_code():
    assert {clean_code(c) for c in ["opc-180", "OPC180", " OPC 180 ", "Opc 180"]} == {"OPC 180"}


def test_the_list_has_35_products_each_once():
    codes = [p["code"] for p in load_catalogue()]
    assert len(codes) == 35 and len(set(codes)) == 35 and all(codes)


def test_no_product_is_free():
    assert all(p["price"] > 0 for p in load_catalogue())
