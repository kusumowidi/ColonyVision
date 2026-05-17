# ColonyVision AI Agent Notes

This project is a local Python desktop prototype for bacterial colony counting and AI-assisted microbiology dashboard workflows.

## Development Guidelines

- Keep GUI code in `gui/` and computer vision code in `core/`.
- Do not add cloud services, databases, or deep-learning dependencies to the MVP.
- Preserve the `count_colonies(image, params)` interface so future detector backends can be added cleanly.
- Keep dashboard data models in `models/`.
- Use colony statuses consistently: `valid`, `artifact`, `merged`, `manual_added`, and `removed`.
- Treat the confidence score as a heuristic quality score, not a trained model probability.
- CFU/ml is calculated as `count * dilution_factor / plated_volume_ml`.
- Treat the software as a research and educational prototype, not a diagnostic medical device.
