# Qorvynexa pricing feed

This feed is separate from `catalog.json`. Pricing automation must never rewrite or modify the catalog.

## Endpoint

`https://nawar79954.github.io/qorvynexa-catalog/prices.json`

## Schema v1

- `schemaVersion`: must be `1`.
- `updatedAt`: UTC ISO-8601 timestamp for the latest successful feed generation, or `null` before generation.
- `automaticPrices`: prices obtained from verified, permitted official sources or trusted APIs.
- `manualOverrides`: owner-maintained records; these take precedence over automatic prices for the same service, plan, country, and currency.
- Each record must contain `serviceId`, `planName`, `countryCode`, `currency`, `amount`, `sourceUrl`, and `updatedAt`.

The field name `sourceUrl` matches the Flutter parser in `lib/data/price_feed.dart`.

## Weekly update

The GitHub Actions workflow `.github/workflows/weekly-price-feed.yml` runs every Monday and supports manual runs. It currently contains a strict Disney+ Netherlands adapter for the `With ads` and `Premium` plans, then validates the resulting feed. It only publishes if the official page exposes one unambiguous EUR monthly amount close to each exact plan label. If the source format changes or a price cannot be uniquely identified, the run fails before writing the feed; investigate the log rather than guessing.

The adapter uses the official page `https://www.disneyplus.com/en-nl`. It does not currently collect prices for other providers or countries.

## Safety rules

1. Never invent, estimate, or currency-convert a subscription price to represent a local price.
2. Use official provider pages or trusted APIs only where access is permitted and the returned plan, market, currency, and amount can be identified reliably.
3. Do not publish an automatic price if its source cannot be validated or its timestamp is stale.
4. Manual overrides take precedence over automatic prices in the app.
5. If a source fails, retain the last valid feed rather than replacing it with an empty or guessed feed. A failed adapter run does not commit `prices.json`.
6. Never put API keys, tokens, or other secrets in this public repository.
7. Never put price-feed generation logic in a step that modifies `catalog.json`.

## Current status

Only Disney+ Netherlands is configured as an automatic source adapter. Other providers and markets remain unconfigured until each has a verified adapter and tests. The app's existing catalog prices remain the fallback when a feed price is absent.
