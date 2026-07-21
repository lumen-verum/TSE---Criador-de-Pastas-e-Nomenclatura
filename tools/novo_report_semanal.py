# -*- coding: utf-8 -*-
"""
TSE Energia e Automação — ferramenta do método (uso interno)
============================================================

novo_report_semanal.py
----------------------

Gera a PRÓXIMA semana do Relatório Semanal TSE a partir do relatório
mais recente encontrado na pasta "8 - Gerenciamento do Projeto\\Semanal".

Convenção do método TSE
~~~~~~~~~~~~~~~~~~~~~~~
* Arquivo: "NNNN-Relatório Semanal-SNN.xlsx" (ex.: 7871-Relatório Semanal-S05.xlsx).
* Novo report = CÓPIA do anterior (preserva formatação e data validations)
  editada via Excel COM (win32com). NUNCA usar openpyxl para editar — ele
  quebra as validações de dados (dropdowns da aba REF).
* Estrutura do arquivo (7 abas):
    - "REF"                        → listas de status para os dropdowns.
    - "Identificação do Projeto"   → rótulos na coluna B, valores na coluna D:
          D7  nº do projeto        D8  nome
          D9  cliente              D10 cidade
          D11 colaboradores        D12 semana de referência "SNN - dd/mm/aaaa"
          D13 status geral         D14 percentual global (0 a 1)
    - "Avanço Por Disciplina"      → cabeçalho na linha 6; dados da linha 7+:
          B=escopo  C=% semana anterior  D=% atual  E==D-C  F=status
    - "Atividades da Semana", "Dificuldades e Bloqueios",
      "Plano da Próxima Semana", "Riscos do Projeto"
                                   → cabeçalho linha 6, dados linha 7+ (col B).

O que o script faz
~~~~~~~~~~~~~~~~~~
1. Localiza na pasta o arquivo com o MAIOR número SNN.
2. Copia para S(N+1) — recusa-se a sobrescrever um S(N+1) já existente.
3. Abre a cópia via Excel COM e atualiza:
   - D12 = "S(N+1) - dd/mm/aaaa" (data via --data, ou a data de hoje);
   - D13 = status geral (se --status for informado);
   - D14 = percentual global 0-1 (se --global-pct for informado; aceita
     "45", "45%" ou "0.45" — valores > 1 são divididos por 100).
4. Com --rolar-avanco: na aba "Avanço Por Disciplina" copia os VALORES da
   coluna D (% atual) para a coluna C (% semana anterior) — as fórmulas da
   coluna E (=D-C) são preservadas.
5. Com --limpar-listas: limpa (ClearContents) as faixas de dados B7:F32 das
   abas de lista ("Atividades da Semana", "Dificuldades e Bloqueios",
   "Plano da Próxima Semana", "Riscos do Projeto").

Exemplos de uso
~~~~~~~~~~~~~~~
    python novo_report_semanal.py --pasta "C:\\...\\8 - Gerenciamento do Projeto\\Semanal"

    python novo_report_semanal.py ^
        --pasta "C:\\...\\Semanal" ^
        --data 24/07/2026 --status "Em andamento" --global-pct 45 ^
        --rolar-avanco --limpar-listas

Requisitos: Windows + Microsoft Excel instalado + pacote pywin32
(pip install pywin32).
"""

import argparse
import os
import re
import shutil
import sys
from datetime import date, datetime

# Console Windows pode quebrar acentos: forca UTF-8 com fallback seguro.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

ABA_IDENTIFICACAO = "Identificação do Projeto"
ABA_AVANCO = "Avanço Por Disciplina"
ABAS_LISTA = [
    "Atividades da Semana",
    "Dificuldades e Bloqueios",
    "Plano da Próxima Semana",
    "Riscos do Projeto",
]
FAIXA_LISTA = "B7:F32"          # faixa de dados das abas de lista
LINHA_INI_AVANCO = 7            # primeira linha de dados do avanco
LINHA_FIM_AVANCO = 32           # ultima linha varrida do avanco

PADRAO_SNN = re.compile(r"[Ss](\d{1,3})(?=\.xlsx$)", re.IGNORECASE)


def falha(msg):
    print("ERRO: " + msg)
    sys.exit(1)


def localizar_ultimo_report(pasta):
    """Retorna (caminho, numero_semana, largura_zeros) do maior SNN da pasta."""
    candidatos = []
    for nome in os.listdir(pasta):
        if nome.lower().endswith(".xlsx") and not nome.startswith("~$"):
            m = PADRAO_SNN.search(nome)
            if m:
                candidatos.append((int(m.group(1)), len(m.group(1)), nome))
    if not candidatos:
        falha("nenhum arquivo '...-SNN.xlsx' encontrado em: " + pasta)
    candidatos.sort()
    num, largura, nome = candidatos[-1]
    return os.path.join(pasta, nome), num, largura


def nome_proxima_semana(caminho_atual, num_atual, largura):
    """Monta o caminho do arquivo S(N+1) mantendo o zero-padding original."""
    pasta, nome = os.path.split(caminho_atual)
    novo_num = num_atual + 1
    novo_tag = "S" + str(novo_num).zfill(max(largura, 2))
    novo_nome = re.sub(r"[Ss]\d{1,3}(?=\.xlsx$)", novo_tag, nome)
    return os.path.join(pasta, novo_nome), novo_num, novo_tag


def normalizar_pct(texto):
    """Aceita '45', '45%', '0.45' ou '0,45' e devolve fracao 0-1."""
    t = texto.strip().replace("%", "").replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        falha("valor de --global-pct invalido: " + texto)
    if v > 1.0:
        v = v / 100.0
    if not (0.0 <= v <= 1.0):
        falha("--global-pct fora da faixa 0-100%: " + texto)
    return v


def validar_data(texto):
    """Valida dd/mm/aaaa e devolve a string normalizada."""
    try:
        d = datetime.strptime(texto.strip(), "%d/%m/%Y")
    except ValueError:
        falha("data invalida (use dd/mm/aaaa): " + texto)
    return d.strftime("%d/%m/%Y")


def atualizar_via_excel(caminho, tag_semana, data_str, status, pct_global,
                        rolar_avanco, limpar_listas):
    try:
        import win32com.client  # noqa: pywin32
    except ImportError:
        falha("pacote pywin32 nao instalado (pip install pywin32).")

    excel = win32com.client.DispatchEx("Excel.Application")
    excel.Visible = False
    excel.DisplayAlerts = False
    wb = None
    try:
        wb = excel.Workbooks.Open(os.path.abspath(caminho))

        # --- Identificacao do Projeto -----------------------------------
        ws_id = wb.Worksheets(ABA_IDENTIFICACAO)
        ws_id.Range("D12").Value = "%s - %s" % (tag_semana, data_str)
        if status is not None:
            ws_id.Range("D13").Value = status
        if pct_global is not None:
            ws_id.Range("D14").Value = pct_global

        # --- Avanco Por Disciplina: rola D (% atual) -> C (% anterior) --
        if rolar_avanco:
            ws_av = wb.Worksheets(ABA_AVANCO)
            for linha in range(LINHA_INI_AVANCO, LINHA_FIM_AVANCO + 1):
                escopo = ws_av.Range("B%d" % linha).Value
                if escopo in (None, ""):
                    continue
                atual = ws_av.Range("D%d" % linha).Value
                ws_av.Range("C%d" % linha).Value = atual
            print("Avanco Por Disciplina: coluna D copiada para C "
                  "(linhas %d-%d)." % (LINHA_INI_AVANCO, LINHA_FIM_AVANCO))

        # --- Abas de lista: limpar faixas -------------------------------
        if limpar_listas:
            for aba in ABAS_LISTA:
                try:
                    ws = wb.Worksheets(aba)
                except Exception:
                    print("AVISO: aba nao encontrada, ignorada: " + aba)
                    continue
                ws.Range(FAIXA_LISTA).ClearContents()
                print("Faixa %s limpa na aba: %s" % (FAIXA_LISTA, aba))

        wb.Save()
    finally:
        if wb is not None:
            wb.Close(SaveChanges=False)
        excel.Quit()


def main():
    ap = argparse.ArgumentParser(
        description="Gera a proxima semana do Relatorio Semanal TSE "
                    "(copia o SNN mais recente para S(N+1) e atualiza via Excel COM).")
    ap.add_argument("--pasta", required=True,
                    help="Pasta 'Semanal' com os arquivos ...-SNN.xlsx")
    ap.add_argument("--data", default=None,
                    help="Data de referencia dd/mm/aaaa (padrao: hoje)")
    ap.add_argument("--status", default=None,
                    help="Status geral do projeto (D13); se omitido, mantem o anterior")
    ap.add_argument("--global-pct", default=None,
                    help="Percentual global (D14): aceita 45, 45%% ou 0.45")
    ap.add_argument("--rolar-avanco", action="store_true",
                    help="Copia %% atual (col D) para %% semana anterior (col C)")
    ap.add_argument("--limpar-listas", action="store_true",
                    help="Limpa B7:F32 das abas de lista (Atividades, Dificuldades, "
                         "Plano, Riscos)")
    args = ap.parse_args()

    pasta = os.path.abspath(args.pasta)
    if not os.path.isdir(pasta):
        falha("pasta nao encontrada: " + pasta)

    data_str = validar_data(args.data) if args.data else date.today().strftime("%d/%m/%Y")
    pct = normalizar_pct(args.global_pct) if args.global_pct is not None else None

    origem, num_atual, largura = localizar_ultimo_report(pasta)
    destino, novo_num, tag = nome_proxima_semana(origem, num_atual, largura)

    print("Report mais recente : " + os.path.basename(origem))
    print("Novo report         : " + os.path.basename(destino))

    if os.path.exists(destino):
        falha("o arquivo da semana %s ja existe — nada foi sobrescrito:\n  %s"
              % (tag, destino))

    shutil.copy2(origem, destino)
    print("Copia criada. Atualizando via Excel COM...")

    try:
        atualizar_via_excel(destino, tag, data_str, args.status, pct,
                            args.rolar_avanco, args.limpar_listas)
    except SystemExit:
        raise
    except Exception as exc:
        print("ERRO ao editar via Excel COM: %s" % exc)
        print("A copia foi mantida em: " + destino)
        sys.exit(1)

    print("OK: %s gerado e atualizado (D12 = '%s - %s')." % (tag, tag, data_str))
    if args.status is not None:
        print("    D13 (status geral) = " + args.status)
    if pct is not None:
        print("    D14 (%% global)    = %.4f" % pct)
    print("Lembrete: %% global = media das disciplinas ativas; confira antes de emitir.")


if __name__ == "__main__":
    main()
