option solver gurobi;

#params
param n; #pocet casov
param p{t in 0 .. n-1}; #ceny
param b{t in 0 .. n-1}; #predosle nakupovana kapacita
param d{t in 0 .. n-1}; #predosle predavana kapacita
param a_0; #pociatocna kapacita
param a_n; #koncova kapacita
param L_x; #spodne ohranicenie kapacity
param U_x; #horne ohranicenie kapacity
param U_u; #ohranicenie nakupovanej kapacity
param U_v; #ohranicenie predavanej kapacity
param alpha; #koeficient ucinnosti nabijania
param beta; #koeficient ucinnosti vybijania
param c; #ohranicenie poctu cyklov

var w{t in 0 .. n-1} binary;
var v{t in 0 .. n-1};

s.t. constraint1{t in 0 .. n-1}: v[t] <= (1-w[t]) * U_v - d[t];
s.t. constraint2{t in 0 .. n-1}: v[t] >= - d[t];

var u{t in 0 .. n-1};

s.t. constraint3{t in 0 .. n-1}: u[t] <= w[t] * U_u - b[t];
s.t. constraint4{t in 0 .. n-1}: u[t] >= - b[t]; 

var x{t in 0 .. n} <= U_x, >= L_x;

s.t. constraint5: x[0] = a_0;
s.t. constraint6{t in 0 .. n-1}: x[t+1] = x[t] + alpha * (u[t] + b[t]) - (v[t] + d[t]) / beta;
s.t. constraint7: x[n] = a_n;

var y1{t in 0 .. n} <= c * (U_x - L_x), >= 0;

s.t. constraint8: y1[0] = 0;
s.t. constraint9{t in 0 .. n-1}: y1[t+1] = y1[t] + alpha * (u[t] + b[t]);

var y2{t in 0 .. n} <= c * (U_x - L_x), >= 0;

s.t. constraint10: y2[0] = 0;
s.t. constraint11{t in 0 .. n-1}: y2[t+1] = y2[t] + (v[t] + d[t]) / beta;

maximize obj_fun: sum{t in 0 .. n-1} p[t] * (v[t] - u[t]);
