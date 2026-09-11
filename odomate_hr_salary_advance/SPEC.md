# SPEC.md — the business specification this module was generated from

This is the business-level specification the module in this folder was generated
from — code, views, security, demo data, tests, and the user guides in `doc/`.
It is written in the voice of the person who would ask for it: the HR manager who
gets asked, three days before payday, whether somebody can have part of their
salary early, who uses Odoo every day and has no knowledge of how Odoo is built
inside. No model names, field names or technical design appear in it; everything
in `models/`, `views/` and `security/` was derived by OdoMate from the plain
requirements below.

**Provenance, stated plainly.** This specification was written by the OdoMate team
as an independent description of what a salary-advance feature should do. It
contains no third-party code, text or configuration. The module was generated from
this document alone.

**What was verified before publication.** The module installs on a freshly created
Odoo 19 Community database on the first attempt with no errors — 65 modules,
including its OCA payroll and accounting dependencies — and its automated tests
pass with no failures and no errors (Odoo's runner reports 0 failed, 0 errors of
55 tests). Its Ukrainian translation is complete and, unlike earlier modules in
this series, actually loads: all 25 code entries reach a Ukrainian installation,
measured with Odoo's own translation loader, and the window titles read
«Аванси із зарплати» and «Мої аванси» rather than English. Every acceptance
criterion was walked against the running database, and the screens were read off
the screen rather than only queried through the data layer — including a real
payslip carrying the deduction line, generated on a payslip with no contract
pinned to it, which is the case the module had to be corrected twice to handle.

**No hand corrections.** Four defects found after the first build — a crashing
salary-rule expression, a deduction that never reached a batch-created payslip, a
Ukrainian catalogue Odoo would not load, and a refused request that still reported
an outstanding balance — were each fixed by asking OdoMate for a new version, not
by editing the generated code. Five versions were generated; the fifth is what
ships here.

Generated with OdoMate (https://www.odomate.pro) — September 2026, Odoo 19
Community. Published unedited apart from publication metadata (store listing page,
banner and icon).

---


# Advance Salary — Spec (Level 1: Business User)

> **Who wrote this:** the HR manager who gets asked, three days before payday, whether somebody can have part of their salary early. They use Odoo every day and have **no** idea how Odoo is built inside.

**What app this touches:** the **Employees** app — a new **Advance Salary** area — and the payslip, where the money has to come back.

**An advance is not a loan.** It is this month's salary, paid early, and it comes back in one piece out of the next payslip. Money lent over months is the *Employee Loans* module, and the two must not be confused.

---

## 1. What I want (the problem)

Somebody's rent is due on the 25th and payday is the 5th. They ask for part of their salary early. We usually say yes, it takes four minutes, and then it goes wrong in one of four ways.

- The payroll person is not told, the advance is never deducted, and the person is paid twice. This has happened, and it is embarrassing to unwind.
- Nobody knows what "part of your salary" is allowed to mean. One person gets 30%, another gets 80%, and the difference is who asked.
- Somebody takes an advance in March, and in April, and in May, and by June they are living a month behind and nobody noticed because each request looked reasonable on its own.
- And when the person asks "did that come off?", the answer is somebody's memory.

I want the request written down, an amount the system can tell me is or is not allowed, a record that the money was actually paid, and **the deduction on the next payslip happening by itself**.

---

## 2. What I want to be able to do

### a) Ask for an advance

A request records: **who**, **how much**, **why** in a sentence, and the **date**. When an employee's request is being entered for them it defaults to whoever is being helped.

### b) Be told immediately how much this person may have

On the request, before anything is submitted, four figures I can read: their **monthly salary**, the **most they are allowed** under our policy, **what they already have outstanding**, and therefore **what is left available to them**. If somebody asks for more than that, the system says no and says why.

### c) Set the policy once, per company

- The **most anybody may take**, as a percentage of their monthly salary — and, if we want a hard ceiling too, a **maximum amount** in money.
- Whether somebody may have a **second advance** while the first is still outstanding. Off by default, because that is how a person ends up living a month behind.

### d) Approve it, or refuse it with a reason

Raised as a **draft**, then **submitted**. An HR officer **approves** or **refuses** — and refusing must ask for a **reason**, in writing, which stays on the record. Approving is not the same as paying.

### e) Pay the money out, and have accounting know about it

A separate step: **Pay**, choosing the **date it is paid** and the **journal** the money leaves through — the bank account, or the cash box. The system **makes the payment itself** and posts it, so finance does not have to re-key anything, and from the advance I can open the payment and the accounting entry it produced. Only from that moment is there something to recover.

*(Amended in S5, ruling 2. This section originally said the money leaving the bank is **not** recorded in accounting by this module, and asked only for a typed payment **reference**. That was checked against the original OpenHRMS module and found to be a real loss of parity: `ohrms_salary_advance` disburses the advance itself, through a payment on a configured journal, and shows the resulting entries. It has no companion accounting module — so the fix is to fold the money into this module rather than add a thirteenth one. The typed reference is kept as an optional note on the payment, not as the only link to finance.)*

### f) Have it come back out of the next payslip, by itself

When a payslip is prepared for a period on or after the day the advance was paid, **the deduction appears on it automatically** for the whole outstanding amount, named so the employee understands it. Confirming the payslip records what was recovered and **closes** the advance.

### g) Cope with a payroll person who reduces it

Sometimes the full amount cannot come off — the month was short, there was unpaid leave. If the payroll person reduces the deduction on the payslip before confirming it, the advance records **what was actually recovered**, stays open for the remainder, and the remainder comes off the following payslip. The system never quietly decides the advance is settled when it is not.

### h) Cancel one that never happened

An advance that was approved but never paid can be **cancelled**. One that has been paid cannot — the money is out, and it has to come back.

### i) See the accounting behind it

From the advance, a way to open the **payment** that was made and the **journal entry** it posted. If the payment is later cancelled in accounting, the advance must not go on claiming it was paid.

### j) See it from the person's side

On an employee's record, a counter for **advances still outstanding**, opening the list.

### k) Let a person see their own, and nothing else

An ordinary employee with no HR role can open **My Advances** and read **their own** — the amount, whether it was paid, what is still to come off. Read-only, and a colleague's must be unreachable by any route. They see the amount and what is still to come off — **not** the journal entry behind it.

---

## 3. What I want to see on screen

- **An Advance Salary area in the Employees app** with two screens: **Advance Salary**, and the company **policy** under Configuration. Plus **My Advances**, which is what an ordinary employee sees.
- **On a request:** the reference number across the top, the state as a bar — *Draft → Submitted → Approved → Paid → Closed*, with *Refused* and *Cancelled* as the ends of the other paths — the employee, their department, the amount, the reason, the date.
- **The four eligibility figures in a block of their own**, side by side and each clearly labelled: monthly salary, most allowed, already outstanding, still available. They are the reason the screen exists; they must read as four labelled amounts, not as four bare numbers.
- **Underneath, what has happened to the money:** the date it was paid, the journal it left through, how much has been recovered so far, and how much is still to come off.
- **A way through to the accounting**, from the advance itself: the payment that was made, and the entry it posted. It appears only once the advance has been paid.
- **The buttons, and when each appears:** *Submit* (draft only) · *Approve* and *Refuse* (submitted only) · *Pay* (approved only) · *Cancel* (draft, submitted and approved — never once paid) · *Set to draft* (draft path only).
- **In the list:** reference, employee, amount, still to recover, state. An advance that is fully recovered should look different from one still outstanding.
- **On the payslip:** the deduction is its own line, named so a person reading their payslip knows what it is.
- **On an employee's record:** a counter for outstanding advances.

---

## 4. What I want to be warned about

- **The deduction only happens if the advance deduction rule is part of the salary structure in use.** This is a one-time setup step and skipping it means advances are approved and paid and nothing ever comes back. It is the most likely reason this module looks broken when it is not.
- **The whole balance comes off the next payslip.** There is no schedule and no instalments — that is what makes it an advance and not a loan. A person who cannot afford to lose a whole advance from one payslip should be given a loan instead.
- **The eligibility figures depend on a current contract.** An employee with no active contract has no monthly salary the system can read, so it cannot say what they are allowed, and the request cannot be submitted.
- **The policy is checked when the request is submitted and again when it is approved** — not continuously. Changing the policy afterwards does not retrospectively invalidate advances already approved.
- **The money cannot be paid out until a journal is chosen.** *(Amended in S5, ruling 2 — this warning previously said the opposite: that nothing here posts to accounting.)* Paying an advance posts a real payment on a real journal, so somebody has to say which one. Until then the *Pay* step refuses, and says why.
- **Paying an advance is an accounting act, and it is not silently reversible.** Cancelling the posted payment is done in Accounting, by somebody who is allowed to; the advance then stops claiming the money went out. This module never deletes a posted entry.
- **Nothing happens automatically when somebody leaves.** An outstanding advance on a departing employee is a conversation. The leaving process flags it; nothing here recovers it.

---

## 5. What is intentionally NOT included (keep the first version honest)

- **No instalments and no schedule.** One deduction, from the next payslip. Spreading repayment over months is what *Employee Loans* is for.
- **No interest, ever.** It is the person's own salary.
- **No bank integration and no reconciliation.** *(Amended in S5, ruling 2 — this exclusion previously covered the accounting entry and the payment record too. It no longer does: the module makes and posts the payment.)* What is still excluded is everything after that — matching the payment against a bank statement, batching payments, or choosing a payment method beyond the journal.
- **No accounting for the recovery.** The money coming *back* is a payroll deduction and stays a payroll deduction. Whatever the customer's payslip-to-accounting arrangement is, it is theirs; this module posts on the way out only.
- **No approval chain.** One approval by one HR officer, whatever the amount.
- **No self-service requesting.** An employee cannot raise their own advance; HR raises it on behalf of whoever asked. Reading your own is included (section 2 k) — seeing what you owe is not the same as asking for more.
- **No second currency.** An advance is in the company's own currency.
- **No minimum service period.** A person who joined last week can be given an advance if HR approves it; whether that is wise is a human judgement, not a rule.
- **No automatic escalation, reminder or chasing.** Nothing emails anybody about an outstanding advance.
- **No relationship to leave, attendance or worked days.** The advance is a fixed amount, unaffected by how much of the month was worked.

---

## 6. How we'll know it works (acceptance criteria)

The setup for most of these: an employee on a monthly salary of **5,000**, a company policy of **50%** and no fixed ceiling — so the most they may take is **2,500**.

1. I raise an advance for that employee and the four eligibility figures read **5,000 / 2,500 / 0 / 2,500** before I have typed an amount. ✅
2. I ask for **3,000** and submit: I am **refused**, with a message saying it exceeds what is available. ✅
3. I ask for **2,000** and submit: it goes to *Submitted*. ✅
4. I **Refuse** it, am asked for a reason, type one, and it is *Refused* with my reason visible on it. ✅
5. On a fresh request for 2,000 I **Approve**: it reaches *Approved*, and the state bar shows *Paid* has not happened yet. ✅
6. I raise a **second** advance for the same employee while the first is outstanding and try to submit it: **refused**, with a message saying multiple advances are not allowed. ✅
7. I switch **allow multiple advances** on and the second submits — and its *already outstanding* figure now reads **2,000** and its *still available* reads **500**. ✅
8. I set a **maximum amount** of 1,000 in the policy: a new request for 2,000 is refused, and the *most allowed* figure reads 1,000 rather than 2,500. ✅
9. An employee with **no active contract** produces a monthly salary of nothing, and their request **cannot be submitted**, with a message saying so. ✅
10. I press **Pay**, choose today's date and the company's bank journal, and confirm: the state is *Paid*, and the date and the journal are on the record. *(Amended in S5, ruling 2 — this criterion originally read "Mark as paid … and the reference `BANK-4471`", with no payment behind it. Criteria 20–22 are new in the same amendment; the numbering of 11–19 is deliberately left alone so the annex's references to 12 and 19 still resolve.)* ✅
11. I try to **cancel** a paid advance and I am refused. I cancel an approved-but-unpaid one and it cancels. ✅
12. **The deduction reaches the payslip.** With the advance deduction rule in the salary structure in use, I prepare a payslip covering a period on or after the payment date, compute it, and a **deduction line of 2,000** appears. ✅
13. I confirm that payslip: the advance reads **Closed**, recovered 2,000, still to recover nothing. ✅
14. **A payslip for a period before the payment date** produces **no** advance deduction. ✅
15. **Partial recovery.** On a fresh paid advance of 2,000 I reduce the deduction on the payslip to **1,200** before confirming: the advance stays **open**, records 1,200 recovered and 800 still to come off, and the **next** payslip carries a deduction of exactly **800**, after which it closes. ✅
16. A payslip prepared for an advance that is already closed produces **no** deduction. ✅
17. On an employee's record the outstanding-advance counter shows the right number and opens the matching list. ✅
18. **Open the request and look at it.** The four eligibility figures render as four labelled amounts in one block, none clipped, overlapping or showing as bare numbers without their labels; the payment date, the journal and the way through to the payment appear only once the advance is paid; the state bar shows the right stage highlighted; and the buttons present are exactly those the stage allows. **This one is checked by looking at the rendered form on screen, not by reading the values behind it.** ✅
19. **As an ordinary employee** — signed in with `base.group_user` and no HR role — I can open **My Advances** and read **my own**; I **cannot** see a colleague's by search or by opening it directly at its address; and I cannot create, submit, approve, refuse, cancel or mark anything as paid. ✅

**Criteria 20–22 are new in S5 (ruling 2) and cover the disbursement.**

20. **A real payment exists, and it is posted.** After criterion 10, the advance opens a **payment** of exactly 2,000 on the journal I chose, dated the day I chose, in the company's currency, made out to that employee, and its state is **posted** — not draft. ✅
21. **A real journal entry exists behind it.** From that payment I reach a posted journal entry whose lines balance and which **credits the journal's own account** by 2,000. Nothing here is written by hand into `account.move.line`. ✅
22. **No journal, no payment.** With no advance journal configured on the company, pressing **Pay** is refused with a message that says a journal must be configured, and the advance stays *Approved* — no half-made payment, no state change. ✅
