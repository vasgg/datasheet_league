MASTER_HEADER = ['Notes', 'Date sent', 'League', 'Bet Name', 'Worst Odds', 'Total Risk', 'Average weighted Odds', 'Win', 'Result', 'Net']
PLAYER_HEADER = ['Notes', 'Date sent', 'League', 'Bet Name', 'Risk', 'Odds', 'Win', 'Result', 'Net']

PLAYER_STATS = [
    ['Current Owe', 'Wins', 'Winrate', 'Avg Pos odds', 'Total Risked', 'ROI %', 'Net Since Start'],
    ['=SUM(Q4,Q6)', '=COUNTIF(H2:H545,"W")', '=L4/(L6+L4)*100', '=AVERAGE(FILTER(F:F,F:F>0))',
     '=SUM(E2:E567)', '=DIVIDE(O6,O4)*100', '=SUM(I2:I1182)'],
    ['Current Pending', 'Losses', 'Historical Payments', 'Avg Neg odds', 'Net Profit', 'Notes', 'Balance To Start'],
    ['=SUMIF(A:A, "Pending", E:E)', '=COUNTIF(H2:H545,"L")-COUNTIF(C2:C545,"Payment")',
     '=SUMIF(A2:A545, "Payment", E2:E545)', '=AVERAGE(FILTER(F:F,F:F<0))', '=SUM(K4,M6,ABS(Q6))', '', ''],
]

MASTER_STATS = [
    ['Current Owe', 'Wins', 'Winrate', 'Avg Pos odds', 'Total Risked', 'ROI %', 'Net Since Start'],
    ['=SUM(R4,R6)', '=COUNTIF(I2:I545,"W")', '=M4/(M6+M4)*100', '=AVERAGE(FILTER(G:G,G:G>0))',
     '=SUM(F2:F567)', '=DIVIDE(P6,P4)*100', '=SUM(J2:J1182)'],
    ['Current Pending', 'Losses', 'Historical Payments', 'Avg Neg odds', 'Net Profit', 'Notes', 'Balance To Start'],
    ['=SUMIF(A:A, "Pending", F:F)', '=COUNTIF(I2:I545,"L")-COUNTIF(C2:C545,"Payment")',
     '=SUMIF(A2:A545, "Payment", F2:F545)', '=AVERAGE(FILTER(G:G,G:G<0))', '=SUM(L4,N6,ABS(R6))', '', ''],
]
