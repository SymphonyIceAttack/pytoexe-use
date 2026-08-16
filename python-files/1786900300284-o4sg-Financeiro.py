# -*- coding: utf-8 -*-

import os
import sqlite3
import calendar
from datetime import date, datetime

ARQUIVO_DB = "financeiro.db"


# ============================================================
# TELA
# ============================================================

def tela_azul():
    os.system("cls" if os.name == "nt" else "clear")

    if os.name == "nt":
        os.system("color 1F")


def pausar():
    input("\nPressione ENTER para continuar...")


def cabecalho(titulo):
    tela_azul()

    print("╔" + "═" * 76 + "╗")
    print("║" + titulo.center(76) + "║")
    print("╠" + "═" * 76 + "╣")


def linha():
    print("─" * 78)


# ============================================================
# FORMATAÇÃO
# ============================================================

def dinheiro(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def data_br(data):
    try:
        return datetime.strptime(data, "%Y-%m-%d").strftime("%d/%m/%Y")
    except:
        return data


# ============================================================
# DATA AUTOMÁTICA
# ============================================================

def ler_data():
    hoje = date.today()
    padrao = hoje.strftime("%d/%m/%Y")

    while True:
        texto = input(f"Data [{padrao}]: ").strip()

        if texto == "":
            return hoje.isoformat()

        if texto.isdigit() and len(texto) == 8:
            try:
                dia = int(texto[0:2])
                mes = int(texto[2:4])
                ano = int(texto[4:8])
                return date(ano, mes, dia).isoformat()
            except ValueError:
                pass

        try:
            return datetime.strptime(texto, "%d/%m/%Y").date().isoformat()
        except ValueError:
            pass

        print("Data inválida. Digite no formato DDMMAAAA ou DD/MM/AAAA.")


# ============================================================
# ENTRADA DE DADOS
# ============================================================

def ler_valor():
    while True:
        texto = input("Valor [R$ 0,00]: ").strip()

        if not texto:
            print("Digite o valor.")
            continue

        texto = texto.replace("R$", "").replace(" ", "")

        try:
            if "," in texto:
                texto = texto.replace(".", "").replace(",", ".")

            valor = float(texto)
            if valor > 0:
                return valor
        except ValueError:
            pass

        print("Valor inválido.")


def inteiro(pergunta, minimo=None, maximo=None):
    while True:
        try:
            valor = int(input(pergunta))

            if minimo is not None and valor < minimo:
                raise ValueError

            if maximo is not None and valor > maximo:
                raise ValueError

            return valor
        except ValueError:
            print("Opção inválida.")


# ============================================================
# BANCO DE DADOS
# ============================================================

def banco():
    return sqlite3.connect(ARQUIVO_DB)


def criar_banco():
    con = banco()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS configuracao (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS salario (
            id INTEGER PRIMARY KEY CHECK(id = 1),
            valor REAL NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS categorias (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL UNIQUE,
            tipo TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS gastos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT NOT NULL,
            descricao TEXT NOT NULL,
            categoria_id INTEGER NOT NULL,
            valor REAL NOT NULL,
            pagamento TEXT NOT NULL,
            parcelas INTEGER DEFAULT 1,
            FOREIGN KEY(categoria_id) REFERENCES categorias(id)
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS parcelas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            gasto_id INTEGER NOT NULL,
            numero INTEGER NOT NULL,
            total_parcelas INTEGER NOT NULL,
            valor REAL NOT NULL,
            ano INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            paga INTEGER DEFAULT 0,
            FOREIGN KEY(gasto_id) REFERENCES gastos(id)
        )
    """)

    categorias_padrao = [
        ("Moradia", "necessidade"),
        ("Alimentação", "necessidade"),
        ("Transporte", "necessidade"),
        ("Saúde", "necessidade"),
        ("Educação", "necessidade"),
        ("Contas", "necessidade"),
        ("Lazer", "desejo"),
        ("Compras", "desejo"),
        ("Assinaturas", "desejo"),
        ("Restaurante", "desejo"),
        ("Outros", "desejo"),
        ("Reserva / Investimento", "reserva")
    ]

    for nome, tipo in categorias_padrao:
        cur.execute("""
            INSERT OR IGNORE INTO categorias (nome, tipo) VALUES (?, ?)
        """, (nome, tipo))

    configuracoes = {
        "necessidade": "50",
        "desejo": "30",
        "reserva": "20",
        "fechamento_cartao": "15"
    }

    for chave, valor in configuracoes.items():
        cur.execute("""
            INSERT OR IGNORE INTO configuracao (chave, valor) VALUES (?, ?)
        """, (chave, valor))

    con.commit()
    con.close()


# ============================================================
# AUXILIARES DE CONFIGURAÇÃO E CARTÃO
# ============================================================

def config(chave, padrao):
    con = banco()
    resultado = con.execute("SELECT valor FROM configuracao WHERE chave = ?", (chave,)).fetchone()
    con.close()

    if resultado:
        try:
            return float(resultado[0])
        except:
            return resultado[0]
    return padrao


def salvar_config(chave, valor):
    con = banco()
    con.execute("INSERT OR REPLACE INTO configuracao (chave, valor) VALUES (?, ?)", (chave, str(valor)))
    con.commit()
    con.close()


def salario():
    con = banco()
    resultado = con.execute("SELECT valor FROM salario WHERE id = 1").fetchone()
    con.close()
    return resultado[0] if resultado else 0


def cadastrar_salario():
    cabecalho("SALÁRIO MENSAL")
    atual = salario()

    if atual:
        print(f"Salário atual: {dinheiro(atual)}\n")

    valor = ler_valor()

    con = banco()
    con.execute("INSERT OR REPLACE INTO salario (id, valor) VALUES (1, ?)", (valor,))
    con.commit()
    con.close()

    print(f"\nSalário definido: {dinheiro(valor)}")
    pausar()


def escolher_categoria():
    con = banco()
    dados = con.execute("SELECT id, nome, tipo FROM categorias ORDER BY nome").fetchall()
    con.close()

    print("\nCATEGORIA")
    linha()

    metade = (len(dados) + 1) // 2
    for i in range(metade):
        idx1 = i
        col1 = f"{idx1+1:02d} - {dados[idx1][1]:<22} [{dados[idx1][2][:1].upper()}]"

        idx2 = i + metade
        if idx2 < len(dados):
            col2 = f"{idx2+1:02d} - {dados[idx2][1]:<22} [{dados[idx2][2][:1].upper()}]"
            print(f"{col1:<38} | {col2}")
        else:
            print(col1)

    print("\n[N] Necessidade | [D] Desejo | [R] Reserva\n")
    opcao = inteiro("Categoria: ", 1, len(dados))
    return dados[opcao - 1]


def mes_fatura(data_compra):
    fechamento = int(config("fechamento_cartao", 15))
    data = datetime.strptime(data_compra, "%Y-%m-%d").date()

    if data.day <= fechamento:
        return (data.year, data.month)
    if data.month == 12:
        return (data.year + 1, 1)
    return (data.year, data.month + 1)


def criar_parcelas(gasto_id, valor_total, quantidade, ano_inicio, mes_inicio):
    valor_base = round(valor_total / quantidade, 2)
    restante = valor_total
    con = banco()
    ano, mes = ano_inicio, mes_inicio

    for numero in range(1, quantidade + 1):
        valor = round(restante, 2) if numero == quantidade else valor_base
        restante = round(restante - valor, 2)

        con.execute("""
            INSERT INTO parcelas (gasto_id, numero, total_parcelas, valor, ano, mes, paga)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        """, (gasto_id, numero, quantidade, valor, ano, mes))

        if mes == 12:
            ano += 1
            mes = 1
        else:
            mes += 1

    con.commit()
    con.close()


# ============================================================
# LANÇAMENTO E HISTÓRICO COM PAGINAÇÃO
# ============================================================

def novo_gasto():
    cabecalho("LANÇAR GASTO")
    print("Digite a data como 16082026 (ENTER = hoje).")
    data = ler_data()

    print()
    descricao = input("Descrição: ").strip()
    while not descricao:
        descricao = input("Descrição: ").strip()

    categoria = escolher_categoria()
    valor = ler_valor()

    print("\nFORMA DE PAGAMENTO")
    linha()
    print("1 - PIX   |   2 - DÉBITO   |   3 - DINHEIRO   |   4 - CARTÃO")
    linha()

    pagamento = inteiro("Opção: ", 1, 4)
    formas = {1: "PIX", 2: "DÉBITO", 3: "DINHEIRO", 4: "CARTÃO"}
    forma = formas[pagamento]

    parcelas = 1
    if forma == "CARTÃO":
        print()
        parcelas = inteiro("Número de parcelas: ", 1, 60)

    con = banco()
    cursor = con.cursor()
    cursor.execute("""
        INSERT INTO gastos (data, descricao, categoria_id, valor, pagamento, parcelas)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (data, descricao, categoria[0], valor, forma, parcelas))
    gasto_id = cursor.lastrowid
    con.commit()
    con.close()

    if forma == "CARTÃO":
        ano_fat, mes_fat = mes_fatura(data)
        criar_parcelas(gasto_id, valor, parcelas, ano_fat, mes_fat)

    cabecalho("CONFIRMAÇÃO DO GASTO")
    print(f"DATA:        {data_br(data)}")
    print(f"DESCRIÇÃO:   {descricao}")
    print(f"CATEGORIA:   {categoria[1]}")
    print(f"VALOR:       {dinheiro(valor)}")
    print(f"PAGAMENTO:   {forma}")

    if forma == "CARTÃO":
        print(f"PARCELAS:    {parcelas}x")
        valor_parcela = round(valor / parcelas, 2)
        print(f"\nValor aproximado por parcela: {dinheiro(valor_parcela)}")
        print("\nCompra gravada e lançada nas faturas futuras com sucesso!")
    else:
        print("STATUS: PAGO")

    linha()
    pausar()


def historico():
    cabecalho("HISTÓRICO GERAL DE GASTOS")
    print("1 - Este mês\n2 - Outro mês\n3 - Todos\n0 - Voltar")
    opcao = inteiro("Opção: ", 0, 3)

    if opcao == 0:
        return

    filtro = ""
    parametros = []
    hoje = date.today()

    if opcao in (1, 2):
        mes = hoje.month if opcao == 1 else inteiro("Mês: ", 1, 12)
        ano = hoje.year if opcao == 1 else inteiro("Ano: ", 2000, 2100)

        inicio = date(ano, mes, 1).isoformat()
        ultimo = calendar.monthrange(ano, mes)[1]
        fim = date(ano, mes, ultimo).isoformat()

        filtro = "WHERE g.data BETWEEN ? AND ?"
        parametros = [inicio, fim]

    con = banco()
    dados = con.execute(f"""
        SELECT g.id, g.data, g.descricao, c.nome, g.valor, g.pagamento, g.parcelas
        FROM gastos g
        JOIN categorias c ON c.id = g.categoria_id
        {filtro}
        ORDER BY g.data DESC, g.id DESC
    """, parametros).fetchall()
    con.close()

    if not dados:
        cabecalho("HISTÓRICO DE GASTOS")
        print("Nenhum gasto encontrado.")
        pausar()
        return

    # Sistema de Paginação (6 itens por página)
    itens_por_pagina = 6
    total_itens = len(dados)
    total_paginas = (total_itens + itens_por_pagina - 1) // itens_por_pagina
    pagina_atual = 1

    while True:
        cabecalho(f"HISTÓRICO DE GASTOS (Pág. {pagina_atual}/{total_paginas})")
        print(f"{'ID':<5}{'DATA':<12}{'DESCRIÇÃO':<22}{'PAGO EM':<10}{'CATEGORIA':<15}{'VALOR':>12}")
        linha()

        inicio_idx = (pagina_atual - 1) * itens_por_pagina
        fim_idx = inicio_idx + itens_por_pagina
        pagina_dados = dados[inicio_idx:fim_idx]

        for item in pagina_dados:
            g_id, g_data, g_desc, c_nome, g_valor, g_pag, g_parc = item
            pag_str = f"{g_pag} ({g_parc}x)" if g_pag == "CARTÃO" else g_pag
            print(f"{g_id:<5}{data_br(g_data):<12}{g_desc[:20]:<22}{pag_str:<10}{c_nome[:14]:<15}{dinheiro(g_valor):>12}")

        linha()

        comandos = []
        if pagina_atual < total_paginas:
            comandos.append("[P] Próxima página")
        if pagina_atual > 1:
            comandos.append("[A] Página anterior")
        comandos.append("[0] Voltar")

        print(" | ".join(comandos))
        opcao_pag = input("\nEscolha uma opção: ").strip().upper()

        if opcao_pag == "P" and pagina_atual < total_paginas:
            pagina_atual += 1
        elif opcao_pag == "A" and pagina_atual > 1:
            pagina_atual -= 1
        elif opcao_pag == "0":
            break


# ============================================================
# FUNCIONALIDADES DO CARTÃO
# ============================================================

def ver_faturas():
    cabecalho("RESUMO DAS PRÓXIMAS FATURAS")
    hoje = date.today()

    for i in range(6):
        ano = hoje.year
        mes = hoje.month

        for _ in range(i):
            if mes == 12:
                ano += 1
                mes = 1
            else:
                mes += 1

        con = banco()
        total = con.execute("""
            SELECT COALESCE(SUM(valor), 0)
            FROM parcelas
            WHERE ano = ? AND mes = ?
        """, (ano, mes)).fetchone()[0]
        con.close()

        nomes_meses = ["", "JANEIRO", "FEVEREIRO", "MARÇO", "ABRIL", "MAIO", "JUNHO", 
                       "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

        print(f"{nomes_meses[mes]}/{ano:<8}{dinheiro(total):>20}")

    print(f"\nFechamento configurado: dia {int(config('fechamento_cartao', 15))}")
    pausar()


def detalhar_fatura():
    cabecalho("DETALHES DA FATURA DO CARTÃO")

    hoje = date.today()
    mes = inteiro(f"Informe o mês (1-12) [{hoje.month}]: ", 1, 12)
    ano = inteiro(f"Informe o ano (ex: 2026) [{hoje.year}]: ", 2000, 2100)

    con = banco()
    itens = con.execute("""
        SELECT 
            g.data,
            g.descricao,
            c.nome,
            p.numero,
            p.total_parcelas,
            p.valor
        FROM parcelas p
        JOIN gastos g ON g.id = p.gasto_id
        JOIN categorias c ON c.id = g.categoria_id
        WHERE p.ano = ? AND p.mes = ?
        ORDER BY g.data ASC
    """, (ano, mes)).fetchall()
    con.close()

    if not itens:
        cabecalho(f"FATURA DE {mes:02d}/{ano}")
        print("Nenhum lançamento no cartão para este mês.")
        pausar()
        return

    # Totalização da fatura
    total_fatura = sum(item[5] for item in itens)

    # Paginação na fatura
    itens_por_pagina = 6
    total_itens = len(itens)
    total_paginas = (total_itens + itens_por_pagina - 1) // itens_por_pagina
    pagina_atual = 1

    while True:
        cabecalho(f"FATURA DE {mes:02d}/{ano} (Pág. {pagina_atual}/{total_paginas})")
        print(f"{'DATA':<12}{'DESCRIÇÃO':<25}{'PARCELA':<10}{'CATEGORIA':<15}{'VALOR':>12}")
        linha()

        inicio_idx = (pagina_atual - 1) * itens_por_pagina
        fim_idx = inicio_idx + itens_por_pagina
        pagina_itens = itens[inicio_idx:fim_idx]

        for data, desc, cat, num_p, tot_p, val_p in pagina_itens:
            parc_str = f"{num_p}/{tot_p}"
            print(f"{data_br(data):<12}{desc[:24]:<25}{parc_str:<10}{cat[:14]:<15}{dinheiro(val_p):>12}")

        linha()
        print(f"TOTAL DA FATURA:{dinheiro(total_fatura):>61}")
        linha()

        comandos = []
        if pagina_atual < total_paginas:
            comandos.append("[P] Próxima página")
        if pagina_atual > 1:
            comandos.append("[A] Página anterior")
        comandos.append("[0] Voltar")

        print(" | ".join(comandos))
        opcao_pag = input("\nEscolha uma opção: ").strip().upper()

        if opcao_pag == "P" and pagina_atual < total_paginas:
            pagina_atual += 1
        elif opcao_pag == "A" and pagina_atual > 1:
            pagina_atual -= 1
        elif opcao_pag == "0":
            break


def configurar_cartao():
    cabecalho("CONFIGURAÇÃO DO CARTÃO")
    atual = int(config("fechamento_cartao", 15))

    print(f"Dia atual de fechamento: {atual}\n")
    dia = inteiro("Dia de fechamento da fatura: ", 1, 31)

    salvar_config("fechamento_cartao", dia)
    print(f"\nFechamento configurado para o dia {dia}.")
    pausar()


def menu_cartao():
    while True:
        cabecalho("MENU CARTÃO DE CRÉDITO")
        print("""
1 - Resumo das faturas
2 - Detalhar gastos de uma fatura
3 - Configurar dia de fechamento
0 - Voltar
""")
        opcao = inteiro("Opção: ", 0, 3)

        if opcao == 0:
            return
        elif opcao == 1:
            ver_faturas()
        elif opcao == 2:
            detalhar_fatura()
        elif opcao == 3:
            configurar_cartao()


# ============================================================
# RELATÓRIOS E MENUS PRINCIPAIS
# ============================================================

def resumo_mes():
    cabecalho("RESUMO DO MÊS")
    renda = salario()
    hoje = date.today()
    mes, ano = hoje.month, hoje.year

    inicio = date(ano, mes, 1).isoformat()
    ultimo = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo).isoformat()

    con = banco()
    imediato = con.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM gastos
        WHERE data BETWEEN ? AND ? AND pagamento != 'CARTÃO'
    """, (inicio, fim)).fetchone()[0]

    fatura = con.execute("""
        SELECT COALESCE(SUM(valor), 0)
        FROM parcelas
        WHERE ano = ? AND mes = ?
    """, (ano, mes)).fetchone()[0]
    con.close()

    comprometido = imediato + fatura
    disponivel = renda - comprometido

    linha()
    print(f"SALÁRIO:            {dinheiro(renda)}")
    print(f"GASTOS PAGOS:       {dinheiro(imediato)}")
    print(f"FATURA DO MÊS:      {dinheiro(fatura)}")
    print(f"TOTAL COMPROMETIDO: {dinheiro(comprometido)}")
    linha()
    print(f"SALDO DISPONÍVEL:   {dinheiro(disponivel)}")
    linha()
    pausar()


def saude_financeira():
    cabecalho("SAÚDE FINANCEIRA (50 / 30 / 20)")
    renda = salario()

    if renda <= 0:
        print("Cadastre seu salário primeiro.")
        pausar()
        return

    hoje = date.today()
    mes, ano = hoje.month, hoje.year

    inicio = date(ano, mes, 1).isoformat()
    ultimo = calendar.monthrange(ano, mes)[1]
    fim = date(ano, mes, ultimo).isoformat()

    con = banco()
    gastos = con.execute("""
        SELECT c.tipo, COALESCE(SUM(g.valor), 0)
        FROM gastos g
        JOIN categorias c ON c.id = g.categoria_id
        WHERE g.data BETWEEN ? AND ? AND g.pagamento != 'CARTÃO'
        GROUP BY c.tipo
    """, (inicio, fim)).fetchall()

    parcelas = con.execute("""
        SELECT c.tipo, COALESCE(SUM(p.valor), 0)
        FROM parcelas p
        JOIN gastos g ON g.id = p.gasto_id
        JOIN categorias c ON c.id = g.categoria_id
        WHERE p.ano = ? AND p.mes = ?
        GROUP BY c.tipo
    """, (ano, mes)).fetchall()
    con.close()

    valores = {"necessidade": 0, "desejo": 0, "reserva": 0}

    for tipo, valor in gastos:
        valores[tipo] += valor

    for tipo, valor in parcelas:
        valores[tipo] += valor

    metas = {
        "necessidade": config("necessidade", 50),
        "desejo": config("desejo", 30),
        "reserva": config("reserva", 20)
    }

    nomes = {"necessidade": "NECESSIDADES", "desejo": "DESEJOS", "reserva": "RESERVA"}

    print(f"\nSalário: {dinheiro(renda)}")
    linha()

    for tipo in ["necessidade", "desejo", "reserva"]:
        limite = (renda * metas[tipo]) / 100
        gasto = valores[tipo]
        restante = limite - gasto

        print(f"\n{nomes[tipo]}")
        print(f"Meta:      {metas[tipo]:.0f}%")
        print(f"Limite:    {dinheiro(limite)}")
        print(f"Utilizado: {dinheiro(gasto)}")

        if restante >= 0:
            print(f"Restante:  {dinheiro(restante)}")
            print("STATUS: OK")
        else:
            print(f"Excedido:  {dinheiro(abs(restante))}")
            print("STATUS: ACIMA DA META")

    linha()
    pausar()


def configurar_503020():
    cabecalho("CONFIGURAR 50 / 30 / 20")
    print("Informe os percentuais. A soma precisa ser 100.\n")

    necessidade = inteiro("Necessidades (%): ", 0, 100)
    desejo = inteiro("Desejos (%): ", 0, 100)
    reserva = inteiro("Reserva (%): ", 0, 100)

    total = necessidade + desejo + reserva

    if total != 100:
        print(f"\nTotal informado: {total}%\nERRO: precisa totalizar 100%.")
    else:
        salvar_config("necessidade", necessidade)
        salvar_config("desejo", desejo)
        salvar_config("reserva", reserva)
        print("\nConfiguração salva.")

    pausar()


def excluir_gasto():
    cabecalho("EXCLUIR GASTO")
    con = banco()
    dados = con.execute("""
        SELECT id, data, descricao, valor, pagamento
        FROM gastos
        ORDER BY id DESC
        LIMIT 50
    """).fetchall()
    con.close()

    if not dados:
        print("Nenhum gasto registrado.")
        pausar()
        return

    for item in dados:
        print(f"{item[0]:<5}{data_br(item[1]):<12}{item[2][:30]:<30}{dinheiro(item[3]):>15}")

    print()
    codigo = inteiro("ID para excluir (0 cancela): ", 0)

    if codigo == 0:
        return

    confirma = input("CONFIRMA EXCLUSÃO? (S/N): ").upper()

    if confirma == "S":
        con = banco()
        con.execute("DELETE FROM parcelas WHERE gasto_id = ?", (codigo,))
        con.execute("DELETE FROM gastos WHERE id = ?", (codigo,))
        con.commit()
        con.close()
        print("\nGasto excluído.")
    else:
        print("\nCancelado.")

    pausar()


def menu_gastos():
    while True:
        cabecalho("GASTOS")
        print("""
1 - Lançar gasto
2 - Histórico geral
3 - Excluir gasto
0 - Voltar
""")
        opcao = inteiro("Opção: ", 0, 3)

        if opcao == 0:
            return
        elif opcao == 1:
            novo_gasto()
        elif opcao == 2:
            historico()
        elif opcao == 3:
            excluir_gasto()


def menu_principal():
    criar_banco()

    while True:
        cabecalho("CONTROLE FINANCEIRO PESSOAL")

        renda = salario()
        hoje = date.today()

        print(f" SALÁRIO: {dinheiro(renda)}")
        print(f" MÊS:     {hoje.strftime('%m/%Y')}")
        print("╠" + "═" * 76 + "╣")
        print("""
1 - GASTOS
2 - CARTÃO
3 - SALÁRIO
4 - RESUMO DO MÊS
5 - SAÚDE FINANCEIRA 50 / 30 / 20
6 - CONFIGURAR 50 / 30 / 20
0 - SAIR
""")
        opcao = inteiro("Opção: ", 0, 6)

        if opcao == 0:
            tela_azul()
            print("Sistema encerrado.")
            break
        elif opcao == 1:
            menu_gastos()
        elif opcao == 2:
            menu_cartao()
        elif opcao == 3:
            cadastrar_salario()
        elif opcao == 4:
            resumo_mes()
        elif opcao == 5:
            saude_financeira()
        elif opcao == 6:
            configurar_503020()


if __name__ == "__main__":
    menu_principal()