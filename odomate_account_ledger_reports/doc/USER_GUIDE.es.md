# Informes contables de auditoría — Guía de usuario

Módulo: `odomate_account_ledger_reports` · Odoo 19.0 · Versión 19.0.1.0.1 · Licencia LGPL-3

## Índice

1. [Qué hace este módulo](#1-qué-hace-este-módulo)
2. [Instalación](#2-instalación)
3. [Quién puede usarlo](#3-quién-puede-usarlo)
4. [Dónde están los informes](#4-dónde-están-los-informes)
5. [El filtro común](#5-el-filtro-común)
6. [Libro mayor](#6-libro-mayor)
7. [Mayor de empresas](#7-mayor-de-empresas)
8. [Saldos por antigüedad](#8-saldos-por-antigüedad)
9. [Informe de impuestos](#9-informe-de-impuestos)
10. [Auditoría de diarios](#10-auditoría-de-diarios)
11. [Impresión del asiento contable](#11-impresión-del-asiento-contable)
12. [Pantallas de apuntes contables](#12-pantallas-de-apuntes-contables)
13. [Limitaciones conocidas](#13-limitaciones-conocidas)
14. [Para desarrolladores: el contrato estable](#14-para-desarrolladores-el-contrato-estable)

---

## 1. Qué hace este módulo

Añade los seis informes contables de auditoría clásicos que piden auditores y contables, como documentos PDF sencillos, más dos pantallas de apuntes contables listas para usar.

| Informe | Responde a |
|---|---|
| Libro mayor | Qué movimientos hubo en cada cuenta, con saldo acumulado |
| Mayor de empresas | Qué movimientos hubo en las cuentas de clientes y proveedores y cuánto deben aún |
| Saldos por antigüedad | Cuánto se ha vencido cada apunte abierto, por tramos de antigüedad |
| Informe de impuestos | Bases e importes de impuesto por cada impuesto, separados en Ventas y Compras |
| Auditoría de diarios | Todos los apuntes de los diarios seleccionados, con resumen de impuestos |
| Asiento contable | Una página por asiento, para archivar o adjuntar a un justificante |

Todos los informes leen los apuntes contables únicamente a través del ORM de Odoo. El módulo no escribe nada fuera de sus propios registros de diálogo ni añade ningún campo a los modelos estándar.

## 2. Instalación

1. Copie la carpeta `odomate_account_ledger_reports` en su ruta de addons.
2. **Aplicaciones → Actualizar lista de aplicaciones**.
3. Busque *Accounting Audit Reports* y pulse **Activar**.

Las únicas dependencias son `account` y `analytic`, ambas incluidas en Odoo Community. Tras la instalación no hace falta configurar nada: no hay página de ajustes, ni tarea programada, ni datos de demostración.

## 3. Quién puede usarlo

Tres grupos contables ya existentes de Odoo pueden abrir los diálogos e imprimir:

- `account.group_account_manager` — administrador de facturación
- `account.group_account_user` — contable
- `account.group_account_readonly` — acceso contable de solo lectura

El módulo no crea ningún grupo propio ni concede nada a otros grupos. Un usuario ajeno a estos tres obtiene `Solo los usuarios de contabilidad pueden imprimir informes contables.` si intenta imprimir, y no ve los menús.

Cada registro de diálogo es transitorio (asistente): los tres grupos tienen lectura, escritura y creación, y nadie tiene borrado — de eso se encarga la limpieza propia de Odoo.

## 4. Dónde están los informes

| Informe | Ruta de menú |
|---|---|
| Libro mayor | Contabilidad → Informes → Informes de auditoría → Libro mayor |
| Auditoría de diarios | Contabilidad → Informes → Informes de auditoría → Auditoría de diarios |
| Mayor de empresas | Contabilidad → Informes → Informes de empresas → Mayor de empresas |
| Saldos por antigüedad | Contabilidad → Informes → Informes de empresas → Saldos por antigüedad |
| Saldos a cobrar por antigüedad | Contabilidad → Informes → Informes de empresas → Saldos a cobrar por antigüedad |
| Saldos a pagar por antigüedad | Contabilidad → Informes → Informes de empresas → Saldos a pagar por antigüedad |
| Informe de impuestos | Contabilidad → Informes → Impuestos → Informe de impuestos |
| Apuntes contables por cuenta | Contabilidad → Informes → Gestión → Apuntes contables por cuenta |
| Apuntes contables por empresa | Contabilidad → Informes → Gestión → Apuntes contables por empresa |

*Saldos a cobrar* y *Saldos a pagar por antigüedad* son el mismo diálogo que *Saldos por antigüedad*, con el tipo de cuenta preseleccionado y oculto.

La impresión de asientos no tiene menú: seleccione uno o varios asientos en **Contabilidad → Contabilidad → Asientos contables** y use **Imprimir → Asiento contable**.

## 5. El filtro común

Todos los diálogos parten del mismo conjunto de cuatro campos.

| Campo | Significado |
|---|---|
| **Asientos** | *Solo asientos contabilizados* (por defecto) o *Todos los asientos*. Los asientos cancelados nunca se incluyen. |
| **Fecha inicial** / **Fecha final** | Acotan los apuntes por su fecha contable. Déjelas vacías para «todas las fechas» donde el diálogo lo permita. |
| **Diarios** | Déjelo vacío para incluir todos los diarios de la compañía. |
| **Compañía** | Visible solo en bases multicompañía. Por defecto, su compañía activa. |

Pulse **Imprimir** para generar el PDF o **Cancelar** para cerrar.

El diálogo rechaza la impresión y explica el motivo cuando:

- la compañía elegida no es una en la que tenga permiso para trabajar;
- la fecha inicial es posterior a la final;
- un diario seleccionado pertenece a otra compañía.

## 6. Libro mayor

**Campos adicionales:** Cuentas, Empresas, Cuentas analíticas (solo con *Contabilidad analítica*), Ordenar por, Mostrar cuentas, Incluir saldo de apertura.

**Columnas:** Fecha · Diario · Empresa · Referencia · Asiento · Descripción · Debe · Haber · Saldo, más Divisa (usuarios multidivisa, solo cuando la divisa del apunte difiere de la de la compañía) y Analítica (usuarios de contabilidad analítica).

**Mostrar cuentas**

- *Todas las cuentas* — todas las cuentas de la compañía, incluso sin movimiento.
- *Con movimientos* (por defecto) — cuentas con apuntes en el período o con apertura distinta de cero.
- *Con saldo distinto de cero* — descarta cuentas cuyo apertura + debe − haber redondea a cero.

**Ordenar por** cambia el orden dentro de cada cuenta: *Fecha* ordena por fecha, número de asiento e id; *Diario y empresa* ordena por diario, luego empresa, luego fecha.

### Ejemplo numérico — el saldo de apertura

Libros de la compañía, ejercicio = año natural, fecha inicial **2024-03-01**, **Incluir saldo de apertura** marcado.

| Asiento | Fecha | Cuenta 121000 (Clientes) | Cuenta 400000 (Ingresos) |
|---|---|---|---|
| E1 | 2023-06-15 | debe 1.000,00 | haber 1.000,00 |
| E2 | 2024-02-10 | debe 500,00 | haber 500,00 |
| E3 | 2024-03-15 | debe 250,00 | haber 250,00 |

Aperturas impresas:

- **121000** es una cuenta de balance, así que abre con *todo* lo contabilizado antes de la fecha inicial: 1.000,00 + 500,00 = **1.500,00**.
- **400000** es una cuenta de resultados, así que abre solo con el ejercicio en curso: E1 cae en el ejercicio anterior y se excluye, quedando **−500,00**.

El saldo acumulado de 121000 muestra entonces 1.500,00 en la fila *Saldo de apertura* y 1.750,00 tras E3; la línea de total de la cuenta muestra Debe 250,00, Haber 0,00, Saldo 1.750,00.

## 7. Mayor de empresas

**Campos adicionales:** Empresas, Tipo de cuenta, Incluir apuntes liquidados, Mostrar importe en divisa (usuarios multidivisa).

**Tipo de cuenta** se corresponde con los tipos de cuenta de Odoo: *Cuentas a cobrar* → `asset_receivable`, *Cuentas a pagar* → `liability_payable`, *Cuentas a cobrar y a pagar* → ambos.

**Columnas:** Fecha · Diario · Cuenta · Asiento · Referencia · Descripción · Debe · Haber · Saldo (reiniciado a cero para cada empresa), más Divisa.

Cada bloque de empresa termina con Debe, Haber, saldo final e **Importe pendiente** — la suma de los importes residuales de los apuntes.

Un apunte queda oculto salvo que marque **Incluir apuntes liquidados** solo cuando está *totalmente* liquidado — es decir, cuando todos los apuntes del otro lado de su conciliación también han sido emparejados y no queda nada pendiente. Una factura pagada parcialmente sigue imprimiendo tanto su propia línea como la de su cobro hasta que eso ocurre, de modo que el saldo final siempre refleja lo que aún está pendiente; una factura totalmente cobrada y su cobro desaparecen juntos, y vuelven a aparecer juntos al marcar **Incluir apuntes liquidados**. Los apuntes sin empresa nunca se imprimen aquí; su sitio es el Libro mayor.

También puede imprimirlo directamente desde un contacto: seleccione uno o varios contactos en **Contactos** y use **Imprimir → Mayor de empresas**. El diálogo se abre con esas empresas, el tipo de cuenta *Cuentas a cobrar y a pagar* y los apuntes liquidados incluidos.

### Ejemplo numérico — una factura pagada parcialmente mantiene su cobro en su propia línea

Se contabiliza una factura de cliente de 1.000,00 y se cobra parcialmente con 400,00. Impreso con **Incluir apuntes liquidados** desmarcado:

| Línea | Debe | Haber | Saldo |
|---|---|---|---|
| Factura | 1.000,00 | | 1.000,00 |
| Cobro | | 400,00 | 600,00 |
| **Total de la empresa** | **1.000,00** | **400,00** | **600,00** |

**Importe pendiente** también muestra 600,00 — ambas líneas se imprimen porque aún quedan 600,00 pendientes en la factura, aunque el propio cobro ya no tenga nada que emparejar. Cuando la factura se pague por completo, ambas líneas desaparecerán de la vista sin marcar y solo volverán a aparecer juntas al marcar **Incluir apuntes liquidados**.

## 8. Saldos por antigüedad

**Campos adicionales:** A fecha de (obligatorio, por defecto hoy), Duración del período (días) (obligatorio, por defecto 30), Tipo de cuenta, Empresas. Fecha inicial y Diarios no se usan en este informe y están ocultos.

Cada apunte abierto se coloca en una de seis columnas según su antigüedad en días enteros, donde antigüedad = *A fecha de* − (fecha de vencimiento, o fecha contable si no hay vencimiento):

| Columna | Antigüedad (P = Duración del período) |
|---|---|
| No vencido | antigüedad ≤ 0 |
| 1 - P | 1 … P |
| P+1 - 2P | P+1 … 2P |
| 2P+1 - 3P | 2P+1 … 3P |
| 3P+1 - 4P | 3P+1 … 4P |
| +4P | antigüedad > 4P |

Una fila con las seis columnas a cero se descarta. Los apuntes sin empresa se agrupan en una fila **Empresa desconocida**. Todos los importes están en la divisa de la compañía; no se aplica ninguna conversión.

### Ejemplo numérico — tramos con P = 30, a fecha 2024-06-30

| Apunte | Vencimiento | Antigüedad | Importe | Columna |
|---|---|---|---|---|
| A | 2024-06-30 | 0 | 10,00 | No vencido |
| B | 2024-06-29 | 1 | 20,00 | 1 - 30 |
| C | 2024-05-31 | 30 | 30,00 | 1 - 30 |
| D | 2024-05-30 | 31 | 40,00 | 31 - 60 |
| E | 2024-03-01 | 121 | 50,00 | +120 |

Fila impresa: No vencido 10,00 · 1-30 50,00 · 31-60 40,00 · 61-90 0,00 · 91-120 0,00 · +120 50,00 · Total 150,00.

### Ejemplo numérico — el importe residual se mide *a la fecha*

Una factura de 1.000,00 se contabiliza el 2024-03-10 y se cobra parcialmente con 400,00 el 2024-05-20.

- A **2024-04-30** el cobro aún no ha ocurrido, así que el informe muestra **1.000,00**.
- A **2024-06-30** muestra **600,00**, y la propia línea de cobro queda a cero y desaparece.

El informe recalcula el residual a partir del histórico de conciliación en lugar de leer el `amount_residual` de hoy, que es lo que hace correcta una antigüedad retroactiva.

## 9. Informe de impuestos

Solo se aplica el filtro común; Fecha inicial y Fecha final son obligatorias y toman por defecto el primer día del mes en curso y hoy.

El informe lista todos los impuestos activos de venta y compra de la compañía en dos secciones. Un grupo de impuestos se representa por sus impuestos hijos bajo el tipo del impuesto padre; el grupo en sí no es una fila. Por cada impuesto:

- **Base imponible** — la suma de los saldos de los apuntes que llevan el impuesto.
- **Importe del impuesto** — la suma de los saldos de las líneas de impuesto generadas por él.

En la sección **Ventas** ambas cifras cambian de signo para que los ingresos se lean en positivo; en **Compras** se imprimen tal como están contabilizadas. Nunca se toma un valor absoluto, de modo que las facturas rectificativas reducen realmente las cifras. Las filas a cero en ambas cifras se omiten y una sección vacía imprime *No hay movimientos de impuestos en este período.*

### Ejemplo numérico — una rectificativa reduce las cifras de ventas

Marzo de 2024, un impuesto de ventas del 20 %:

| Documento | Base | Impuesto |
|---|---|---|
| Factura de cliente, 1.000,00 + 20 % | 1.000,00 | 200,00 |
| Factura rectificativa, 400,00 + 20 % | −400,00 | −80,00 |
| **Fila «Ventas» impresa** | **600,00** | **120,00** |

## 10. Auditoría de diarios

**Campos adicionales:** Diarios (obligatorio — por defecto los diarios de venta y compra de su compañía), Ordenar asientos por, Mostrar importe en divisa.

Una sección por cada diario seleccionado, en el orden propio de los diarios. **Columnas:** Asiento · Fecha · Cuenta · Empresa · Descripción · Debe · Haber, más Divisa. Cada sección termina con los totales de Debe y Haber del diario.

Cuando el diario tiene apuntes con impuestos, a continuación aparece una pequeña tabla resumen Impuesto / Importe base / Importe del impuesto con la misma regla de signo que el Informe de impuestos (impuestos de venta con signo cambiado). Los diarios sin apuntes con impuestos simplemente no tienen esa tabla.

## 11. Impresión del asiento contable

Sin diálogo: seleccione asientos y use **Imprimir → Asiento contable**. Una página por asiento, cada uno impreso con el membrete y la divisa de su propia compañía.

La cabecera muestra el número de asiento, diario, fecha, empresa, referencia y estado. La tabla de apuntes muestra Cuenta · Descripción · Empresa · Analítica · Debe · Haber · Divisa, en el orden propio de líneas del asiento, excluyendo líneas de sección, subsección y nota. La fila de totales suma debe y haber en la divisa de la compañía del asiento — iguales en cualquier asiento contabilizado.

## 12. Pantallas de apuntes contables

Dos vistas guardadas sobre `account.move.line`, ambas en lista / tabla dinámica / gráfico con el panel de búsqueda estándar de apuntes de Odoo, y ambas excluyendo líneas de sección, subsección y nota:

- **Apuntes contables por cuenta** — agrupado por cuenta, solo asientos contabilizados.
- **Apuntes contables por empresa** — agrupado por empresa, asientos contabilizados, prefiltrado a cuentas a cobrar, a pagar y apuntes no conciliados.

Son listas normales de Odoo: puede reagrupar, filtrar, exportar y entrar en un asiento desde ahí.

## 13. Limitaciones conocidas

- **Solo divisa de la compañía.** Cada cifra es el importe en divisa de la compañía. La columna opcional Divisa muestra el importe en moneda extranjera del apunte como referencia; no se convierte nada.
- **Sin exportación a Excel.** Los informes son solo PDF. Use las dos pantallas de apuntes cuando necesite una hoja de cálculo.
- **Los saldos por antigüedad ignoran los diarios.** Por diseño cubren todos los diarios de la compañía; el campo Diarios está oculto en ese diálogo.
- **Sin navegación al detalle.** Los PDF son documentos estáticos; no enlazan de vuelta a Odoo.
- **`account.report` intacto.** El módulo no extiende el motor de informes dinámicos de Odoo, por lo que estos informes no aparecen en su selector de variantes.
- **Alcance del informe de impuestos.** Solo se listan impuestos cuyo `type_tax_use` sea `sale` o `purchase`; los impuestos con *None* nunca aparecen.
- **Columna «Analítica».** La información analítica se lee de `analytic_distribution`; los porcentajes mostrados son los de la distribución, no importes.

## 14. Para desarrolladores: el contrato estable

Los módulos hermanos pueden confiar en lo siguiente, que no cambiará:

**Modelo** `odomate.account.report.filter` (`TransientModel` concreto, base de herencia por prototipo) con los campos `company_id`, `date_from`, `date_to`, `journal_ids`, `target_move` y los métodos:

| Elemento | Tipo | Propósito |
|---|---|---|
| `_odomate_journals()` | registro | Diarios seleccionados, o todos los de la compañía |
| `_odomate_state_domain()` | registro | Condición de estado para el `target_move` elegido |
| `_odomate_line_domain(date_field='date', date_from=None, date_to=None)` | registro | El dominio base de apuntes contables |
| `_odomate_check_filter()` | registro | Validación; amplíelo con `super()` |
| `_odomate_report_data()` | registro | Carga útil con solo valores primitivos |
| `_odomate_print(report_xmlid=None)` | registro | Validar y devolver la acción de informe |
| `action_odomate_print()` | registro | El botón Imprimir del diálogo |
| `_odomate_report_xmlid` | atributo de clase | XML ID del informe por defecto del diálogo |
| `_odomate_options_from_data(data)` | modelo | Convierte la carga útil de nuevo en registros y fechas |
| `_odomate_check_report_access()` | modelo | Lanza `AccessError` fuera de los tres grupos contables |
| `_odomate_initial_balance_domain(company, date_from, journals=None, target_move='posted')` | modelo | Dominio del saldo de apertura |

**Vista** `odomate_account_ledger_reports.view_odomate_account_report_filter_form` — herede con `mode="primary"` y añada sus campos después del nodo `journal_ids` o del nodo `target_move`. Esos son los dos únicos puntos de anclaje admitidos.

**QWeb** `odomate_account_ledger_reports.report_filter_header` — parámetros `company`, `date_from`, `date_to`, `journals`, `target_move_label`.

**Formato de papel** `odomate_account_ledger_reports.paperformat_odomate_ledger_landscape` — A4 horizontal, márgenes de 10 mm.

**Menú** `odomate_account_ledger_reports.menu_odomate_account_reports_audit` — la carpeta *Informes de auditoría*.

Todo lo demás — campos propios de cada diálogo, métodos auxiliares de construcción de filas, nombres de los modelos de informe, redacción de las plantillas, orden de las claves de los diccionarios — es interno y puede cambiar.

---

© OdoMate · <https://odomate.pro> · <support@odomate.pro>
