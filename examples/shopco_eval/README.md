# ShopCo Eval Example

Demonstrates evaluating a customer support bot using binary safety guards.

## Run

```bash
python -m examples.shopco_eval.run_eval
```

## What it does

- Loads 3 test scenarios (safety issue, refund, jailbreak)
- Runs them through a mock pipeline
- Evaluates with CrisisGuard and JailbreakGuard
- Prints a summary report
