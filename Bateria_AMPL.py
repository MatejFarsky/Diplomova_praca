import math
import time
import numpy as np
import pandas as pd
from amplpy import AMPL, Environment, DataFrame

def round_dw(x, dec):
    return math.floor(x * 10**dec) / 10**dec

start = time.time()

#Presnost
dec = 2

#Nacitanie dat
df1 = pd.read_excel('Data_input.xlsx')
p = df1.loc[:,"p"]
b = df1.loc[:,"b"]
d = df1.loc[:,"d"]

#Definovanie parametrov
alpha, beta = 0.92, 0.93
vykon = 1
a_0 = 0.5   #pociatocna podmienka
a_n = 0.5   #koncova podmienka
L_x, U_x = 0, 1
U_v, U_u = round_dw(vykon / 4 * beta, dec), round_dw(vykon / (4 * alpha), dec)
c = 2       #max pocet cyklov
n = len(p)

#Solving
ampl = AMPL(Environment('C:\\Users\\Matej\\AMPL'))
ampl.read('bateria.mod')

ampl.getParameter('n').setValues([n])
ampl.getParameter('p').setValues(p)
ampl.getParameter('b').setValues(b)
ampl.getParameter('d').setValues(d)
ampl.getParameter('a_0').setValues([a_0])
ampl.getParameter('a_n').setValues([a_n])
ampl.getParameter('L_x').setValues([L_x])
ampl.getParameter('U_x').setValues([U_x])
ampl.getParameter('U_u').setValues([U_u])
ampl.getParameter('U_v').setValues([U_v])
ampl.getParameter('alpha').setValues([alpha])
ampl.getParameter('beta').setValues([beta])
ampl.getParameter('c').setValues([c])

ampl.solve()

vari = ampl.getVariable('x').getValues().toList()
x_opt = [vari[t][1] for t in range(len(vari))]
vari = ampl.getVariable('y1').getValues().toList()
y1_opt = [vari[t][1] for t in range(len(vari))]
vari = ampl.getVariable('y2').getValues().toList()
y2_opt = [vari[t][1] for t in range(len(vari))]

vari = ampl.getVariable('u').getValues().toList()
u_opt = [vari[t][1] for t in range(len(vari))]
vari = ampl.getVariable('v').getValues().toList()
v_opt = [vari[t][1] for t in range(len(vari))]
vari = ampl.getVariable('w').getValues().toList()
w_opt = [vari[t][1] for t in range(len(vari))]

opt_val = ampl.get_value('obj_fun')

print("x_opt: ", x_opt)
print("y1_opt: ", y1_opt)
print("y2_opt: ", y2_opt)
print("u_opt: ", u_opt)
print("v_opt: ", v_opt)
print("w_opt: ", w_opt)
print("opt_val:", opt_val)

b = df1.loc[:,"b"].tolist()
d = df1.loc[:,"d"].tolist()

#ulozenie dat
df2 = df1
df2 = df2.drop(df2.columns[0], axis=1)
df2.b = pd.Series(np.add(u_opt, b))
df2.d = pd.Series(np.add(v_opt, d))
df2.to_excel('Data_output.xlsx')


stop = time.time()
print("Seconds elapsed: ",stop - start)
#Seconds elapsed:  89.15838241577148
