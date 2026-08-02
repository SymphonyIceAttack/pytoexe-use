import math
import sys
import os
import subprocess

# Força o backend 'Agg' (sem interface gráfica, gera imagens)
import matplotlib
matplotlib.use('Agg')
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
    
    m_teste = obter_float("Massa de teste (gramas): ")
    A0 = obter_float("Amplitude inicial (sem massa de teste): ")
    A1 = obter_float("Amplitude com massa em 0°: ")
    A2 = obter_float("Amplitude com massa em 120°: ")
    A3 = obter_float("Amplitude com massa em 240°: ")
    
    if A0 == 0:
        print("A amplitude inicial não pode ser zero (sem vibração).")
        return
    
    # Cálculo do vetor T
    x = (2*A1*A1 - A2*A2 - A3*A3) / (6 * A0)
    y = (A3*A3 - A2*A2) / (2 * math.sqrt(3) * A0)
    
    T_mag = math.hypot(x, y)
    if T_mag == 0:
        print("O efeito da massa de teste é zero. Verifique as medições.")
        return
    
    theta_T = math.degrees(math.atan2(y, x))
    m_corr = A0 * m_teste / T_mag
    theta_corr = (theta_T + 180.0) % 360.0
    
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
    
    resp = input("\nDeseja gerar o gráfico vetorial? (s/N): ").strip().lower()
    if resp == 's':
        nome_arquivo = "grafico_balanceamento.png"
        try:
            gerar_e_salvar_grafico(A0, x, y, nome_arquivo)
            print(f"\n✅ Gráfico salvo como '{nome_arquivo}'")
            abrir_imagem(nome_arquivo)
        except Exception as e:
            print(f"\n❌ Erro ao gerar o gráfico: {e}")
            print("   Verifique se os valores inseridos são coerentes.")
    else:
        print("\nOK, gráfico não será gerado.")
    
    input("\nPressione Enter para sair...")

def gerar_e_salvar_grafico(A0, x, y, nome_arquivo):
    """Gera o diagrama vetorial e salva como PNG."""
    # Definir componentes escalares para evitar erro de tamanho
    ux = A0       # componente x do vetor U
    uy = 0.0      # componente y do vetor U (zero, pois U está alinhado com 0°)
    tx = x        # componente x do vetor T
    ty = y        # componente y do vetor T
    
    angulos = [0, 120, 240]
    cores = ['blue', 'green', 'red']
    rotulos = ['0°', '120°', '240°']
    
    fig, ax = plt.subplots(figsize=(8,8))
    ax.set_aspect('equal')
    ax.grid(True, linestyle='--', alpha=0.6)
    ax.axhline(0, color='black', linewidth=0.5)
    ax.axvline(0, color='black', linewidth=0.5)
    
    # Vetor U (inicial)
    ax.quiver(0, 0, ux, uy, angles='xy', scale_units='xy', scale=1,
              color='purple', label='U (inicial)', width=0.008)
    ax.text(ux/2, uy/2, 'U', fontsize=12, color='purple')
    
    # Vetor T (massa de teste)
    ax.quiver(0, 0, tx, ty, angles='xy', scale_units='xy', scale=1,
              color='orange', label='T (massa teste)', width=0.008)
    ax.text(tx/2, ty/2, 'T', fontsize=12, color='orange')
    
    # Vetores resultantes U + T em cada ângulo
    for ang, cor, rot in zip(angulos, cores, rotulos):
        rad = math.radians(ang)
        # Rotacionar T pelo ângulo
        tx_rot = tx * math.cos(rad) - ty * math.sin(rad)
        ty_rot = tx * math.sin(rad) + ty * math.cos(rad)
        rx = ux + tx_rot
        ry = uy + ty_rot
        ax.quiver(0, 0, rx, ry, angles='xy', scale_units='xy', scale=1,
                  color=cor, alpha=0.6, label=f'U + T @ {rot}', width=0.005)
        # Circunferência auxiliar
        circ = plt.Circle((0,0), math.hypot(rx, ry), color=cor,
                          fill=False, linestyle='dotted', alpha=0.3)
        ax.add_patch(circ)
    
    # Vetor correção (-U)
    ax.quiver(0, 0, -ux, -uy, angles='xy', scale_units='xy', scale=1,
              color='red', label='Correção (-U)', width=0.008, linestyle='dashed')
    ax.text(-ux/2, -uy/2, '-U', fontsize=12, color='red')
    
    # Ajuste dos limites
    max_val = max(math.hypot(ux, uy), math.hypot(tx, ty),
                  math.hypot(ux+tx, uy+ty),
                  math.hypot(ux + tx*math.cos(math.radians(120)) - ty*math.sin(math.radians(120)),
                             uy + tx*math.sin(math.radians(120)) + ty*math.cos(math.radians(120))),
                  math.hypot(ux + tx*math.cos(math.radians(240)) - ty*math.sin(math.radians(240)),
                             uy + tx*math.sin(math.radians(240)) + ty*math.cos(math.radians(240))))
    margin = max_val * 0.2
    ax.set_xlim(-max_val-margin, max_val+margin)
    ax.set_ylim(-max_val-margin, max_val+margin)
    ax.set_xlabel('Componente real')
    ax.set_ylabel('Componente imaginária')
    ax.set_title('Diagrama Vetorial - Método de 3 Pontos')
    ax.legend(loc='upper right')
    
    plt.savefig(nome_arquivo, dpi=150, bbox_inches='tight')
    plt.close(fig)

def abrir_imagem(caminho):
    try:
        if sys.platform == 'win32':
            os.startfile(caminho)
        else:
            subprocess.run(['xdg-open', caminho], check=True)
        print("📷 O gráfico foi aberto no visualizador padrão.")
    except Exception as e:
        print(f"⚠️ Não foi possível abrir automaticamente: {e}")
        print(f"   O arquivo está em: {os.path.abspath(caminho)}")

if __name__ == "__main__":
    main()