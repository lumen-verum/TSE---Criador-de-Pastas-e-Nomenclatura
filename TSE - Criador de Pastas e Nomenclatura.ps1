<#
================================================================================
  TSE — CRIADOR DE PASTAS E NOMENCLATURA DE ARQUIVOS
  Ferramenta isolada: cria a estrutura padrão de pastas de um projeto e monta
  nomes de arquivo conforme a planilha "Indice de detalhamento e numeração".

  COMO USAR (no PowerShell, dentro da pasta onde está este arquivo):
    1) Menu interativo:        .\"TSE - Criador de Pastas e Nomenclatura.ps1"
    2) Só carregar as funções: . .\"TSE - Criador de Pastas e Nomenclatura.ps1"
       depois:  New-TSEProjeto -Numero 8044 -Categoria PROJ -Descricao "TERMINAL PORTUARIO COFCCO"
                New-TSENome -Cliente CO -Projeto 8044 -Area A10 -Doc 1 -Tipo MC -Conteudo SG -Rev 0 -Descricao "Memorial de Calculo Guarda-Corpo" -Extensao docx

  Se o PowerShell bloquear a execução, rode uma vez:
    Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
================================================================================
#>

# ============================ CONFIGURAÇÃO ============================
# >>> AJUSTE estes dois caminhos para a sua realidade <<<
# Pasta-RAIZ onde os projetos de TODOS os clientes são criados:
$RaizProjetos = "C:\Users\SamuelMorais\OneDrive - TSE ENERGIA E AUTOMACAO LTDA\Área de Trabalho\Claude\Linha de Vida Caminhão TSE"
# Pasta-MODELO de onde se copia a planilha de numeração e o guia de fontes CAD:
$PastaModelo  = Join-Path $RaizProjetos "Memorial\Exemplo\7164 - ELET MONTAR LINH ELETR SE138KV"

$ArquivosModelo = @("Indice de detalhamento e numeração.xlsx", "TAMANHOS DE FONTES PARA CAD.jpeg")
$SubPastas = @(
    "0 - Pedido de Compras", "1 - Recebidos", "2 - Fotos", "3 - ART",
    "4 - Editáveis", "5 - Vínculos", "6 - PDF's",
    "7 - Informações do Projeto", "8 - Gerenciamento do Projeto"
)

# ===================== TABELAS DE CÓDIGOS (aba NOMENCLATURA) =====================
$CLIENTE = [ordered]@{
    AA="ANGLO AMERICAN"; UN="UNILEVER"; UF="UNILEVER BEST FOOD"; SY="SYNGENTA"
    AR="ARCOR"; NT="NESTLE"; CF="CARTA FABRIL"; AM="AMCOR"; TS="TSEA"
    AL="AIR LIQUIDE"; CA="CARGILL"; HK="HEINEKEN"; CO="COFCO"
}
$AREA = [ordered]@{
    A00="ADMINISTRATIVO"; A01="CANTEIRO DE OBRAS"; A02="ARMAZÉM"; A03="CAPTAÇÃO"
    A04="ESTAÇÃO DE TRATAMENTO DE ESGOTO"; A05="ESTAÇÃO DE TRATAMENTO DE ÁGUA"
    A06="PORTARIA"; A07="SILO"; A08="SUBESTAÇÃO"; A09="CENTRO DE CONTROLE DE MOTORES"; A10="EXTERNA"
}
$TIPO = [ordered]@{
    PJ="PROJETO"; LM="LISTA DE MATERIAIS"; MD="MEMORIAL DESCRITIVO"; CR="CRONOGRAMA"
    ET="ESPECIFICAÇÃO TÉCNICA"; RT="RELATÓRIO TÉCNICO"; QC="QUADRO DE CARGAS"
    RL="RELATÓRIO LUMINOTÉCNICO"; LT="LAUDO TÉCNICO"; CT="COMUNICADO TÉCNICO"
    LD="LISTA DE DOCUMENTOS"; MC="MEMORIAL DE CÁLCULO"
}
$CONTEUDO = [ordered]@{
    AR="ARQUITETURA DE REDE"; CE="CABEAMENTO ESTRUTURADO"; FO="FORÇA"
    II="INSTRUMENTAÇÃO INDUSTRIAL"; IT="ILUMINAÇÃO E TOMADAS"; LU="LUMINOTÉCNICO"
    MT="MÉDIA TENSÃO"; SE="SUBESTAÇÃO"; GE="GERAL"; AT="ATERRAMENTO"; SP="SPDA"
    LT="LINHA DE TRANSMISSÃO"; SG="SEGURANÇA"
}

# ===================== FUNÇÃO 1: criar estrutura de pastas =====================
function New-TSEProjeto {
    param(
        [Parameter(Mandatory)][string]$Numero,     # ex.: 8044
        [Parameter(Mandatory)][string]$Categoria,  # ex.: PROJ / ELET
        [Parameter(Mandatory)][string]$Descricao   # ex.: TERMINAL PORTUARIO COFCCO
    )
    $nome = "{0} - {1} {2}" -f $Numero, $Categoria.ToUpper(), $Descricao.ToUpper()
    $proj = Join-Path $RaizProjetos $nome
    foreach ($s in $SubPastas) {
        New-Item -ItemType Directory -Force -Path (Join-Path $proj $s) | Out-Null
    }
    foreach ($m in $ArquivosModelo) {
        $src = Join-Path $PastaModelo $m
        if (Test-Path -LiteralPath $src) { Copy-Item -LiteralPath $src -Destination $proj -Force }
        else { Write-Warning "Arquivo-modelo nao encontrado (pulado): $m" }
    }
    Write-Host "`nProjeto criado: $proj" -ForegroundColor Green
    Get-ChildItem -LiteralPath $proj | ForEach-Object {
        $t = if ($_.PSIsContainer) { "[DIR] " } else { "      " }
        Write-Host ("  {0}{1}" -f $t, $_.Name)
    }
    return $proj
}

# ===================== FUNÇÃO 2: montar nome de arquivo =====================
function New-TSENome {
    param(
        [Parameter(Mandatory)][string]$Cliente,    # CO
        [Parameter(Mandatory)][string]$Projeto,    # 8044
        [Parameter(Mandatory)][string]$Area,       # A10
        [Parameter(Mandatory)][string]$Doc,        # 1  -> 01
        [Parameter(Mandatory)][string]$Tipo,       # MC
        [Parameter(Mandatory)][string]$Conteudo,   # SG
        [int]$Rev = 0,                              # 0  -> R00
        [string]$Descricao = "",
        [string]$Extensao = ""
    )
    $Cliente=$Cliente.ToUpper(); $Area=$Area.ToUpper(); $Tipo=$Tipo.ToUpper(); $Conteudo=$Conteudo.ToUpper()
    if (-not $CLIENTE.Contains($Cliente))   { Write-Warning "CLIENTE '$Cliente' nao esta na tabela." }
    if (-not $AREA.Contains($Area))         { Write-Warning "AREA '$Area' nao esta na tabela." }
    if (-not $TIPO.Contains($Tipo))         { Write-Warning "TIPO '$Tipo' nao esta na tabela." }
    if (-not $CONTEUDO.Contains($Conteudo)) { Write-Warning "CONTEUDO '$Conteudo' nao esta na tabela." }
    $docN = "{0:D2}" -f [int]$Doc
    $revN = "R{0:D2}" -f $Rev
    $base = "{0}{1}-{2}-{3}-{4}-{5}-{6}" -f $Cliente, $Projeto, $Area, $docN, $Tipo, $Conteudo, $revN
    if ($Descricao) { $base += "_" + (($Descricao.Trim()) -replace '\s+', '_') }
    if ($Extensao)  { $base += "." + ($Extensao.TrimStart('.').ToLower()) }
    return $base
}

# ===================== MENU INTERATIVO =====================
function Show-TSETabela($titulo, $tab) {
    Write-Host "`n$titulo" -ForegroundColor Cyan
    $tab.GetEnumerator() | ForEach-Object { Write-Host ("  {0} = {1}" -f $_.Key, $_.Value) }
}
function Start-TSEMenu {
    while ($true) {
        Write-Host "`n===== TSE — Criador de Pastas e Nomenclatura =====" -ForegroundColor Cyan
        Write-Host " 1) Criar estrutura de pastas de um novo projeto"
        Write-Host " 2) Gerar nome de arquivo (nomenclatura)"
        Write-Host " 3) Ver tabelas de codigos"
        Write-Host " 0) Sair"
        switch (Read-Host "Escolha") {
            "1" {
                $n = Read-Host "Numero do projeto (ex. 8044)"
                $c = Read-Host "Categoria (ex. PROJ, ELET)"
                $d = Read-Host "Descricao (ex. TERMINAL PORTUARIO COFCCO)"
                New-TSEProjeto -Numero $n -Categoria $c -Descricao $d | Out-Null
            }
            "2" {
                $cl = Read-Host "Cliente (2 letras)"
                $pj = Read-Host "Projeto (numero)"
                $ar = Read-Host "Area (Axx)"
                $dc = Read-Host "Numero do documento"
                $tp = Read-Host "Tipo (2 letras)"
                $ct = Read-Host "Conteudo (2 letras)"
                $rv = Read-Host "Revisao (numero, 0 = emissao inicial)"
                $ds = Read-Host "Descricao (texto livre)"
                $ex = Read-Host "Extensao (docx/pdf/dwg) [opcional]"
                $nome = New-TSENome -Cliente $cl -Projeto $pj -Area $ar -Doc $dc -Tipo $tp -Conteudo $ct -Rev ([int]$rv) -Descricao $ds -Extensao $ex
                Write-Host "`n  $nome" -ForegroundColor Yellow
            }
            "3" {
                Show-TSETabela "CLIENTE"  $CLIENTE
                Show-TSETabela "AREA"     $AREA
                Show-TSETabela "TIPO"     $TIPO
                Show-TSETabela "CONTEUDO" $CONTEUDO
            }
            "0" { return }
            default { Write-Host "Opcao invalida." -ForegroundColor Red }
        }
    }
}

# Só abre o menu quando o script é EXECUTADO direto (não quando é dot-sourced para carregar funções)
if ($MyInvocation.InvocationName -ne '.') { Start-TSEMenu }
