# -*- coding: utf-8 -*-
"""
pid_extrai_tags.py — extrai as tags dos baloes de instrumento de um P&ID em PDF
cujo texto foi VETORIZADO (convertido em curvas), sem OCR.

Problema que resolve
--------------------
E comum o P&ID chegar como PDF 100% vetorial em que apenas os rotulos de
equipamento e as notas estao no text layer; o texto dentro dos baloes de
instrumento virou curva e `get_text()` nao devolve nada. Contar a mao 400+
baloes e lento e sujeito a erro.

Como funciona
-------------
1. Acha os baloes pela geometria (paths de bbox quase-quadrada e diametro
   constante, parametro --diam).
2. Acha os glifos: paths pequenos de altura constante contidos no balao.
   ATENCAO: digitos e letras tipo S/L/M costumam ser contornos preenchidos,
   mas o 'T' pode ser desenhado como DOIS tracos de espessura zero (barra
   horizontal + haste vertical) — por isso ha deteccao separada para eles.
3. Agrupa os glifos em linhas por 'y' e ordena por 'x'.
4. Assinatura = rasterizacao da GEOMETRIA do path (nao da pagina), normalizada
   pela bbox do glifo, com supersampling.
5. Agrupa as assinaturas por distancia de Hamming.
6. Emite uma folha de contato (PDF/PNG) com uma amostra REAL de cada grupo
   para o usuario identificar o caractere olhando, e salva um JSON de rotulos.
7. Na segunda passada, com o JSON de rotulos preenchido, decodifica tudo.

Uso
---
    # passo 1: gera a folha de contato e o esqueleto de rotulos
    python pid_extrai_tags.py "P&ID.pdf" --paginas 1-3 --amostras

    # passo 2: abrir amostras_glifos.png, preencher rotulos.json e decodificar
    python pid_extrai_tags.py "P&ID.pdf" --paginas 1-3 --rotulos rotulos.json \
        --saida tags.csv

Opcoes uteis
------------
    --diam 19.3       diametro do balao em pontos (medir no desenho)
    --altura 3.6      altura do glifo em pontos
    --limiar 14       bits de diferenca para unir duas assinaturas
    --nuvem "0,0.72,0"  cor RGB da nuvem de revisao; marca os baloes contidos
                        nela na coluna EM_NUVEM (separa escopo novo x existente)

Depende de PyMuPDF (fitz).
"""
import argparse, collections, csv, json, os, sys

try:
    import fitz
except ImportError:
    sys.exit("necessario PyMuPDF:  pip install pymupdf")

SS = 4            # supersampling da assinatura
GW, GH = 10, 14   # grade da assinatura


# --------------------------------------------------------------------------- geometria
def pontos_do_item(item):
    out = []
    for el in item[1:]:
        if hasattr(el, "x"):
            out.append((el.x, el.y))
        elif isinstance(el, fitz.Rect):
            out += [(el.x0, el.y0), (el.x1, el.y1)]
    return out


def segmentos(path):
    """Segmentos (x0,y0,x1,y1) do path, amostrando as bezier."""
    segs = []
    for it in path["items"]:
        k = it[0]
        if k == "l":
            a, b = it[1], it[2]
            segs.append((a.x, a.y, b.x, b.y))
        elif k == "c":
            p0, p1, p2, p3 = it[1], it[2], it[3], it[4]
            ant = (p0.x, p0.y)
            for i in range(1, 9):
                t = i / 8.0
                m = 1 - t
                x = m**3 * p0.x + 3*m*m*t * p1.x + 3*m*t*t * p2.x + t**3 * p3.x
                y = m**3 * p0.y + 3*m*m*t * p1.y + 3*m*t*t * p2.y + t**3 * p3.y
                segs.append((ant[0], ant[1], x, y))
                ant = (x, y)
        elif k == "re":
            r = it[1]
            segs += [(r.x0, r.y0, r.x1, r.y0), (r.x1, r.y0, r.x1, r.y1),
                     (r.x1, r.y1, r.x0, r.y1), (r.x0, r.y1, r.x0, r.y0)]
        elif k == "qu":
            q = it[1]
            pts = [q.ul, q.ur, q.lr, q.ll]
            for i in range(4):
                a, b = pts[i], pts[(i + 1) % 4]
                segs.append((a.x, a.y, b.x, b.y))
    return segs


def assinatura(path):
    r = path["rect"]
    w = max(r.width, 1e-6); h = max(r.height, 1e-6)
    HWi, HHi = GW * SS, GH * SS
    hi = [[0] * HWi for _ in range(HHi)]
    for (x0, y0, x1, y1) in segmentos(path):
        dx = abs(x1 - x0) / w * HWi
        dy = abs(y1 - y0) / h * HHi
        n = max(2, int(max(dx, dy) * 2) + 1)
        for i in range(n + 1):
            t = i / n
            gx = int(((x0 + (x1 - x0) * t) - r.x0) / w * (HWi - 1) + 0.5)
            gy = int(((y0 + (y1 - y0) * t) - r.y0) / h * (HHi - 1) + 0.5)
            if 0 <= gx < HWi and 0 <= gy < HHi:
                hi[gy][gx] = 1
    bits = []
    for gy in range(GH):
        for gx in range(GW):
            s = sum(hi[yy][xx]
                    for yy in range(gy * SS, (gy + 1) * SS)
                    for xx in range(gx * SS, (gx + 1) * SS))
            bits.append("1" if s >= 2 else "0")
    return "".join(bits)


def hamming(a, b):
    return sum(1 for i in range(len(a)) if a[i] != b[i])


# --------------------------------------------------------------------------- coleta
def coleta_pagina(page, diam, altura, tol=0.9):
    dr = page.get_drawings()
    bal = []
    for it in dr:
        r = it["rect"]
        w, h = r.width, r.height
        if w > 0 and h > 0 and abs(w - h) / max(w, h) < 0.12 and abs(w - diam) < tol:
            bal.append(r)
    uq = []
    for r in bal:
        if not any(abs(r.x0 - u.x0) < 3 and abs(r.y0 - u.y0) < 3 for u in uq):
            uq.append(r)
    cheios = [it for it in dr
              if 0.4 < it["rect"].width < altura * 0.95
              and altura * 0.82 < it["rect"].height < altura * 1.2]
    hastes = [it for it in dr
              if it["rect"].width < 0.35 and altura * 0.88 < it["rect"].height < altura * 1.12]
    barras = [it for it in dr
              if it["rect"].height < 0.35 and 1.5 < it["rect"].width < altura * 0.95]
    return uq, cheios, hastes, barras, dr


def dentro(b, r, m=1.0):
    return b.x0 - m < r.x0 and r.x1 < b.x1 + m and b.y0 - m < r.y0 and r.y1 < b.y1 + m


def nuvens_da_pagina(dr, cor, dilat=3.0):
    """Une os tracos da cor dada em regioes (nuvem de revisao e feita de arcos)."""
    alvo = [fitz.Rect(it["rect"]) for it in dr if it.get("color") == cor]
    grupos = []
    for r in alvo:
        exp = fitz.Rect(r.x0 - dilat, r.y0 - dilat, r.x1 + dilat, r.y1 + dilat)
        posto = False
        for i, g in enumerate(grupos):
            if g.intersects(exp):
                grupos[i] = g | r; posto = True; break
        if not posto:
            grupos.append(fitz.Rect(r))
    mudou = True
    while mudou:
        mudou = False
        for i in range(len(grupos)):
            for j in range(i + 1, len(grupos)):
                a = fitz.Rect(grupos[i])
                a.x0 -= dilat; a.y0 -= dilat; a.x1 += dilat; a.y1 += dilat
                if a.intersects(grupos[j]):
                    grupos[i] = grupos[i] | grupos[j]; del grupos[j]
                    mudou = True; break
            if mudou:
                break
    return [g for g in grupos if g.width > 12 and g.height > 12]


# --------------------------------------------------------------------------- principal
def faixa(txt):
    out = []
    for p in txt.split(","):
        if "-" in p:
            a, b = p.split("-"); out += list(range(int(a), int(b) + 1))
        else:
            out.append(int(p))
    return [n - 1 for n in out]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf")
    ap.add_argument("--paginas", default="1", help="ex.: 1-3 ou 1,2,5 (base 1)")
    ap.add_argument("--diam", type=float, default=19.3, help="diametro do balao (pt)")
    ap.add_argument("--altura", type=float, default=3.6, help="altura do glifo (pt)")
    ap.add_argument("--limiar", type=int, default=14, help="bits p/ unir assinaturas")
    ap.add_argument("--amostras", action="store_true",
                    help="gera a folha de contato e o esqueleto de rotulos e sai")
    ap.add_argument("--rotulos", help="JSON {indice_do_grupo: caractere}")
    ap.add_argument("--nuvem", help='cor RGB da nuvem, ex.: "0,0.72,0"')
    ap.add_argument("--saida", default="tags_pid.csv")
    a = ap.parse_args()

    cor_nuvem = None
    if a.nuvem:
        cor_nuvem = tuple(float(x) for x in a.nuvem.split(","))

    doc = fitz.open(a.pdf)
    pgs = [p for p in faixa(a.paginas) if 0 <= p < doc.page_count]
    registros = []   # (pg, rect_balao, [[ (sig|char, x) ]], em_nuvem)

    for pg in pgs:
        page = doc[pg]
        baloes, cheios, hastes, barras, dr = coleta_pagina(page, a.diam, a.altura)
        nuv = nuvens_da_pagina(dr, cor_nuvem) if cor_nuvem else []
        for b in baloes:
            elems = []
            for g in cheios:
                if dentro(b, g["rect"]):
                    elems.append({"x": g["rect"].x0, "y": g["rect"].y0,
                                  "sig": assinatura(g), "rect": g["rect"]})
            hs = [h for h in hastes if dentro(b, h["rect"])]
            bs = [h for h in barras if dentro(b, h["rect"])]
            for h in hs:
                rh = h["rect"]
                tem = any(abs(rb["rect"].y0 - rh.y0) < 0.6 and
                          rb["rect"].x0 - 0.8 <= rh.x0 <= rb["rect"].x1 + 0.8 for rb in bs)
                elems.append({"x": rh.x0 - (1.0 if tem else 0.0), "y": rh.y0,
                              "sig": "T" if tem else "I", "rect": rh, "fixo": True})
            if not elems:
                continue
            centro = fitz.Point((b.x0 + b.x1) / 2, (b.y0 + b.y1) / 2)
            registros.append({"pg": pg + 1, "bbox": b, "elems": elems,
                              "nuvem": any(n.contains(centro) for n in nuv)})
    print(f"baloes com texto: {len(registros)}")

    # agrupamento das assinaturas (ignora os glifos fixos T/I)
    cont = collections.Counter(e["sig"] for r in registros for e in r["elems"]
                               if not e.get("fixo"))
    centros, mapa = [], {}
    for sig, _ in cont.most_common():
        achou = None
        for c in centros:
            if hamming(sig, c) <= a.limiar:
                achou = c; break
        if achou is None:
            centros.append(sig); mapa[sig] = sig
        else:
            mapa[sig] = achou
    peso = collections.Counter()
    for s, n in cont.items():
        peso[mapa[s]] += n
    centros.sort(key=lambda c: -peso[c])
    idx = {c: i for i, c in enumerate(centros)}
    print(f"grupos de glifo: {len(centros)}")

    if a.amostras:
        amostra = {}
        for r in registros:
            for e in r["elems"]:
                if e.get("fixo"):
                    continue
                g = idx[mapa[e["sig"]]]
                amostra.setdefault(g, (r["pg"] - 1, e["rect"]))
        cols = 6
        rows = (len(centros) + cols - 1) // cols
        CW, CH = 120, 160
        out = fitz.open()
        pg = out.new_page(width=cols * CW, height=rows * CH)
        for i in range(len(centros)):
            p0, rr = amostra[i]
            src = fitz.Rect(rr.x0 - 0.5, rr.y0 - 0.5, rr.x1 + 0.5, rr.y1 + 0.5)
            cx, cy = (i % cols) * CW, (i // cols) * CH
            dest = fitz.Rect(cx + 28, cy + 36, cx + CW - 28, cy + CH - 20)
            pg.show_pdf_page(dest, doc, p0, clip=src)
            pg.draw_rect(dest, color=(0.75, 0.75, 0.75), width=0.4)
            pg.insert_text((cx + 6, cy + 22), f"[{i}] n={peso[centros[i]]}", fontsize=10)
        out.save("amostras_glifos.pdf")
        out[0].get_pixmap(dpi=140).save("amostras_glifos.png")
        out.close()
        json.dump({str(i): "?" for i in range(len(centros))},
                  open("rotulos.json", "w"), indent=1)
        print("gerados amostras_glifos.png e rotulos.json — "
              "identifique cada grupo e preencha rotulos.json")
        return

    if not a.rotulos:
        sys.exit("informe --rotulos rotulos.json (gere antes com --amostras)")
    rot = {int(k): v for k, v in json.load(open(a.rotulos, encoding="utf-8")).items()}

    linhas_csv = []
    for r in registros:
        linhas = []
        for e in sorted(r["elems"], key=lambda e: (e["y"], e["x"])):
            posto = False
            for ln in linhas:
                if abs(ln[0]["y"] - e["y"]) < 1.5:
                    ln.append(e); posto = True; break
            if not posto:
                linhas.append([e])
        linhas.sort(key=lambda ln: ln[0]["y"])
        txt = []
        for ln in linhas:
            txt.append("".join(
                e["sig"] if e.get("fixo") else rot.get(idx[mapa[e["sig"]]], "?")
                for e in sorted(ln, key=lambda e: e["x"])))
        linhas_csv.append({
            "TAG": "-".join(txt), "LINHAS": " | ".join(txt),
            "TIPO": txt[0] if len(txt) >= 3 else "",
            "FOLHA": r["pg"], "X": round(r["bbox"].x0, 1), "Y": round(r["bbox"].y0, 1),
            "EM_NUVEM": "SIM" if r["nuvem"] else "NAO",
        })
    with open(a.saida, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=list(linhas_csv[0].keys()), delimiter=";")
        w.writeheader()
        w.writerows(linhas_csv)
    print(f"gravado {a.saida} com {len(linhas_csv)} baloes")
    tipos = collections.Counter(l["TIPO"] for l in linhas_csv)
    print("tipos:", dict(tipos.most_common(12)))
    if cor_nuvem:
        n = sum(1 for l in linhas_csv if l["EM_NUVEM"] == "SIM")
        print(f"dentro da nuvem: {n} | fora: {len(linhas_csv)-n}")
    doc.close()


if __name__ == "__main__":
    main()
