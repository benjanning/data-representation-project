/* Pure rules mirrored by rentals.py and checked against shared contract fixtures. */
(function (root) {
  "use strict";
  class RentalError extends Error {
    constructor(message, code = "invalid_reservation", status = 400) {
      super(message);
      this.code = code;
      this.status = status;
    }
  }
  function calendar(v) {
    if (typeof v !== "string" || !/^\d{4}-\d{2}-\d{2}$/.test(v))
      throw new RentalError("Choose valid calendar dates.");
    const n = Date.parse(v + "T00:00:00Z");
    if (
      !Number.isFinite(n) ||
      Number(v.slice(0, 4)) < 1 ||
      new Date(n).toISOString().slice(0, 10) !== v
    )
      throw new RentalError("Choose valid calendar dates.");
    return n;
  }
  const today = () => new Date().toISOString().slice(0, 10),
    addDays = (d, n) =>
      new Date(calendar(d) + n * 86400000).toISOString().slice(0, 10);
  function period(a, b, now) {
    const start = calendar(a),
      end = calendar(b),
      asof = calendar(now),
      days = (end - start) / 86400000;
    if (start < asof)
      throw new RentalError("Collection cannot be before today (UTC).");
    if ((start - asof) / 86400000 > 365)
      throw new RentalError("Choose collection within the next 365 days.");
    if (days < 1 || days > 365)
      throw new RentalError("Return must be 1–365 days after collection.");
    return days;
  }
  function selection(p) {
    if (!p || typeof p !== "object" || Array.isArray(p))
      throw new RentalError("Provide a reservation object.");
    for (const k of ["vehicle_id", "customer_id"])
      if (!Number.isInteger(p[k]) || p[k] < 1 || p[k] > 2147483647)
        throw new RentalError("Choose an existing vehicle and customer.");
    return Object.fromEntries(
      ["vehicle_id", "customer_id", "start_date", "end_date"].map((k) => [
        k,
        p[k],
      ]),
    );
  }
  const overlaps = (r, a, b) =>
    r.status === "confirmed" && r.start_date < b && a < r.end_date;
  function quote(cars, customers, rows, p, now) {
    const chosen = selection(p),
      days = period(chosen.start_date, chosen.end_date, now),
      car = cars.find((c) => c.id === chosen.vehicle_id),
      customer = customers.find((c) => c.id === chosen.customer_id);
    if (!car || !customer)
      throw new RentalError(
        "The selected vehicle or customer no longer exists.",
        "record_missing",
        404,
      );
    if (
      rows.some(
        (r) =>
          r.vehicle_id === car.id &&
          overlaps(r, chosen.start_date, chosen.end_date),
      )
    )
      throw new RentalError(
        "This vehicle is already reserved for part of that period. Choose other dates or a different vehicle.",
        "vehicle_unavailable",
        409,
      );
    if (!Number.isInteger(car.Price) || car.Price < 0 || car.Price > 1e9)
      throw new RentalError(
        "This vehicle has an invalid daily rate.",
        "invalid_rate",
        409,
      );
    return {
      ...chosen,
      days,
      daily_rate_cents: car.Price * 100,
      total_cents: car.Price * 100 * days,
      vehicle_ref: car.Reg,
      vehicle_model: car.Model,
      customer_name: customer.Name,
    };
  }
  function requestId(p) {
    if (
      typeof p.request_id !== "string" ||
      !/^[A-Za-z0-9_-]{8,80}$/.test(p.request_id)
    )
      throw new RentalError("Provide a valid request identifier.");
    return p.request_id;
  }
  function replay(rows, p) {
    const key = requestId(p),
      row = rows.find((r) => r.request_id === key);
    if (
      row &&
      (["vehicle_id", "customer_id", "start_date", "end_date"].some(
        (k) => row[k] !== p[k],
      ) ||
        row.total_cents !== p.quoted_total_cents ||
        row.daily_rate_cents !== p.quoted_daily_rate_cents)
    )
      throw new RentalError(
        "That request identifier has already been used for a different selection.",
        "request_conflict",
        409,
      );
    return row;
  }
  function confirm(cars, customers, rows, p, now) {
    selection(p);
    const key = requestId(p),
      existing = replay(rows, p);
    if (existing) return [existing, false];
    const q = quote(cars, customers, rows, p, now);
    if (
      ["daily_rate_cents", "total_cents"].some(
        (k) => !Number.isInteger(p["quoted_" + k]) || p["quoted_" + k] !== q[k],
      )
    )
      throw new RentalError(
        "The daily rate or quotation changed. Review a fresh quote before confirming.",
        "quote_changed",
        409,
      );
    return [
      {
        ...q,
        id: Math.max(0, ...rows.map((r) => r.id)) + 1,
        status: "confirmed",
        request_id: key,
        created_on: now,
      },
      true,
    ];
  }
  function transition(row, status, now) {
    if (!["cancelled", "completed"].includes(status))
      throw new RentalError("Choose cancelled or completed.");
    if (row.status === status) return { ...row };
    if (row.status !== "confirmed")
      throw new RentalError(
        "A terminal reservation cannot be changed.",
        "invalid_transition",
        409,
      );
    if (status === "completed" && row.end_date > now)
      throw new RentalError(
        "Complete this rental on or after its scheduled return date.",
        "return_not_due",
        409,
      );
    return { ...row, status, updated_on: now };
  }
  function availability(cars, rows, a, b, now) {
    period(a, b, now);
    return cars.map((c) => ({
      vehicle_id: c.id,
      available: !rows.some((r) => r.vehicle_id === c.id && overlaps(r, a, b)),
    }));
  }
  function summary(cars, rows, a, b, now) {
    return {
      vehicles: cars.length,
      available: availability(cars, rows, a, b, now).filter((r) => r.available)
        .length,
      active: rows.filter(
        (r) =>
          r.status === "confirmed" && r.start_date <= now && now < r.end_date,
      ).length,
      upcoming: rows.filter(
        (r) => r.status === "confirmed" && r.start_date > now,
      ).length,
      return_due: rows.filter(
        (r) => r.status === "confirmed" && r.end_date <= now,
      ).length,
      confirmed_value_cents: rows
        .filter((r) => r.status === "confirmed")
        .reduce((n, r) => n + r.total_cents, 0),
    };
  }
  function seeded(cars, customers, spec, now) {
    const rows = [];
    spec.forEach((s, i) => {
      const a = addDays(now, s.start_offset),
        b = addDays(now, s.end_offset),
        q = quote(
          cars,
          customers,
          rows,
          {
            vehicle_id: s.vehicle_id,
            customer_id: s.customer_id,
            start_date: a,
            end_date: b,
          },
          a,
        );
      rows.push({
        ...q,
        id: i + 1,
        status: "confirmed",
        request_id: "seed-rental-" + (i + 1),
        created_on: a,
      });
    });
    return rows;
  }
  function validateSaved(data) {
    if (!Array.isArray(data.reservations))
      throw Error("Invalid reservation history");
    const ids = new Set(),
      requests = new Set();
    for (const r of data.reservations) {
      selection(r);
      requestId(r);
      if (
        !Number.isSafeInteger(r.id) ||
        r.id < 1 ||
        ids.has(r.id) ||
        requests.has(r.request_id) ||
        !["confirmed", "cancelled", "completed"].includes(r.status)
      )
        throw Error("Invalid reservation identity");
      ids.add(r.id);
      requests.add(r.request_id);
      const days = (calendar(r.end_date) - calendar(r.start_date)) / 86400000;
      if (
        days < 1 ||
        days > 365 ||
        r.days !== days ||
        !Number.isSafeInteger(r.daily_rate_cents) ||
        r.daily_rate_cents < 0 ||
        r.daily_rate_cents > 1e11 ||
        r.daily_rate_cents % 100 ||
        r.total_cents !== days * r.daily_rate_cents
      )
        throw Error("Invalid reservation totals");
      if (
        !data.cars.some((c) => c.id === r.vehicle_id) ||
        !data.customers.some((c) => c.id === r.customer_id)
      )
        throw Error("Missing reservation reference");
      for (const k of ["vehicle_ref", "vehicle_model", "customer_name"])
        if (typeof r[k] !== "string" || r[k].length < 1 || r[k].length > 250)
          throw Error("Invalid reservation snapshot");
      calendar(r.created_on);
      if (r.updated_on) calendar(r.updated_on);
      if (
        r.status === "confirmed" &&
        data.reservations.some(
          (other) =>
            other.id !== r.id &&
            other.vehicle_id === r.vehicle_id &&
            overlaps(other, r.start_date, r.end_date),
        )
      )
        throw Error("Overlapping saved reservations");
    }
    return data;
  }
  const rules = {
    RentalError,
    today,
    calendar,
    addDays,
    period,
    selection,
    overlaps,
    quote,
    confirm,
    transition,
    availability,
    summary,
    seeded,
    validateSaved,
  };
  if (typeof module !== "undefined") module.exports = rules;
  else root.FleetRentals = rules;
})(typeof window !== "undefined" ? window : globalThis);
