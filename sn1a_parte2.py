# -*- coding: utf-8 -*-
"""SN1a-Parte2

Automatically generated by Colaboratory.

Original file is located at
    https://colab.research.google.com/drive/1o0xoM_HgD5r--WIz_VTZlp2J3MtSD_KV

# Supernovas Ia - Parte 2

**CUIDADO!** Rodar o código inteiro demora um bom tempo! Cheque primeiro os resultados já salvos, e depois coloque tudo pra rodar. Pode demorar algumas horas.

---

## Baixando os dados observacionais

Para o cálculo do $\chi^2$ é necessário comparar os valores calculados com valores observados. Para isso, usaremos observações de módulos de distâncias de Supernovas do tipo 1a.
"""

import pandas as pd
import io
import requests
# Site dos dados (moodle)
url="https://edisciplinas.usp.br/pluginfile.php/5306663/mod_resource/content/1/SNeIa.txt"
s=requests.get(url).content
# Passando os dados para um dataframe
dados = pd.read_csv(io.StringIO(s.decode('utf-8')), sep=' ',names=['z', 'mu', 'sigmamu'])
# Checando se estão ok
dados

"""

---



## Cálculo do módulo da distância

Como na atividade anterior nós criamos uma função que calculasse o valor do módulo da distância e mostramos que essa função funciona bem, podemos reutilizá-la para essa atividade. O código é praticamente igual, com uma única mudança no final onde não retornamos mais o valor da distância de luminosidade, somente o valor de $\mu$."""

from scipy.integrate import quad
from math import sqrt
import numpy as np

#definindo H0 como variavel global
global H0, c
H0 = 70 #km/s/Mpc
c = 299792.458 #km/s

def calc_mu(z, omM, omEE, w):

  # calculo do omegaK
  omegaK = 1 - omM - omEE  

  # definimos a funcao 1/E(z)
  def E(zz):
    return 1/(sqrt(omM*(1+zz)**3 + omEE*(1+zz)**(3*(1+w)) + omegaK*(1+zz)**2))
  # distancia de Hubble
  dH = c/H0
  # distancia comovel
  dC = dH*quad(E, 0, z)[0]

  # para calcular a distancia comovel transversa devemos analisar omegaK
  if omegaK > 0:
    dM = dH/sqrt(omegaK)*np.sinh(sqrt(omegaK)*dC/dH)
  elif omegaK == 0:
    dM = dC
  elif omegaK < 0:
    dM = dH/sqrt(abs(omegaK))*np.sin(sqrt(abs(omegaK))*dC/dH)

  # podemos calcular a distancia de luminosidade finalmente
  dL = (1+z)*dM

  # o modulo de distancias em Mpc
  mu = 5*np.log10(dL) + 25

  return mu

"""

---

## Funções auxiliares e MCMC

Para essa atividade realizaremos contas parecidas diversas vezes. Por isso, definimos algumas funções auxiliares que nos pouparão muito tempo e linhas de códigos pela frente. Essas funções fazem exatamente o que o nome sugere."""

# importando algumas funcoes de fora
from statistics import stdev, median

# calcula o chi2
def chi2(dados, omM, omEE, w):
  chi2=0
  for index, row in dados.iterrows():
    chi2 += (row[1] - calc_mu(row[0], omM, omEE, w))**2/row[2]**2
  return chi2


# mostra para o usuario quanto tempo falta para o codigo terminar de rodar
from IPython.display import clear_output
import time

def time_left(iter, itermax, timenow, timebefore):
    clear_output(wait=True)
    print(f'Calculando a iteração {iter}/{itermax}')
    diftime = (timenow-timebefore)/10
    print('Expectativa de tempo p/ terminar: ', end =" "),
    print(f'{int((itermax-iter)*diftime/3600)}h ', end =" "),
    print(f'{int((itermax-iter)*diftime/60)}m ', end =" "),
    print(f'{int((itermax-iter)*diftime%60)}s', end =" ")
    if iter==itermax:
      clear_output(wait=True)
      print(f'Acabaram as {itermax} iterações!')
    return

"""No caso do MCMC e dos plots isso vai variar um pouco conforme a tarefa. Por isso, é possível ver algumas condições *if's* no meio do código."""

# calcula uma simulacao por MCMC
# o codigo varia dependendo de qual tarefa estamos fazendo
import random

def MCMC(tarefa, dados, omEE_inicial, omM_inicial, w_incial, itermax, sigma):
  # valores iniciais
  omEE, omM, w = [omEE_inicial], [omM_inicial], [w_inicial]
  chi2_vec = [chi2(dados, omM[0], omEE[0], w[0])]
  if tarefa=='c':
    chi2_vec[0] += ((1-omM[0]-omEE[0])+0.06)**2/0.05**2
  
  timebefore = time.time()

  # iniciando a simulacao
  for iter in range(1,itermax+1):

    # mostrando quantas iteracoes e tempo faltam
    if iter%10 == 0:
      timenow = time.time()
      time_left(iter,itermax,timenow,timebefore)
      timebefore = time.time()

    # definindo os valores atuais
    w_at = w[iter-1]
    omEE_at = omEE[iter-1]
    omM_at = omM[iter-1]
    if tarefa == 'a':
      omM_at = 1 - omEE_at

    # calculando os valores propostos de omegaEE e omegaM
    omEE_prop = random.gauss(omEE_at, sigma)
    omM_prop = random.gauss(omM_at, sigma)
    w_prop = w_at
    if tarefa=='a':
      omM_prop = 1 - omEE_prop
    elif tarefa=='d':
      omEE_prop = 1-omM_prop
      w_prop = random.gauss(w_at, sigma)

    # checando se omegaEE e omegaM estão sempre no intervalo 0,1
    while ((omEE_prop > 1 or omEE_prop < 0) or (omM_prop > 1 or omM_prop < 0)):
      omEE_prop = random.gauss(omEE_at, sigma)
      omM_prop = random.gauss(omM_at, sigma)
      if tarefa=='a':
        omM_prop = 1 - omEE_prop
      elif tarefa=='d':
        omEE_prop = 1-omM_prop

    # calculando o número r
    r = random.random() 

    # checando se aceitamos ou não o valor proposto baseado no chi2
    chi2_prop = chi2(dados, omM_prop, omEE_prop, w_prop)
    if tarefa=='c':
      chi2_prop += ((1-omM_prop-omEE_prop)+0.06)**2/0.05**2
    chi2_at = chi2_vec[iter-1]

    # salvando os novos valores propostos
    if r < np.exp(- chi2_prop/2 + chi2_at/2):
        omEE.append(omEE_prop)
        omM.append(omM_prop)
        w.append(w_prop)
        chi2_vec.append(chi2_prop)
    else:
        omEE.append(omEE_at)
        omM.append(omM_at)
        w.append(w_at)
        chi2_vec.append(chi2_at)
  
  # removendo os primeiros elementos pelo burn-in
  omEE = omEE[100:]
  omM = omM[100:]
  w = w[100:]
  chi2_vec = chi2_vec[100:]

  # depois de fazer a simulacao retorna todos os valores calculados
  return omEE, omM, w, chi2_vec

"""Para o plot decidi deixar a tarefa A sem função. Como"""

# funcao para plotar os resultados
import matplotlib.pyplot as plt
from scipy.stats import gaussian_kde
from scipy.interpolate import Rbf

def plotar(x,y, nameX, nameY, title):
  x = np.array(x + [min(x),max(x), min(x), max(x)])
  y = np.array(y + [min(y), max(y), max(y), min(y)])

  # Calculate the point density
  xy = np.vstack([x,y])
  z = 10*gaussian_kde(xy)(xy)

  # Sort the points by density, so that the densest points are plotted last
  idx = z.argsort()
  x, y, z = x[idx], y[idx], z[idx]
  # z = [x**2 for x in z]

  fig, ax = plt.subplots(figsize=(10,10))
  plt.tricontourf(x, y, z, 10, cmap='viridis')
  plt.colorbar(orientation="horizontal", pad=0.2)
  ax.scatter(median(x), median(y), c='red', s=30, edgecolors='k', label='Mediana')


  plt.xlabel(nameX, fontsize=20)
  plt.ylabel(nameY, fontsize=20)
  plt.title(title, fontsize=20)
  plt.legend(fontsize=20)
  plt.show()

# calculando as incertezas de cada parametro
from tabulate import tabulate

def incertezas(x,y,itermax, xname, yname):
    
  n_obj = itermax+1-100

  # numero de objetos que serao selecionados
  nsigma1 = int(0.628*itermax)
  nsigma2 = int(0.955*itermax)
  nsigma3 = int(0.997*itermax)

  #distancia ate mediana (norma L2)
  aux1 = [i-median(x) for i in x]
  aux2 = [j-median(y) for j in y]
  aux1 = [i**2 for i in aux1]
  aux2 = [j**2 for j in aux2]
  aux = [i+j for i,j in zip(aux1,aux2)]
  distance = [sqrt(k) for k in aux]

  df = {'x': x, 'y': y, 'dist': distance}
  df = pd.DataFrame(df)
  # arrumando valores em ordem crescente de distancia
  dfsorted = df.sort_values('dist')
  df1 = dfsorted.head(nsigma1)
  sigma1xp = abs(df1.max()['x'] - median(x))
  sigma1xn = abs(df1.min()['x'] - median(x))
  sigma1yp = abs(df1.max()['y'] - median(y))
  sigma1yn = abs(df1.min()['y'] - median(y))
  df2 = dfsorted.head(nsigma2)
  sigma2xp = abs(df2.max()['x'] - median(x))
  sigma2xn = abs(df2.min()['x'] - median(x))
  sigma2yp = abs(df2.max()['y'] - median(y))
  sigma2yn = abs(df2.min()['y'] - median(y))
  df3 = dfsorted.head(nsigma3)
  sigma3xp = abs(df3.max()['x'] - median(x))
  sigma3xn = abs(df3.min()['x'] - median(x))
  sigma3yp = abs(df3.max()['y'] - median(y))
  sigma3yn = abs(df3.min()['y'] - median(y))

  dic = {'sigmas':[1,2,3], 
         'x+':[sigma1xp, sigma2xp, sigma3xp],
         'x-':[sigma1xn, sigma2xn, sigma3xn], 
         'y+':[sigma1yp, sigma2yp, sigma3yp],
         'y-':[sigma1yn, sigma2yn, sigma3yn]}

  print(tabulate(dic, 
                 headers=['sigmas',xname+'+',xname+'-',yname+'+',yname+'-'],
                 tablefmt='github',
                 numalign='center',
                 stralign='center'))
  
  return dic

df1.min()['x']

"""

---



## a) $\Omega_{EE}$ com Universo Plano

Nessa tarefa estudamos como o valor de $\Omega_{EE}$ varia conforme tentamos chegar mais próximos das observações. Como o Universo é plano, temos que $\Omega_{K}=0$. Por conta disso, existe uma relação direta entre $\Omega_{EE}$ e $\Omega_{M}$, da forma $\Omega_{EE}+\Omega_{M}=1$."""

#tarefa a
w_inicial = -1
#omegaK=0, entao omM = 1-omEE
omEE_inicial = 0.7 #chute inicial
omM_inicial = 1 - omEE_inicial
itermax = 10000
sigma = 0.2

# o sufixo 'a' significa que sao os resultados da tarefa 'a'
omEE_a, omM_a, w_a, chi2_a = MCMC('a', dados, omEE_inicial, omM_inicial, w_inicial, itermax, sigma)

# plotando

#calculando P(omega_EE) = exp(-chi2)
prob_a = np.exp([-chi/2+min(chi2_a)/2 for chi in chi2_a])
x = np.array(omEE_a)
y = np.array(prob_a)
melhor_omEE = median(x)
sigma_omEE = stdev(x)
print('Melhor OmegaEE =', median(omEE_a))
print('Sigma de OmegaEE =', sigma_omEE)
# Calculate the point density
xy = np.vstack([x,y])
z = 10*gaussian_kde(xy)(xy)

# Sort the points by density, so that the densest points are plotted last
idx = z.argsort()
x, y, z = x[idx], y[idx], z[idx]
z = [x**2 for x in z]

fig, ax = plt.subplots(figsize=(10,5))
im = ax.scatter(x, y, c=z, cmap='jet')
fig.colorbar(im, ax=ax)
plt.axvline(melhor_omEE, linestyle='--',color='k',label=r'mediana de $\Omega_{EE}$')
plt.axvline(melhor_omEE+sigma_omEE, linestyle='--', color='r', label=rf'$1 \sigma$')
plt.axvline(melhor_omEE-sigma_omEE, linestyle='--', color='r')
plt.axvline(melhor_omEE+2*sigma_omEE, linestyle='--', color='y', label=r'2 $\sigma$')
plt.axvline(melhor_omEE-2*sigma_omEE, linestyle='--', color='y')
plt.axvline(melhor_omEE+3*sigma_omEE, linestyle='--', color='b', label=r'3 $\sigma$')
plt.axvline(melhor_omEE-3*sigma_omEE, linestyle='--', color='b')
plt.xlabel(r'$\Omega_{EE}$', fontsize=20)
plt.ylabel(r'$P(\Omega_{EE})$', fontsize=20)
plt.legend(loc='upper right')
plt.title('Função de Distribuição de Probabilidades')
plt.show()

from scipy.interpolate import interp1d
#interpolando esses pontos
f1 = interp1d(omEE_a, prob_a, kind='cubic')

### PRECISO FAZER AINDA A PARTE DA INTEGRAL
# não tenho ctz como vou fazer ainda

"""

---


## b) Variando $\Omega_{EE}$ e $\Omega_{M}$"""

#parte b
w_inicial = -1
omEE_inicial = 0.5 #chute inicial
omM_inicial = 0.5
itermax = 10000
sigma = 0.2

# calculando a cadeia
omEE_b, omM_b, w_b, chi2_b = MCMC('b', dados, omEE_inicial, omM_inicial, w_inicial, itermax, sigma)

# plotando os resultados
plotar(omEE_b, omM_b, '$\Omega_{EE}$', '$\Omega_M$', 'Tarefa B')

# printando incertezas
print('Mediana de cada valor:')
print('OmegaEE =', median(omEE_b))
print('OmegaM =', median(omM_b))
print('Incertezas para a Tarefa D com relação à mediana')
dic_d = incertezas(omEE_b, omM_b, itermax, 'Omega_{EE}', 'Omega_M')

"""## c) Variando $\Omega_{EE}$ e $\Omega_{M}$ com chi2 diferente"""

#parte c

w_inicial = -1
omEE_inicial = 0.5 #chute inicial
omM_inicial = 0.5
itermax = 10000
sigma = 0.2

# calculando a cadeia
omEE_c, omM_c, w_c, chi2_c = MCMC('c', dados, omEE_inicial, omM_inicial, w_inicial, itermax, sigma)

plotar(omEE_c, omM_c, '$\Omega_{EE}$', '$\Omega_M$', 'Tarefa C')

# printando incertezas
print('Mediana de cada valor:')
print('OmegaEE =', median(omEE_c))
print('OmegaM =', median(omM_c))
print('Incertezas para a Tarefa D com relação à mediana')
dic_c = incertezas(omEE_c, omM_c, itermax, 'Omega_EE', 'Omega_M')

"""## d) Variando $\Omega_{M}$ e $w$"""

#parte d
w_inicial = 0
omM_inicial = 0.5
omEE_inicial = 1 - omM_inicial
itermax = 10000
sigma = 0.2

# calculando a cadeia
omEE_d, omM_d, w_d, chi2_d = MCMC('d', dados, omEE_inicial, omM_inicial, w_inicial, itermax, sigma)

plotar(w_d, omM_d, '$w$', '$\Omega_M$', 'Tarefa D')

# printando incertezas
print('Mediana de cada valor:')
print('w =', median(w_d))
print('OmegaM =', median(omM_d))
print('Incertezas para a Tarefa D com relação à mediana')
dic_d = incertezas(w_d, omM_d, itermax, 'w', 'Omega_M')

"""

* parte da equacao do modulo da distancia
* por que usamos os dados de supernovas
* falar do MCMC
* falar um pouco do colab
* por que nao usamos os outros
* a) falar sobre a convergendia do MCMC, falar sobre a mediana cair no meio e comparar com o valor real (teste-z)
* falar que a integral vai ser 1, ou seja, omegaEE so pode ser positivo
* b) falar sobre como éé vantajoso fixar w e dizer que o universo eh plano enquanto se calcula omegaM e omegaEE
* falar sobre a distribuicao dos dois e comparar o resultado com a literatura
* c) adicionando um termo a mais no chi2 para ficar mais proximo do real. fazer comparacao com o resultado da b
* d) falar sobre o por que de variar o w e comparar com a literatura.
* conclusao: 

* falar sobre como foi o algoritmo (tempo, precisao, distribuicao, etc) vantagens e desvantagens
* falar que a aproximacao do modulo de distancia foi razoavel
* comentar sobre os resultados (como ficaram legais)
* deixar a ideia sobre uma proxima simulacao: falar em nao definir o valor de w, nem de M,EE e K, e ver como que esses resultados variam conforme o chi2 (isso demoraria muito tempo e exige muito processamento)


"""