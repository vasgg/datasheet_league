def convert_us_to_dec(x: int) -> float:
    new_odds = -100 / x + 1 if x <= -100 else x / 100 + 1
    return round(new_odds, 4)


def convert_dec_to_us(x: float) -> float:
    new_odds = (x - 1) * 100 if x >= 2 else -100 / (x - 1)
    return round(new_odds, 2)
