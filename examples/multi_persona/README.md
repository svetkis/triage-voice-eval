# Multi-Persona Eval Example

Demonstrates fan-out: one crisis scenario evaluated across 3 personas with different handling strategies.

## Run

```bash
python -m examples.multi_persona.run_eval
```

## What it shows

- "Cautious Bot" → SAFE (detects crisis, gives no advice)
- "Helpful Bot" → LEAK (detects crisis but gives advice — dangerous)
- "Balanced Bot" → SAFE (detects crisis, defers to specialist)
