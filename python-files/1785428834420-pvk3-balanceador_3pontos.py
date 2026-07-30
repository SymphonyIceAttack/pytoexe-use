import math
import numpy as np
import matplotlib.pyplot as plt

def obter_float(mensagem):
    while True:
        try:
            valor = float(input(mensagem))
            if valor < 0:
                print("Valor não pode ser negativo. Tente novamente.")
                continue
            return valor
        except ValueError:
            print("Entrada inválida. Digite um número.")

def main():
    print("="*60)
    print("BALANCEADOR DE VENTILADORES - MÉTODO GRÁFICO DE 3 PONTOS")
    print("="*60)
    
    # Entrada da massa de teste
    m_teste = obter_float("Massa de teste (gramas): ")
    
    # Entrada das amplitudes de vibração
    A0 = obter_float("Amplitude inicial (sem massa de teste): ")
    A1 = obter_float("Amplitude com massa em 0°: ")
    A2 = obter_float("Amplitude com massa em 120°: ")
    A3 = obter_float("Amplitude com massa em 240°: ")
    
    # Verificação básica
    if A0 == 0:
        print("A amplitude inicial não pode ser zero (sem vibração).")
        return
    
    # Cálculo do vetor T (efeito da massa de teste)
    # x = (2*A1^2 - A2^2 - A3^2) / (6*A0)
    # y = (A3^2 - A2^2) / (2*sqrt(3)*A0)
    x = (2*A1*A1 - A2*A2 - A3*A3) / (6 * A0)
    y = (A3*A3 - A2*A2) / (2 * math.sqrt(3) * A0)
    
    T_mag = math.hypot(x, y)
    if T_mag == 0:
        print("O efeito da massa de teste é zero. Verifique as medições.")
        return
    
    theta_T = math.degrees(math.atan2(y, x))  # ângulo do vetor T
    
    # Massa corretiva e ângulo
    m_corr = A0 * m_teste / T_mag
    theta_corr = theta_T + 180.0
    # Normalizar para 0-360
    theta_corr = theta_corr % 360.0
    
    # Exibição dos resultados
    print("\n" + "="*60)
    print("RESULTADOS DO BALANCEAMENTO")
    print("="*60)
    print(f"Vetor T (efeito da massa de teste):")
    print(f"  Componente real (x) = {x:.4f}")
    print(f"  Componente imaginária (y) = {y:.4f}")
    print(f"  Magnitude |T| = {T_mag:.4f}")
    print(f"  Ângulo de T = {theta_T:.2f}°")
    print("\nMassa corretiva:")
    print(f"  Massa = {m_corr:.2f} gramas")
    print(f"  Ângulo de instalação = {theta_corr:.2f}° (a partir da posição de 0° da massa de teste)")
    print("="*60)
    
    # Perguntar se deseja gráfico
    resp = input("\nDeseja visualizar o gráfico vetorial? (s/N): ").strip().lower()
    if resp == 's':
        gerar_grafico(A0, x, y, m_teste, m_corr, theta_corr)

def gerar_grafico(A0, x, y, m_teste, m_corr, theta_corr):
    # Vetor U (desbalanceamento original)
    U = np.array([A0, 0])
    T = np.array([x, y])
    
    # Vetores resultantes para cada posição
    angulos = [0, 120, 240]
    cores = ['blue', 'green', 'red']
    rotulos = ['0°', '120°', '240°']
    
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.axhline(0, color='black', linewidth=0.5)
    ax.axvline(0, color='black', linewidth=0.5)
    
    # Desenhar vetor U
    ax.quiver(0, 0, U[0], U[1], angles='xy', scale_units='xy', scale=1, color='purple', label='U (inicial)', width=0.008)
    ax.text(U[0]/2, U[1]/2, 'U', fontsize=12, color='purple')
    
    # Desenhar vetor T
    ax.quiver(0, 0, T[0], T[1], angles='xy', scale_units='xy', scale=1, color='orange', label='T (massa teste)', width=0.008)
    ax.text(T[0]/2, T[1]/2, 'T', fontsize=12, color='orange')
    
    # Vetores resultantes
    for ang, cor, rot in zip(angulos, cores, rotulos):
        rad = math.radians(ang)
        R = U + T * np.exp(1j * rad)  # rotação complexa
        R_real = R.real
        R_imag = R.imag
        ax.quiver(0, 0, R_real, R_imag, angles='xy', scale_units='xy', scale=1, color=cor, alpha=0.6, label=f'U + T @ {rot}', width=0.005)
        # Circunferência para indicar a magnitude
        circ = plt.Circle((0,0), np.hypot(R_real, R_imag), color=cor, fill=False, linestyle='dotted', alpha=0.3)
        ax.add_patch(circ)
    
    # Vetor correção (massa corretiva)
    corr_vec = -U
    ax.quiver(0, 0, corr_vec[0], corr_vec[1], angles='xy', scale_units='xy', scale=1, color='red', label='Correção (-U)', width=0.008, linestyle='dashed')
    ax.text(corr_vec[0]/2, corr_vec[1]/2, '-U', fontsize=12, color='red')
    
    # Configurar limites
    max_val = max(np.hypot(U[0], U[1]), np.hypot(x, y), 
                  np.hypot(U[0]+T[0], U[1]+T[1]),
                  np.hypot(U[0]+T[0]*np.cos(np.radians(120))-T[1]*np.sin(np.radians(120)), 
                           U[1]+T[0]*np.sin(np.radians(120))+T[1]*np.cos(np.radians(120))),
                  np.hypot(U[0]+T[0]*np.cos(np.radians(240))-T[1]*np.sin(np.radians(240)), 
                           U[1]+T[0]*np.sin(np.radians(240))+T[1]*np.cos(np.radians(240))))
    margin = max_val * 0.2
    ax.set_xlim(-max_val-margin, max_val+margin)
    ax.set_ylim(-max_val-margin, max_val+margin)
    ax.set_xlabel('Componente real')
    ax.set_ylabel('Componente imaginária')
    ax.set_title('Diagrama Vetorial - Método de 3 Pontos')
    ax.legend(loc='upper right')
    plt.show()

if __name__ == "__main__":
    main()