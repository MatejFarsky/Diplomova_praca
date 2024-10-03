import math
import time as tm
import numpy as np
import pandas as pd
from amplpy import AMPL, Environment, DataFrame

def round_dw(x, dec):
    return math.floor(x * 10**dec) / 10**dec

def load_data():
    df1 = pd.read_excel('Data_input.xlsx')
    return df1.loc[:,"price"], df1.loc[:,"buy_prev"], df1.loc[:,"sell_prev"]

def solve_battery(n, price, buy_prev, sell_prev, cap_0, cap_n, Lower_cap, Upper_cap, Upper_buy, Upper_sell, alpha, beta, c):
    ampl = AMPL(Environment('C:\\Users\\Matej\\AMPL'))
    ampl.read('bateria.mod')
    
    ampl.getParameter('n').setValues([n])
    ampl.getParameter('price').setValues(price)
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

def save_data(buy_opt, sell_opt, cap_opt):
    df1 = pd.read_excel('Data_input.xlsx')
    buy_prev = df1.loc[:,"buy_prev"].tolist()
    sell_prev = df1.loc[:,"sell_prev"].tolist()
    df2 = df1
    df2 = df2.drop(df2.columns[0], axis=1)
    df2.buy_prev = pd.Series(np.add(buy_opt, buy_prev))
    df2.sell_prev = pd.Series(np.add(sell_opt, sell_prev))
    df2.insert(len(df2.columns),'buy_opt', pd.Series(buy_opt))
    df2.insert(len(df2.columns), 'sell_opt', pd.Series(sell_opt))
    df2.insert(len(df2.columns), 'cap_opt', pd.Series(cap_opt))
    df2.to_excel('Data_output.xlsx')

def iteration(tm):
    start = tm.time()
    
    #Presnost
    dec = 2
    
    #Nacitanie dat
    price, buy_prev, sell_prev = load_data()
    
    #Definovanie parametrov
    alpha, beta = 0.92, 0.93
    vykon = 1
    cap_0 = 0.5   #pociatocna podmienka
    cap_n = 0.5   #koncova podmienka
    Lower_cap, Upper_cap = 0, 1
    Upper_sell, Upper_buy = round_dw(vykon / 4 * beta, dec), round_dw(vykon / 4, dec)
    c = 2       #max pocet cyklov
    n = len(price)
    
    #Solving
    cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val = solve_battery(n, price, buy_prev, sell_prev, cap_0, cap_n, Lower_cap, Upper_cap, Upper_buy, Upper_sell, alpha, beta, c)
    
    #ulozenie dat
    save_data(buy_opt, sell_opt, cap_opt)
    
    stop = tm.time()
    time = stop - start

    return cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, time

cap_opt, buy_cycles_opt, sell_cycles_opt, buy_opt, sell_opt, buy_or_sell_opt, opt_val, time = iteration(tm)

print("cap_opt: ", cap_opt)
print("buy_cycles_opt: ", buy_cycles_opt)
print("sell_cycles_opt: ", sell_cycles_opt)
print("buy_opt: ", buy_opt)
print("sell_opt: ", sell_opt)
print("buy_or_sell_opt: ", buy_or_sell_opt)
print("opt_val:", opt_val)
print("Seconds elapsed: ", time)
#Seconds elapsed:  0.6950726509094238
