# TSE — Método de Projetos de Elétrica e Automação

Repositório **privado do grupo TSE Energia e Automação** que centraliza o método de organização e execução de projetos de elétrica/automação — do primeiro dia (criar as pastas e dar nome aos arquivos) à execução assistida por IA (Claude Code) com ferramentas de automação de CAD e gestão.

O método foi validado em projeto real e evolui a cada projeto: as lições aprendidas voltam para o **playbook vivo** versionado aqui.

---

## Por onde começar

| Quero... | Vá para |
|---|---|
| Criar a estrutura de um projeto novo e dar nome aos arquivos | [1. Script de pastas e nomenclatura](#1-script-de-pastas-e-nomenclatura) |
| Organizar e documentar um projeto com o Claude Code | [2. Agente e playbook](#2-agente-e-playbook-claude-code) |
| Gerar relatório semanal, cronograma ou lançar símbolos no CAD | [3. Ferramentas](#3-ferramentas-tools) |
| Saber se o método já cobre a minha situação | [O que o método já cobre](#o-que-o-método-já-cobre) |
| Registrar uma lição aprendida | [Como contribuir com o método](#como-contribuir-com-o-método) |

Para ter o repositório na sua máquina (é privado — precisa de acesso à organização `lumen-verum` no GitHub):

```bash
git clone https://github.com/lumen-verum/TSE---Criador-de-Pastas-e-Nomenclatura.git
```

---

## Mapa do repositório

| Caminho | O que é |
|---|---|
| `TSE - Criador de Pastas e Nomenclatura.ps1` | Script PowerShell: cria a estrutura padrão de pastas do projeto e monta nomes de arquivo no padrão TSE (`CLIENTE+PROJETO-ÁREA-NN-TIPO-CONTEÚDO-Rxx_Descrição.ext`) |
| `Cidade\0000 - ISO\` | **Template-mestre** de projeto: `Indice de detalhamento e numeração.xlsx`, `TAMANHOS DE FONTES PARA CAD.jpeg` e os modelos em branco das pastas 7 (Critérios e Informações do Projeto) e 8 (Relatório Semanal S00). O git não guarda pasta vazia — as pastas 0–6 não vêm no clone; quem as cria é o script |
| `.claude\agents\tse-organizador-projetos.md` | Agente do Claude Code que aplica o método de organização de projetos |
| `.claude\tse-playbook-organizacao.md` | **Playbook vivo (autoaprendente)** do método — fases, receitas e o Log de aprendizado |
| `tools\` | Ferramentas genéricas de automação (Python + AutoLISP), com [README próprio](tools/README.md) |
| `tools\novo_report_semanal.py` | Gera o próximo Relatório Semanal (Excel COM) copiando o anterior |
| `tools\cronograma_msproject.py` | Cria/atualiza cronogramas em XML do MS Project (listar, set, marcos, nova revisão) |
| `tools\tse_lanca_blocos.lsp` | Lançamento em lote de símbolos no AutoCAD (compatível com blocos inteligentes do ProElétrica) |
| `tools\extrai_blocos_dxf.py` | Extrai símbolos limpos de uma legenda/biblioteca DXF (ezdxf) |
| `LICENSE` | Licença MIT |

---

## Como tudo se conecta

```mermaid
flowchart TB
    subgraph REPO["📦 Este repositório"]
        direction LR
        PS["⚙️ Script PowerShell<br/><b>TSE - Criador de Pastas e Nomenclatura.ps1</b>"]
        TPL["🗂️ Template-mestre<br/><b>Cidade/0000 - ISO</b><br/>Índice de numeração + Fontes CAD<br/>+ modelos das pastas 7 e 8"]
        CC["🤖 Claude Code<br/><b>.claude/</b><br/>agente tse-organizador-projetos<br/>+ playbook vivo do método"]
        TOOLS["🧰 Ferramentas<br/><b>tools/</b><br/>report semanal · cronograma XML<br/>lançamento de blocos · extrator DXF"]
    end

    NOVO([🆕 Projeto novo]) --> PS

    PS -->|"New-TSEProjeto<br/>nº + categoria + descrição"| PASTAS["📁 Estrutura padrão criada<br/>0 - Pedido de Compras … 8 - Gerenciamento<br/>+ Índice + Fontes CAD"]
    TPL -.->|"Índice + Fontes CAD<br/>copiados pelo script"| PASTAS
    PS -->|"New-TSENome<br/>valida as tabelas de códigos"| NOME["🏷️ Nomenclatura padronizada<br/>CA7871-A11-01-PJ-II-R00_Planta_de_Pontos.dwg"]

    PASTAS --> TRAB
    NOME --> TRAB
    TPL -.->|"modelos das pastas 7 e 8<br/>copiados pelo agente ou à mão"| TRAB

    subgraph TRAB["🔄 Execução do projeto (com Claude Code)"]
        direction TB
        ORG["Organizar recebidos · preencher Índice de numeração<br/>· Critérios e Informações (pasta 7)<br/>· Relatório Semanal + Cronograma (pasta 8)"]
        ENG["Engenharia assistida:<br/>planilhas de cálculo e listas (I/O, cabos, quadro de cargas)<br/>· as-built · DXF/AutoLISP · documentos de emissão"]
        ORG --> ENG
    end

    CC -->|"o agente lê o playbook<br/>e aplica o método"| TRAB
    TOOLS -->|"chamadas pelo Claude<br/>ou direto pelo time"| TRAB
    TRAB -->|"lições aprendidas voltam ao Log do playbook<br/>(commit + push no fim da sessão)"| CC

    style REPO fill:#f0f7f4,stroke:#0a7a5c
    style TRAB fill:#f4f4fb,stroke:#4a4a9c
    style NOVO fill:#fff4e0,stroke:#c98a00
```

**Em resumo:** o script cria a casa e dá nome aos arquivos; o template garante que toda casa nasce igual; o agente + playbook fazem o Claude Code trabalhar do jeito TSE dentro dela; as ferramentas de `tools/` executam as partes repetitivas (relatório, cronograma, CAD); e cada projeto realimenta o playbook — o método aprende.

---

## Como usar cada parte

### 1. Script de pastas e nomenclatura

No PowerShell, dentro da pasta onde está o `.ps1`:

```powershell
# 1) Menu interativo
.\"TSE - Criador de Pastas e Nomenclatura.ps1"

# 2) Só carregar as funções (dot-source) e chamar direto
. .\"TSE - Criador de Pastas e Nomenclatura.ps1"

New-TSEProjeto -Numero 8044 -Categoria PROJ -Descricao "TERMINAL PORTUARIO COFCO"

New-TSENome -Cliente CO -Projeto 8044 -Area A10 -Doc 1 `
            -Tipo MC -Conteudo SG -Rev 0 `
            -Descricao "Memorial de Calculo Guarda-Corpo" -Extensao docx
# -> CO8044-A10-01-MC-SG-R00_Memorial_de_Calculo_Guarda-Corpo.docx
```

Se o PowerShell bloquear a execução, rode uma vez:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

**Antes do primeiro uso**, ajuste as duas variáveis no topo do `.ps1` — elas vêm com os caminhos da máquina de quem versionou por último:

```powershell
$RaizProjetos = "C:\...\Pasta-onde-os-projetos-serao-criados"
$PastaModelo  = "C:\...\Pasta-com-Indice.xlsx-e-Fontes-CAD.jpeg"
```

Sugestão: aponte `$PastaModelo` para a pasta `Cidade\0000 - ISO\` do seu clone deste repositório.

O script cria as pastas **0 a 8** e copia o Índice e o guia de fontes CAD. Os **modelos das pastas 7 e 8** (`XXXX-...` → trocar pelo nº do projeto) são copiados do template-mestre à mão ou pelo agente — veja a [estrutura de pastas](#estrutura-de-pastas).

<details>
<summary>Detalhe: menu do script</summary>

```
MENU:  1) Criar estrutura de pastas  →  New-TSEProjeto  (nº, categoria, descrição → pastas 0–8 + modelos)
       2) Gerar nome de arquivo      →  New-TSENome     (cliente, projeto, área, doc, tipo, conteúdo, rev → nome validado)
       3) Ver tabelas de códigos     →  Show-TSETabela  (CLIENTE / AREA / TIPO / CONTEUDO)
       0) Sair
```
</details>

### 2. Agente e playbook (Claude Code)

Abra o **Claude Code na pasta do seu clone deste repositório** — é lá que o agente `tse-organizador-projetos` fica disponível — e indique o caminho da pasta do projeto. Os projetos ficam **fora** do repo (veja a [regra de dados](#regra-de-dados--leia-antes-de-commitar)).

Exemplo de pedido:

> *Use o agente tse-organizador-projetos no projeto `C:\...\8044 - PROJ TERMINAL PORTUARIO`: entenda o escopo pela proposta, organize os recebidos, monte o índice de numeração e preencha as pastas 7 e 8.*

O agente lê o playbook (`.claude\tse-playbook-organizacao.md`) antes de começar e conduz o projeto pelo método TSE. Seções do playbook:

- **0–7. O núcleo do método**: princípios → fase ENTENDER (escopo) → ESTRUTURA (pastas) → ORGANIZAR (recebidos) → NOMENCLATURA + Índice → pastas 7 e 8 → EXTRAIR informações → entregáveis terminais.
- **8. Relatório Semanal** — as 7 abas, mapeamento de células, cópia do report anterior via Excel COM, % global.
- **9. Cronograma MS Project XML** — estrutura Task/Resources/Assignments, fases com marcos, ciclo de revisões R(n)→R(n+1).
- **10. Narrativa de emissão** — notas padrão de desenho/planilha, versão cliente × interna, ciclo R00 preliminar → as-built.
- **11. Entregáveis por template** — quadro de cargas e lista de I/O a partir de planilha-exemplo aprovada (fórmulas e base NBR 5410 preservadas), com verificação independente em Python obrigatória.
- **12. Automação CAD e ProElétrica** — arquitetura "Python cérebro + LISP mão", regra de ouro dos blocos inteligentes, método âncoras→overlay, gotchas de DXF.
- **Exemplo de referência** — um projeto real percorrido do escopo aos entregáveis (tags, valores e contagens reais ficam fora do repo).
- **Log de aprendizado** — lições datadas, em ordem cronológica, acrescentadas a cada projeto. **O playbook é autoaprendente:** o agente registra o que aprende, e o Log é sempre mais atual que este README.

### 3. Ferramentas (tools/)

Guia completo em [`tools/README.md`](tools/README.md). Uma linha de cada:

```bat
:: Próximo Relatório Semanal (copia o anterior e preenche semana/status/% via Excel COM)
python tools\novo_report_semanal.py --pasta "C:\...\8 - Gerenciamento do Projeto\Semanal"

:: Cronograma MS Project XML (também: set | add-marco | nova-revisao)
python tools\cronograma_msproject.py listar --arquivo Cronograma_R01.xml

:: Símbolos limpos a partir de uma legenda DXF
python tools\extrai_blocos_dxf.py --lib legenda.dxf --out simbolos_limpos.dxf

:: No AutoCAD: APPLOAD -> tse_lanca_blocos.lsp -> comando TSELANCA
:: (replica um símbolo-fonte em todos os pontos da lista *TSE_PTS* gerada por Python)
```

---

## O que o método já cobre

Situações que já passaram por projeto real e onde está a receita no playbook. Se a sua não estiver aqui, procure por palavra-chave no **Log de aprendizado**.

| Situação | Onde no playbook |
|---|---|
| Projeto novo com proposta/RFQ: escopo → pastas → nomenclatura → pastas 7 e 8 | Seções 0–7 + Exemplo de referência |
| Preencher Critérios e Informações do Projeto para o import do sistema TSE (formato que o import aceita) | Seção 5 + Log 22/06 |
| Relatório semanal e % global — inclusive na S00 e com escopo ainda aberto | Seção 8 + Log 04/08 e 12/08 |
| Cronograma: gerar o XML, revisar, ler e validar um `.mpp` via COM (sem nunca salvar por cima) | Seção 9 + Log 12/08 |
| Projeto de **as-built** que nasce do cronograma da obra | Log 12/08 |
| Projeto que nasce de um **laudo/ensaio de campo** | Log 04/08 |
| Projeto de **demanda interna** (e-mail + WhatsApp, sem RFQ) | Log 28/09 |
| Empreendimento com várias frentes; códigos `PROJ` × `ELET` do mesmo empreendimento | Log 04/08 |
| **Lista de I/O** a partir de projeto básico de terceiro + lista de materiais do fabricante (painel Rockwell/EPLAN) | Seção 11 + Log 01/10 |
| Quadro de cargas e listas por planilha-template, com verificação independente | Seção 11 |
| Notas de emissão; R00 preliminar → as-built; entregável faseado quando falta dado de terceiro | Seção 10 + Log 01/10 |
| Lançamento de símbolos em planta e trabalho com ProElétrica | Seção 12 + `tools/` |

---

## Padrão de nomenclatura

```
CLIENTE + PROJETO - AREA - NN - TIPO - CONTEUDO - Rxx _ Descrição . ext
   CA      7871     A11   01    PJ      II        R00   Planta_de_Pontos  dwg
```

Campos:

| Campo     | Exemplo | Origem                                        |
|-----------|---------|-----------------------------------------------|
| Cliente   | `CA`    | Tabela `$CLIENTE` (2 letras)                  |
| Projeto   | `7871`  | Nº interno TSE                                |
| Área      | `A11`   | Tabela `$AREA` (`Axx`)                        |
| Doc       | `01`    | Nº do documento dentro da área (2 dígitos)    |
| Tipo      | `PJ`    | Tabela `$TIPO` (2 letras)                     |
| Conteúdo  | `II`    | Tabela `$CONTEUDO` (2 letras)                 |
| Revisão   | `R00`   | `R` + 2 dígitos (0 = emissão inicial)         |
| Descrição | texto   | Espaços viram `_`                             |
| Extensão  | `dwg`   | docx / pdf / dwg / xlsx ... (opcional)        |

As tabelas de códigos vivem dentro do próprio `.ps1` e podem ser editadas — basta acrescentar novas linhas nos hashtables `$CLIENTE`, `$AREA`, `$TIPO`, `$CONTEUDO`.

**Empreendimento com várias frentes:** cada frente vira uma **ÁREA** (`A11`, `A12`…) no índice do projeto — não uma pasta. A árvore de disciplinas continua única.

---

## Estrutura de pastas

```
NÚMERO - CATEGORIA DESCRIÇÃO\
├── 0 - Pedido de Compras
├── 1 - Recebidos
├── 2 - Fotos
├── 3 - ART
├── 4 - Editáveis
├── 5 - Vínculos
├── 6 - PDF's
├── 7 - Informações do Projeto        ← modelos XXXX-Critérios / XXXX-Informações (do template)
├── 8 - Gerenciamento do Projeto
│   └── Semanal                       ← XXXX-Relatório Semanal-S00 (do template)
├── Indice de detalhamento e numeração.xlsx
└── TAMANHOS DE FONTES PARA CAD.jpeg
```

O script cria as pastas 0–8 e copia os dois arquivos da raiz; os modelos marcados com ← vêm de `Cidade\0000 - ISO\`. A pasta `9 - Boletim de Medição` existe no template-mestre, mas o script não a cria — crie à mão se o projeto precisar.

---

## Requisitos

| Parte | Requisito |
|---|---|
| Clonar e contribuir | Git + acesso à organização `lumen-verum` no GitHub |
| Script de pastas/nomenclatura | Windows PowerShell 5+ |
| Agente + playbook | Claude Code (pastas 7 e 8 são editadas via Excel COM → **Excel instalado**) |
| `novo_report_semanal.py` | Python 3.11+ com `pywin32` + **Excel instalado** (edição via COM) |
| `cronograma_msproject.py` | Python 3.11+ (gera XML puro; abrir no MS Project) |
| `extrai_blocos_dxf.py` | Python 3.11+ com `ezdxf` |
| `tse_lanca_blocos.lsp` | AutoCAD completo (com o plugin do símbolo carregado, ex.: ProElétrica) |
| Ler/validar `.mpp` | MS Project instalado (opcional — via COM, só leitura) |

```bat
pip install ezdxf pywin32
```

---

## Como contribuir com o método

### Regra de dados — leia antes de commitar

**Dados de cliente NUNCA entram neste repositório.** Nada de propostas, valores, contatos, P&IDs, listas de tags reais, contagens de I/O de projeto, DWGs/planilhas de cliente. O que entra aqui é só o **método**: templates em branco, ferramentas genéricas, exemplos fictícios ou anonimizados e as lições do playbook (escritas de forma genérica). Os arquivos do projeto vivem na pasta do projeto, fora do repo.

### Registrar uma lição no playbook

1. **Escreva no Log de aprendizado**, no fim do arquivo, em ordem de data:
   `- **AAAA-MM-DD** — **Título curto.** O que fazer, por quê e onde isso se aplica.`
   Trabalhando com o agente, ele mesmo faz esse registro.
2. **Escreva de forma genérica** — "num projeto com duas frentes", não o nome do cliente ou o nº do projeto.
3. **Faça a varredura antes do commit.** Este comando lista as linhas novas com valores em R$ ou números de 4 dígitos com cara de nº de projeto — acrescente os nomes dos clientes em que você trabalhou:

   ```bash
   git diff -U0 | grep "^+[^+]" | grep -n -i -E 'R\$ ?[0-9]|\b[3-9][0-9]{3}\b|nome-do-cliente'
   ```

4. **Commit + push no fim de cada sessão em que entrou lição nova** — não deixe acumular no disco (já aconteceu de 20 lições ficarem dois meses fora do repo, sem o grupo ver). Mensagem no formato `Playbook: <resumo das lições>`.
5. **Lição que virou regra estável** sobe do Log para a seção correspondente do playbook; o Log continua como histórico.

---

## Licença

[MIT](LICENSE).
