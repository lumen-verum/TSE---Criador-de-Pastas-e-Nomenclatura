;;; ====================================================================
;;; TSE_LANCA_BLOCOS.LSP
;;; Rotina generica de lancamento de simbolos em lote (validada em
;;; producao no metodo TSE, ex.: Planta de Pontos CA7871-A11-01-PJ-II).
;;;
;;; OBS: comentarios sem acento de proposito - o carregador de LISP do
;;; AutoCAD le o arquivo como ANSI e acentos em UTF-8 aparecem quebrados.
;;;
;;; --------------------------------------------------------------------
;;; REGRAS APRENDIDAS (nao remover - sao o motivo desta rotina existir):
;;;
;;; 1) POR QUE "._copy" E NAO O COMANDO DO PLUGIN:
;;;    Comandos definidos em LISP por plugins (ex.: CCM do ProEletrica)
;;;    NAO sao chamaveis via (command "CCM") - o interpretador nao
;;;    enxerga comandos C:XXX de outro contexto como comandos nativos.
;;;    Ja o comando NATIVO ._copy preserva XDATA e configuracao do
;;;    bloco copiado, e o ProEletrica RECONHECE a copia como bloco
;;;    inteligente valido. Portanto: quem "cria" o bloco inteligente e
;;;    o plugin (o usuario insere UM simbolo-fonte manualmente); esta
;;;    rotina apenas REPLICA esse simbolo-fonte por copia nativa.
;;;
;;; 2) POR QUE CLIQUE COM SNAP CENTER E NAO (assoc 10):
;;;    O ponto de insercao (assoc 10) de blocos ProEletrica e DESLOCADO
;;;    do centro visual do simbolo. Usar assoc 10 como origem lanca
;;;    tudo fora de posicao. A origem correta e o CENTRO VISUAL, obtido
;;;    por clique do usuario com OSMODE 4 (snap Center) forcado apenas
;;;    no momento desse clique.
;;;
;;; 3) UMA COPIA COMPLETA POR PONTO:
;;;    (command "._copy" ss "" org destino "") - um ciclo completo do
;;;    comando por ponto de destino. Nao usar o modo Multiple: o ciclo
;;;    completo e o comportamento validado que mantem o ProEletrica
;;;    reconhecendo cada copia.
;;;
;;; 4) CMDECHO LIGADO (1): transparencia total - o usuario ve cada
;;;    comando ecoado na linha de comando e pode auditar o lote.
;;;
;;; --------------------------------------------------------------------
;;; USO:
;;;   1. Preencha *TSE_PTS* abaixo (normalmente gerada por Python).
;;;   2. APPLOAD neste arquivo.
;;;   3. Digite TSELANCA.
;;;   4. Para cada tipo: selecione o simbolo-fonte ja inserido/configurado
;;;      pelo plugin, clique no CENTRO dele (snap center ja forcado) e a
;;;      rotina replica o simbolo em todos os pontos do tipo.
;;;   5. Entre tipos, escolha [Continua/Sair].
;;;
;;; COMO GERAR *TSE_PTS* VIA PYTHON (arquitetura "Python cerebro + LISP mao"):
;;;   O script Python (ezdxf/openpyxl) le as fontes de dados (planilha de
;;;   I/O, DXF de ancoras etc.), calcula as coordenadas WCS de cada ponto
;;;   e imprime este arquivo (ou so o bloco setq) com algo como:
;;;
;;;     linhas = ['(setq *TSE_PTS* (list']
;;;     for tipo, pontos in dados.items():
;;;         itens = ' '.join('(list %.4f %.4f 0.0)' % (x, y) for x, y in pontos)
;;;         linhas.append('  (list "%s" %s)' % (tipo, itens))
;;;     linhas.append('))')
;;;
;;;   Depois basta recarregar o .lsp gerado por APPLOAD.
;;; ====================================================================

;;; --------------------------------------------------------------------
;;; LISTA DE PONTOS - EXEMPLO FICTICIO (substitua pela lista gerada)
;;; Estrutura: (("TIPO" (x y z) (x y z) ...) ("TIPO2" ...) ...)
;;; Coordenadas em WCS; a rotina converte para UCS corrente via trans.
;;; --------------------------------------------------------------------
(setq *TSE_PTS*
  (list
    (list "SENSOR_TEMPERATURA"
      (list 1000.0 2000.0 0.0)
      (list 1000.0 2350.0 0.0)
    )
    (list "CHAVE_DE_NIVEL"
      (list 3500.0 1800.0 0.0)
      (list 3500.0 2600.0 0.0)
      (list 4200.0 1800.0 0.0)
    )
    (list "SENSOR_ROTACAO"
      (list 5100.0 900.0 0.0)
    )
  )
)

;;; --------------------------------------------------------------------
;;; C:TSELANCA - lancamento em lote, tipo a tipo
;;; --------------------------------------------------------------------
(defun C:TSELANCA (/ eco-ant os-ant resto grupo tipo pts ss org d resp n)
  (setq eco-ant (getvar "CMDECHO")
        os-ant  (getvar "OSMODE"))
  ;; Regra 4: eco ligado para auditoria do lote
  (setvar "CMDECHO" 1)

  (if (null *TSE_PTS*)
    (prompt "\n*TSE_PTS* vazia. Gere a lista via Python e recarregue o .lsp.")
    (progn
      (prompt (strcat "\nTSELANCA - " (itoa (length *TSE_PTS*)) " tipo(s) na lista."))
      (setq resto *TSE_PTS*)
      (while resto
        (setq grupo (car resto)
              resto (cdr resto)
              tipo  (car grupo)
              pts   (cdr grupo)
              n     0)

        (prompt (strcat "\n=== Tipo: " tipo " - " (itoa (length pts)) " ponto(s) ==="))
        (prompt (strcat "\nSelecione o SIMBOLO-FONTE de " tipo
                        " (ja inserido e configurado pelo plugin):"))
        (setq ss (ssget))

        (if (null ss)
          (prompt (strcat "\nNada selecionado - tipo " tipo " PULADO."))
          (progn
            ;; Regra 2: origem = CENTRO VISUAL clicado com snap Center
            ;; forcado SOMENTE durante este getpoint (nunca assoc 10).
            (setvar "OSMODE" 4)
            (setq org (getpoint (strcat "\nClique no CENTRO do simbolo-fonte de "
                                        tipo ": ")))
            (setvar "OSMODE" os-ant)

            (if (null org)
              (prompt (strcat "\nSem origem - tipo " tipo " PULADO."))
              (progn
                ;; Regras 1 e 3: UMA copia completa por ponto, comando
                ;; nativo ._copy (preserva XDATA; ProEletrica reconhece).
                (foreach d pts
                  (command "._copy" ss "" org (trans d 0 1) "")
                  (setq n (1+ n))
                )
                (prompt (strcat "\n" tipo ": " (itoa n) " copia(s) lancada(s)."))
              )
            )
          )
        )

        ;; [Continua/Sair] entre tipos (so pergunta se ainda ha tipos)
        (if resto
          (progn
            (initget "Continua Sair")
            (setq resp (getkword "\nProximo tipo? [Continua/Sair] <Continua>: "))
            (if (= resp "Sair")
              (progn
                (prompt "\nLancamento interrompido pelo usuario.")
                (setq resto nil)
              )
            )
          )
        )
      )
    )
  )

  ;; Restaura ambiente
  (setvar "OSMODE" os-ant)
  (setvar "CMDECHO" eco-ant)
  (princ "\nTSELANCA concluido.")
  (princ)
)

(princ "\ntse_lanca_blocos.lsp carregado. Comando: TSELANCA")
(princ)
