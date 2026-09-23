# Informes contables diarios — guía del usuario

Impresiones en PDF del libro diario, el libro de caja y el libro de bancos para Odoo 19 Community.

## Índice

1. [Descripción general](#1-descripción-general)
2. [Instalación](#2-instalación)
3. [Quién puede usarlo](#3-quién-puede-usarlo)
4. [Libro diario](#4-libro-diario)
5. [Libro de caja](#5-libro-de-caja)
6. [Libro de bancos](#6-libro-de-bancos)
7. [Cómo se calculan los importes](#7-cómo-se-calculan-los-importes)
8. [Multicompañía](#8-multicompañía)
9. [Limitaciones](#9-limitaciones)
10. [Soporte](#10-soporte)

## 1. Descripción general

El módulo añade tres libros imprimibles en **Contabilidad → Informes → Audit Reports**:

| Informe | Qué muestra | Diarios cubiertos |
|---|---|---|
| **Libro diario** | Todos los apuntes del período, agrupados en un bloque por día natural | Todos los tipos de diario |
| **Libro de caja** | Movimientos de caja por cuenta, con saldo acumulado | diarios de tipo `cash` |
| **Libro de bancos** | Movimientos de banco y tarjeta de crédito por cuenta, con saldo acumulado | diarios de tipo `bank` y `credit` |

Los tres informes son **de solo lectura**. Nunca crean, modifican ni eliminan un registro, por lo que no se ven afectados por las fechas de bloqueo y pueden ejecutarse con seguridad desde un perfil contable de solo lectura.

El módulo reutiliza el diálogo de filtros compartido, la cabecera de página y el formato de papel horizontal de **Accounting Audit Reports** (`odomate_account_ledger_reports`), de modo que los seis informes tienen un aspecto y un comportamiento coherentes.

La cabecera impresa — empresa, período, diarios y la selección de **Asientos** (*Solo asientos contabilizados* / *Todos los asientos*) — se muestra en el idioma de su sesión, gracias a las traducciones propias del módulo (`uk`, `pl`, `de`, `es`, `fr`, `pt_BR`).

## 2. Instalación

1. Copie `odomate_account_daily_reports` en la ruta de addons de su Odoo.
2. **Aplicaciones → Actualizar lista de aplicaciones**.
3. Busque *Accounting Daily Reports* y pulse **Instalar**.

`account` y `odomate_account_ledger_reports` se instalan automáticamente si aún no están presentes.

## 3. Quién puede usarlo

Los tres menús y los tres diálogos están disponibles para:

- `account.group_account_manager` — administrador de contabilidad
- `account.group_account_user` — funciones contables completas
- `account.group_account_readonly` — contabilidad de solo lectura

Los usuarios que solo tienen `account.group_account_invoice` (Facturación) no ven el menú ni tienen acceso: al imprimir se muestra *«Only accounting users can print accounting reports.»*

El módulo **no crea ningún grupo de seguridad nuevo** ni modifica ningún usuario.

## 4. Libro diario

**Contabilidad → Informes → Audit Reports → Day Book**

| Campo | Significado |
|---|---|
| **Asientos** | *Solo asientos contabilizados* o *Todos los asientos* (añade borradores). Los asientos cancelados no aparecen nunca. |
| **Fecha inicial** / **Fecha final** | Ambas son **obligatorias**. Por defecto toman la fecha de hoy. |
| **Diarios** | Déjelo vacío para incluir todos los diarios de la compañía. |
| **Compañía** | Visible en configuraciones multicompañía. |

Pulse **Print** para obtener el PDF, o **Cancel** para cerrar el diálogo.

La impresión agrupa los apuntes en un bloque por día. Las columnas son *Diario, Asiento, Empresa, Referencia, Etiqueta, Debe, Haber, Diferencia* (además de *Moneda* para los usuarios multimoneda). Cada día cierra con una fila **Total del día**, y el informe con una fila **Total**.

Los días sin apuntes no generan bloque: el informe nunca imprime un día vacío. Si no hay coincidencias, el PDF muestra *«No entries in this period.»*

El libro diario **no tiene saldo inicial ni saldo acumulado**: es una relación cronológica, no un mayor.

## 5. Libro de caja

**Contabilidad → Informes → Audit Reports → Cash Book**

Los mismos filtros que el libro diario, y además:

| Campo | Significado |
|---|---|
| **Ordenar por** | *Fecha* o *Diario y empresa* — cambia el orden de los apuntes dentro de cada cuenta. |
| **Mostrar cuentas** | *Todas las cuentas*, *Con movimientos* (por defecto) o *Con saldo distinto de cero*. |
| **Incluir saldo inicial** | Imprime una fila **Saldo inicial** por cuenta. Requiere una fecha inicial. |
| **Con moneda** | Añade la columna *Moneda*. Solo visible para los usuarios del grupo **Multimoneda**. |

El campo **Diarios** solo acepta diarios de caja. Elegir un diario de banco provoca el mensaje *«This book only covers cash journals.»*

La impresión tiene un bloque por cuenta, ordenadas por código de cuenta, con las columnas *Fecha, Diario, Asiento, Empresa, Referencia, Etiqueta, Debe, Haber, Saldo*. Cada bloque cierra con una fila **Total de la cuenta**, y el informe con una fila **Total**.

### Qué cuentas aparecen

El libro de caja no se limita a listar «todo lo que tocaron los diarios de caja». El conjunto de cuentas se resuelve a partir de:

- la **cuenta por defecto** y la **cuenta transitoria** de cada diario,
- las cuentas de **cobros pendientes / pagos pendientes** de cada diario,
- y toda cuenta de tipo `asset_cash` realmente utilizada por un apunte del período.

Las cuentas pertenecientes a otra compañía se descartan. Gracias a ello, un diario de caja sin cuenta por defecto configurada se imprime igualmente de forma correcta.

## 6. Libro de bancos

**Contabilidad → Informes → Audit Reports → Bank Book**

Idéntico al libro de caja, salvo que cubre los diarios de **banco** y de **tarjeta de crédito**, y que su conjunto de cuentas incluye además las cuentas de tipo `liability_credit_card`. Elegir un diario de caja provoca el mensaje *«This book only covers bank and credit card journals.»*

## 7. Cómo se calculan los importes

### Saldo inicial

Con **Incluir saldo inicial** marcado, la fila de saldo inicial suma todo lo contabilizado en esa cuenta **antes de la fecha inicial**, con la misma regla respetuosa con el ejercicio fiscal que el libro mayor de *Accounting Audit Reports*. Para las cuentas de caja y de tarjeta de crédito, que siempre arrastran su saldo, esto equivale sencillamente a todos los apuntes anteriores.

### Saldo acumulado

La columna **Saldo** es un verdadero saldo acumulado por cuenta:

```
saldo de una fila = saldo de la fila anterior + debe de esta fila − haber de esta fila
```

La primera fila parte del saldo inicial, o de cero cuando el saldo inicial no se imprime.

### Saldo final

```
Total de la cuenta = Saldo inicial + Σ debe − Σ haber
```

Se suma a partir de los apuntes, nunca se lee de la última fila.

### Ejemplo numérico

Cuenta **101100 Cash A**, período 01/03/2024 → 31/03/2024, con saldo inicial activado.

| Fila | Debe | Haber | Saldo |
|---|---:|---:|---:|
| Saldo inicial | 1.000,00 | 0,00 | **1.000,00** |
| 05/03/2024 CASH-IN | 200,00 | 0,00 | **1.200,00** |
| 10/03/2024 CASH-OUT | 0,00 | 50,00 | **1.150,00** |
| **Total de la cuenta** | **200,00** | **50,00** | **1.150,00** |

Comprobación: `1.000,00 + 200,00 − 50,00 = 1.150,00`.

El mismo período en el libro diario, para el 05/03/2024 — un cobro en efectivo de 200,00 y un cobro bancario de 300,00:

| | Debe | Haber | Diferencia |
|---|---:|---:|---:|
| **Total del día** | 500,00 | 500,00 | **0,00** |

En una contabilidad cuadrada, la columna **Diferencia** siempre vale 0,00; un valor distinto de cero señala un asiento descuadrado.

### Moneda

Todos los importes se imprimen en la **moneda de la compañía**: no se convierte nada. La columna opcional *Moneda* muestra el importe del apunte en su propia moneda siempre que esta difiera de la moneda de la compañía, incluidos los importes negativos.

## 8. Multicompañía

Cada impresión cubre exactamente una compañía: la elegida en el diálogo. Los apuntes de otras compañías no aparecen nunca. Elegir una compañía en la que no tiene permiso para trabajar provoca el mensaje *«You cannot print a report for a company you are not allowed to work in.»*

Los cuatro modelos de diálogo son transitorios y no almacenan datos propios de compañía, por lo que no hace falta una regla de registro: el filtro de compañía vive en el paso de validación y en todos los dominios.

## 9. Limitaciones

- **Solo PDF y HTML.** No hay exportación a XLSX ni CSV, ni versión interactiva en pantalla.
- **Sin desglose.** El PDF es una impresión; pulsar sobre un importe no abre el asiento subyacente.
- **Una compañía por impresión.** No se admiten libros multicompañía consolidados.
- **Sin conversión de moneda.** Los apuntes en moneda extranjera se muestran por su valor contabilizado en la moneda de la compañía; el informe no los reconvierte a un tipo de cambio elegido.
- **Sin columnas analíticas.** Si necesita la distribución analítica, use el libro mayor de *Accounting Audit Reports*.
- **El libro diario no tiene saldos**, por diseño; para saldos acumulados y finales use el libro de caja o el de bancos.
- **Sin datos de demostración.** Estos informes imprimen lo que ya contiene su base de datos.

## 10. Soporte

- Autor: OdoMate — <https://odomate.pro>
- Soporte: <support@odomate.pro>

Versión en inglés de esta guía: `USER_GUIDE.md`.
