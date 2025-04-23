option solver gurobi;
option show_stats 1;
option gurobi_options 'outlev=0 mipgap=0.01 timelim=1000 multiobj=1' ;
option presolve_eps 1e-11;

#params
param n; #pocet casov
param m; #pocet minut predikcie
param price_bid{i in 0 .. m-1, t in 0 .. n-1}; #ceny predaja
param price_ask{i in 0 .. m-1, t in 0 .. n-1}; #ceny nakupu
param restrict_buy{i in 0 .. m-1, t in 0 .. n-1}; #obmedzenie obchodovatelnosti
param restrict_sell{i in 0 .. m-1, t in 0 .. n-1}; #obmedzenie obchodovatelnosti
param cap_0; #pociatocna kapacita
param cap_n; #koncova kapacita
param buy_prev_0t{t in 0 .. n-1}; #aktualna predosle nakupovana kapacita
param sell_prev_0t{t in 0 .. n-1}; #aktualna predosle predavana kapacita
param Lower_cap; #spodne ohranicenie kapacity
param Upper_cap; #horne ohranicenie kapacity
param Upper_buy; #ohranicenie nakupovanej kapacity
param Upper_sell; #ohranicenie predavanej kapacity
param alpha; #koeficient ucinnosti nabijania
param beta; #koeficient ucinnosti vybijania
param c; #ohranicenie poctu cyklov

var buy_or_sell{i in 0 .. m-1, t in 0 .. n-1} binary;
var sell{i in 0 .. m-1, t in 0 .. n-1};
var buy{i in 0 .. m-1, t in 0 .. n-1};

var cap{i in 0 .. m-1, t in 0 .. n} <= Upper_cap, >= Lower_cap; #kapacita baterie
var buy_cycles{i in 0 .. m-1, t in 0 .. n} <= c * (Upper_cap - Lower_cap), >= 0; #celkova nakupovana kapacita
var sell_cycles{i in 0 .. m-1, t in 0 .. n} <= c * (Upper_cap - Lower_cap), >= 0; #celkova predavana kapacita
var buy_prev{i in 0 .. m, t in 0 .. n-1}; #predosle nakupovana kapacita
var sell_prev{i in 0 .. m, t in 0 .. n-1}; #predosle predavana kapacita

s.t. constraint1{i in 0 .. m-1, t in 0 .. n-1}: sell[i,t] <= ((1-buy_or_sell[i,t]) * Upper_sell - sell_prev[i,t]) * restrict_sell[i,t];
s.t. constraint2{i in 0 .. m-1, t in 0 .. n-1}: sell[i,t] >= - sell_prev[i,t] * restrict_sell[i,t];

s.t. constraint3{i in 0 .. m-1, t in 0 .. n-1}: buy[i,t] <= (buy_or_sell[i,t] * Upper_buy - buy_prev[i,t]) * restrict_buy[i,t];
s.t. constraint4{i in 0 .. m-1, t in 0 .. n-1}: buy[i,t] >= - buy_prev[i,t] * restrict_buy[i,t]; 

s.t. constraint5{i in 0 .. m-1}: cap[i,0] = cap_0;
s.t. constraint6{i in 0 .. m-1, t in 0 .. n-1}: cap[i,t+1] = cap[i,t] + alpha * (buy[i,t] + buy_prev[i,t]) - (sell[i,t] + sell_prev[i,t]) / beta;
s.t. constraint7: cap[m-1,n] = cap_n;

s.t. constraint8{i in 0 .. m-1}: buy_cycles[i,0] = 0;
s.t. constraint9{i in 0 .. m-1, t in 0 .. n-1}: buy_cycles[i,t+1] = buy_cycles[i,t] + alpha * (buy[i,t] + buy_prev[i,t]);

s.t. constraint10{i in 0 .. m-1}: sell_cycles[i,0] = 0;
s.t. constraint11{i in 0 .. m-1, t in 0 .. n-1}: sell_cycles[i,t+1] = sell_cycles[i,t] + (sell[i,t] + sell_prev[i,t]) / beta;

s.t. constraint12{t in 0 .. n-1}: buy_prev[0,t] = buy_prev_0t[t];
s.t. constraint13{i in 0 .. m-1, t in 0 .. n-1}: buy_prev[i+1,t] = buy_prev[i,t] + buy[i,t];

s.t. constraint14{t in 0 .. n-1}: sell_prev[0,t] = sell_prev_0t[t];
s.t. constraint15{i in 0 .. m-1, t in 0 .. n-1}: sell_prev[i+1,t] = sell_prev[i,t] + sell[i,t];

maximize obj_fun: sum{i in 0 .. m-1, t in 0 .. n-1} (price_bid[i,t] * sell[i,t] - price_ask[i,t] * buy[i,t]);
