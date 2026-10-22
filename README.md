# Fleetdesk / rental management

Allocate a synthetic vehicle to a customer for a date range, review a quotation and follow the reservation through cancellation or completion.

![Latest verified release: actual vehicle availability and blocking periods](https://raw.githubusercontent.com/benjanning/data-representation-project/portfolio-published/portfolio/export/assets/availability-roster.jpg)

**Python · Flask · REST APIs · MySQL · JavaScript · Transactional business rules**

**[Try the public demonstration →](https://benjanning.github.io/data-representation-project/)** · [Visual case study](https://benjanning.github.io/projects/projects/car-rental/) · [Portfolio](https://benjanning.github.io/projects/)

The public version stores fictional records in your browser. The same frontend also runs against the local Flask API and optional MySQL store. No actual fleet, rental, payment or customer account is managed.

## The problem and approach

Editing vehicle records is useful, but a rental application also has to answer: is this particular vehicle available, what price did the customer review, and can two people allocate it at the same time?

The extension keeps the original vehicle/customer CRUD and adds a separate reservation model. Availability is checked again when the allocation is written. Prices and names are saved as snapshots, and request IDs make a lost-response retry safe.

## From an availability count to a useful decision

The overview now shows which individual vehicles are available for the selected period. Expand **See all vehicles for these dates** to inspect the actual confirmed periods blocking each vehicle. Choose **Quote this vehicle** to enter the existing quotation flow with that vehicle and date range selected. Cancellation releases the allocation; adjacent collection/return boundaries remain valid. This is an advisory view: confirmation still rechecks the authoritative rules and transaction.

Reservations can be searched by stored customer name, vehicle, reference, dates or rental ID, together with the existing status filters. **Export shown reservations CSV** exports exactly that view, including cancelled/completed history and original quotation snapshots. Integer-cent columns preserve exact amounts; these are not revenue. Exports quote commas/newlines/Unicode and prefix formula-like text for spreadsheet safety. They do not rename historical customers when current records change.

Keyboard focus returns to the stable workspace after confirmation and to the search field after search/clear. The roster uses a native disclosure and labelled vehicle actions; mobile layouts stack decisions without page overflow. See [workspace design and evidence](RESERVATION-WORKSPACE.md).

## A two-minute example

1. On **Overview**, choose dates and expand the vehicle availability list. Choose an available vehicle, then a fictional customer. You can also start from **Reservations → New reservation**.
2. Choose collection/return dates and review the calculated quotation. A three-day €68 rental totals €204.
3. Confirm. Try the same vehicle and overlapping dates again: the application refuses the conflict.
4. Search the new reservation and export the shown CSV. Cancel to release its allocation; use **History** to inspect its saved quotation. Complete a **Return due** example to preserve completed history. **Reset demo data** restores the original workspace.

![Latest verified reservation list](https://raw.githubusercontent.com/benjanning/data-representation-project/portfolio-published/portfolio/export/assets/reservations.jpg)

The dashboard derives its figures from actual sample records: availability for the chosen period, active/upcoming/return-due counts and the total of confirmed example quotations. The latter is explicitly not revenue. Existing inventory/customer search and editing remain available.

## The engineering challenge

A quote can become stale before confirmation. Memory writes use a shared lock; browser writes serialize across tabs with Web Locks; MySQL locks the vehicle row within the same transaction as the overlap check and insert. Foreign keys protect references, and identical retries return the original reservation.

Python and JavaScript follow a deterministic 27-case contract covering calendar validation, overlapping/adjacent periods, money and status rules. Tests also simulate a server commit followed by a lost response, and two tabs trying to allocate the same vehicle. See [reservation design and architecture](RESERVATION-DESIGN.md) for the rules, API, calculations and trade-offs.

## Run and verify

```bash
python -m pip install -r requirements.txt
# Set DEMO_MODE=1 in your shell, then:
python CarServer.py
```

Open http://127.0.0.1:5000. Dates use UTC. Collection is included and return excluded, allowing same-day handovers. Reservations last 1–365 days. Completion is allowed on/after the scheduled return date; early-return pricing and amendments are outside this prototype.

```bash
python -m unittest discover -p "test_*.py" -v
python scripts/build-rental-fixtures.py --check
python scripts/build-demo.py
npm ci
npm run test:rules
npx playwright install chromium
npm run test:browser
```

The default Python run skips the two opt-in live database checks. Source CI runs those against a fresh, explicitly named `portfolio_integration` MySQL 8.4 database before releasing. Seven JavaScript checks include independent Python CSV round-tripping. Eleven browser journeys exercise the original workflows and the new availability/search/export decisions in both modes. Browser tests start their own Flask/static servers and capture genuine desktop/mobile screens only after meaningful workflows pass. The exported manifest identifies the exact source commit, successful run and image hashes.

## Optional MySQL

Use a disposable local MySQL 8.4/InnoDB database. Set `DB_HOST`, `DB_PORT`, `DB_USER`, `DB_PASSWORD`, `DB_NAME`, `DEMO_USERNAME` and `DEMO_PASSWORD` in your process environment. With `DEMO_MODE` unset or `0`, API access requires the configured Basic credentials. Never use real records or reuse production credentials.

For a fresh schema, `python createDatabase.py` creates missing tables and seeds vehicle/customer tables only when empty. For an existing V3 schema, run `python migrate_reservations.py`: it adds the reservation table without replacing, dropping or reseeding records. The existing `cars` and `customer` tables must use compatible integer primary keys and InnoDB. MySQL starts with no reservation history; the three relative-date sample reservations belong to the disposable synthetic modes.

The integration test refuses any database name except `portfolio_integration`. See the release workflow for the isolated service and required test environment. It verifies actual database allocation contention, immutable quotes, referential integrity, retries and lifecycle transitions.

## Scope and preservation

The browser demo coordinates tabs within one origin/browser profile, not different devices. A browser supporting Web Locks is required for safe local mutations. Existing V3 browser record edits are imported with an empty reservation history; reset deliberately restores the new samples. A corrupted saved workspace is reported and restored to samples.

Original `/cars` and `/customer` routes and integer `Price` fields are preserved. Customer vehicle-reference/rate fields remain historical descriptive fields; new reservations reference actual vehicle/customer IDs. Cancellation and completion retain saved history, and referenced records cannot be deleted. Original frontend and coursework remain in `static/legacy`, [COURSEWORK.md](COURSEWORK.md) and Git history.

This prototype has no production identity system, cross-device public backend, actual stock operation, tax/deposit accounting or payment handling. The practical evidence is the implemented code, repeatable tests, genuine captures and explicit design decisions.

[Visual provenance](assets/PROVENANCE.md) · [Latest verified export receipt](https://github.com/benjanning/data-representation-project/blob/portfolio-published/portfolio/export/manifest.json)
