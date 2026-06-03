# 🚀 GS2026 — Sistema de Monitoramento de Missão Espacial

> **Global Solution 2026 — Soluções em Energias Renováveis e Sustentáveis**  
> Curso: Ciência da Computação | Disciplina: Programação Aplicada

---

## 📋 Descrição

Sistema inteligente de monitoramento para missão espacial experimental, desenvolvido em Python.  
Monitora dados operacionais simulados (temperatura, energia, comunicação), aplica conceitos de **energia renovável fotovoltaica** e utiliza **IA introdutória baseada em regras** para tomada de decisão automatizada.

---

## ✅ Funcionalidades

| Módulo | Descrição |
|--------|-----------|
| 📡 Inserir dados | Entrada manual de temperatura, energia e comunicação |
| 📊 Status atual | Painel completo com análise energética em tempo real |
| 🔬 Análise completa | Estatísticas, médias, ocorrências e eficiência solar |
| 📋 Histórico | Tabela de todas as leituras com eficiência dos painéis |
| 🤖 Simulação | Geração automática de dados de sensores |
| 🧠 Log da IA | Registro de todas as decisões automatizadas |
| ☀ Painel Solar | Análise completa do sistema fotovoltaico por temperatura |

---

## ⚡ Conceitos de Energia Aplicados

- **Potência (W):** painéis solares geram 5.000 W; consumo da nave é 3.200 W
- **Energia (Wh):** bateria de 20.000 Wh — calculada proporcionalmente ao nível (%)
- **Eficiência fotovoltaica:** células perdem 0,4% de eficiência por °C acima de 25°C
- **Saldo energético:** diferença entre geração e consumo determina se a bateria carrega ou descarrega
- **Autonomia:** tempo estimado de operação com a energia disponível

---

## 🧠 IA — Tomada de Decisão Baseada em Regras

O sistema possui um motor de regras que avalia cada leitura e dispara ações automáticas:

| Condição | Prioridade | Ação |
|----------|-----------|------|
| Temperatura > 90°C | 🔴 5 | DESLIGAR_AQUECEDORES |
| Temperatura > 80°C | 🔴 4 | ATIVAR_RESFRIAMENTO |
| Energia < 10% | 🔴 5 | MODO_EMERGENCIA |
| Energia < 20% | 🟡 4 | MODO_ECONOMIA |
| Comunicação = 0 | 🟡 4 | REBOOT_ANTENA |
| Saldo energético < -500 W | 🟡 3 | REDUZIR_CONSUMO |
| Bateria > 90% e saldo positivo | 🟢 1 | MODO_NORMAL |

---

## 🛠 Como executar

**Pré-requisito:** Python 3.8 ou superior

```bash
python gs2026_missao_espacial.py
```

Ou no Windows:

```bash
py gs2026_missao_espacial.py
```

Não requer instalação de bibliotecas externas — usa apenas a biblioteca padrão do Python.

---

## 📁 Estrutura do projeto

```
gs2026_missao_espacial.py   # Código-fonte principal
README.md                   # Este arquivo
```

---

## 🔬 Estruturas de dados utilizadas

- **Listas** (`historico`, `log_alertas`) — armazenamento de leituras e decisões
- **Dicionários** — cada leitura e decisão é um dicionário com chaves tipadas
- **Funções** — cada módulo encapsulado em função dedicada
- **Condicionais** — verificação de alertas e tomada de decisão
- **Laços** — menu principal, simulação e exibição do histórico
- **List comprehensions** — cálculo de médias, filtragens e contagens

---

## 👥 Integrantes do grupo

- Rhuan Pacheco Carreri - RM570129
- Fabio Pena Vieira - RM570441


