from calc.odds_convertor import convert_us_to_dec, convert_dec_to_us


def average_weighted_odds(bets) -> float:
    summ = 0
    total_risk = 0

    for bet in bets:
        summ += convert_us_to_dec(bet.odds) * bet.risk_amount
        total_risk += bet.risk_amount
    average_weighted_odds_res = summ / total_risk if total_risk != 0 else 0
    return convert_dec_to_us(average_weighted_odds_res)
