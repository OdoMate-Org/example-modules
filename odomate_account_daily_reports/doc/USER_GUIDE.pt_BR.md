# Relatórios contábeis diários — guia do usuário

Impressões em PDF do livro diário, do livro caixa e do livro banco para o Odoo 19 Community.

## Sumário

1. [Visão geral](#1-visão-geral)
2. [Instalação](#2-instalação)
3. [Quem pode usar](#3-quem-pode-usar)
4. [Livro diário](#4-livro-diário)
5. [Livro caixa](#5-livro-caixa)
6. [Livro banco](#6-livro-banco)
7. [Como os valores são calculados](#7-como-os-valores-são-calculados)
8. [Multiempresa](#8-multiempresa)
9. [Limitações](#9-limitações)
10. [Suporte](#10-suporte)

## 1. Visão geral

O módulo adiciona três livros imprimíveis em **Financeiro → Relatórios → Audit Reports**:

| Relatório | O que traz | Diários abrangidos |
|---|---|---|
| **Livro diário** | Todos os itens de lançamento do período, agrupados em um bloco por dia do calendário | Todos os tipos de diário |
| **Livro caixa** | Movimentos de caixa por conta, com saldo acumulado | diários do tipo `cash` |
| **Livro banco** | Movimentos de banco e cartão de crédito por conta, com saldo acumulado | diários do tipo `bank` e `credit` |

Os três relatórios são **somente leitura**. Nunca criam, alteram ou excluem um registro, portanto não são afetados pelas datas de bloqueio e podem ser executados com segurança por um contador com permissão apenas de leitura.

O módulo reaproveita a janela de filtros compartilhada, o cabeçalho de página e o formato de papel paisagem do **Accounting Audit Reports** (`odomate_account_ledger_reports`), de modo que os seis relatórios tenham aparência e comportamento consistentes.

O cabeçalho impresso — empresa, período, diários e a seleção de **Lançamentos** (*Somente lançamentos publicados* / *Todos os lançamentos*) — é exibido no idioma da sua sessão, graças às traduções próprias do módulo (`uk`, `pl`, `de`, `es`, `fr`, `pt_BR`).

## 2. Instalação

1. Copie `odomate_account_daily_reports` para o caminho de addons do seu Odoo.
2. **Aplicativos → Atualizar lista de aplicativos**.
3. Procure por *Accounting Daily Reports* e clique em **Instalar**.

`account` e `odomate_account_ledger_reports` são instalados automaticamente caso ainda não estejam presentes.

## 3. Quem pode usar

Os três menus e as três janelas estão disponíveis para:

- `account.group_account_manager` — administrador contábil
- `account.group_account_user` — recursos contábeis completos
- `account.group_account_readonly` — contabilidade somente leitura

Usuários que possuem apenas `account.group_account_invoice` (Faturamento) não veem o menu nem têm acesso: a impressão gera a mensagem *"Only accounting users can print accounting reports."*

O módulo **não cria nenhum grupo de segurança novo** e não altera nenhum usuário.

## 4. Livro diário

**Financeiro → Relatórios → Audit Reports → Day Book**

| Campo | Significado |
|---|---|
| **Lançamentos** | *Somente lançamentos publicados* ou *Todos os lançamentos* (inclui rascunhos). Lançamentos cancelados nunca aparecem. |
| **Data inicial** / **Data final** | Ambas são **obrigatórias**. Por padrão, assumem a data de hoje. |
| **Diários** | Deixe em branco para abranger todos os diários da empresa. |
| **Empresa** | Visível em configurações multiempresa. |

Clique em **Print** para obter o PDF ou em **Cancel** para fechar a janela.

A impressão agrupa os itens em um bloco por dia. As colunas são *Diário, Lançamento, Parceiro, Referência, Rótulo, Débito, Crédito, Diferença* (além de *Moeda* para usuários multimoeda). Cada dia encerra com uma linha **Total do dia**, e o relatório com uma linha **Total**.

Dias sem itens não geram bloco — o relatório nunca imprime um dia vazio. Se nada corresponder, o PDF exibe *"No entries in this period."*

O livro diário **não tem saldo inicial nem saldo acumulado**: é uma relação cronológica, não um razão.

## 5. Livro caixa

**Financeiro → Relatórios → Audit Reports → Cash Book**

Os mesmos filtros do livro diário, e ainda:

| Campo | Significado |
|---|---|
| **Ordenar por** | *Data* ou *Diário e parceiro* — altera a ordem dos itens dentro de cada conta. |
| **Exibir contas** | *Todas as contas*, *Com movimentos* (padrão) ou *Com saldo diferente de zero*. |
| **Incluir saldo inicial** | Imprime uma linha **Saldo inicial** por conta. Exige uma data inicial. |
| **Com moeda** | Acrescenta a coluna *Moeda*. Visível apenas para usuários do grupo **Multimoeda**. |

O campo **Diários** aceita somente diários de caixa. Escolher um diário bancário gera a mensagem *"This book only covers cash journals."*

A impressão traz um bloco por conta, ordenadas pelo código da conta, com as colunas *Data, Diário, Lançamento, Parceiro, Referência, Rótulo, Débito, Crédito, Saldo*. Cada bloco encerra com uma linha **Total da conta**, e o relatório com uma linha **Total**.

### Quais contas aparecem

O livro caixa não lista simplesmente "tudo o que os diários de caixa tocaram". O conjunto de contas é resolvido a partir de:

- a **conta padrão** e a **conta transitória** de cada diário,
- as contas de **recebimentos pendentes / pagamentos pendentes** de cada diário,
- e toda conta do tipo `asset_cash` efetivamente movimentada por um item no período.

Contas pertencentes a outra empresa são descartadas. Assim, um diário de caixa sem conta padrão configurada ainda é impresso corretamente.

## 6. Livro banco

**Financeiro → Relatórios → Audit Reports → Bank Book**

Idêntico ao livro caixa, exceto por abranger os diários de **banco** e de **cartão de crédito**, e por seu conjunto de contas incluir também as contas do tipo `liability_credit_card`. Escolher um diário de caixa gera a mensagem *"This book only covers bank and credit card journals."*

## 7. Como os valores são calculados

### Saldo inicial

Com **Incluir saldo inicial** marcado, a linha de saldo inicial soma tudo o que foi registrado naquela conta **antes da data inicial**, usando a mesma regra respeitando o exercício fiscal do razão geral do *Accounting Audit Reports*. Para contas de caixa e de cartão de crédito, que sempre transportam seu saldo, isso equivale simplesmente a todos os itens anteriores.

### Saldo acumulado

A coluna **Saldo** é um verdadeiro saldo acumulado por conta:

```
saldo de uma linha = saldo da linha anterior + débito desta linha − crédito desta linha
```

A primeira linha parte do saldo inicial, ou de zero quando o saldo inicial não é impresso.

### Saldo final

```
Total da conta = Saldo inicial + Σ débito − Σ crédito
```

Ele é somado a partir dos itens, nunca lido da última linha.

### Exemplo numérico

Conta **101100 Cash A**, período 01/03/2024 → 31/03/2024, com saldo inicial ativado.

| Linha | Débito | Crédito | Saldo |
|---|---:|---:|---:|
| Saldo inicial | 1.000,00 | 0,00 | **1.000,00** |
| 05/03/2024 CASH-IN | 200,00 | 0,00 | **1.200,00** |
| 10/03/2024 CASH-OUT | 0,00 | 50,00 | **1.150,00** |
| **Total da conta** | **200,00** | **50,00** | **1.150,00** |

Conferência: `1.000,00 + 200,00 − 50,00 = 1.150,00`.

O mesmo período no livro diário, para 05/03/2024 — um recebimento em espécie de 200,00 e um recebimento bancário de 300,00:

| | Débito | Crédito | Diferença |
|---|---:|---:|---:|
| **Total do dia** | 500,00 | 500,00 | **0,00** |

Em uma contabilidade equilibrada, a coluna **Diferença** é sempre 0,00; um valor diferente de zero aponta um lançamento desbalanceado.

### Moeda

Todos os valores são impressos na **moeda da empresa** — nada é convertido. A coluna opcional *Moeda* mostra o valor do item em sua própria moeda sempre que essa moeda for diferente da moeda da empresa, inclusive valores negativos.

## 8. Multiempresa

Cada impressão abrange exatamente uma empresa — a escolhida na janela. Itens de outras empresas nunca aparecem. Escolher uma empresa na qual você não tem permissão para trabalhar gera a mensagem *"You cannot print a report for a company you are not allowed to work in."*

Os quatro modelos de janela são transitórios e não guardam dados próprios de empresa, portanto nenhuma regra de registro é necessária: o filtro por empresa está na etapa de validação e em todos os domínios.

## 9. Limitações

- **Somente PDF e HTML.** Não há exportação para XLSX ou CSV, nem versão interativa em tela.
- **Sem detalhamento.** O PDF é uma impressão; clicar em um valor não abre o lançamento correspondente.
- **Uma empresa por impressão.** Livros multiempresa consolidados não são suportados.
- **Sem conversão de moeda.** Itens em moeda estrangeira são exibidos pelo valor registrado na moeda da empresa; o relatório não os reconverte a uma taxa escolhida.
- **Sem colunas analíticas.** Se precisar da distribuição analítica, use o razão geral do *Accounting Audit Reports*.
- **O livro diário não tem saldos**, por definição; para saldos acumulados e finais use o livro caixa ou o livro banco.
- **Sem dados de demonstração.** Estes relatórios imprimem o que a sua base de dados já contém.

## 10. Suporte

- Autor: OdoMate — <https://odomate.pro>
- Suporte: <support@odomate.pro>

Versão em inglês deste guia: `USER_GUIDE.md`.
