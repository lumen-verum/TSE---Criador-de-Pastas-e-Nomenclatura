# tools/ — Ferramentas do método TSE

Ferramentas genéricas de automação de projeto (CAD + gestão), validadas em projeto real. Nenhuma contém dados de cliente: tudo é template/exemplo.

## Requisitos gerais

| Ferramenta | Requisitos |
|---|---|
| `tse_lanca_blocos.lsp` | AutoCAD completo (com o plugin do símbolo já carregado, ex.: ProElétrica) |
| `extrai_blocos_dxf.py` | Python 3 + `pip install ezdxf` |
| `novo_report_semanal.py` | Python 3 + `pip install pywin32` + Excel instalado (usa COM) |
| `cronograma_msproject.py` | Python 3 (gera XML puro; abrir no MS Project) |
| `pid_extrai_tags.py` | Python 3 + `pip install pymupdf` |
| `eplan_extrai_io.py` | Python 3 + `pip install pymupdf` |

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

## pid_extrai_tags.py — tags de instrumento de um P&ID com texto vetorizado

Extrai as tags dos balões de instrumento de um P&ID em PDF **cujo texto foi convertido em curvas** (`get_text()` não devolve nada dentro dos balões) — sem OCR e sem contar à mão. Validado num P&ID real de 3 folhas: 439 balões, 390 TT lidos corretamente.

```bat
rem passo 1 — gera a folha de contato e o esqueleto de rótulos
python pid_extrai_tags.py "P&ID.pdf" --paginas 1-3 --amostras

rem passo 2 — abra amostras_glifos.png, preencha rotulos.json e decodifique
python pid_extrai_tags.py "P&ID.pdf" --paginas 1-3 --rotulos rotulos.json ^
    --nuvem "0,0.72,0" --saida tags.csv
```

Como funciona: acha os balões pela geometria (círculo de diâmetro constante, `--diam`), acha os glifos dentro deles, agrupa em linhas (tipo / loop / número), gera uma **assinatura rasterizando a geometria do path** (não a página — rasterizar a página traz o fundo e arruína a assinatura), agrupa as assinaturas por **distância de Hamming** e emite uma folha de contato com uma amostra real de cada grupo para você identificar o caractere olhando uma vez só. Milhares de glifos caem em ~30 grupos.

Dois pontos que custam caro se ignorados:

- **Letras feitas de traço somem no filtro.** Dígitos e letras como S/L/M são contornos preenchidos, mas o `T` costuma ser **dois traços de espessura zero** (barra + haste) — qualquer filtro por largura/altura descarta os dois. A ferramenta já detecta e pareia (barra+haste = `T`, haste sozinha = `I`). Regra geral: se um caractere esperado não aparece no inventário, é filtro, não ausência.
- **`--nuvem` separa escopo novo de existente.** A nuvem de revisão marca o que é "FUTURO"/novo; a coluna `EM_NUVEM` diz se o balão está dentro dela. A nuvem é desenhada como dezenas de arcos, então a ferramenta **une os traços da cor por proximidade** antes de testar a contenção — filtrar por "traço grande da cor" acha zero.

A ordem dos grupos muda a cada execução (depende da frequência), então **regenere `rotulos.json` com `--amostras` sempre que mudar de desenho ou de parâmetros**.

Lembre que **nem todo balão é instrumento de campo** (ISA 5.1 / NBR 8190): `PSV` é válvula de segurança — elemento final, não instrumento; `ZSO`/`ES`/`LSH` são chaves de outros sistemas. Filtre por tipo antes de fechar quantitativo de I/O. Material de referência em `Área de Trabalho\Claude\Instrumentação`.

## eplan_extrai_io.py — configuração de I/O de um painel, a partir do desenho de fabricação

Levanta rack, slot, código do cartão, designação do módulo e régua de bornes de campo direto do **PDF de fabricação do EPLAN**. É a base para montar o endereçamento físico de uma lista de I/O.

```bat
python eplan_extrai_io.py painel.pdf --resumo --bornes
python eplan_extrai_io.py *.pdf --saida config_io.csv
```

**Por que não usar a lista de materiais.** Quando o painel já foi comprado e fabricado, o quantitativo tem de sair do desenho. A lista de materiais / exportação do configurador costuma refletir uma **alocação anterior**. Caso real que motivou a ferramenta: a lista dizia 64 cartões analógicos, o desenho mostrava **66**, com distribuição diferente entre os painéis — e a conclusão tirada da lista (faltar cartão numa remota) estava **invertida**: aquela era justamente a remota de maior folga. Isso foi parar num e-mail ao cliente.

**Conferência dupla, obrigatória.** A opção `--bornes` procura, na *lista de peças totalizada* do próprio painel, a quantidade de bornes de campo. Num cartão analógico com RTD a 3/4 fios é **um borne de 4 pontos de conexão por canal**, então o número tem que fechar com `nº de cartões × canais`. Validado em quatro painéis reais: 144, 168, 152 e 64 bornes contra 18, 21, 19 e 8 cartões de 8 canais. **Se os dois métodos não fecharem, não emita.**

**Gotcha.** A designação da régua pode passar de dois dígitos (`-100X01.11`). A ferramenta usa `-\d{2,3}X`; com `-\d\dX` metade dos slots some sem avisar.

Depois do levantamento, o endereçamento se monta cruzando isto com a tabela *Wiring Connections* do **manual do cartão** (terminal × canal). Lembre que **qual ponto vai em qual canal é decisão de projeto**, não dado a resgatar: painel entregue com a descrição dos canais em branco significa que ninguém definiu ainda — emita como "alocação proposta, a validar".
