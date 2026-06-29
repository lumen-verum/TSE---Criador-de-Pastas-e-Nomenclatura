# TSE — Criador de Pastas e Nomenclatura

Script **PowerShell** que automatiza duas tarefas repetitivas no início de cada projeto de engenharia da **TSE Energia e Automação**:

1. **Cria a estrutura padrão de pastas** de um projeto novo (e copia os arquivos-modelo).
2. **Monta o nome do arquivo** seguindo o padrão de nomenclatura interno (`CLIENTE+PROJETO-ÁREA-NN-TIPO-CONTEÚDO-Rxx_Descrição.ext`).

Junto do script vem o **template-mestre** `Cidade\0000 - ISO\`, que contém a estrutura 0–9 vazia + o `Indice de detalhamento e numeração.xlsx` e o `TAMANHOS DE FONTES PARA CAD.jpeg` em branco.

---

## Como usar

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

---

## Antes do primeiro uso — configurar caminhos

No topo do `.ps1` há duas variáveis para ajustar à sua máquina:

```powershell
$RaizProjetos = "C:\...\Pasta-onde-os-projetos-serao-criados"
$PastaModelo  = "C:\...\Pasta-com-Indice.xlsx-e-Fontes-CAD.jpeg"
```

Sugestão: aponte `$PastaModelo` para a pasta `Cidade\0000 - ISO\` deste repositório.

---

## Diagrama do fluxo

```
                ┌────────────────────────────────────┐
                │  TSE - Criador de Pastas...ps1     │
                └──────────────┬─────────────────────┘
                               │
                  Executa direto  /  Dot-source ( . )
                               │
                               ▼
                ┌────────────────────────────────────┐
                │            MENU                    │
                │ 1) Criar estrutura de pastas       │
                │ 2) Gerar nome de arquivo           │
                │ 3) Ver tabelas de códigos          │
                │ 0) Sair                            │
                └──┬──────────┬──────────┬───────────┘
                   ▼          ▼          ▼
       ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐
       │ New-TSEProjeto   │ │ New-TSENome      │ │ Show-TSETabela   │
       │  - Nº, Categoria,│ │  - Cliente, Proj,│ │   CLIENTE / AREA │
       │    Descrição     │ │    Area, Doc,    │ │   TIPO / CONTEUDO│
       │  - Cria 9        │ │    Tipo, Conteúdo│ └──────────────────┘
       │    subpastas     │ │  - Rev, Descrição│
       │  - Copia modelos │ │  - Valida tabelas│
       └────────┬─────────┘ └────────┬─────────┘
                ▼                    ▼
        Pasta-Projeto\        CO8044-A10-01-
         0..8 + xlsx +         MC-SG-R00_...
         jpeg                  .docx
```

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

---

## Estrutura de pastas criada

```
NÚMERO - CATEGORIA DESCRIÇÃO\
├── 0 - Pedido de Compras
├── 1 - Recebidos
├── 2 - Fotos
├── 3 - ART
├── 4 - Editáveis
├── 5 - Vínculos
├── 6 - PDF's
├── 7 - Informações do Projeto
├── 8 - Gerenciamento do Projeto
├── Indice de detalhamento e numeração.xlsx
└── TAMANHOS DE FONTES PARA CAD.jpeg
```

O template-mestre em `Cidade\0000 - ISO\` traz também a subpasta `9 - Boletim de Medição` e a estrutura `8 - Gerenciamento do Projeto\Semanal\` com o `XXXX-Relatório Semanal-S00.xlsx` em branco.

---

## Licença

[MIT](LICENSE).
