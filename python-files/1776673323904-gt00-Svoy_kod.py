import numpy as np
import matplotlib.pyplot as plt
# from scipy.stats import norm
import math
# from dataclasses import dataclass
# from typing import Dict


def P_geometr_perechvat(s,d):
    if s<d:
        P_gp=1-(s/d)**2;
    else:
        P_gp=0;
    return(round(P_gp,3))

def P_uderzan(m,v,sigma, d_set, S_set, eps):
    E_k = 0.5*m*v**2;
    E_p = sigma*d_set*S_set*eps;
    P_ud = 1 - math.exp(-(E_p/E_k)**2)
    return(round(P_ud,3))

def P_viziv(m_VV,R):
    P_izb= 0.3;
    P_pik = 0.084 + 0.27*((m_VV**(1/3))/R)**2 +0.7*((m_VV**(1/3))/R)**3;
    P_viz =  math.exp(-(P_pik/P_izb)**3)
    return(round(P_viz,3))
def P_udar_v(m_VV,R,H):
    P_pik = 0.084 + 0.27*((m_VV**(1/3))/R)**2 +0.7*((m_VV**(1/3))/R)**3;
    k=0.035*m_VV**(1/3) + 0.42;
    P_udar =  P_pik*(0.15+0.85*math.exp(-k*(H/R)));
    return(round(P_udar,3))
def P_nepr(T_gab,m_oskl,V_oskl, alfa_oskl, S_oskl, K):
    if K == 'gravel':
        K_gab = 1.5e8;
    elif K == 'sand':
        K_gab = 1.2e8;
    else: 
        K_gab = 0.8e8;
    T_treb = (m_oskl*(V_oskl**2)* np.sin(alfa_oskl))/(2*K_gab*S_oskl)
    P_udar = math.exp(-(T_treb/T_gab)**2);
    return(round(P_udar,3))
# ============================================================================
# Ввод данных
# ============================================================================
Bpla = [['Лютий',        300, 41.7, 6.7, 75, 0.002, 1800, 1e-4], 
        ['UJ-22 Airborne', 85, 43,  4.4, 15, 0.002, 1800, 1e-4],
        ['UJ-26 Beaver', 150, 41.7, 3.5, 20, 0.002, 1800, 1e-4],
        ['Hero 900',      97, 33.3, 4.5, 20, 0.002, 1800, 1e-4],
        ['FPV-дрон',     1.5, 25,  0.3, 0.5, 0.002, 1800, 1e-4],
        ['FPV-дрон',     1.5, 25,  0.3, 0.5, 0.002, 1800, 1e-4],
        ['СИЧ',          8.5, 22.2,  3, 4.0, 0.002, 1800, 1e-4]];
"""
  БпЛА: Название, масса БпЛА кг, скорость км/ч,размах БпЛА м,
  Масса ВВ БпЛА, кг, Масса осколков, кг, Скорость осколков км/ч, размер осколков м^2
  """
Sety =  [['Рабица',   0.045, 0.010, 1e5,   5e5, 2, 1e5, 2e4],
          ['Ловушка',  0.050, 0.004, 8e4,   4e5, 2.4, 2e5, 3e4],
          ['3D Забор', 0.035, 0.007, 1.2e5, 6e5, 1.6, 1.5e5, 2.5e4],
          ['Режущая',  0.091, 0.003, 2e5,   8e5, 1.2, 2e5, 4e4]]
"""
  Сетка: Название, Размер ячейки м, толщина нити м,коэффициенты жёсткости,
  критический прогиб до разрыва, м, максимальная энергия поглощения, Дж, 
  параметр разброса (для вероятности при превышении E_max)
"""
Gabions =    [['Габион h=0.5м', 0.5, 1.0, 'gravel'],
              ['Габион h=1м', 1.0, 1.5, 'sand'],
              ['Габион h=2м', 2.0, 2.0, 'clay'],
                ['Габион h=3м', 3.0, 3.0, 'gravel']];
"""
  Габион: Название, Высота м, толщина м, Материал габиона)
"""
# ============================================================================
# Сетки
# ============================================================================
F= np.zeros((len(Sety),len(Bpla)), dtype=float);
F2= np.zeros((len(Sety),len(Bpla)), dtype=float);
F3= np.zeros((len(Sety),len(Bpla)), dtype=float);
P_set = np.zeros((len(Sety),len(Bpla)), dtype=float);
for i in range(len(Sety)):
    for j in range(len(Bpla)):
        F[i,j] = P_geometr_perechvat(Sety[i][1],Bpla[j][3])
        F2[i,j] = P_uderzan(Bpla[j][1],Bpla[j][2],Sety[i][6],Sety[i][2],Bpla[j][3]*0.2,Sety[i][5]) 
        F3[i,j] = P_viziv(Bpla[j][4],5)
        P_set[i,j] = (round(F[i,j]*F2[i,j]+(1-F[i,j]*F2[i,j])*F3[i,j],3));
        # P_set[i,j] = F[i,j]+(1-F[i,j])*F2[i,j]+(1-F2[i,j])*F3[i,j];
# print (P_set)
    
# ============================================================================
# Габионы
# ============================================================================
F= np.zeros((len(Gabions),len(Bpla)), dtype=float);
F2= np.zeros((len(Gabions),len(Bpla)), dtype=float);
P_gab= np.zeros((len(Gabions),len(Bpla)), dtype=float);
for i in range(len(Gabions)):
    for j in range(len(Bpla)):
        F[i,j] = P_udar_v(Bpla[j][4],3,Gabions[i][1])
        F2[i,j] = P_nepr(Gabions[i][2],Bpla[j][5],Bpla[j][6],90,Bpla[j][7],Gabions[i][3])
        P_gab [i][j]= F[i,j]* F2[i,j]
E_pass= np.zeros((len(Bpla),len(Sety),len(Gabions)), dtype=float);
# print(P_gab)
# ============================================================================
# Эффективность
# ============================================================================
for j in range(len(Bpla)):
    for i in range(len(Gabions)):
        for k in range(len(Gabions)):
   
            E_pass [j][i][k] = round(P_set[i][j] + (1- P_set[i][j])*P_gab [k][j],3);
# print(E_pass)

# =============================================================================
# ГРАФИКИ: E_pass от массы ВВ (0.5 – 100 кг) для разных комбинаций Сетка + Габион
# =============================================================================

# Диапазон массы ВВ, который нас интересует
# m_vv_range = np.logspace(np.log(0.5), np.log(80), 200)  # 200 точек, логарифмическая шкала выглядит лучше

m_vv_range = np.linspace(0.5, 100, 200) 

# Выбираем несколько интересных комбинаций Сетка + Габион (можно менять по желанию)
combinations = [
    (0, 0),  # Рабица + Габион h=0.5м
    (0, 1),  # Рабица + Габион h=1м
    (0, 2),  # Рабица + Габион h=3м
    (0, 3),  # Ловушка + Габион h=1м
    # (0, 1),  # 3D Забор + Габион h=1м
    # (1, 2),
   
]

plt.figure(figsize=(16, 8))

# Словарь для легенды
legend_labels = []

# Здесь будем сохранять данные для таблицы
table_data = {}

for idx_set, idx_gab in combinations:
    bpla_name = Bpla[idx_set][0]
    set_name = Sety[idx_set][0]
    gab_name = Gabions[idx_gab][0]
    label = f"{gab_name}"
    legend_labels.append(label)
    
    E_pass_values = []
    
    for m_vv in m_vv_range:
        # Пересчитываем все вероятности для текущей массы ВВ
        # (оставляем все остальные параметры от FPV-дрона, т.к. они почти не влияют на пассивную защиту)
        Pgp = P_geometr_perechvat(Sety[idx_set][1], Bpla[4][3])                     # геометрия та же
        Pud = P_uderzan(Bpla[4][1], Bpla[4][2], Sety[idx_set][6], Sety[idx_set][2], 
                        Bpla[4][3]*0.2, Sety[idx_set][5])                           # удержание сеткой
        Pviz = P_viziv(m_vv, 5)                                                    # инициирование ВУ (зависит от m_vv!)
        P_set_current = Pgp * Pud + (1 - Pgp * Pud) * Pviz
        
        P_udar = P_udar_v(m_vv, 3, Gabions[idx_gab][1])                             # удар в габион
        P_nepr_current = P_nepr(Gabions[idx_gab][2], Bpla[4][5], Bpla[4][6], 90, 
                                Bpla[4][7], Gabions[idx_gab][3])                   # непробитие габиона осколками
        
        P_gab_current = 1-P_udar * P_nepr_current
        E_pass_current =P_gab_current
        # E_pass_current = P_set_current + (1 - P_set_current) * P_gab_current
        E_pass_current = round(E_pass_current, 4)
        
        E_pass_values.append(E_pass_current)
    
    plt.plot(m_vv_range, E_pass_values, linewidth=2.5)
    table_data[label] = list(zip(m_vv_range, E_pass_values))  # сохраняем для таблицы

# plt.xscale('log')
plt.xlabel('Масса ВВ БпЛА, кг', fontsize=14)
plt.ylabel('Эффективность габионной защиты', fontsize=14)
plt.title('Зависимость эффективности защиты ОИЖД габионами\n (от массы заряда БпЛА)', fontsize=15)
plt.grid(True, which="both", ls="--", alpha=0.7)
plt.legend(legend_labels, loc='lower right', fontsize=11)
plt.ylim(0, 1.05)
plt.xlim(0.5, 60)

plt.tight_layout()
plt.show()

# =============================================================================
# ТАБЛИЦА значений E_pass для ключевых масс ВВ
# =============================================================================

key_masses = [0.5, 1.0, 1.5, 2.0, 3.0, 4.0, 8.0, 10.0, 15.0, 20.0, 30.0, 50.0, 75.0, 100.0]

print("\n" + "="*50)
print("ЭФФЕКТИВНОСТЬ ПАССИВНОЙ ЗАЩИТЫ ДЛЯ РАЗНЫХ МАСС ВВ")
print("="*50)
print(f"{'Масса ВВ, кг':>15}", end="")
for label in legend_labels:
    print(f" | {label:>10}", end="")
print("\n" + "-"*50)

for m in key_masses:
    print(f"{m:5.1f}", end="")
    for label in legend_labels:
        # Находим ближайшее значение из рассчитанных
        distances = [(abs(m - mv), e) for mv, e in table_data[label]]
        _, e_best = min(distances, key=lambda x: x[0])
        print(f" | {e_best:12.4f}", end="")
    print()
print("="*50)
# set_idx = 1
# set = ['Режущая',  0.091, 0.003, 2e5,   8e5, 1.2, 2e5, 4e4]
# gab_idx = 1
# gab = ['Габион h=2м', 2.0, 2.0, 'clay']
# bpla_base =['Лютий', 300, 41.7, 6.7,None, 75, 0.002, 1800, 1e-4]
# R = 5.0
# H = gab[1]
# m_VV_values = np.linspace(0.5,75,120)
# E_pass_values=[]

# for m_VV in m_VV_values:
#     bpla = bpla_base.copy()
#     bpla[4]=m_VV
    
#     F = P_geometr_perechvat(set[1], bpla[3])
#     F2 = P_uderzan(bpla[1], bpla[2], set[6], set[2], bpla[3]*0.2, set[5])
#     F3 = P_viziv(bpla[4], R)
    
#     P_setka = F*F2+(1-F)*F2*F3
    
#     F_g=P_udar_v(bpla[4], R, H)
#     F2_g=P_nepr(gab[2], bpla[5], bpla[6], bpla[7], bpla[8], gab[3])
#     P_gab = 1-F_g*F2_g
    
#     # E_pass =P_setka+(1-P_setka)*P_gab
#     E_pass=P_gab
#     E_pass_values.append(E_pass)
#     print(E_pass)    
    
# plt.figure(figsize=(10,6), dpi=110)
# y1 = 
# plt.plot(m_VV_values, E_pass_values, color='darkred',linewidth=2, label='Эффективность')
# plt.plot(m_VV_values, y2, color='darkred',linewidth=2, label='Эффективность')
    
# plt.title(f"Зависимость эффективности от массы ВВ"
#               f"Сетка: {set[0]}, Габион: {gab[0]}, R = {R} м, H={H} м",
#               fontsize = 14, pad=12)
# plt.xlabel("Масса ВВ БпЛА, кг", fontsize=12)
# plt.ylabel("Эффективностть перехвата", fontsize=12)
    
# plt.grid(True, linestyle='--',alpha=0.6)
# plt.minorticks_on()
# plt.ylim(0, 1.05)
# plt.xlim(0, 75)
# plt.legend(fontsize=11, loc='lower right')
# plt.tight_layout()
# plt.show()










# distances = np.linspace(0, 20, 100)

# # График для тяжелого дрона
# # y_vals_1 = [calc_E_corrected(m_list[0], v_list[0], d_list[0], s_net[3], sigma[3], t_wire[3], d, epsilon[3]) for d in distances]
# # plt.plot(distances, y_vals_1, label=f'{names_net[3]} vs {names_bpla[0]}', linewidth=2)

# E_ppp = 
# y1 = E_pass[1][1][1]
# plt.plot(distances, y1, linewidth=2)





# # 1. Вычислим матрицы, не зависящие от R
# P_geom = np.zeros((len(Sety), len(Bpla)))
# P_uderz = np.zeros((len(Sety), len(Bpla)))
# for i in range(len(Sety)):
#     for j in range(len(Bpla)):
#         P_geom[i,j] = P_geometr_perechvat(Sety[i][1], Bpla[j][3])
#         P_uderz[i,j] = P_uderzan(Bpla[j][1], Bpla[j][2], Sety[i][6], Sety[i][2], Bpla[j][3]*0.2, Sety[i][5])

# P_nepr_gab = np.zeros((len(Gabions), len(Bpla)))
# for k in range(len(Gabions)):
#     for j in range(len(Bpla)):
#         P_nepr_gab[k,j] = P_nepr(Gabions[k][2], Bpla[j][5], Bpla[j][6], 90, Bpla[j][7], Gabions[k][3])

# # 2. Задаём диапазон расстояний
# R_values = np.linspace(2, 15, 200)  # от 1 до 50 м, 200 точек
# Z_values=[]
# for i in range(len(Bpla)):
#     Z_values.append(Bpla[i][4])


# # 3. Массив для хранения E_pass: [R, БПЛА, сетка, габион]
# E_pass_vs_R = np.zeros((len(R_values), len(Bpla), len(Sety), len(Gabions)))

# # 4. Цикл по расстояниям
# for r_idx, R in enumerate(R_values):
#     # P_viziv для всех БПЛА
#     P_viziv_R = np.array([P_viziv(Bpla[j][4], R) for j in range(len(Bpla))])
    
#     # P_udar_v для всех габионов и БПЛА
#     P_udar_v_R = np.zeros((len(Gabions), len(Bpla)))
#     for k in range(len(Gabions)):
#         for j in range(len(Bpla)):
#             P_udar_v_R[k,j] = P_udar_v(Bpla[j][4], R, Gabions[k][1])
    
#     # P_set для всех сеток и БПЛА
#     P_set_R = np.zeros((len(Sety), len(Bpla)))
#     for i in range(len(Sety)):
#         for j in range(len(Bpla)):
#             P_set_R[i,j] = P_geom[i,j] * P_uderz[i,j] + (1 - P_geom[i,j]*P_uderz[i,j]) * P_viziv_R[j]
    
#     # P_gab для всех габионов и БПЛА
#     P_gab_R = np.zeros((len(Gabions), len(Bpla)))
#     for k in range(len(Gabions)):
#         for j in range(len(Bpla)):
#             P_gab_R[k,j] = P_udar_v_R[k,j] * P_nepr_gab[k,j]
    
#     # Итоговая эффективность E_pass
#     for j in range(len(Bpla)):
#         for i in range(len(Sety)):
#             for k in range(len(Gabions)):
#                 E_pass_vs_R[r_idx, j, i, k] = P_set_R[i,j] + (1 - P_set_R[i,j]) * P_gab_R[k,j]
# # print(E_pass_vs_R)
# # Удобнее создать отдельный массив P_gab_vs_R
# P_gab_vs_R = np.zeros((len(R_values), len(Gabions), len(Bpla)))

# for r_idx, R in enumerate(R_values):
#     for k in range(len(Gabions)):
#         for j in range(len(Bpla)):
#             P_udar = P_udar_v(Bpla[j][4], R, Gabions[k][1])
#             P_gab_vs_R[r_idx, k, j] = 1 - P_udar * P_nepr_gab[k, j]  # P_nepr_gab не зависит от R
# # print(P_gab_vs_R)

# # plt.figure(figsize=(12, 8))
# # for k in range(len(Z_values)):
#     # Для примера возьмём первый БПЛА
#     # plt.plot(R_values, P_gab_vs_R[:, k, 0], linewidth=1.5, label=f'{Gabions[k][0]} (БПЛА: {Bpla[0][0]})')
#     # plt.plot(Z_values, E_pass_vs_R[:, k, 0], linewidth=1.5)
# # plt.xlabel('Масса заряда, кг')
# # plt.ylabel('Эффективность')
# # plt.title('Вероятность поражения только габионом (без сетки)')
# # plt.grid(True)
# # plt.legend()
# # plt.show()


# # # GRAPHICS
# # dist = np.linspace(1, 15, 100) # От 2 до 15 метров
# # plt.figure(figsize=(10, 6))
# # x1 = 0
# # y1 = (E_pass [j][i][k])
# # plt.plot(x1,y1,label="1 gr", linewidth=2)


# # # # y_vals_1 = [calc_E_corrected(m_list[0], v_list[0], d_list[0], s_net[3], sigma[3], t_wire[3], d, epsilon[3]) for d in distances]
# # # # plt.plot(distances, y_vals_1, label=f'{names_net[3]} vs {names_bpla[0]}', linewidth=2)


# # plt.xlabel("Расстояние")
# # plt.ylabel("Эфективность")
# # plt.title("Эффективность пассивной защиты")
# # plt.grid(True, alpha=0.3)
# # plt.legend()
# # plt.tight_layout()
# # plt.show()