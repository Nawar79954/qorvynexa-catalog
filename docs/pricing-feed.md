# Qorvynexa pricing feed

This feed is separate from `catalog.json`. It must never rewrite or modify the bundled catalog.

## Endpoint

After this file is merged and the existing GitHub Pages deployment publishes the repository root, the intended URL is:

`https://nawar79954.github.io/qorvynexa-catalog/prices.json`

Verify the URL responds with JSON before configuring the Flutter app to use it.

## Schema v1

- `schemaVersion`: feed schema version.
- `updatedAt`: UTC ISO-8601 timestamp for the latest successful feed generation, or `null` before the first generation.
- `automaticPrices`: prices supplied by a verified, permitted source adapter.
- `manualOverrides`: prices entered and maintained by the repository owner. These take precedence over automatic prices for the same service, plan, country, and currency.
- Each price record should contain `serviceId`, `planName`, `countryCode`, `currency`, `amount`, `source`, and `updatedAt`.

## Safety rules

1. Do not invent or infer subscription prices.
2. Do not scrape a provider unless its terms and access method permit it.
3. Do not publish a new automatic price unless the source response is validated and sufficiently fresh.
4. Manual overrides take precedence over automatic values.
5. If the feed is unavailable, invalid, stale, or missing a price, the app falls back to its last valid cached feed and then to the bundled catalog.
6. Never put API keys, tokens, or other secrets in this public file.

## Current status

This is an initial empty schema only. It does not claim that any provider is already connected, and it does not yet perform daily price collection. Provider adapters and the Flutter merge/cache logic must be implemented and tested before the feature is considered active.
