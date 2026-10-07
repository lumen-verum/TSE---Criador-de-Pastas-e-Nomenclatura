# -*- coding: utf-8 -*-
"""
eplan_extrai_io.py — levanta a configuracao de I/O de um painel a partir do PDF
de fabricacao gerado pelo EPLAN (desenho do fabricante).

Para que serve
--------------
Quando o painel ja foi comprado e fabricado, o quantitativo de hardware tem de
sair do DESENHO DE FABRICACAO, nunca da lista de materiais / exportacao do
configurador: a lista costuma refletir uma alocacao anterior e diverge. Caso
real que motivou esta ferramenta: a lista de materiais dizia 64 cartoes
analogicos e o desenho mostrava 66, com distribuicao diferente entre os paineis
— e a conclusao tirada da lista (faltar cartao numa remota) estava invertida.

O que extrai
------------
Para cada modulo de I/O: rack, slot, codigo do cartao, designacao do modulo
(ex.: -35A01.03) e a regua de bornes de campo (ex.: -44X01.03). Com isso, mais a
tabela terminal x canal do manual do cartao, monta-se o enderecamento fisico.

Como identifica os modulos
--------------------------
Pelo TITULO DA PAGINA do EPLAN, que normalmente tem a forma
    "<algo>_<codigo-do-cartao>_R<rack>S<slot>"
    ex.: "Entradas Digitais_5094-IB16_R01S01"
O titulo e a linha logo apos o campo "data da ultima alteracao" do carimbo.
Use --titulo para ajustar o padrao em outro projeto.

Uso
---
    python eplan_extrai_io.py painel.pdf
    python eplan_extrai_io.py painel.pdf --saida io_painel.csv
    python eplan_extrai_io.py *.pdf --saida config.csv --resumo
    python eplan_extrai_io.py painel.pdf --titulo "IO_(?P<cat>[A-Z0-9-]+)_R(?P<rack>\\d+)S(?P<slot>\\d+)"

Confira SEMPRE o resultado por um segundo caminho: a lista de pecas do painel
traz a quantidade de bornes de campo, e num cartao analogico de RTD a 3/4 fios e
um borne de 4 pontos de conexao POR CANAL — logo "152 bornes" = 19 cartoes de 8
canais. Use --bornes para a ferramenta procurar esse numero e comparar.

Depende de PyMuPDF (fitz).
"""
import argparse, collections, csv, glob, os, re, sys

try:
    import fitz
except ImportError:
    sys.exit("necessario PyMuPDF:  pip install pymupdf")

# padrao do titulo de pagina de modulo de I/O (EPLAN, carimbo em pt-BR)
TITULO = r'(?P<desc>.+?)[ _](?P<cat>[0-9]{3,4}-[A-Z0-9]+)[_ ]R(?P<rack>\d{1,2})S(?P<slot>\d{1,2})'
# marcador do carimbo que antecede o titulo da pagina
MARCA = "LTIMA ALTERA"


def titulo_da_pagina(texto, marca=MARCA):
    ls = [l.strip() for l in texto.split("\n") if l.strip()]
    for j, l in enumerate(ls):
        if marca in l and j + 1 < len(ls):
            return ls[j + 1]
    return ""


def extrai(pdf, pat, marca=MARCA):
    """Devolve {(rack,slot): {...}} para um PDF de painel."""
    d = fitz.open(pdf)
    mods = {}
    for i in range(d.page_count):
        t = d[i].get_text()
        m = re.match(pat, titulo_da_pagina(t, marca))
        if not m:
            continue
        rack, slot = m.group("rack").zfill(2), m.group("slot").zfill(2)
        cat = m.group("cat")
        # designacao do modulo e regua de campo carregam o proprio rack.slot;
        # o prefixo pode passar de 2 digitos (-100X01.11) -> \d{2,3}
        desig = set(re.findall(r'-\d{2,3}A' + rack + r'\.' + slot, t))
        regua = set(re.findall(r'-\d{2,3}X' + rack + r'\.' + slot, t))
        k = (rack, slot)
        if k in mods:
            mods[k]["desig"] |= desig
            mods[k]["regua"] |= regua
            mods[k]["paginas"].append(i + 1)
        else:
            mods[k] = {"cat": cat, "desc": m.group("desc").strip(),
                       "desig": desig, "regua": regua, "paginas": [i + 1]}
    d.close()
    return mods


def bornes_na_lista_de_pecas(pdf, alvo="pontos", pag_lista="totalizad"):
    """
    Procura a quantidade de bornes de campo na LISTA DE PECAS TOTALIZADA.
    So olha as paginas cujo titulo contem `pag_lista` — as paginas de lista
    individualizada repetem o texto e dao falso positivo.
    """
    d = fitz.open(pdf)
    achados = []
    for i in range(d.page_count):
        tit = titulo_da_pagina(d[i].get_text())
        cab = d[i].get_text()[:400].lower()
        if pag_lista not in tit.lower() and pag_lista not in cab:
            continue
        ws = d[i].get_text("words")
        for w in ws:
            if alvo not in w[4].lower():
                continue
            linha = sorted([x for x in ws if abs(x[1] - w[1]) < 6], key=lambda x: x[0])
            txt = " ".join(x[4] for x in linha)
            if "conex" not in txt.lower() and "cone" not in txt.lower():
                continue
            nums = [x[4] for x in linha if re.fullmatch(r'\d+', x[4])]
            achados.append((i + 1, nums[:3], txt[:100]))
    d.close()
    return achados


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", nargs="+", help="PDF(s) do painel (aceita curinga)")
    ap.add_argument("--titulo", default=TITULO,
                    help="regex do titulo de pagina com grupos cat, rack, slot")
    ap.add_argument("--marca", default=MARCA, help="texto do carimbo que antecede o titulo")
    ap.add_argument("--canais", default="5094-IY8=8,5094-IB16=16",
                    help="canais por cartao, ex.: 5094-IY8=8,5094-IB16=16")
    ap.add_argument("--bornes", action="store_true",
                    help="procura a quantidade de bornes de campo na lista de pecas (conferencia)")
    ap.add_argument("--saida", help="arquivo CSV de saida")
    ap.add_argument("--resumo", action="store_true", help="imprime so o resumo por painel")
    a = ap.parse_args()

    canais = {}
    for p in a.canais.split(","):
        if "=" in p:
            k, v = p.split("=")
            canais[k.strip()] = int(v)

    arquivos = []
    for g in a.pdf:
        arquivos += sorted(glob.glob(g)) or [g]

    linhas = []
    for pdf in arquivos:
        nome = os.path.basename(pdf)
        mods = extrai(pdf, a.titulo, a.marca)
        if not mods:
            print(f"{nome}: nenhum modulo reconhecido — ajuste --titulo")
            continue
        tot = collections.Counter()
        for (rack, slot), v in sorted(mods.items()):
            n = canais.get(v["cat"])
            tot[v["cat"]] += 1
            linhas.append({
                "PAINEL": nome, "RACK": rack, "SLOT": slot, "CARTAO": v["cat"],
                "DESIGNACAO": ";".join(sorted(v["desig"])) or "-",
                "REGUA_CAMPO": ";".join(sorted(v["regua"])) or "-",
                "CANAIS": n if n else "", "PAGINAS": ";".join(str(x) for x in v["paginas"]),
                "DESCRICAO": v["desc"],
            })
        canais_tot = sum(canais.get(c, 0) * n for c, n in tot.items())
        print(f"\n{nome}")
        print(f"   modulos: {dict(tot)}  | canais totais: {canais_tot}")
        racks = collections.Counter(r for r, _ in mods)
        print(f"   racks: {dict(racks)}")
        falta = [f"R{r}S{s}" for (r, s), v in mods.items() if not v["desig"] or not v["regua"]]
        if falta:
            print(f"   ATENCAO — sem designacao ou regua: {falta}")
        if not a.resumo:
            for (rack, slot), v in sorted(mods.items()):
                print(f"      R{rack} S{slot}  {v['cat']:<12} "
                      f"{';'.join(sorted(v['desig'])) or '-':<14} "
                      f"regua {';'.join(sorted(v['regua'])) or '-'}")
        if a.bornes:
            ach = bornes_na_lista_de_pecas(pdf)
            if ach:
                print("   bornes de campo na lista de pecas (conferencia):")
                for pg, nums, txt in ach:
                    print(f"      pag {pg}: qtd={nums}  {txt[:70]}")
            else:
                print("   (nao achei linha de borne na lista de pecas)")

    if a.saida and linhas:
        with open(a.saida, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=list(linhas[0].keys()), delimiter=";")
            w.writeheader()
            w.writerows(linhas)
        print(f"\ngravado {a.saida} com {len(linhas)} modulos")


if __name__ == "__main__":
    main()
