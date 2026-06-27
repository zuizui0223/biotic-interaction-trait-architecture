"""Write the canonical parameter-sweep stability summary as CSV."""

from __future__ import annotations

import csv
from pathlib import Path

from trait_architecture.stability import assess_sign_stability, canonical_scenarios


if __name__ == "__main__":
    report = assess_sign_stability(canonical_scenarios(), resolution=11)
    destination = Path("sign_stability_report.csv")
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "scenario_id",
                "n_optima",
                "covariance_attraction_defence",
                "correlation_attraction_defence",
                "association_sign",
                "strategy_counts",
                "cross_scenario_status",
            ),
        )
        writer.writeheader()
        for summary in report.summaries:
            writer.writerow(
                {
                    "scenario_id": summary.scenario_id,
                    "n_optima": summary.n_optima,
                    "covariance_attraction_defence": summary.covariance,
                    "correlation_attraction_defence": summary.correlation,
                    "association_sign": summary.sign.value,
                    "strategy_counts": ";".join(
                        f"{name}:{count}" for name, count in sorted(summary.strategy_counts.items())
                    ),
                    "cross_scenario_status": report.status.value,
                }
            )
    print(f"{report.status.value}: wrote {len(report.summaries)} scenario summaries to {destination}")
