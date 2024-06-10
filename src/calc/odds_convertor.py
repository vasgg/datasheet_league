def convert_us_to_dec(odds: list[int]) -> list[float]:
    new_odds = [-100 / x + 1 if x <= -100 else x / 100 + 1 for x in odds]
    new_odds = [round(x, 4) for x in new_odds]
    return new_odds


def convert_dec_to_us(odds: list[float]) -> list[int]:
    new_odds = [(x - 1) * 100 if x >= 2 else -100 / (x - 1) for x in odds]
    new_odds = [round(x) for x in new_odds]
    return new_odds


