# RISKCAST Python SDK

Official Python SDK for the RISKCAST Marine Cargo Insurance API.

## Installation

```bash
pip install riskcast-sdk
```

## Quick Start

```python
from riskcast import RiskcastClient

# Initialize client
client = RiskcastClient(api_key="your_api_key")

# Request a quote
quote = client.quotes.request(
    origin_port="CNSHA",
    destination_port="USLAX",
    cargo_type="ELECTRONICS",
    cargo_value_usd=100000,
    departure_date="2024-03-15",
    arrival_date="2024-04-05"
)

print(f"Quote ID: {quote.id}")
print(f"Premium: ${quote.total_premium_usd}")

# Accept and bind
client.quotes.accept(quote.id)
policy = client.quotes.bind(quote.id)
```

## Documentation

Full documentation available at: https://docs.riskcast.io

## License

MIT License
