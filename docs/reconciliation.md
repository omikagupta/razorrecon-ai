# Reconciliation rules

## Monetary representation

Amounts are stored as `NUMERIC(18,2)` and processed as Python `Decimal`. Currency values must be compared only within the same currency. Monetary values are serialized to API consumers as fixed two-decimal strings where totals are returned.

## Current matching states

The current matcher uses `payment_id` as its key and compares a payment against the associated settlement record.

| Status | Meaning | Expected amount | Actual amount | Difference |
| --- | --- | ---: | ---: | ---: |
| `MATCHED` | Same currency and exact amount | payment amount | settlement amount | `0.00` |
| `AMOUNT_MISMATCH` | Same currency, different amounts | payment amount | settlement amount | `expected - actual` |
| `MISSING_SETTLEMENT` | No settlement found | payment amount | `null` (financially zero) | payment amount on persistence |
| `CURRENCY_MISMATCH` | Settlement exists in another currency | payment amount | settlement amount | not comparable |
| `DUPLICATE_SETTLEMENT` | More than one settlement is associated with a payment | payment amount | ambiguous | not comparable |

`MISSING_SETTLEMENT` deliberately persists the exposure as `expected - 0.00`. This preserves the invariant:

```text
sum(result.difference) = sum(expected_amount) - sum(coalesce(actual_amount, 0))
```

The dashboard currently displays the absolute sum of differences as total financial exposure. Reporting that is different from a signed ledger variance; a production dashboard should expose both explicitly.

## Fees, refunds, and adjustments

Current deterministic intelligence can explain an amount mismatch if the gross payment-to-settlement difference exactly equals recorded fees, or fees plus adjustments. Evidence generation includes refunds, but refunds are not yet part of the matching calculation.

The target settlement formula should be policy-driven rather than inferred from a single gross payment:

```text
gross payable = captured payment amount - eligible refunds
mdr            = round(gross payable * MDR rate, 2)
gst on MDR     = round(mdr * GST rate, 2)
net expected   = gross payable - mdr - gst on MDR +/- signed adjustments
variance       = net expected - actual settlement
```

Important policy choices must be explicit and versioned per merchant/provider:

- Define whether fees are supplied tax-inclusive or tax-exclusive. Do not calculate GST a second time for tax-inclusive fee rows.
- Apply refunds only when their provider status and settlement eligibility date make them part of the settlement batch. A partial refund must reduce the expected net amount without being mistaken for a missing settlement.
- Preserve signed adjustment direction (`credit` versus `debit`) rather than treating every adjustment as a positive deduction.
- Quantize each contractual component at the provider's stated rounding point, using `ROUND_HALF_UP` unless the agreement specifies another rule.
- Record fee policy/version and calculation inputs with every result so a past reconciliation can be reproduced.

## Settlement timing

Settlement absence is not always a financial exception. Evaluate the payment timestamp in the merchant's settlement timezone against a policy that defines the cutoff, business-day calendar, T+1/T+2 lag, and grace period. Before the eligible settlement deadline, use a pending state such as `AWAITING_SETTLEMENT` rather than `MISSING_SETTLEMENT`. Weekends, bank holidays, retries, and late provider files must advance the deadline using that same calendar.

## Exception handling

The deterministic analysis classifies explainable fee or fee-plus-adjustment differences separately from unexplained discrepancies. The AI layer may summarize the evidence, but it cannot resolve a financial state. Human review is required for uncertain, sensitive, or policy-exception cases and records an audit log.
