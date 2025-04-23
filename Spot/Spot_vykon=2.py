import math
import time as tm
import pandas as pd
from amplpy import AMPL, Environment


def round_dw(x, dec):
    return math.floor(x * 10**dec) / 10**dec

def solve_battery_spot(n, price_bid, price_ask, buy_prev, sell_prev, cap_0, cap_n, Lower_cap, Upper_cap, Upper_buy, Upper_sell, alpha, beta, c):
    ampl = AMPL(Environment('C:\\Users\\Matej\\AMPL'))
    ampl.read('bateria_spot.mod')

    ampl.getParameter('n').setValues([n])
    ampl.getParameter('price_bid').setValues(price_bid)
    ampl.getParameter('price_ask').setValues(price_ask)
    ampl.getParameter('buy_prev').setValues(buy_prev)
    ampl.getParameter('sell_prev').setValues(sell_prev)
    ampl.getParameter('cap_0').setValues([cap_0])
    ampl.getParameter('cap_n').setValues([cap_n])
    ampl.getParameter('Lower_cap').setValues([Lower_cap])
    ampl.getParameter('Upper_cap').setValues([Upper_cap])
    ampl.getParameter('Upper_buy').setValues([Upper_buy])
    ampl.getParameter('Upper_sell').setValues([Upper_sell])
    ampl.getParameter('alpha').setValues([alpha])
    ampl.getParameter('beta').setValues([beta])
    ampl.getParameter('c').setValues([c])

    ampl.solve()

    vari = ampl.getVariable('cap').getValues().toList()
    cap_opt = [vari[t][1] for t in range(len(vari))]
    vari = ampl.getVariable('buy_cycles').getValues().toList()
    buy_cycles_opt = [vari[t][1] for t in range(len(vari))]
    vari = ampl.getVariable('sell_cycles').getValues().toList()
    sell_cycles_opt = [vari[t][1] for t in range(len(vari))]

    vari = ampl.getVariable('buy').getValues().toList()
    buy_opt = [vari[t][1] for t in range(len(vari))]
    vari = ampl.getVariable('sell').getValues().toList()
    sell_opt = [vari[t][1] for t in range(len(vari))]
    vari = ampl.getVariable('buy_or_sell').getValues().toList()
    buy_or_sell_opt = [vari[t][1] for t in range(len(vari))]

    opt_val = ampl.get_value('obj_fun')

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val

def iteration_spot(tm, df1):
    start = tm.time()

    # Presnost
    dec = 2

    # Nacitanie dat
    price_bid, price_ask, buy_prev, sell_prev = df1.loc[:, "price_bid"], df1.loc[:, "price_ask"], df1.loc[:,"buy_prev"], df1.loc[:,"sell_prev"]

    # Definovanie parametrov
    alpha, beta = 0.92, 0.93
    vykon = 2
    cap_0 = 0.5  # pociatocna podmienka
    cap_n = 0.5  # koncova podmienka
    Lower_cap, Upper_cap = 0, 1
    Upper_sell, Upper_buy = round_dw(vykon * beta, dec), round_dw(vykon, dec)
    c = 2  # max pocet cyklov
    n = len(price_bid)

    # Solving
    cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val = solve_battery_spot(n, price_bid,price_ask,buy_prev,sell_prev,cap_0, cap_n,Lower_cap,Upper_cap,Upper_buy,Upper_sell,alpha, beta,c)

    # ulozenie dat
    save_data(buy_opt, sell_opt)

    stop = tm.time()
    time = stop - start

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, time

def save_data(buy_opt, sell_opt):
    df2 = pd.read_excel('Data_input.xlsx')
    df2 = df2.drop(df1.columns[0], axis=1)
    for i in range(len(buy_opt)):
        for j in range(4):
            df2.buy_prev[i*4+j] = pd.Series(buy_opt)[i]/4
            df2.sell_prev[i*4+j] = pd.Series(sell_opt)[i]/4
    df2.to_excel('Data_input.xlsx')

#main
df1 = pd.read_excel('Data_input_spot.xlsx')
cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, time = iteration_spot(tm,df1)
print(opt_val)


