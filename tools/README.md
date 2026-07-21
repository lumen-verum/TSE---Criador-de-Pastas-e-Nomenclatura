# tools/ — Ferramentas do método TSE

Ferramentas genéricas de automação de projeto (CAD + gestão), validadas em projeto real. Nenhuma contém dados de cliente: tudo é template/exemplo.

## Requisitos gerais

| Ferramenta | Requisitos |
|---|---|
| `tse_lanca_blocos.lsp` | AutoCAD completo (com o plugin do símbolo já carregado, ex.: ProElétrica) |
| `extrai_blocos_dxf.py` | Python 3 + `pip install ezdxf` |
| `novo_report_semanal.py` | Python 3 + `pip install pywin32` + Excel instalado (usa COM) |
| `cronograma_msproject.py` | Python 3 (gera XML puro; abrir no MS Project) |

---

## tse_lanca_blocos.lsp — lançamento de símbolos em lote no AutoCAD

Replica um símbolo-fonte (inserido e configurado manualmente uma única vez) em dezenas/centenas de pontos calculados por Python. Arquitetura **"Python cérebro + LISP mão"**: o Python lê as fontes (planilha de I/O, DXF de âncoras), calcula coordenadas e gera a lista `*TSE_PTS*`; o LISP só executa cópias nativas.

Uso:
1. Gere/edite a lista `*TSE_PTS*` no topo do arquivo (formato `(("TIPO" (x y 0.0) ...) ...)` — há exemplo fictício e receita Python no cabeçalho).
2. No AutoCAD: `APPLOAD` → carregar o .lsp → comando `TSELANCA`.
3. Para cada tipo: selecione o símbolo-fonte, clique no **centro** dele (snap Center já vem forçado) e a rotina copia para todos os pontos. `[Continua/Sair]` entre tipos.

Por que funciona com blocos inteligentes: o `._copy` **nativo** preserva XDATA/configuração e o ProElétrica reconhece a cópia. Comandos LISP do plugin não são chamáveis via `(command ...)`, e o ponto de inserção (`assoc 10`) é deslocado do centro visual — por isso a origem é sempre um clique com snap center.

## extrai_blocos_dxf.py — símbolos limpos a partir de legenda DXF

Extrai os blocos de uma biblioteca/legenda DXF: achata blocos aninhados recursivamente (`virtual_entities()`), recentra pela bbox da geometria achatada, reconstrói blocos limpos com prefixo, opcionalmente adiciona ATTDEFs `TAG`/`ALTURA` e reescala. Saída sempre em **DXF R2013 ASCII** (formato validado — evita inflar o arquivo).

```bat
python extrai_blocos_dxf.py --lib legenda.dxf --out simbolos_limpos.dxf
python extrai_blocos_dxf.py --lib legenda.dxf --out simbolos.dxf --escala 0.5 --attdefs --blocos SENSOR_TEMP CHAVE_NIVEL
```

Gotchas documentados na docstring: bloco-casca aninhado, HATCH que degrada para contorno, bbox do bloco original não confiável.

## novo_report_semanal.py — relatório semanal do projeto (Excel)

Gera o próximo `NNNN-Relatório Semanal-SNN.xlsx` em `8 - Gerenciamento do Projeto\Semanal` **copiando o relatório anterior** (preserva formatação e validações de dados — openpyxl quebra as validations, por isso a edição é via Excel COM/win32com), limpa as faixas de dados e preenche as 7 abas (Identificação, Avanço por Disciplina, Atividades, Dificuldades, Plano, Riscos, REF). O % global é a média das disciplinas ativas.

O script localiza sozinho o maior `SNN` na pasta e gera o `S(N+1)` — o único argumento obrigatório é `--pasta`:

```bat
python novo_report_semanal.py --pasta "C:\...\8 - Gerenciamento do Projeto\Semanal"

python novo_report_semanal.py --pasta "C:\...\Semanal" ^
    --data 24/07/2026 --status "Em andamento" --global-pct 45 ^
    --rolar-avanco --limpar-listas
```

Argumentos opcionais: `--data` (D12), `--status` (D13), `--global-pct` (D14; aceita `45`, `45%` ou `0.45`), `--rolar-avanco` (copia % atual → % semana anterior) e `--limpar-listas` (ClearContents nas abas de lista). Consulte o `--help` para detalhes.

## cronograma_msproject.py — cronograma em XML do MS Project

Gera/atualiza cronograma no formato XML do MS Project (namespace `schemas.microsoft.com/project`): fases como summary tasks nível 1, **marcos explícitos** (`Milestone=1`, duração zero) fechando cada fase (emissão preliminar → levantamento de campo → as-built), IDs seguindo a ordem dos elementos. Revisões: copiar R(n) → R(n+1) e editar; nunca sobrescrever revisão emitida.

```bat
python cronograma_msproject.py --help
```

---

## Regra de ouro do ProElétrica

A inteligência elétrica do ProElétrica mora **dentro do DWG** (XDATA `PE_DATCNX`/`PE_HDNREF`/`PE_INFSYM`, blocos `_C__PRO_ELET_DAT_*`, XRECORDs); o `.PPE` é só manifesto. Portanto:

- **Nunca** fabricar bloco ProElétrica por script, nem round-tripar DWG dele por conversores.
- Quem insere bloco inteligente é o **ProElétrica dentro do AutoCAD** — automações apenas **replicam por `._copy` nativo** (que o plugin reconhece) ou geram geometria burra de apoio (overlays, âncoras, guias).
