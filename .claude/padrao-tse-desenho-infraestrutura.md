# Padrão TSE de desenho de infraestrutura: Planta de Pontos (instrumentação) e Projeto de Força

Documento de referência para quem gera ou revisa desenho TSE de instrumentação e força (inclusive por automação).
**Leia inteiro antes de desenhar.** É o padrão; o que não estiver aqui se confirma com o engenheiro antes de fazer.

- **Origem:** estudo quantitativo de 4 projetos-modelo TSE, em 14/10/2026.
  - Rede de eletrodutos montada e cada nó classificado.
  - Contagens nos DXF e nos PDF plotados.
- **Modelos:** os nomes dos clientes ficam fora deste repositório. Os modelos ficam na pasta local `Exemplo de Projetos/`, que é ignorada pelo git.
  - **I-A:** instrumentação, área classificada, as-built. É o mais recente e o mais consistente.
  - **I-B:** instrumentação, projeto.
  - **I-C:** instrumentação de correia transportadora. Traçado mínimo.
  - **F-A:** força, sala de CCM. Leito, fiação por letra, taxa de ocupação.
- **Correções do engenheiro (Samuel)** feitas durante um as-built real. Estão marcadas **[Samuel]** e valem por cima dos modelos.

---

## 1. Princípios

1. **Padrão à risca.** Não inventar formato, símbolo ou representação que não exista nos modelos. Na dúvida, perguntar.
2. **Estudar antes de produzir.** Para cada tipo de entregável:
   - renderizar trechos dos modelos e contar por tipo de situação;
   - montar um documento do padrão com recortes;
   - **pedir validação antes de gerar** [Samuel: "pega o padrão da TSE e aprende ele profundamente, antes de sair fazendo as coisas loucamente"].
3. **O ponto fica onde ele é; quem se adequa é o texto** [Samuel]. Instrumento, motor e chave ficam na posição real (levantada ou validada). Para resolver sobreposição, só se move texto: atributos, rótulos, legendas de fiação, SOBE/DESCE.
4. **As-built = como construído**:
   - **posição:** a do levantamento de campo validado, vindo de vídeo, fotos, 3D do cliente e relato do eletricista;
   - **rota:** a levantada. Rota desenhada ou ajustada pelo engenheiro no DXF de orientação é a espinha do traçado;
   - nada de dentro de painel muda (disjuntor, proteção, I/O): divergência vira observação.
5. **Força e instrumentação sempre em projetos separados**, inclusive os DXF de orientação [Samuel].
6. **Ordem econômica da instalação** [Samuel]:
   - mínimo de duto pelo melhor percurso;
   - aproveitar ao máximo o encaminhamento lógico;
   - nada de cruzamento ou paralelo que não exista em campo.

---

## 2. Folha

| Item | Padrão |
|---|---|
| Formato | **A0** (841 × 1189 mm, ISO full bleed). Um modelo de correia usa A0 estendido (1276 × 841). |
| Modelo | metros 1:1 no modelspace; texto 0,10 m = 2,0 mm a 1:50 |
| Escala | **1:50**. 1:100 só se a planta não couber. |
| Viewport | uma por planta, recortada, deixando o carimbo livre no paperspace |
| Moldura | grade de coordenadas: letras na horizontal (A–T), números na vertical (1–14) |
| Coluna da direita | **174 mm**, de cima para baixo: LEGENDA DE SÍMBOLOS → LEGENDA DE CORES (só se houver EX i/EX d/SCI) → NOTAS → PLANTA CHAVE (prédio hachurado em vermelho) → APROVAÇÃO → CONTROLE DE REVISÕES (a mais nova em cima; o as-built leva a descrição "As-Built") → carimbo |
| Carimbo | o "de sempre" da TSE, `Carimbo_Rocha` [Samuel]: data, arquivo, revisão e número da prancha nn/NN; o conteúdo da prancha vai em MTEXT `TEXTO carimbo` |
| Título de vista | bloco `Tag_Prancha_Rocha`: "Projeto de Instrumentação - EL +xxxx" ou "Projeto de Força - EL +xxxx", mais "Esc. 1:50" |
| Continuidade | seta com "VEM / VAI PARA AS COORDENADAS (G5) DA PRANCHA nn/NN", com o total de folhas certo |
| Impressão | `TSE.ctb` (também aparece `Eng.Allyff.ctb`), DWG To PDF |
| Títulos dos quadros | 4 mm, azuis |

## 3. Camadas, cores e textos

| Informação | Camada | Cor | Texto (papel) |
|---|---|---|---|
| Instrumento | `Instrumentação` (EX i verde / EX d azul / SCI cinza) | 92 / 5 / 54 | tag 2,0 mm |
| Eletroduto | `RAAG-ELETRODUTO_FG_APARENTE` | 5 | — |
| Condulete e bucha de redução | `CONDULETES` | 1 | tipo 1,2 mm |
| Bitola / altura do trecho | `INDICACAO_DIAM_TUBULACAO` | 1 | 2,0 mm |
| Símbolo de cabo | `FIACAO` | 212 | — |
| NxCabos | `INDICACAO_CIRCUITO_FIA` | 10 | 1,9 mm |
| Classificação (EX / EX i / EX d) | `INDICACAO_CIRCUITO` | 2 | 2,0 mm |
| Linha de chamada | `LINHA_DE_CHAMADA` | 1 | — |
| Eletrocalha de instrumentação | `ELETROCALHA_*` | 190 roxo | rótulo 1,5–2,0 mm |
| Leito de força | leito em escada | 1 vermelho | por legenda |
| SOBE/DESCE | seta em `RAAG-ELETRODUTO_FG_APARENTE`; caixa de texto na camada `0` | 5 | 2,0 mm |
| Fundo civil/arquitetura | `CIVIL` / xref | 252–253 cinza | — |

- **Altura de texto única**, pela tabela TSE: 2,0 mm no papel; 0,10 m a 1:50; 0,15 m a 1:75 [Samuel].
- Camada com espessura "Default" estoura símbolo pequeno: fixar espessura 0 nas camadas de desenho.

## 4. Pontos

- **Instrumento:**
  - círculo duplo de r ≈ 0,186 m, com letra ou pictograma do tipo;
  - **tag à direita, 0,02 m depois da borda**, com a linha de base no centro;
  - **"h=" logo abaixo (−0,13 m)**, num formato único;
  - se não couber, à esquerda ou acima.
- **Grupo denso** (vários instrumentos juntos):
  - **círculo numerado** sobre cada instrumento;
  - **quadro-lista** "nº · tag · h=" com o nome do grupo.

  Nos modelos, **nenhum texto fica sobre outro**.
- **Motor e chave local** (os modelos de força não trazem em planta; vale a biblioteca TSE):
  - chave `TSE_SECCIONADORA_LOCAL` com atributos TAG e ALTURA;
  - motor com tag, "xxCV" e "h=".
- **Quadro / remota:** triângulo preto cheio com o nome. Painel do CCM em azul, com o nome sob a frente.

## 5. Traçado do eletroduto

**O traçado define a quantidade de caixas.** Traçado com muitos nós gera caixas excessivas [Samuel: "as caixas estão excessivas"].

1. **Tronco único** saindo do leito ou da prumada, **reto e paralelo ao equipamento ou à fileira de pontos**, com o **mínimo de curvas**. No modelo de correia: tronco de 60 m com 2 curvas e outro de 35 m sem nenhuma.
2. **Derivação:** um **T no tronco alinhado a cada ponto ou par de pontos**, com o **ramal reto e perpendicular**. No modelo de correia, nenhum ramal tem curva.
3. **Ortogonal:** 87–96% da extensão. Diagonal só para contornar obstáculo.
4. **Cruzamentos:**
   - correia 0; instrumentação I-B 5 e I-A 23, sempre sem caixa e sem quebra;
   - **meta: zero**. Nunca cruzar ou duplicar duto por causa da ordem em que o traçado foi gerado.
5. **Feixe:** quando vários dutos seguem juntos, ficam paralelos a 0,05–0,12 m (I-A). É exceção, não regra.
6. **Chegada ao ponto:** a ponta do duto ou a caixa do condulete **encosta no círculo**, com folga zero.
7. **Um duto por coluna de pontos, cada um saindo da prumada, está errado**: cria paralelos e cruzamentos que não existem.

## 6. Conduletes: quando usar

Contagem por tipo de nó. "Com" quer dizer condulete a até 0,15 m do nó.

| Nó | I-A (com / sem) | I-B | Correia |
|---|---|---|---|
| Cruzamento | **0 / 23** | **0 / 5** | (não há cruzamento) |
| Saída da eletrocalha (bloco "saída para eletroduto") | **6 / 37** (os 6 são descida logo depois) | 2 / 27 | LB + seta de descida |
| Trecho reto longo | sem caixa (até 9,9 m) | sem caixa (até 32,6 m) | **TB a cada 6,0 m** |
| Derivação | ~51 / 1 (T; TB se sai para baixo) | 22 / 4 | 6 / 6 |
| Subida ou descida | 129 / 8 (**LB + seta + caixa de destino**) | 32 / 63 | LB+LB no kit |
| Curva 90° em planta | 60 / 19 (as sem caixa em arco r = 0,10 m) | 15 / 19 (canto vivo) | 3 / 3 (o tronco quase não tem curva) |
| Chegada ao instrumento | LB encostado, ou duto reto depois de um LB/LR/T a 0,3–0,6 m | LB ou T encostado | kit: LB+LB → LR c/ furo → Ø3/4" → LL |

**Regra (as-built I-A):**
- **Com caixa:**
  - derivação (**T**; **TB** quando a saída vai para baixo; **X** só se 4 dutos se ligam no ponto);
  - descida ou chegada ao ponto (**LB** encostado no símbolo);
  - **curva real de 90° junto a ponto ou derivação** (**LL / LR**).
- **Sem caixa:**
  - cruzamento;
  - saída do leito ou da prumada (bloco "saída para eletroduto");
  - reta de qualquer comprimento;
  - desvio suave;
  - curva de tronco ou de feixe (canto vivo ou arco r = 0,10 m).
- **Opção da correia** (confirmar com o engenheiro): TB de passagem a cada 6 m e kit de descida completo por par de instrumentos.
- **Bloco:** a geometria real do condulete define as saídas. O giro tem que bater com os dutos que chegam, e nenhuma saída pode ficar "indo pro nada" [Samuel].
  - LB = +x e traseira;
  - LL = +x e −y;
  - LR = +x e +y;
  - T = ±x e −y;
  - TB = ±x e traseira;
  - X = 4 lados.
- **Tipo escrito ao lado** (LB, LL, LR, T, TB, X), 1,2 mm, a cerca de 0,15 m, girado com a caixa.
- **Bucha de redução** (triângulo vermelho) em toda queda de bitola.
- O duto é interrompido na borda da caixa.

## 7. Bitola e altura do trecho

| | I-A / I-B | Correia |
|---|---|---|
| Quando escreve a bitola | **só quando difere do padrão da nota** (o Ø padrão foi rotulado em 1 de 33 trechos) | em todo trecho entre conduletes |
| Quantas vezes | **uma por trecho contínuo**, paralela e colada ao duto; em trecho vertical, girada 90° | um par Ø + h por trecho |
| Altura do duto (h=) | I-B sim; **I-A (as-built) não** | sempre (h=~1,8 m tronco, h=~0,5 m descida) |
| Redução típica | Ø1.1/2" tronco → Ø1" ramal → Ø3/4" final, com bucha | igual |

- A nota define o padrão ("ELETRODUTOS SEM INDICAÇÃO DE DIÂMETRO SERÃO Ø…").
- Bitola real informada pelo eletricista vale mais que premissa.
- No as-built, altura de duto só se foi levantada.

## 8. Subida e descida

- **Seta:** `TBU_SOBE` / `TBU_DESC`, com haste de 1,0 m e o círculo r = 0,035 m **no ponto**, **sempre em diagonal (~45°)**.
  - SOBE aponta para fora.
  - DESCE aponta para o ponto.
  - Se o desenho só tiver o TBU_SOBE, o TBU_DESC é definido igual ao do modelo.
- **Caixa:** LB no ponto da mudança de nível.
- **Texto:** **caixa de texto com o destino**, por exemplo "SOBE P/ EL +13380", "DESCE P/ TÉRREO", "VAI PARA A SALA DE REMOTAS".
  - **Nunca "SOBE/DESCE" genérico** [Samuel].
  - Posicionar onde não encubra símbolo nem texto.
- **Leito vertical (prumada):** em planta, o leito é o corte junto da estrutura que ele acompanha (elevador, pilar).
  - Em pavimento, leito horizontal só onde ele de fato corre (chegada do CCM, painel). O resto é eletroduto [Samuel, relato do eletricista].
  - Leito instalado de lado: representação padrão (deitado), com "instalado na vertical" no rótulo [Samuel].

## 9. Fiação: instrumentação (I-A / I-B)

1. **Linha de chamada de 3 pontos**:
   - começa sobre o duto ou a eletrocalha;
   - sobe em **diagonal de ~45°** (0,5–0,6 m);
   - termina numa **prateleira horizontal de ~0,6 m**, à esquerda ou à direita.
2. **Símbolo e textos:**
   - **símbolo do tipo de cabo no meio da prateleira**; o símbolo é que dá o significado (forquilha, tridente, losango com ou sem ponto…), com um tipo por linha da legenda;
   - **"NxCabos" centrado 0,23 m acima**;
   - **classificação embaixo** (EX; EX i / EX d em área classificada).
3. **Vários tipos no mesmo trecho:**
   - símbolos **lado a lado na mesma prateleira, a ~0,65 m**, cada um com seu NxCabos;
   - **uma classificação só**;
   - deixar espaço para o texto (~0,6 m por NxCabos a 1,9 mm).
4. **Um rótulo por percurso**, no trecho longo:
   - não repetir a cada condulete;
   - não rotular cada ramal curto;
   - nas derivações, raramente os 3 ramos são rotulados.
5. **Descidas congestionadas:** letras em círculo (A, B, C…) junto aos dutos e um quadro **"LEGENDA DE CABOS"** com NxCabos, símbolo e classificação de cada letra.
6. **Legenda de cabos:** "XXxCABOS" + símbolo sobre o traço + descrição, por exemplo "CABO DE INSTRUMENTAÇÃO COM BLINDAGEM COLETIVA … - 1x(2x1,5)mm²".

## 10. Fiação: força (F-A)

1. **Uma letra por conjunto diferente de cabos** (A, B, C…), trocando a cada derivação, ou seja, quando um circuito sai ou entra.
   - Círculo vermelho r = 0,14 m e letra de 0,113 m.
   - Chamada com seta, a ~60°, com patamar curto.
   - Vai 1–2 vezes por trecho de leito e no ponto onde o circuito sai ou chega.
2. **LEGENDA DE CABOS por letra:** uma linha vermelha com um bloco de fiação por carga, com:
   - o nome da carga em cima;
   - as marcas cruzando a linha: | fase, ⌐ neutro, T terra, •T PEN;
   - a formação embaixo no formato **"N#Smm²-3F / N#Smm²-N / N#Smm²-T"** (N = total de condutores).
3. **TAXA DE OCUPAÇÃO DE CONDUTOS:** só para trecho de **leito**, uma linha por letra:
   - corte do leito ampliado, com os cabos agrupados por circuito;
   - "xx% de Ocupação" e "Leito WxHmm";
   - rodapé "Conduto: … (ABNT NBR 5410:2008 – item 3.3.5)";
   - o critério do % tem que ser escrito (no modelo, ele não se reproduz pelo desenho).
4. **Leito:** em escada, na largura real, travessa a cada 200 mm.
   - Cada tamanho e cada acessório (curva, tê, redução) é item da legenda.
   - Suportação a cada ~1,5 m, com item de legenda.
5. **Aterramento dentro da força:**
   - nota "cabo de cobre nu …mm² conectado ao BEP … NBR 5410";
   - BEP desenhado;
   - condutor de proteção como conjunto com letra própria.

   Não há projeto de aterramento separado [Samuel].
6. **"NxCabos / EX" não é o padrão de força** (é de instrumentação e rede).
7. **Medição de cabo:** uma polilinha por circuito numa camada não plotável, pelo eixo da infra, com o vertical somado.
   - Na lista vai o comprimento real mais a folga combinada.
   - Na rede/DE-PARA: real + 20 m.

## 11. Legendas, notas e detalhes

- **Legenda:**
  - todos os conduletes usados ("CX. CONDULETE TIPO LB C/ TAMPA CEGA" …, LR "C/ TAMPA C/ FURO");
  - bucha de redução;
  - cada tipo de cabo;
  - eletrocalha/leito por tamanho;
  - SOBE e DESCE;
  - quadro/remota.
- **Notas padrão de instrumentação** (corrigir os erros de digitação dos modelos):
  - bitola padrão do eletroduto;
  - cabos multivias com blindagem coletiva;
  - malha de equipotencialização (cobre nu) em todo o percurso das eletrocalhas, fixada a cada 1,5 m;
  - emendas com rosca BSP, ou NPT em área classificada;
  - eletrocalhas e peças com tampas de encaixe;
  - conferência de local, quantidade e especificação de cada instrumento pelo contratante;
  - em área classificada: infraestrutura comum com barreira intrínseca, prensa-cabos à prova de explosão e unidade seladora na saída da eletrocalha.
- **Nota de as-built:** "ESTE DESENHO REFLETE A INSTALAÇÃO EXECUTADA EM CAMPO (AS-BUILT), CONFORME LEVANTAMENTO DE …".
  - O quadro de notas tem altura fixa: nota longa empurra as outras para cima da borda.
- **Detalhes típicos** (faixa inferior ou folha própria): mudança de nível para instrumento, saída de eletrocalha para eletroduto, bucha de redução, curvas verticais, curva de inversão, redução de eletrocalha e suportes.

## 12. Revisão

- Revisão emitida nunca é sobrescrita. Nova revisão = cópia da anterior, com carimbo (data, arquivo, número da revisão), nova linha no controle de revisões e títulos e notas atualizados.
- **Pastas por revisão dentro de cada disciplina** [Samuel].
- **Não copiar os erros dos modelos:**
  - numeração de prancha errada;
  - código R01 num desenho R03;
  - nota inexistente referenciada;
  - formatos de h= misturados;
  - LR usado como derivação e T usado como curva;
  - SOBE/DESCE sem destino ou com o sentido invertido.

---

## 13. Automação (AutoCAD accoreconsole + AutoLISP gerado por Python): armadilhas reais

- **Início do script:** `(setvar "TILEMODE" 1) (setvar "OSMODE" 0) (setvar "ORTHOMODE" 0) (setvar "AUTOSNAP" 0) (setvar "SNAPMODE" 0)`.
  - DWG que abre num layout manda o `entmake` para o espaço de papel, e o COPY/MOVE falham com "not in current space".
- **Nunca usar o comando MOVE para posicionar ponto.** ORTHO e o rastreamento polar do desenho desviam o destino: num caso, 23 de 53 instrumentos foram parar até 0,7 m fora.
  - Editar a coordenada (`entmod` do grupo 10) e deslocar os ATTRIB junto.
- **Strings AutoLISP:** `\U+00E7` serve para texto novo (o AutoCAD exibe certo), mas **não casa** com o texto gravado, que tem o caractere real.
  - Para achar ou trocar texto, usar âncoras só ASCII e cortar por posição.
  - MTEXT longo vem em vários grupos 3 + o 1 final; juntar antes de procurar e regravar em blocos de 250.
- **Arquivos:**
  - script `.scr` em UTF-8 **com BOM** (sem BOM, os acentos de caminho quebram);
  - não duplicar o BOM ao reescrever um `.ps1`;
  - plotar com nome ASCII e renomear depois (o "ç" no nome do PDF falha);
  - caminho com acento: chamar o accoreconsole pelo PowerShell, não pelo bash.
- **Blocos anônimos de legenda (`*Unn`):** a geometria fica longe do ponto de inserção.
  - Para reaproveitar, achatar com `virtual_entities()`, recentrar pela bbox e recriar como bloco nomeado.
  - HATCH vira rosquinha (LWPOLYLINE de 2 vértices com largura = raio).
- **Antes de mover símbolo,** comparar a posição do DXF de orientação com o **próprio DWG da revisão anterior** (dump por handle), não com backup do DXF. O DXF de orientação pode ter vindo com grupos já realocados.
- **Conferir no PDF plotado e no DWG** (dump de posições), não só no script.

## 14. Fluxo de as-built que funcionou

1. Levantamento de campo: vídeo, fotos, áudio do eletricista e 3D do cliente.
2. **DXF de orientação por nível e por disciplina**, sobre a base do projeto, com o 3D do cliente em XREF:
   - proposta em camadas próprias: P10/P11 leito, P12/P13 eletroduto, P14 sobe/desce, P20 posição de campo, P90 dúvidas, P91 notas, P92 instruções;
   - o engenheiro corrige no CAD;
   - leitura das edições por handle.
3. **Documento do padrão validado** (este, mais o recorte do projeto).
4. Geração da revisão sobre cópia da anterior, só com as regras validadas:
   - traçado econômico;
   - caixas só onde têm função;
   - fiação no padrão da disciplina;
   - textos sem sobreposição;
   - ponto parado.
5. Conferência no PDF plotado e no DWG; entrega ao lado do DWG; organização por revisão.

## 15. Traçado em feixe: quando o campo tem um eletroduto por terminal

Vale quando o levantamento mostra tubos individuais saindo da prumada: um por chave local na força, um por equipamento na instrumentação. Nesse caso o tronco comum dos modelos vira um **feixe de tubos paralelos**.

- **Árvore de caminhos:**
  - ponto mais perto primeiro;
  - L que menos cruza;
  - a rota que o engenheiro desenhou é tronco obrigatório.
  - Como cada terminal tem o seu tubo, **desvio custa tubo de verdade**. Penalizar o caminho que se afasta do direto (fator ~0,7), senão o ponto ao sul sai para o norte e dá a volta.
- **Ordem das faixas** (garante zero cruzamento):
  - em cada trecho reto, quem sai primeiro para um lado fica por fora daquele lado;
  - quem segue até o fim fica no meio;
  - ao virar, a ordem esquerda→direita se mantém.
- **Espaçamento:** 0,07 m (o LEM usa 0,02–0,12 m).
  - Os LB de saída da prumada ficam desencontrados ao longo do tubo, porque lado a lado se encostam.
- **Feixe largo em trecho curto dobra sobre si mesmo.**
  - Escolher, em cada trecho, para que lado da linha o feixe se abre. Testar o centro, os dois lados e os quartos, e ficar com o que não dobra, não cruza e não encobre símbolo.
  - Conferir no fim: **cruzamentos entre tubos = 0** e nenhum trecho que volta.
- **O tronco precisa de folga dos símbolos** (o feixe tem largura) e não deriva colado na chegada de outro terminal.
- **Ao derivar de um nó já existente** (encaixe até 0,12 m), refazer o L a partir do nó. Senão sai um trecho diagonal.
- **Chegada:**
  - avaliar os 4 lados do símbolo;
  - penalizar o trecho final que passa por outro símbolo, inclusive do mesmo grupo.
- **No equipamento:** um tubo com T em cada derivação e LB em cada sensor. Condulete só aí, na saída e na chegada; curva de feixe sem caixa.
- **Força: da chave ao motor, sealtubo** (arco curto no mesmo layer do eletroduto).
- **Fiação com feixe:**
  - uma letra em círculo por tubo;
  - um quadro "LEGENDA DE CABOS" por nível: na força, carga/chave/formação; na instrumentação, equipamento e, por tipo, símbolo e quantidade;
  - rodapé explicando a letra.
  - Se o desenho já tem uma "legenda de cabos" geral com outro significado, renomeá-la para não haver dois quadros com o mesmo nome.
- **Bitola no feixe:** "Nx Ø2"" uma vez por trecho; o tubo sozinho só no seu maior trecho.
- **Quadro em espaço livre e visível:**
  - o DXF de orientação não tem a planta completa do prédio (fica em blocos/XREF);
  - usar o PDF plotado da revisão anterior como mapa de ocupação, calibrado pelo viewport:
    - 1:50 = 56,693 pt por metro;
    - centro da vista = grupo 12 + alvo 17;
    - a página do PDF pode estar rotacionada;
  - restringir à área visível do viewport (o quadro pode cair fora da folha).
- **Largura de texto da fonte TSE ≈ 0,82 × altura por caractere** (medida no PDF). Com 0,62 os quadros e o organizador de textos deixam sobreposição.
- **O que é traçado do engenheiro no DXF de orientação:** o que já existia antes da proposta, mais o que não está no `.bak` deixado pelo AutoCAD quando ele salvou. O resto é proposta automática, mesmo que ele tenha só arrastado uma ponta ao mover a prumada.
- **Comprimento de cabo pelo traçado:** só recalcular quando a posição de cada painel de destino estiver confirmada. Se a lista e o desenho divergem sobre qual painel atende cada nível, manter a lista e perguntar.

