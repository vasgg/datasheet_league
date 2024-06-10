from calc.odds_convertor import convert_us_to_dec, convert_dec_to_us


def test_convertors():
    src = [-215, 110]
    dec_v = convert_us_to_dec(src)
    us_v = convert_dec_to_us(dec_v)
    assert src == us_v
