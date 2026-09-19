# Relatórios contábeis de auditoria — Guia do usuário

Módulo: `odomate_account_ledger_reports` · Odoo 19.0 · Versão 19.0.1.0.1 · Licença LGPL-3

## Sumário

1. [O que este módulo faz](#1-o-que-este-módulo-faz)
2. [Instalação](#2-instalação)
3. [Quem pode usar](#3-quem-pode-usar)
4. [Onde encontrar os relatórios](#4-onde-encontrar-os-relatórios)
5. [O filtro comum](#5-o-filtro-comum)
6. [Razão geral](#6-razão-geral)
7. [Razão de parceiros](#7-razão-de-parceiros)
8. [Saldos por idade](#8-saldos-por-idade)
9. [Relatório de impostos](#9-relatório-de-impostos)
10. [Auditoria de diários](#10-auditoria-de-diários)
11. [Impressão do lançamento contábil](#11-impressão-do-lançamento-contábil)
12. [Telas de itens de diário](#12-telas-de-itens-de-diário)
13. [Limitações conhecidas](#13-limitações-conhecidas)
14. [Para desenvolvedores: o contrato estável](#14-para-desenvolvedores-o-contrato-estável)

---

## 1. O que este módulo faz

Ele acrescenta os seis relatórios contábeis de auditoria clássicos que auditores e contadores pedem, como documentos PDF simples, além de duas telas de itens de diário prontas para uso.

| Relatório | Responde a |
|---|---|
| Razão geral | Qual foi a movimentação de cada conta, com saldo acumulado |
| Razão de parceiros | Qual foi a movimentação nas contas de clientes e fornecedores e quanto ainda devem |
| Saldos por idade | Há quanto tempo cada item em aberto está vencido, por faixas |
| Relatório de impostos | Valores líquidos e de imposto por imposto, separados em Vendas e Compras |
| Auditoria de diários | Todos os itens dos diários selecionados, com resumo de impostos |
| Lançamento contábil | Uma página por lançamento, para arquivar ou anexar a um comprovante |

Todos os relatórios leem os itens de diário apenas pelo ORM do Odoo. O módulo não grava nada fora de seus próprios registros de janela e não adiciona nenhum campo a modelos padrão.

## 2. Instalação

1. Copie a pasta `odomate_account_ledger_reports` para o seu caminho de addons.
2. **Aplicativos → Atualizar lista de aplicativos**.
3. Procure por *Accounting Audit Reports* e clique em **Ativar**.

As únicas dependências são `account` e `analytic`, ambas incluídas no Odoo Community. Após a instalação não há nada a configurar: não existe página de configurações, tarefa agendada nem dados de demonstração.

## 3. Quem pode usar

Três grupos contábeis já existentes do Odoo podem abrir as janelas e imprimir:

- `account.group_account_manager` — administrador de faturamento
- `account.group_account_user` — contador
- `account.group_account_readonly` — acesso contábil somente leitura

O módulo não cria nenhum grupo próprio e não concede nada a outros grupos. Um usuário fora desses três recebe `Somente usuários da contabilidade podem imprimir relatórios contábeis.` ao tentar imprimir, e sequer vê os menus.

Cada registro de janela é transitório (assistente): os três grupos recebem leitura, gravação e criação, e ninguém recebe exclusão — a limpeza é feita pelo próprio mecanismo do Odoo.

## 4. Onde encontrar os relatórios

| Relatório | Caminho no menu |
|---|---|
| Razão geral | Financeiro → Relatórios → Relatórios de auditoria → Razão geral |
| Auditoria de diários | Financeiro → Relatórios → Relatórios de auditoria → Auditoria de diários |
| Razão de parceiros | Financeiro → Relatórios → Relatórios de parceiros → Razão de parceiros |
| Saldos por idade | Financeiro → Relatórios → Relatórios de parceiros → Saldos por idade |
| Contas a receber por idade | Financeiro → Relatórios → Relatórios de parceiros → Contas a receber por idade |
| Contas a pagar por idade | Financeiro → Relatórios → Relatórios de parceiros → Contas a pagar por idade |
| Relatório de impostos | Financeiro → Relatórios → Impostos → Relatório de impostos |
| Itens de diário por conta | Financeiro → Relatórios → Gerenciamento → Itens de diário por conta |
| Itens de diário por parceiro | Financeiro → Relatórios → Gerenciamento → Itens de diário por parceiro |

*Contas a receber* e *Contas a pagar por idade* são a mesma janela de *Saldos por idade*, com o tipo de conta pré-selecionado e oculto.

A impressão do lançamento não tem menu: selecione um ou mais lançamentos em **Financeiro → Financeiro → Lançamentos contábeis** e use **Imprimir → Lançamento contábil**.

## 5. O filtro comum

Toda janela parte do mesmo conjunto de quatro campos.

| Campo | Significado |
|---|---|
| **Lançamentos** | *Somente lançamentos publicados* (padrão) ou *Todos os lançamentos*. Lançamentos cancelados nunca são incluídos. |
| **Data inicial** / **Data final** | Delimitam os itens de diário pela data contábil. Deixe ambas em branco para «todas as datas» onde a janela permitir. |
| **Diários** | Deixe em branco para abranger todos os diários da empresa. |
| **Empresa** | Visível apenas em bases multiempresa. O padrão é a sua empresa ativa. |

Pressione **Imprimir** para gerar o PDF ou **Cancelar** para fechar.

A janela recusa a impressão e explica o motivo quando:

- a empresa escolhida não é uma em que você tem permissão para trabalhar;
- a data inicial é posterior à data final;
- um diário selecionado pertence a outra empresa.

## 6. Razão geral

**Campos adicionais:** Contas, Parceiros, Contas analíticas (apenas com *Contabilidade analítica*), Ordenar por, Exibir contas, Incluir saldo de abertura.

**Colunas:** Data · Diário · Parceiro · Referência · Lançamento · Descrição · Débito · Crédito · Saldo, além de Moeda (usuários multimoeda, apenas quando a moeda do item difere da moeda da empresa) e Analítica (usuários de contabilidade analítica).

**Exibir contas**

- *Todas as contas* — todas as contas da empresa, mesmo sem movimentação.
- *Com movimentação* (padrão) — contas com itens no período ou com abertura diferente de zero.
- *Com saldo diferente de zero* — descarta contas cuja abertura + débito − crédito arredonda para zero.

**Ordenar por** altera a ordem dentro de cada conta: *Data* ordena por data, número do lançamento e id; *Diário e parceiro* ordena por diário, depois parceiro, depois data.

### Exemplo numérico — o saldo de abertura

Escrituração da empresa, exercício = ano civil, data inicial **2024-03-01**, **Incluir saldo de abertura** marcado.

| Lançamento | Data | Conta 121000 (Clientes) | Conta 400000 (Receitas) |
|---|---|---|---|
| E1 | 2023-06-15 | débito 1.000,00 | crédito 1.000,00 |
| E2 | 2024-02-10 | débito 500,00 | crédito 500,00 |
| E3 | 2024-03-15 | débito 250,00 | crédito 250,00 |

Aberturas impressas:

- **121000** é conta patrimonial, portanto abre com *tudo* lançado antes da data inicial: 1.000,00 + 500,00 = **1.500,00**.
- **400000** é conta de resultado, portanto abre apenas com o exercício corrente: E1 cai no exercício anterior e é excluído, restando **−500,00**.

O saldo acumulado da 121000 mostra então 1.500,00 na linha *Saldo de abertura* e 1.750,00 após E3; a linha de total da conta mostra Débito 250,00, Crédito 0,00, Saldo 1.750,00.

## 7. Razão de parceiros

**Campos adicionais:** Parceiros, Tipo de conta, Incluir itens liquidados, Mostrar valor na moeda (usuários multimoeda).

**Tipo de conta** corresponde aos tipos de conta do Odoo: *Contas a receber* → `asset_receivable`, *Contas a pagar* → `liability_payable`, *Contas a receber e a pagar* → ambos.

**Colunas:** Data · Diário · Conta · Lançamento · Referência · Descrição · Débito · Crédito · Saldo (reiniciando do zero para cada parceiro), além de Moeda.

Cada bloco de parceiro termina com Débito, Crédito, saldo final e **Valor em aberto** — a soma dos valores residuais dos itens.

Um item fica oculto a menos que **Incluir itens liquidados** esteja marcado somente quando está *totalmente* liquidado — ou seja, quando todos os itens do outro lado da sua conciliação também já foram baixados e nada resta em aberto. Uma fatura parcialmente paga continua imprimindo tanto sua própria linha quanto a linha do pagamento até que isso aconteça, de modo que o saldo final sempre reflete o que ainda está em aberto; uma fatura totalmente paga e seu pagamento desaparecem juntos, e voltam a aparecer juntos ao marcar **Incluir itens liquidados**. Itens sem parceiro nunca são impressos aqui; o lugar deles é a Razão geral.

Também é possível imprimir direto de um contato: selecione um ou mais contatos em **Contatos** e use **Imprimir → Razão de parceiros**. A janela abre com esses parceiros, o tipo de conta *Contas a receber e a pagar* e os itens liquidados incluídos.

### Exemplo numérico — uma fatura parcialmente paga mantém o pagamento em sua própria linha

Uma fatura de cliente de 1.000,00 é lançada e depois parcialmente recebida com 400,00. Impressa com **Incluir itens liquidados** desmarcado:

| Linha | Débito | Crédito | Saldo |
|---|---|---|---|
| Fatura | 1.000,00 | | 1.000,00 |
| Pagamento | | 400,00 | 600,00 |
| **Total do parceiro** | **1.000,00** | **400,00** | **600,00** |

**Valor em aberto** também mostra 600,00 — as duas linhas são impressas porque ainda restam 600,00 em aberto do lado da fatura, mesmo que o próprio pagamento já não tenha nada a baixar. Quando a fatura for paga integralmente, as duas linhas desaparecem da visão desmarcada e só voltam a aparecer juntas ao marcar **Incluir itens liquidados**.

## 8. Saldos por idade

**Campos adicionais:** Na data de (obrigatório, padrão hoje), Duração do período (dias) (obrigatório, padrão 30), Tipo de conta, Parceiros. Data inicial e Diários não são usados neste relatório e ficam ocultos.

Cada item em aberto é colocado em uma das seis colunas conforme sua idade em dias inteiros, onde idade = *Na data de* − (data de vencimento, ou data contábil quando não houver vencimento):

| Coluna | Idade (P = Duração do período) |
|---|---|
| A vencer | idade ≤ 0 |
| 1 - P | 1 … P |
| P+1 - 2P | P+1 … 2P |
| 2P+1 - 3P | 2P+1 … 3P |
| 3P+1 - 4P | 3P+1 … 4P |
| +4P | idade > 4P |

Uma linha com as seis colunas zeradas é descartada. Itens sem parceiro são agrupados em uma linha **Parceiro desconhecido**. Todos os valores estão na moeda da empresa; nenhuma conversão é aplicada.

### Exemplo numérico — faixas com P = 30, na data de 2024-06-30

| Item | Vencimento | Idade | Valor | Coluna |
|---|---|---|---|---|
| A | 2024-06-30 | 0 | 10,00 | A vencer |
| B | 2024-06-29 | 1 | 20,00 | 1 - 30 |
| C | 2024-05-31 | 30 | 30,00 | 1 - 30 |
| D | 2024-05-30 | 31 | 40,00 | 31 - 60 |
| E | 2024-03-01 | 121 | 50,00 | +120 |

Linha impressa: A vencer 10,00 · 1-30 50,00 · 31-60 40,00 · 61-90 0,00 · 91-120 0,00 · +120 50,00 · Total 150,00.

### Exemplo numérico — o residual é medido *na data*

Uma fatura de 1.000,00 é lançada em 2024-03-10 e parcialmente recebida com 400,00 em 2024-05-20.

- Em **2024-04-30** o recebimento ainda não ocorreu, então o relatório mostra **1.000,00**.
- Em **2024-06-30** ele mostra **600,00**, e a própria linha de recebimento zera e desaparece.

O relatório recalcula o residual a partir do histórico de conciliação em vez de ler o `amount_residual` de hoje — é isso que torna correta uma análise retroativa.

## 9. Relatório de impostos

Aplica-se apenas o filtro comum; Data inicial e Data final são obrigatórias e assumem por padrão o primeiro dia do mês corrente e hoje.

O relatório lista todos os impostos ativos de venda e compra da empresa em duas seções. Um grupo de impostos é representado por seus impostos filhos sob o tipo do imposto pai; o grupo em si não é uma linha. Para cada imposto:

- **Valor líquido** — a soma dos saldos dos itens que carregam o imposto.
- **Valor do imposto** — a soma dos saldos das linhas de imposto geradas pelo imposto.

Na seção **Vendas** ambos os valores têm o sinal invertido para que a receita fique positiva; em **Compras** são impressos como foram lançados. Nunca se toma um valor absoluto, de modo que notas de crédito realmente reduzem os números. Linhas zeradas em ambos os valores são omitidas, e uma seção vazia imprime *Nenhuma movimentação de imposto neste período.*

### Exemplo numérico — uma nota de crédito reduz os valores de vendas

Março de 2024, um imposto de venda de 20 %:

| Documento | Líquido | Imposto |
|---|---|---|
| Fatura de cliente, 1.000,00 + 20 % | 1.000,00 | 200,00 |
| Nota de crédito, 400,00 + 20 % | −400,00 | −80,00 |
| **Linha «Vendas» impressa** | **600,00** | **120,00** |

## 10. Auditoria de diários

**Campos adicionais:** Diários (obrigatório — por padrão os diários de venda e compra da sua empresa), Ordenar lançamentos por, Mostrar valor na moeda.

Uma seção por diário selecionado, na ordem própria dos diários. **Colunas:** Lançamento · Data · Conta · Parceiro · Descrição · Débito · Crédito, além de Moeda. Cada seção termina com os totais de Débito e Crédito do diário.

Quando o diário tem itens com impostos, segue uma pequena tabela de resumo Imposto / Base de cálculo / Valor do imposto, com a mesma regra de sinal do Relatório de impostos (impostos de venda invertidos). Diários sem itens tributados simplesmente não têm essa tabela.

## 11. Impressão do lançamento contábil

Sem janela: selecione lançamentos e use **Imprimir → Lançamento contábil**. Uma página por lançamento, cada um impresso com o papel timbrado e a moeda da própria empresa.

O cabeçalho mostra o número do lançamento, diário, data, parceiro, referência e situação. A tabela de itens mostra Conta · Descrição · Parceiro · Analítica · Débito · Crédito · Moeda, na ordem própria das linhas do lançamento, excluindo linhas de seção, subseção e observação. A linha de totais soma débito e crédito na moeda da empresa do lançamento — iguais em qualquer lançamento publicado.

## 12. Telas de itens de diário

Duas visões salvas sobre `account.move.line`, ambas em lista / dinâmica / gráfico com o painel de busca padrão de itens de diário do Odoo, e ambas excluindo linhas de seção, subseção e observação:

- **Itens de diário por conta** — agrupado por conta, somente lançamentos publicados.
- **Itens de diário por parceiro** — agrupado por parceiro, lançamentos publicados, pré-filtrado em contas a receber, contas a pagar e itens não conciliados.

São listas comuns do Odoo: você pode reagrupar, filtrar, exportar e abrir um lançamento a partir dali.

## 13. Limitações conhecidas

- **Somente moeda da empresa.** Todo valor é o montante na moeda da empresa. A coluna opcional Moeda mostra o valor em moeda estrangeira do item apenas para referência; nada é convertido.
- **Sem exportação para Excel.** Os relatórios são apenas em PDF. Use as duas telas de itens de diário quando precisar de planilha.
- **Saldos por idade ignoram diários.** Por projeto, abrangem todos os diários da empresa; o campo Diários fica oculto nessa janela.
- **Sem navegação para o detalhe.** Os PDFs são documentos estáticos e não têm links de volta ao Odoo.
- **`account.report` intocado.** O módulo não estende o motor de relatórios dinâmicos do Odoo, por isso estes relatórios não aparecem no seletor de variantes dele.
- **Escopo do relatório de impostos.** Só são listados impostos cujo `type_tax_use` seja `sale` ou `purchase`; impostos com *None* nunca aparecem.
- **Coluna «Analítica».** A informação analítica é lida de `analytic_distribution`; os percentuais mostrados são os da distribuição, não valores.

## 14. Para desenvolvedores: o contrato estável

Módulos irmãos podem contar com o seguinte, que não mudará:

**Modelo** `odomate.account.report.filter` (`TransientModel` concreto, base para herança por protótipo) com os campos `company_id`, `date_from`, `date_to`, `journal_ids`, `target_move` e os métodos:

| Elemento | Tipo | Finalidade |
|---|---|---|
| `_odomate_journals()` | registro | Diários selecionados, ou todos os diários da empresa |
| `_odomate_state_domain()` | registro | Condição de situação para o `target_move` escolhido |
| `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` | registro | O domínio base dos itens de diário |
| `_odomate_check_filter()` | registro | Validação; estenda com `super()` |
| `_odomate_report_data()` | registro | A carga contendo apenas tipos primitivos |
| `_odomate_print(report_xmlid=None)` | registro | Validar e retornar a ação de relatório |
| `action_odomate_print()` | registro | O botão Imprimir da janela |
| `_odomate_report_xmlid` | atributo de classe | XML ID padrão do relatório da janela |
| `_odomate_options_from_data(data)` | modelo | Converte a carga de volta em registros e datas |
| `_odomate_check_report_access()` | modelo | Lança `AccessError` fora dos três grupos contábeis |
| `_odomate_initial_balance_domain(company, date_from, journals=None, target_move='posted')` | modelo | Domínio do saldo de abertura |

**Visão** `odomate_account_ledger_reports.view_odomate_account_report_filter_form` — herde com `mode="primary"` e acrescente seus campos após o nó `journal_ids` ou o nó `target_move`. Esses são os dois únicos pontos de ancoragem suportados.

**QWeb** `odomate_account_ledger_reports.report_filter_header` — parâmetros `company`, `date_from`, `date_to`, `journals`, `target_move_label`.

**Formato de papel** `odomate_account_ledger_reports.paperformat_odomate_ledger_landscape` — A4 paisagem, margens de 10 mm.

**Menu** `odomate_account_ledger_reports.menu_odomate_account_reports_audit` — a pasta *Relatórios de auditoria*.

Todo o restante — campos de cada janela, métodos auxiliares de montagem de linhas, nomes dos modelos de relatório, redação dos modelos QWeb, ordem das chaves dos dicionários — é interno e pode mudar.

---

© OdoMate · <https://odomate.pro> · <support@odomate.pro>
