# -*- coding: utf-8 -*-
"""
extrai_blocos_dxf.py — Extrai símbolos de uma biblioteca DXF de legenda
e reconstrói blocos "limpos" (achatados, recentrados, opcionalmente com
ATTDEFs e reescala) em um DXF de saída pronto para uso em plantas.

Método TSE (validado em produção — ex.: legenda da Planta de Pontos):
o DXF de legenda vem cheio de blocos ANINHADOS (bloco-casca que só
contém outro INSERT, que contém outro...). Para virar um símbolo útil,
a geometria precisa ser ACHATADA até as entidades primitivas.

GOTCHAS APRENDIDOS (não ignorar):

1. BLOCO ANINHADO / "CASCA": um bloco pode conter apenas um INSERT de
   outro bloco. Achate RECURSIVAMENTE via insert.virtual_entities() —
   ela já devolve as entidades TRANSFORMADAS (posição/rotação/escala
   do INSERT aplicadas). Nunca leia a definição do bloco filho direto,
   senão perde a transformação.

2. RECENTRAGEM: o ponto-base do bloco original costuma ser deslocado do
   centro visual. Recalcule o centro pela BBOX DA GEOMETRIA ACHATADA
   (nunca pela bbox/base do bloco original) e translade tudo para que o
   novo bloco tenha base no centro visual.

3. HATCH: em conversões (e em alguns exploders) o HATCH degrada para
   contorno. Se o símbolo depende de preenchimento sólido, confira o
   resultado no CAD; se degradar, redesenhe o hatch no bloco limpo.

4. VERSÃO DE SAÍDA: salvar como DXF R2013 **ASCII** (padrão do ezdxf).
   Versões novas + binário já inflaram um DXF de 318 MB para 1,17 GB
   em produção. R2013 ASCII é o formato validado.

5. ProElétrica — REGRA DE OURO: este script gera blocos BURROS
   (geometria pura). NUNCA use-o para fabricar/round-tripar bloco
   inteligente do ProElétrica: a inteligência mora em XDATA dentro do
   DWG e só o próprio plugin insere bloco inteligente válido.

Requisitos: pip install ezdxf

Uso:
    python extrai_blocos_dxf.py --lib legenda.dxf --out simbolos_limpos.dxf
    python extrai_blocos_dxf.py --lib legenda.dxf --out simbolos.dxf ^
           --escala 0.5 --attdefs --prefixo TSE_ --blocos SENSOR_TEMP CHAVE_NIVEL
"""

import argparse
import math
import sys

try:
    import ezdxf
    from ezdxf.math import Matrix44
    from ezdxf import bbox as ez_bbox
except ImportError:
    print("ERRO: ezdxf nao instalado. Rode: pip install ezdxf")
    sys.exit(1)


def achatar_recursivo(entidades, saida, profundidade=0, max_prof=16):
    """Achata INSERTs aninhados recursivamente via virtual_entities().

    virtual_entities() devolve copias virtuais ja transformadas para o
    espaco do pai — por isso a recursao preserva posicao/rotacao/escala
    de cada nivel de aninhamento (gotcha 1).
    """
    if profundidade > max_prof:
        return
    for e in entidades:
        tipo = e.dxftype()
        if tipo == "INSERT":
            try:
                achatar_recursivo(e.virtual_entities(), saida,
                                  profundidade + 1, max_prof)
            except Exception as exc:
                print("  aviso: falha ao explodir INSERT aninhado (%s)" % exc)
        elif tipo in ("ATTDEF", "ATTRIB"):
            # Definicoes de atributo do bloco original nao entram na
            # geometria limpa; ATTDEFs novos sao adicionados a parte.
            continue
        else:
            saida.append(e)


def bbox_entidades(entidades):
    """BBox da geometria ACHATADA (gotcha 2) via ezdxf.bbox."""
    cache = ez_bbox.Cache()
    box = ez_bbox.extents(entidades, cache=cache)
    if not box.has_data:
        return None
    return box


def nomes_de_blocos(doc, filtro):
    """Blocos 'de verdade' da biblioteca (ignora layouts e anonimos)."""
    nomes = []
    for b in doc.blocks:
        nome = b.name
        if nome.lower().startswith(("*model_space", "*paper_space")):
            continue
        if nome.startswith("*"):          # anonimos (*D..., *U...)
            continue
        if filtro and nome not in filtro:
            continue
        nomes.append(nome)
    return nomes


def adicionar_attdefs(bloco, meia_altura, escala_texto):
    """ATTDEFs padrao TSE (TAG e ALTURA) abaixo do simbolo."""
    h = max(escala_texto, 1e-6)
    y0 = -(meia_altura + 1.5 * h)
    for i, (tag, prompt_txt) in enumerate((("TAG", "Tag do ponto"),
                                           ("ALTURA", "Altura / nivel"))):
        bloco.add_attdef(
            tag=tag,
            insert=(0.0, y0 - i * 1.4 * h),
            height=h,
            dxfattribs={"prompt": prompt_txt, "layer": "TSE_ATRIBUTOS"},
        )


def extrair(caminho_lib, caminho_out, escala, com_attdefs, prefixo, filtro):
    print("Lendo biblioteca: %s" % caminho_lib)
    origem = ezdxf.readfile(caminho_lib)

    # Saida SEMPRE em R2013 (gotcha 4).
    destino = ezdxf.new("R2013")
    msp = destino.modelspace()

    nomes = nomes_de_blocos(origem, filtro)
    if not nomes:
        print("Nenhum bloco elegivel encontrado na biblioteca.")
        return 0

    print("%d bloco(s) a processar." % len(nomes))
    col, passo, criados = 0, 0.0, 0

    for nome in sorted(nomes):
        bloco_orig = origem.blocks.get(nome)
        planas = []
        achatar_recursivo(iter(bloco_orig), planas)
        if not planas:
            print("- %s: sem geometria util, pulado." % nome)
            continue

        box = bbox_entidades(planas)
        if box is None:
            print("- %s: bbox indisponivel, pulado." % nome)
            continue

        centro = box.center
        largura = (box.extmax.x - box.extmin.x) or 1.0
        altura = (box.extmax.y - box.extmin.y) or 1.0

        # Recentra pela bbox do achatado e aplica reescala (gotcha 2).
        m = Matrix44.translate(-centro.x, -centro.y, -centro.z)
        if escala != 1.0:
            m = m @ Matrix44.scale(escala, escala, escala)

        nome_novo = prefixo + nome
        if nome_novo in destino.blocks:
            print("- %s: destino ja tem %s, pulado." % (nome, nome_novo))
            continue
        bloco_novo = destino.blocks.new(name=nome_novo)

        n_ent = 0
        for e in planas:
            try:
                copia = e.copy()
                copia.transform(m)
                bloco_novo.add_entity(copia)
                n_ent += 1
            except Exception as exc:
                print("  aviso em %s: entidade %s nao copiada (%s)"
                      % (nome, e.dxftype(), exc))

        if n_ent == 0:
            print("- %s: nenhuma entidade copiada, bloco vazio." % nome)
            continue

        if com_attdefs:
            adicionar_attdefs(bloco_novo, (altura * escala) / 2.0,
                              max(largura, altura) * escala * 0.15)

        # Catalogo: uma referencia de cada bloco em grade no modelspace.
        if passo == 0.0:
            passo = max(largura, altura) * escala * 2.5
        pos = (col * passo, 0.0)
        ref = msp.add_blockref(nome_novo, pos)
        if com_attdefs:
            ref.add_auto_attribs({"TAG": nome_novo, "ALTURA": ""})
        col += 1
        criados += 1
        print("- %s -> %s (%d entidades)" % (nome, nome_novo, n_ent))

    destino.saveas(caminho_out)   # R2013 ASCII (gotcha 4)
    print("OK: %d bloco(s) limpos gravados em %s" % (criados, caminho_out))
    return criados


def main():
    ap = argparse.ArgumentParser(
        description="Extrai simbolos de biblioteca DXF de legenda: achata "
                    "blocos aninhados, recentra pela bbox e reconstroi "
                    "blocos limpos (saida R2013 ASCII).")
    ap.add_argument("--lib", required=True, help="DXF da biblioteca/legenda")
    ap.add_argument("--out", required=True, help="DXF de saida (R2013)")
    ap.add_argument("--escala", type=float, default=1.0,
                    help="fator de reescala dos simbolos (default 1.0)")
    ap.add_argument("--attdefs", action="store_true",
                    help="adiciona ATTDEFs TAG/ALTURA a cada bloco limpo")
    ap.add_argument("--prefixo", default="TSE_",
                    help="prefixo dos blocos limpos (default TSE_)")
    ap.add_argument("--blocos", nargs="*", default=None,
                    help="nomes especificos a extrair (default: todos)")
    args = ap.parse_args()

    if args.escala <= 0 or not math.isfinite(args.escala):
        ap.error("--escala deve ser um numero positivo")

    filtro = set(args.blocos) if args.blocos else None
    extrair(args.lib, args.out, args.escala, args.attdefs,
            args.prefixo, filtro)


if __name__ == "__main__":
    main()
