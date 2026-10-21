/* Rental workflow presentation; adapters and pure business rules remain separate. */
(function (root) {
  "use strict";
  root.FleetReservationUI = {
    create(ctx) {
      const R = root.FleetRentals,
        $ = (s) => document.querySelector(s),
        esc = (v) =>
          String(v ?? "").replace(
            /[&<>"']/g,
            (c) =>
              ({
                "&": "&amp;",
                "<": "&lt;",
                ">": "&gt;",
                '"': "&quot;",
                "'": "&#39;",
              })[c],
          );
      const money = (n) =>
        new Intl.NumberFormat("en-IE", {
          style: "currency",
          currency: "EUR",
        }).format(n / 100);
      let period = { start_date: R.today(), end_date: R.addDays(R.today(), 3) },
        filter = "all",
        quotation = null,
        requestId = null,
        busy = false;
      const modal = $("#rental-editor"),
        form = $("#rental-form");
      function metrics() {
        const d = ctx.getData();
        return R.summary(
          d.cars,
          d.reservations,
          period.start_date,
          period.end_date,
          R.today(),
        );
      }
      function dashboard() {
        const s = metrics();
        return `<section class="panel rental-overview" aria-labelledby="rental-overview-title"><div class="panel-heading"><div><span class="eyebrow">PLAN THE NEXT JOURNEY</span><h2 id="rental-overview-title">From availability to allocation.</h2><p>One vehicle, one confirmed rental period. All records are synthetic.</p></div><button type="button" class="primary" data-new-rental>＋ New reservation</button></div><form id="availability-form" class="period-picker"><label>Collect on (UTC)<input name="start_date" type="date" min="${R.today()}" value="${period.start_date}" required></label><label>Return on (UTC)<input name="end_date" type="date" min="${R.addDays(period.start_date, 1)}" value="${period.end_date}" required></label><button type="submit" class="secondary">Check availability</button></form><div class="rental-metrics"><article><span>Available for these dates</span><strong id="available-total">${s.available} <small>/ ${s.vehicles}</small></strong></article><article><span>Active today</span><strong>${s.active}</strong></article><article><span>Upcoming</span><strong>${s.upcoming}</strong></article><article><span>Return due</span><strong>${s.return_due}</strong></article></div><div class="rental-value"><span>Confirmed example value <strong>${money(s.confirmed_value_cents)}</strong></span><a href="#reservations">See reservations →</a></div><p class="fine">Collection is included; return is excluded, allowing same-day handovers. Active/upcoming/due use today in UTC. Value sums confirmed quotation snapshots, including returns awaiting completion; it is not revenue.</p></section>`;
      }
      function bucket(r) {
        if (r.status !== "confirmed") return r.status;
        if (r.end_date <= R.today()) return "due";
        return r.start_date > R.today() ? "upcoming" : "active";
      }
      function render() {
        const d = ctx.getData(),
          rows = d.reservations.filter(
            (r) =>
              filter === "all" ||
              (filter === "history"
                ? r.status !== "confirmed"
                : bucket(r) === filter),
          );
        return `<div class="page-heading"><div><span class="eyebrow">DATES, PEOPLE AND A CLEAR PLAN</span><h1>Every journey starts here.</h1><p>Quote a rental, reserve a vehicle and follow its demonstration status.</p></div><button class="primary" type="button" data-new-rental>＋ New reservation</button></div><section class="panel rental-guide"><strong>A useful two-minute walkthrough.</strong><p>Choose a customer and an available vehicle, check a date-based quote, then confirm. Try reserving those dates again to see overlap protection, or cancel to release the allocation.</p></section><div class="rental-filters" role="group" aria-label="Filter reservations">${[
          ["all", "All reservations"],
          ["active", "Active"],
          ["upcoming", "Upcoming"],
          ["due", "Return due"],
          ["history", "History"],
        ]
          .map(
            ([value, label]) =>
              `<button type="button" data-rental-filter="${value}" aria-pressed="${filter === value}">${label}</button>`,
          )
          .join(
            "",
          )}</div><div class="reservation-list">${rows.map((r) => `<article class="panel reservation-card"><div class="reservation-top"><span class="eyebrow">DEMO RENTAL / ${String(r.id).padStart(3, "0")}</span><span class="reservation-status ${bucket(r)}">${{ due: "Return due", active: "Active", upcoming: "Upcoming", cancelled: "Cancelled", completed: "Completed" }[bucket(r)]}</span></div><h2>${esc(r.vehicle_model.split(" · ")[0])}</h2><p><span class="reg">${esc(r.vehicle_ref)}</span> · ${esc(r.customer_name)}</p><dl class="reservation-details"><div><dt>Collection (UTC)</dt><dd>${r.start_date}</dd></div><div><dt>Return (exclusive)</dt><dd>${r.end_date}</dd></div><div><dt>Saved quotation</dt><dd>${money(r.total_cents)} <small>${r.days} days × ${money(r.daily_rate_cents)}</small></dd></div></dl>${r.status === "confirmed" ? `<div class="reservation-actions"><button class="secondary" type="button" data-rental-status="cancelled" data-rental-id="${r.id}">Cancel reservation</button><button class="primary" type="button" data-rental-status="completed" data-rental-id="${r.id}" ${r.end_date > R.today() ? "disabled" : ""}>Mark completed</button></div>${r.end_date > R.today() ? '<p class="fine">Completion becomes available on the scheduled return date. Cancel to release this allocation earlier.</p>' : ""}` : '<p class="fine">Saved history. Vehicle, customer and rate snapshots are retained.</p>'}</article>`).join("") || '<div class="empty"><h2>No reservations in this view.</h2><p>Try another filter or create your first demonstration reservation.</p><button class="primary" type="button" data-new-rental>New reservation →</button></div>'}</div><p class="fine">${rows.length} of ${d.reservations.length} reservations shown. Confirmed periods block overlaps; terminal records remain as history. No payment or real rental is created.</p>`;
      }
      function clearQuote() {
        quotation = null;
        requestId = null;
        $("#rental-quote").hidden = true;
        $("#confirm-rental").hidden = true;
        $("#quote-rental").textContent = "Check availability & quote →";
      }
      function open() {
        const d = ctx.getData();
        if (!d.cars.length || !d.customers.length) {
          ctx.notify(
            "Reservations need at least one vehicle and one customer. Add the missing records first.",
            true,
          );
          return;
        }
        form.reset();
        clearQuote();
        $("#rental-error").hidden = true;
        for (const [id, rows, label] of [
          ["rental-customer", d.customers, "Name"],
          ["rental-vehicle", d.cars, "Model"],
        ])
          $("#" + id).innerHTML =
            '<option value="">Choose ' +
            (id === "rental-customer" ? "a customer" : "a vehicle") +
            "</option>" +
            rows
              .map(
                (r) =>
                  `<option value="${r.id}">${esc(r[label])}${label === "Model" ? " / " + esc(r.Reg) + " / " + money(r.Price * 100) + " per day" : ""}</option>`,
              )
              .join("");
        form.elements.start_date.value = period.start_date;
        form.elements.end_date.value = period.end_date;
        form.elements.start_date.min = R.today();
        form.elements.start_date.max = R.addDays(R.today(), 365);
        form.elements.end_date.min = R.addDays(period.start_date, 1);
        modal.showModal();
      }
      const chosen = () => ({
        vehicle_id: Number(form.elements.vehicle_id.value),
        customer_id: Number(form.elements.customer_id.value),
        start_date: form.elements.start_date.value,
        end_date: form.elements.end_date.value,
      });
      function fail(error) {
        $("#rental-error").hidden = false;
        $("#rental-error").textContent = error.message;
        $("#rental-error").focus();
      }
      function working(value) {
        busy = value;
        for (const field of form.querySelectorAll("input, select"))
          field.disabled = value;
        $("#quote-rental").disabled = value;
        $("#confirm-rental").disabled = value;
        form.setAttribute("aria-busy", String(value));
      }
      form.addEventListener("input", () => {
        if (busy) return;
        clearQuote();
        $("#rental-error").hidden = true;
        try {
          form.elements.end_date.min = R.addDays(
            form.elements.start_date.value,
            1,
          );
        } catch {
          /* Calendar validation occurs on submission. */
        }
      });
      form.addEventListener("change", () => {
        if (!busy) clearQuote();
      });
      form.addEventListener("submit", async (event) => {
        event.preventDefault();
        if (busy) return;
        working(true);
        $("#rental-error").hidden = true;
        try {
          const p = chosen(),
            d = ctx.getData();
          quotation = ctx.server
            ? await ctx.api("./api/reservations/quote", "POST", p)
            : R.quote(d.cars, d.customers, d.reservations, p, R.today());
          requestId = crypto.randomUUID();
          $("#rental-quote").innerHTML =
            `<span class="eyebrow">AVAILABLE / YOUR EXAMPLE QUOTE</span><h3>${esc(quotation.vehicle_model)}</h3><p>${esc(quotation.customer_name)} · ${quotation.start_date} → ${quotation.end_date}</p><p>${quotation.days} days × ${money(quotation.daily_rate_cents)} <strong>${money(quotation.total_cents)}</strong></p><small>Whole-euro vehicle rate saved in cents. No tax, deposit or payment is added. Availability and price are checked again when confirming.</small>`;
          $("#rental-quote").hidden = false;
          $("#confirm-rental").hidden = false;
          $("#quote-rental").textContent = "Refresh quote";
        } catch (error) {
          clearQuote();
          fail(error);
        } finally {
          working(false);
        }
      });
      $("#confirm-rental").addEventListener("click", async () => {
        if (busy || !quotation) return;
        working(true);
        $("#rental-error").hidden = true;
        try {
          const p = {
            ...chosen(),
            request_id: requestId,
            quoted_daily_rate_cents: quotation.daily_rate_cents,
            quoted_total_cents: quotation.total_cents,
          };
          if (ctx.server) await ctx.api("./api/reservations", "POST", p);
          else
            await ctx.write((d) => {
              const [row, created] = R.confirm(
                d.cars,
                d.customers,
                d.reservations,
                p,
                R.today(),
              );
              if (created) d.reservations.push(row);
              return row;
            });
          await ctx.load();
          modal.close();
          filter = "all";
          location.hash = "reservations";
          ctx.render();
          ctx.notify(
            "Reservation confirmed. Your vehicle allocation and saved quotation are ready.",
          );
        } catch (error) {
          if (
            ["quote_changed", "vehicle_unavailable", "record_missing"].includes(
              error.code,
            )
          )
            clearQuote();
          fail(error);
        } finally {
          working(false);
        }
      });
      modal.addEventListener("cancel", (e) => {
        if (busy) e.preventDefault();
      });
      document.addEventListener("submit", (e) => {
        if (e.target.id !== "availability-form") return;
        e.preventDefault();
        try {
          const f = e.target;
          R.period(
            f.elements.start_date.value,
            f.elements.end_date.value,
            R.today(),
          );
          period = {
            start_date: f.elements.start_date.value,
            end_date: f.elements.end_date.value,
          };
          ctx.render();
          ctx.notify("Availability updated for the selected rental period.");
        } catch (error) {
          ctx.notify(error.message, true);
        }
      });
      document.addEventListener("click", (e) => {
        if (e.target.closest("[data-new-rental]")) open();
        if (e.target.closest("[data-rental-close]") && !busy) modal.close();
        const tab = e.target.closest("[data-rental-filter]");
        if (tab) {
          filter = tab.dataset.rentalFilter;
          ctx.render();
          document.querySelector(`[data-rental-filter="${filter}"]`).focus();
        }
        const action = e.target.closest("[data-rental-status]");
        if (!action) return;
        const id = Number(action.dataset.rentalId),
          status = action.dataset.rentalStatus,
          row = ctx.getData().reservations.find((r) => r.id === id);
        if (!row) return;
        ctx.ask(
          status === "cancelled"
            ? "Cancel this reservation?"
            : "Complete this rental?",
          status === "cancelled"
            ? `${row.vehicle_ref} will become available for this period. Its saved history will remain.`
            : "The scheduled rental has ended. Save it as completed history.",
          status === "cancelled" ? "Cancel allocation" : "Complete rental",
          async () => {
            if (ctx.server)
              await ctx.api("./api/reservations/" + id + "/status", "POST", {
                status,
              });
            else
              await ctx.write((d) => {
                const i = d.reservations.findIndex((r) => r.id === id);
                if (i < 0) throw Error("Reservation no longer exists.");
                d.reservations[i] = R.transition(
                  d.reservations[i],
                  status,
                  R.today(),
                );
              });
            await ctx.load();
            ctx.render();
            ctx.notify(
              status === "cancelled"
                ? "Reservation cancelled. The vehicle allocation has been released."
                : "Rental marked completed. Its quotation is preserved in history.",
            );
          },
        );
      });
      return { dashboard, render };
    },
  };
})(window);
