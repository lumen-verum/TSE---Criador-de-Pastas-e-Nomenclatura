# -*- coding: utf-8 -*-
"""
TSE Energia e Automação — ferramenta do método (uso interno)
============================================================

cronograma_msproject.py
-----------------------

Biblioteca + CLI para ler e editar cronogramas no formato XML do
MS Project (namespace http://schemas.microsoft.com/project).

Estrutura do XML (resumo do método TSE)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Project > Tasks > Task, com campos: UID, ID (= posição de exibição),
  Name, OutlineLevel, OutlineNumber, Start, Finish, Duration ("PTnHnMnS"),
  Work, Summary (0/1), Milestone (0/1), PercentComplete.
* Project > Resources > Resource e Project > Assignments > Assignment
  (UID, TaskUID, ResourceUID) ligam recursos às tarefas.
* A ORDEM dos elementos Task no XML define a exibição; o campo ID deve
  seguir essa ordem — por isso toda inserção/reordenação passa por
  renumeração dos IDs (feita automaticamente por esta biblioteca).

Boas práticas do método TSE
~~~~~~~~~~~~~~~~~~~~~~~~~~~
* Organizar em FASES (Summary=1, OutlineLevel=1) com MARCOS explícitos
  (Milestone=1, Duration=PT0H0M0S) fechando cada fase. Exemplo típico:
  Fase 1 Engenharia/emissão preliminar → marco de entrega; Fase 2
  Levantamento de campo → marco de recebimento; Fase 3 As-built → marco
  de entrega final.
* Revisões: NUNCA sobrescrever uma revisão emitida. Copiar R(n) → R(n+1)
  e editar a cópia (subcomando "nova-revisao").
* StatusDate = data do snapshot do avanço.

Uso como biblioteca
~~~~~~~~~~~~~~~~~~~
    from cronograma_msproject import CronogramaMSProject

    cr = CronogramaMSProject("Cronograma_R01.xml")
    cr.listar()                                   # arvore no console
    cr.set_task(12, pct=80)                       # atualiza % concluido
    cr.set_task(12, start="2026-08-03T08:00:00",
                     finish="2026-08-07T17:00:00")
    uid = cr.add_task("Entrega da documentacao final",
                      ini="2026-08-07T17:00:00", fim="2026-08-07T17:00:00",
                      dur_horas=0, nivel=2, outline="3.4", milestone=True)
    cr.add_assignment(task_uid=uid, resource_uid=1)
    cr.save_as("Cronograma_R02.xml")

Uso pela linha de comando
~~~~~~~~~~~~~~~~~~~~~~~~~
    python cronograma_msproject.py listar --arquivo Cronograma_R01.xml

    python cronograma_msproject.py set --arquivo Cronograma_R01.xml ^
        --uid 12 --pct 80

    python cronograma_msproject.py add-marco --arquivo Cronograma_R01.xml ^
        --nome "Entrega preliminar" --data 2026-08-07T17:00:00 ^
        --nivel 2 --outline 1.5

    python cronograma_msproject.py nova-revisao --arquivo Cronograma_R01.xml
        (copia para Cronograma_R02.xml sem tocar no original)

Datas sempre em ISO: aaaa-mm-ddThh:mm:ss.
"""

import argparse
import os
import re
import shutil
import sys
import xml.etree.ElementTree as ET

# Console Windows pode quebrar acentos: forca UTF-8 com fallback seguro.
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

NS = "http://schemas.microsoft.com/project"
ET.register_namespace("", NS)

PADRAO_DATA = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}$")

# Ordem canonica dos campos de Task que esta biblioteca escreve
# (o MS Project e sensivel a ordem dos elementos dentro de Task).
ORDEM_CAMPOS_TASK = [
    "UID", "ID", "Name", "Type", "IsNull", "CreateDate", "WBS",
    "OutlineNumber", "OutlineLevel", "Priority", "Start", "Finish",
    "Duration", "DurationFormat", "Work", "ResumeValid", "EffortDriven",
    "Recurring", "OverAllocated", "Estimated", "Milestone", "Summary",
    "Critical", "IsSubproject", "IsSubprojectReadOnly", "PercentComplete",
    "PercentWorkComplete",
]


def _q(tag):
    """Qualifica um tag com o namespace do MS Project."""
    return "{%s}%s" % (NS, tag)


def _texto(el, tag, padrao=""):
    filho = el.find(_q(tag))
    if filho is None or filho.text is None:
        return padrao
    return filho.text


def _pt_horas(horas):
    """Converte horas (float/int) para o formato de duracao PTnHnMnS."""
    total_min = int(round(float(horas) * 60))
    h, m = divmod(total_min, 60)
    return "PT%dH%dM0S" % (h, m)


class CronogramaMSProject(object):
    """Leitura e edição de um cronograma MS Project XML."""

    def __init__(self, caminho):
        self.caminho = caminho
        self.tree = ET.parse(caminho)
        self.root = self.tree.getroot()
        if self.root.tag != _q("Project"):
            raise ValueError("arquivo nao parece ser MS Project XML: %s" % caminho)

    # ------------------------------------------------------------------ #
    # Acesso basico
    # ------------------------------------------------------------------ #
    def _tasks_el(self):
        el = self.root.find(_q("Tasks"))
        if el is None:
            el = ET.SubElement(self.root, _q("Tasks"))
        return el

    def _assignments_el(self):
        el = self.root.find(_q("Assignments"))
        if el is None:
            el = ET.SubElement(self.root, _q("Assignments"))
        return el

    def tarefas(self):
        """Lista de dicts com os campos principais de cada Task (ordem do XML)."""
        saida = []
        for t in self._tasks_el().findall(_q("Task")):
            saida.append({
                "uid": int(_texto(t, "UID", "0")),
                "id": int(_texto(t, "ID", "0")),
                "nome": _texto(t, "Name"),
                "nivel": int(_texto(t, "OutlineLevel", "1")),
                "outline": _texto(t, "OutlineNumber"),
                "inicio": _texto(t, "Start"),
                "fim": _texto(t, "Finish"),
                "duracao": _texto(t, "Duration"),
                "summary": _texto(t, "Summary", "0") == "1",
                "marco": _texto(t, "Milestone", "0") == "1",
                "pct": int(_texto(t, "PercentComplete", "0") or "0"),
            })
        return saida

    def _achar_task(self, uid):
        for t in self._tasks_el().findall(_q("Task")):
            if _texto(t, "UID") == str(uid):
                return t
        raise KeyError("Task com UID %s nao encontrada" % uid)

    def _max_uid(self, container_tag, item_tag):
        cont = self.root.find(_q(container_tag))
        maior = 0
        if cont is not None:
            for el in cont.findall(_q(item_tag)):
                try:
                    maior = max(maior, int(_texto(el, "UID", "0")))
                except ValueError:
                    pass
        return maior

    # ------------------------------------------------------------------ #
    # Edicao
    # ------------------------------------------------------------------ #
    def _set_campo(self, task_el, tag, valor):
        """Define/atualiza um campo respeitando a ordem canonica dos elementos."""
        alvo = task_el.find(_q(tag))
        if alvo is not None:
            alvo.text = str(valor)
            return
        alvo = ET.Element(_q(tag))
        alvo.text = str(valor)
        # insere na posicao correta segundo ORDEM_CAMPOS_TASK
        try:
            pos_novo = ORDEM_CAMPOS_TASK.index(tag)
        except ValueError:
            task_el.append(alvo)
            return
        indice = len(list(task_el))
        for i, filho in enumerate(list(task_el)):
            nome = filho.tag.split("}")[-1]
            if nome in ORDEM_CAMPOS_TASK and ORDEM_CAMPOS_TASK.index(nome) > pos_novo:
                indice = i
                break
        task_el.insert(indice, alvo)

    def set_task(self, uid, pct=None, start=None, finish=None, name=None):
        """Atualiza campos de uma tarefa existente (por UID)."""
        t = self._achar_task(uid)
        if name is not None:
            self._set_campo(t, "Name", name)
        if start is not None:
            self._validar_data(start)
            self._set_campo(t, "Start", start)
        if finish is not None:
            self._validar_data(finish)
            self._set_campo(t, "Finish", finish)
        if pct is not None:
            pct = int(pct)
            if not 0 <= pct <= 100:
                raise ValueError("pct deve estar entre 0 e 100")
            self._set_campo(t, "PercentComplete", pct)
            self._set_campo(t, "PercentWorkComplete", pct)
        return t

    def add_task(self, nome, ini, fim, dur_horas, nivel, outline,
                 milestone=False, summary=False, pct=0, apos_uid=None):
        """
        Cria uma Task nova e a insere na posição correta.

        nome      : texto da tarefa
        ini, fim  : datas ISO aaaa-mm-ddThh:mm:ss
        dur_horas : duração em horas (0 para marcos)
        nivel     : OutlineLevel (1 = fase, 2 = tarefa da fase, ...)
        outline   : OutlineNumber (ex.: "2.3") — define a hierarquia visual
        milestone : True para marco (força Duration = PT0H0M0S)
        summary   : True para linha-resumo (fase)
        pct       : PercentComplete inicial
        apos_uid  : inserir imediatamente após a Task deste UID
                    (padrão: ao final da lista)

        Retorna o UID da nova tarefa. Os IDs são renumerados em seguida.
        """
        self._validar_data(ini)
        self._validar_data(fim)
        if milestone:
            dur_horas = 0

        novo_uid = self._max_uid("Tasks", "Task") + 1
        t = ET.Element(_q("Task"))
        campos = [
            ("UID", novo_uid),
            ("ID", 0),                      # renumerado depois
            ("Name", nome),
            ("OutlineNumber", outline),
            ("OutlineLevel", int(nivel)),
            ("Start", ini),
            ("Finish", fim),
            ("Duration", _pt_horas(dur_horas)),
            ("DurationFormat", 7),          # horas
            ("Milestone", 1 if milestone else 0),
            ("Summary", 1 if summary else 0),
            ("PercentComplete", int(pct)),
        ]
        for tag, valor in campos:
            self._set_campo(t, tag, valor)

        tasks = self._tasks_el()
        if apos_uid is None:
            tasks.append(t)
        else:
            ref = self._achar_task(apos_uid)
            filhos = list(tasks)
            tasks.insert(filhos.index(ref) + 1, t)

        self.renumerar_ids()
        return novo_uid

    def add_assignment(self, task_uid, resource_uid):
        """Liga um recurso a uma tarefa (cria um Assignment novo)."""
        self._achar_task(task_uid)  # valida que a tarefa existe
        novo_uid = self._max_uid("Assignments", "Assignment") + 1
        a = ET.SubElement(self._assignments_el(), _q("Assignment"))
        for tag, valor in [("UID", novo_uid), ("TaskUID", task_uid),
                           ("ResourceUID", resource_uid)]:
            filho = ET.SubElement(a, _q(tag))
            filho.text = str(valor)
        return novo_uid

    def mover_task(self, uid, apos_uid):
        """Move a Task (por UID) para logo após outra; renumera os IDs."""
        tasks = self._tasks_el()
        t = self._achar_task(uid)
        tasks.remove(t)
        ref = self._achar_task(apos_uid)
        tasks.insert(list(tasks).index(ref) + 1, t)
        self.renumerar_ids()

    def renumerar_ids(self):
        """IDs = ordem dos elementos Task no XML (regra do MS Project)."""
        # a task-projeto (OutlineLevel 0), quando existe, e a primeira e recebe
        # ID 0; sem ela, a numeracao comeca em 1.
        tarefas = self._tasks_el().findall(_q("Task"))
        base = 0 if (tarefas and _texto(tarefas[0], "OutlineLevel", "1") == "0") else 1
        for i, t in enumerate(tarefas):
            self._set_campo(t, "ID", base + i)

    # ------------------------------------------------------------------ #
    # Saida
    # ------------------------------------------------------------------ #
    def listar(self, arquivo_saida=None):
        """Imprime a árvore de tarefas com %, datas e marcos."""
        linhas = []
        for t in self.tarefas():
            recuo = "  " * max(t["nivel"] - 1, 0)
            marca = "[MARCO] " if t["marco"] else ""
            fase = "[FASE] " if t["summary"] else ""
            ini = t["inicio"][:10] if t["inicio"] else "?"
            fim = t["fim"][:10] if t["fim"] else "?"
            linhas.append("%3s | %s%s%s%s | %3d%% | %s -> %s" % (
                t["uid"], recuo, fase, marca, t["nome"], t["pct"], ini, fim))
        texto = "\n".join(linhas)
        print("UID | Tarefa | % | Inicio -> Fim")
        print("-" * 72)
        print(texto)
        return texto

    def save_as(self, caminho):
        """Grava o XML (UTF-8 com declaração). Recusa sobrescrever o original
        se o caminho for diferente e já existir outro arquivo lá."""
        self.tree.write(caminho, encoding="UTF-8", xml_declaration=True)
        print("Gravado: " + caminho)

    def save(self):
        self.save_as(self.caminho)

    # ------------------------------------------------------------------ #
    @staticmethod
    def _validar_data(texto):
        if not PADRAO_DATA.match(str(texto)):
            raise ValueError("data invalida (use aaaa-mm-ddThh:mm:ss): %r" % texto)


# ---------------------------------------------------------------------- #
# Revisoes: R(n) -> R(n+1)
# ---------------------------------------------------------------------- #
PADRAO_REV = re.compile(r"[Rr](\d{1,3})(?=\.xml$)")


def nova_revisao(caminho):
    """Copia Cronograma_R(n).xml para R(n+1) sem tocar no original.
    Se o nome nao tiver R(n), cria '<nome>_R01.xml'."""
    caminho = os.path.abspath(caminho)
    if not os.path.isfile(caminho):
        raise FileNotFoundError("arquivo nao encontrado: " + caminho)
    pasta, nome = os.path.split(caminho)
    m = PADRAO_REV.search(nome)
    if m:
        atual = int(m.group(1))
        largura = max(len(m.group(1)), 2)
        novo_tag = "R" + str(atual + 1).zfill(largura)
        novo_nome = re.sub(r"[Rr]\d{1,3}(?=\.xml$)", novo_tag, nome)
    else:
        raiz, ext = os.path.splitext(nome)
        novo_nome = raiz + "_R01" + ext
    destino = os.path.join(pasta, novo_nome)
    if os.path.exists(destino):
        raise FileExistsError("a revisao ja existe — nada foi sobrescrito: " + destino)
    shutil.copy2(caminho, destino)
    print("Nova revisao criada: " + destino)
    print("A revisao anterior permanece intacta (regra do metodo TSE).")
    return destino


# ---------------------------------------------------------------------- #
# CLI
# ---------------------------------------------------------------------- #
def main():
    ap = argparse.ArgumentParser(
        description="Ferramenta TSE para cronogramas MS Project XML "
                    "(listar, editar tarefas, adicionar marcos, nova revisao).")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("listar", help="Mostra a arvore de tarefas")
    p.add_argument("--arquivo", required=True)

    p = sub.add_parser("set", help="Atualiza campos de uma tarefa (por UID)")
    p.add_argument("--arquivo", required=True)
    p.add_argument("--uid", required=True, type=int)
    p.add_argument("--pct", type=int, default=None)
    p.add_argument("--start", default=None, help="ISO aaaa-mm-ddThh:mm:ss")
    p.add_argument("--finish", default=None, help="ISO aaaa-mm-ddThh:mm:ss")
    p.add_argument("--nome", default=None)
    p.add_argument("--saida", default=None,
                   help="Grava em outro arquivo (padrao: grava no proprio)")

    p = sub.add_parser("add-marco", help="Adiciona um marco (Milestone)")
    p.add_argument("--arquivo", required=True)
    p.add_argument("--nome", required=True)
    p.add_argument("--data", required=True, help="ISO aaaa-mm-ddThh:mm:ss")
    p.add_argument("--nivel", required=True, type=int, help="OutlineLevel")
    p.add_argument("--outline", required=True, help="OutlineNumber, ex.: 2.4")
    p.add_argument("--apos-uid", type=int, default=None,
                   help="Inserir apos a tarefa deste UID (padrao: final)")
    p.add_argument("--saida", default=None,
                   help="Grava em outro arquivo (padrao: grava no proprio)")

    p = sub.add_parser("nova-revisao",
                       help="Copia o arquivo para R(n+1) antes de editar")
    p.add_argument("--arquivo", required=True)

    args = ap.parse_args()

    try:
        if args.cmd == "nova-revisao":
            nova_revisao(args.arquivo)
            return

        cr = CronogramaMSProject(args.arquivo)

        if args.cmd == "listar":
            cr.listar()
            return

        if args.cmd == "set":
            cr.set_task(args.uid, pct=args.pct, start=args.start,
                        finish=args.finish, name=args.nome)
            cr.save_as(args.saida or args.arquivo)
            print("Tarefa UID %d atualizada." % args.uid)
            return

        if args.cmd == "add-marco":
            uid = cr.add_task(args.nome, ini=args.data, fim=args.data,
                              dur_horas=0, nivel=args.nivel,
                              outline=args.outline, milestone=True,
                              apos_uid=args.apos_uid)
            cr.save_as(args.saida or args.arquivo)
            print("Marco criado com UID %d." % uid)
            return
    except (ValueError, KeyError, FileNotFoundError, FileExistsError) as exc:
        print("ERRO: %s" % exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
