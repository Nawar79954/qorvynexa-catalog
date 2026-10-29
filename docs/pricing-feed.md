# Qorvynexa pricing feed

This feed is separate from `catalog.json`. The pricing automation must never rewrite or modify the catalog.

## Endpoint

`https://nawar79954.github.io/qorvynexa-catalog/prices.json`

## Schema v1

- `schemaVersion`: must be `1`.
- `updatedAt`: UTC ISO-8601 timestamp for the latest successful feed generation, or `null` before generation.
- `automaticPrices`: prices obtained from verified, permitted official sources or trusted APIs.
- `manualOverrides`: owner-maintained records; these take precedence over automatic prices for the same service, plan, country, and currency.
- Each record must contain `serviceId`, `planName`, `countryCode`, `currency`, `amount`, `sourceUrl`, and `updatedAt`.

The field name `sourceUrl` matches the Flutter parser in `lib/data/price_feed.dart`.

## Weekly validation

The GitHub Actions workflow `.github/workflows/weekly-price-feed.yml` validates the feed every Monday and supports manual runs. Validation does not scrape sites, generate prices, or modify `prices.json`. A separate source adapter must be implemented and verified before automated prices can be published.

## Safety rules

1. Never invent, estimate, or currency-convert a subscription price to represent a local price.
2. Use official provider pages or trusted APIs only where access is permitted and the returned plan, market, currency, and amount can be identified reliably.
3. Do not publish an automatic price if its source cannot be validated or its timestamp is stale.
4. Manual overrides take precedence over automatic prices.
5. If a source fails, retain the last valid price rather than replacing it with an empty or guessed value.
6. Never put API keys, tokens, or other secrets in this public repository.
7. Never modify `catalog.json` as part of price-feed generation.

## Current status

This workflow currently validates the feed only. It does not claim that any provider adapter is connected. Until a provider adapter is implemented, `prices.json` may remain empty and the app should continue using its existing catalog prices.
