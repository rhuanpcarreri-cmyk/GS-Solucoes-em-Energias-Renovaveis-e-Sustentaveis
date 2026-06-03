import os
import time
import random
import math
from datetime import datetime

# ══════════════════════════════════════════════════════════════════════════════
#  CORES ANSI
# ══════════════════════════════════════════════════════════════════════════════
RESET   = "\033[0m";  BOLD    = "\033[1m"
RED     = "\033[91m"; GREEN   = "\033[92m"; YELLOW  = "\033[93m"
BLUE    = "\033[94m"; MAGENTA = "\033[95m"; CYAN    = "\033[96m"
WHITE   = "\033[97m"; BG_RED  = "\033[41m"; BG_GREEN= "\033[42m"
BG_CYAN = "\033[46m"

# ══════════════════════════════════════════════════════════════════════════════
#  ESTADO GLOBAL
# ══════════════════════════════════════════════════════════════════════════════
historico   = []   # leituras dos sensores
log_alertas = []   # log centralizado de alertas/decisões da IA

# Constantes energéticas da nave
POTENCIA_PAINEIS_W  = 5000   # Watts gerados pelos painéis solares
POTENCIA_CONSUMO_W  = 3200   # Watts consumidos em modo normal
CAPACIDADE_BATERIA_WH = 20000  # Wh totais da bateria

# ══════════════════════════════════════════════════════════════════════════════
#  UTILITÁRIOS DE INTERFACE
# ══════════════════════════════════════════════════════════════════════════════
def limpar():
    os.system("cls" if os.name == "nt" else "clear")

def linha(char="─", cor=CYAN, tam=60):
    print(f"{cor}{char * tam}{RESET}")

def cabecalho(subtitulo="Missão Ativa"):
    limpar()
    linha("═", CYAN, 60)
    print(f"{CYAN}{BOLD}{'🚀  SISTEMA DE MONITORAMENTO ESPACIAL  🚀':^60}{RESET}")
    print(f"{BLUE}{subtitulo:^60}{RESET}")
    linha("═", CYAN, 60)
    print()

def pausar():
    input(f"\n{WHITE}  Pressione ENTER para continuar...{RESET}")

def barra_progresso(valor, maximo=100, tam=30, cor=GREEN):
    preenchido = int((valor / maximo) * tam)
    barra = "█" * preenchido + "░" * (tam - preenchido)
    return f"{cor}[{barra}]{RESET} {valor:.1f}%"

# ══════════════════════════════════════════════════════════════════════════════
#  FUNÇÕES DE COR / STATUS
# ══════════════════════════════════════════════════════════════════════════════
def cor_temp(t):
    return RED if t > 80 else (YELLOW if t > 60 else GREEN)

def cor_energia(e):
    return RED if e < 20 else (YELLOW if e < 50 else GREEN)

def status_comm(c):
    return f"{GREEN}ATIVO ✔{RESET}" if c == 1 else f"{RED}FALHA ✖{RESET}"

# ══════════════════════════════════════════════════════════════════════════════
#  CÁLCULOS ENERGÉTICOS
# ══════════════════════════════════════════════════════════════════════════════
def calcular_energia_disponivel_wh(percentual):
    """Converte % de bateria para Wh."""
    return (percentual / 100) * CAPACIDADE_BATERIA_WH

def calcular_autonomia_horas(percentual):
    """Quantas horas a nave aguenta com a bateria atual."""
    wh_disponiveis = calcular_energia_disponivel_wh(percentual)
    consumo_liquido = POTENCIA_CONSUMO_W - POTENCIA_PAINEIS_W
    if consumo_liquido <= 0:
        return float("inf")  # painéis cobrem consumo
    return wh_disponiveis / consumo_liquido

def calcular_eficiencia_solar(temperatura):
    """
    Painéis solares perdem ~0.4% de eficiência por grau acima de 25°C.
    Abaixo de 25°C, eficiência aumenta levemente.
    """
    delta = temperatura - 25
    eficiencia = 100 - (delta * 0.4)
    return max(10, min(105, eficiencia))

def calcular_potencia_atual_w(temperatura, percentual_painel=100):
    """Potência real gerada considerando temperatura e % de painel ativo."""
    ef = calcular_eficiencia_solar(temperatura)
    return POTENCIA_PAINEIS_W * (ef / 100) * (percentual_painel / 100)

def calcular_saldo_energetico(temperatura):
    """Retorna saldo W (positivo = carregando, negativo = descarregando)."""
    pot_gerada = calcular_potencia_atual_w(temperatura)
    return pot_gerada - POTENCIA_CONSUMO_W

# ══════════════════════════════════════════════════════════════════════════════
#  MOTOR DE IA — TOMADA DE DECISÃO AUTOMÁTICA
# ══════════════════════════════════════════════════════════════════════════════
REGRAS_IA = [
    # (condição_fn, prioridade, ação, descrição)
    (lambda l: l["temperatura"] > 90,         5, "DESLIGAR_AQUECEDORES",   "Temperatura crítica (>90°C) — desligar sistemas de aquecimento"),
    (lambda l: l["temperatura"] > 80,         4, "ATIVAR_RESFRIAMENTO",    "Superaquecimento detectado — ativar sistema de resfriamento"),
    (lambda l: l["energia"] < 10,             5, "MODO_EMERGENCIA",        "Bateria crítica (<10%) — ativar modo de emergência total"),
    (lambda l: l["energia"] < 20,             4, "MODO_ECONOMIA",          "Bateria baixa (<20%) — ativar modo de economia de energia"),
    (lambda l: l["comunicacao"] == 0,         4, "REBOOT_ANTENA",          "Falha de comunicação — reiniciar sistema de antena"),
    (lambda l: calcular_saldo_energetico(l["temperatura"]) < -500, 3,
                                                  "REDUZIR_CONSUMO",        "Saldo energético negativo — reduzir consumo de sistemas não-essenciais"),
    (lambda l: l["energia"] > 90 and calcular_saldo_energetico(l["temperatura"]) > 0, 1,
                                                  "MODO_NORMAL",            "Sistemas energéticos estáveis — operação normal"),
]

def ia_tomada_decisao(leitura):
    """Avalia regras e retorna lista de decisões ordenadas por prioridade."""
    decisoes = []
    for cond, prioridade, acao, descricao in REGRAS_IA:
        try:
            if cond(leitura):
                decisoes.append({
                    "prioridade": prioridade,
                    "acao": acao,
                    "descricao": descricao,
                    "timestamp": leitura["timestamp"]
                })
        except Exception:
            pass
    decisoes.sort(key=lambda d: -d["prioridade"])
    return decisoes

def cor_prioridade(p):
    return RED if p >= 5 else (YELLOW if p >= 4 else (CYAN if p >= 3 else GREEN))

# ══════════════════════════════════════════════════════════════════════════════
#  ANÁLISE DE ALERTAS SIMPLES
# ══════════════════════════════════════════════════════════════════════════════
def analisar_alertas(leitura):
    alertas = []
    if leitura["temperatura"] > 80:
        alertas.append(f"{RED}{BOLD}  ⚠  ALERTA: Superaquecimento! Temperatura = {leitura['temperatura']}°C{RESET}")
    if leitura["energia"] < 20:
        alertas.append(f"{YELLOW}{BOLD}  ⚠  ALERTA: Energia crítica! Nível = {leitura['energia']}%{RESET}")
    if leitura["comunicacao"] == 0:
        alertas.append(f"{BG_RED}{WHITE}{BOLD}  ✖  CRÍTICO: Falha de comunicação!{RESET}")
    return alertas

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 1 — INSERIR DADOS
# ══════════════════════════════════════════════════════════════════════════════
def inserir_dados():
    cabecalho("Inserção Manual de Dados")
    print(f"{CYAN}{BOLD}  📡  SENSORES DA NAVE{RESET}\n")
    linha()
    try:
        t = float(input(f"  {WHITE}Temperatura (°C)              : {RESET}"))
        e = float(input(f"  {WHITE}Nível de energia (%)          : {RESET}"))
        c = 1 if input(f"  {WHITE}Comunicação (1=ativo/0=falha) : {RESET}").strip() == "1" else 0
    except ValueError:
        print(f"\n{RED}  Entrada inválida.{RESET}")
        pausar(); return

    leitura = {
        "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
        "temperatura": t, "energia": e, "comunicacao": c, "origem": "Manual"
    }
    historico.append(leitura)

    # IA avalia e registra decisões
    decisoes = ia_tomada_decisao(leitura)
    for d in decisoes:
        log_alertas.append(d)

    print()
    alertas = analisar_alertas(leitura)
    if alertas:
        linha("─", RED)
        for a in alertas: print(a)
        linha("─", RED)
    else:
        print(f"{GREEN}  ✔  Sistemas normais.{RESET}")

    if decisoes:
        print(f"\n{MAGENTA}{BOLD}  🤖  IA — Decisões automáticas:{RESET}")
        for d in decisoes:
            cp = cor_prioridade(d["prioridade"])
            print(f"  {cp}[P{d['prioridade']}] {d['acao']}{RESET} — {d['descricao']}")
    pausar()

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 2 — STATUS ATUAL COM PAINEL ENERGÉTICO
# ══════════════════════════════════════════════════════════════════════════════
def visualizar_status():
    cabecalho("Status Atual da Missão")
    if not historico:
        print(f"{YELLOW}  Nenhuma leitura registrada.{RESET}")
        pausar(); return

    l = historico[-1]
    t, e, c = l["temperatura"], l["energia"], l["comunicacao"]

    ef_solar = calcular_eficiencia_solar(t)
    pot_gerada = calcular_potencia_atual_w(t)
    saldo = calcular_saldo_energetico(t)
    autonomia = calcular_autonomia_horas(e)
    wh = calcular_energia_disponivel_wh(e)

    linha()
    print(f"  {WHITE}Leitura  :{RESET} {l['timestamp']}  [{l['origem']}]")
    linha("─", BLUE)
    print(f"  {WHITE}🌡  Temperatura   :{RESET} {cor_temp(t)}{BOLD}{t}°C{RESET}")
    print(f"  {WHITE}⚡  Bateria       :{RESET} {barra_progresso(e, cor=cor_energia(e))}")
    print(f"  {WHITE}📡  Comunicação   :{RESET} {status_comm(c)}")
    linha("─", BLUE)
    print(f"\n  {CYAN}{BOLD}☀  PAINEL SOLAR (Energia Renovável){RESET}")
    print(f"  {WHITE}Eficiência atual   :{RESET} {GREEN if ef_solar > 80 else YELLOW}{ef_solar:.1f}%{RESET}")
    print(f"  {WHITE}Potência gerada    :{RESET} {GREEN}{pot_gerada:.0f} W{RESET}")
    print(f"  {WHITE}Consumo da nave    :{RESET} {WHITE}{POTENCIA_CONSUMO_W} W{RESET}")
    cor_saldo = GREEN if saldo >= 0 else RED
    sinal = "+" if saldo >= 0 else ""
    print(f"  {WHITE}Saldo energético   :{RESET} {cor_saldo}{BOLD}{sinal}{saldo:.0f} W{RESET}")
    print(f"  {WHITE}Energia disponível :{RESET} {WHITE}{wh:.0f} Wh{RESET}")
    if autonomia == float("inf"):
        print(f"  {WHITE}Autonomia estimada :{RESET} {GREEN}Indefinida (painéis suprem consumo){RESET}")
    else:
        print(f"  {WHITE}Autonomia estimada :{RESET} {cor_energia(e)}{autonomia:.1f} horas{RESET}")
    linha()

    decisoes = ia_tomada_decisao(l)
    if decisoes:
        print(f"\n  {MAGENTA}{BOLD}🤖  IA — Ações recomendadas:{RESET}")
        for d in decisoes:
            cp = cor_prioridade(d["prioridade"])
            print(f"  {cp}▶ {d['acao']}{RESET} — {d['descricao']}")
    else:
        print(f"  {GREEN}✔  Missão estável. Nenhuma ação necessária.{RESET}")
    pausar()

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 3 — ANÁLISE COMPLETA
# ══════════════════════════════════════════════════════════════════════════════
def executar_analise():
    cabecalho("Análise Completa das Leituras")
    if not historico:
        print(f"{YELLOW}  Nenhuma leitura para analisar.{RESET}")
        pausar(); return

    temps = [l["temperatura"] for l in historico]
    energ = [l["energia"]     for l in historico]
    falhas_comm = sum(1 for l in historico if l["comunicacao"] == 0)
    super_aq    = sum(1 for l in historico if l["temperatura"] > 80)
    crit_en     = sum(1 for l in historico if l["energia"] < 20)

    # Energia total gerada (simulada com base nas leituras)
    energia_gerada_total = sum(calcular_potencia_atual_w(t) for t in temps)
    ef_media = sum(calcular_eficiencia_solar(t) for t in temps) / len(temps)

    linha()
    print(f"  {WHITE}Total de leituras      :{RESET} {BOLD}{len(historico)}{RESET}")
    linha("─", BLUE)
    print(f"  {CYAN}{BOLD}🌡  TEMPERATURA{RESET}")
    print(f"  Média   : {cor_temp(sum(temps)/len(temps))}{sum(temps)/len(temps):.1f}°C{RESET}")
    print(f"  Máxima  : {cor_temp(max(temps))}{max(temps):.1f}°C{RESET}")
    print(f"  Mínima  : {cor_temp(min(temps))}{min(temps):.1f}°C{RESET}")
    linha("─", BLUE)
    print(f"  {CYAN}{BOLD}⚡  ENERGIA{RESET}")
    print(f"  Média   : {cor_energia(sum(energ)/len(energ))}{sum(energ)/len(energ):.1f}%{RESET}")
    print(f"  Mínima  : {cor_energia(min(energ))}{min(energ):.1f}%{RESET}")
    print(f"  Máxima  : {cor_energia(max(energ))}{max(energ):.1f}%{RESET}")
    linha("─", BLUE)
    print(f"  {CYAN}{BOLD}☀  ENERGIAS RENOVÁVEIS — PAINEL SOLAR{RESET}")
    print(f"  Eficiência média       : {GREEN}{ef_media:.1f}%{RESET}")
    print(f"  Potência total gerada  : {GREEN}{energia_gerada_total:.0f} W·leitura{RESET}")
    linha("─", BLUE)
    print(f"  {CYAN}{BOLD}⚠  OCORRÊNCIAS{RESET}")
    print(f"  Superaquecimentos : {RED if super_aq else GREEN}{super_aq}{RESET}")
    print(f"  Energia crítica   : {RED if crit_en  else GREEN}{crit_en}{RESET}")
    print(f"  Falhas de comm.   : {RED if falhas_comm else GREEN}{falhas_comm}{RESET}")
    linha()

    total = super_aq + crit_en + falhas_comm
    if total == 0:
        print(f"  {GREEN}{BOLD}✔  Missão dentro dos parâmetros normais.{RESET}")
    else:
        print(f"  {YELLOW}{BOLD}⚠  {total} ocorrência(s) detectada(s).{RESET}")

    print(f"\n  {MAGENTA}{BOLD}🤖  RESUMO DA IA — Decisões registradas: {len(log_alertas)}{RESET}")
    pausar()

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 4 — HISTÓRICO
# ══════════════════════════════════════════════════════════════════════════════
def ver_historico():
    cabecalho("Histórico de Leituras")
    if not historico:
        print(f"{YELLOW}  Nenhuma leitura registrada.{RESET}")
        pausar(); return

    linha()
    print(f"  {'#':<4} {'Timestamp':<22} {'Temp':>7} {'Energ':>7} {'Ef.Solar':>9} {'Comm':<8} {'Origem'}")
    linha("─", BLUE)
    for i, l in enumerate(historico, 1):
        ef = calcular_eficiencia_solar(l["temperatura"])
        comm = f"{GREEN}OK{RESET}" if l["comunicacao"] else f"{RED}FALHA{RESET}"
        print(f"  {i:<4} {l['timestamp']:<22} "
              f"{cor_temp(l['temperatura'])}{l['temperatura']:>5.1f}°C{RESET} "
              f"{cor_energia(l['energia'])}{l['energia']:>5.1f}%{RESET} "
              f"{GREEN if ef > 80 else YELLOW}{ef:>7.1f}%{RESET}  "
              f"{comm:<18} {l['origem']}")
    linha()
    pausar()

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 5 — SIMULAÇÃO AUTOMÁTICA
# ══════════════════════════════════════════════════════════════════════════════
def simular_sensores():
    cabecalho("Simulação Automática de Sensores")
    linha()
    try:
        n = int(input(f"  {WHITE}Quantas leituras simular? {RESET}"))
        if n <= 0: raise ValueError
    except ValueError:
        print(f"{RED}  Valor inválido.{RESET}"); pausar(); return

    print()
    novos_alertas = 0
    for i in range(1, n + 1):
        t = round(random.uniform(15, 100), 1)
        e = round(random.uniform(5, 100), 1)
        c = random.choice([0, 1, 1, 1])
        l = {
            "timestamp": datetime.now().strftime("%d/%m/%Y %H:%M:%S"),
            "temperatura": t, "energia": e, "comunicacao": c, "origem": "Sensor"
        }
        historico.append(l)
        decisoes = ia_tomada_decisao(l)
        for d in decisoes: log_alertas.append(d)
        novos_alertas += len(decisoes)

        alertas = analisar_alertas(l)
        status = f"{GREEN}OK{RESET}" if not alertas else f"{RED}ALERTA{RESET}"
        ef = calcular_eficiencia_solar(t)
        print(f"  [{i:03d}] {CYAN}{l['timestamp']}{RESET}  "
              f"T:{cor_temp(t)}{t:5.1f}°{RESET}  "
              f"E:{cor_energia(e)}{e:5.1f}%{RESET}  "
              f"Sol:{GREEN if ef>80 else YELLOW}{ef:5.1f}%{RESET}  "
              f"{'✔' if c else '✖'}  {status}")
        time.sleep(0.12)

    print(f"\n{GREEN}  ✔  {n} leitura(s) adicionada(s). {MAGENTA}🤖 {novos_alertas} decisão(ões) da IA registrada(s).{RESET}")
    pausar()

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 6 — LOG DA IA
# ══════════════════════════════════════════════════════════════════════════════
def ver_log_ia():
    cabecalho("Log de Decisões da IA")
    if not log_alertas:
        print(f"{YELLOW}  Nenhuma decisão registrada ainda.{RESET}")
        pausar(); return

    linha()
    print(f"  {MAGENTA}{BOLD}🤖  DECISÕES AUTOMÁTICAS REGISTRADAS{RESET}\n")
    for i, d in enumerate(log_alertas, 1):
        cp = cor_prioridade(d["prioridade"])
        print(f"  {WHITE}[{i:03d}]{RESET} {CYAN}{d['timestamp']}{RESET}  "
              f"{cp}[P{d['prioridade']}] {BOLD}{d['acao']}{RESET}")
        print(f"         {WHITE}{d['descricao']}{RESET}")
    linha()
    # Resumo por ação
    from collections import Counter
    contagem = Counter(d["acao"] for d in log_alertas)
    print(f"  {CYAN}{BOLD}Resumo por tipo:{RESET}")
    for acao, qtd in contagem.most_common():
        print(f"  {WHITE}{acao:<25}{RESET} {YELLOW}{qtd}x{RESET}")
    linha()
    pausar()

# ══════════════════════════════════════════════════════════════════════════════
#  MÓDULO 7 — PAINEL DE ENERGIA RENOVÁVEL
# ══════════════════════════════════════════════════════════════════════════════
def painel_energetico():
    cabecalho("Painel de Energia Renovável — Painéis Solares")
    print(f"{CYAN}{BOLD}  ☀  ANÁLISE DO SISTEMA FOTOVOLTAICO{RESET}\n")
    linha()
    print(f"  {WHITE}Capacidade dos painéis    :{RESET} {GREEN}{POTENCIA_PAINEIS_W} W{RESET}")
    print(f"  {WHITE}Consumo base da nave      :{RESET} {WHITE}{POTENCIA_CONSUMO_W} W{RESET}")
    print(f"  {WHITE}Capacidade da bateria     :{RESET} {CYAN}{CAPACIDADE_BATERIA_WH} Wh{RESET}")
    linha("─", BLUE)
    print(f"\n  {CYAN}Simulação por temperatura:{RESET}\n")
    print(f"  {'Temp (°C)':<12} {'Eficiência':<14} {'Pot. Gerada':<14} {'Saldo':<12} {'Status'}")
    linha("─", BLUE)
    for temp in [15, 25, 40, 60, 75, 85, 95]:
        ef  = calcular_eficiencia_solar(temp)
        pot = calcular_potencia_atual_w(temp)
        sal = pot - POTENCIA_CONSUMO_W
        cor_s = GREEN if sal >= 0 else RED
        sinal = "+" if sal >= 0 else ""
        status = "Carregando" if sal >= 0 else "Descarregando"
        print(f"  {cor_temp(temp)}{temp:<12}{RESET} {GREEN if ef>80 else YELLOW}{ef:<14.1f}{RESET} "
              f"{GREEN}{pot:<14.0f}{RESET} {cor_s}{sinal}{sal:<12.0f}{RESET} {cor_s}{status}{RESET}")
    linha()
    print(f"  {WHITE}Nota:{RESET} Painéis solares perdem 0,4% de eficiência por °C acima de 25°C.")
    print(f"  {WHITE}      Em missão espacial, células fotovoltaicas são a principal fonte{RESET}")
    print(f"  {WHITE}      de energia renovável — sustentando a operação continuamente.{RESET}")
    pausar()

# ══════════════════════════════════════════════════════════════════════════════
#  MENU PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
def menu():
    while True:
        cabecalho()
        total = len(historico)
        decisoes_ia = len(log_alertas)
        print(f"  {WHITE}Leituras: {CYAN}{BOLD}{total}{RESET}   {WHITE}Decisões IA: {MAGENTA}{BOLD}{decisoes_ia}{RESET}\n")
        linha()
        print(f"  {CYAN}[1]{RESET}  📡  Inserir dados manualmente")
        print(f"  {CYAN}[2]{RESET}  📊  Visualizar status atual + energia")
        print(f"  {CYAN}[3]{RESET}  🔬  Análise completa das leituras")
        print(f"  {CYAN}[4]{RESET}  📋  Histórico de leituras")
        print(f"  {CYAN}[5]{RESET}  🤖  Simulação automática de sensores")
        print(f"  {MAGENTA}[6]{RESET}  🧠  Log de decisões da IA")
        print(f"  {GREEN}[7]{RESET}  ☀   Painel de energia renovável")
        print(f"  {RED}[0]{RESET}  🔴  Encerrar sistema")
        linha()

        op = input(f"\n  {WHITE}Selecione: {RESET}").strip()
        if   op == "1": inserir_dados()
        elif op == "2": visualizar_status()
        elif op == "3": executar_analise()
        elif op == "4": ver_historico()
        elif op == "5": simular_sensores()
        elif op == "6": ver_log_ia()
        elif op == "7": painel_energetico()
        elif op == "0":
            cabecalho("Encerrando...")
            print(f"{CYAN}{BOLD}  🚀  Sistema encerrado. Missão finalizada!{RESET}\n")
            break
        else:
            print(f"\n{RED}  Opção inválida.{RESET}")
            time.sleep(1)

# ══════════════════════════════════════════════════════════════════════════════
if __name__ == "__main__":
    menu()
