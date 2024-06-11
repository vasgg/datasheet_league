import pytest

from calc.odds_convertor import convert_us_to_dec, convert_dec_to_us


def test_convertors():

    def hobbit(v):
        dec_v = convert_us_to_dec(v)
        assert pytest.approx(v, 0.1) == convert_dec_to_us(dec_v)

    for i in range(-1000, -100):
        hobbit(i)

    for i in range(100, 1000):
        hobbit(i)
