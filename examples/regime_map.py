"""Write a small qualitative regime map to CSV using only the standard library."""

from __future__ import annotations

import csv
from pathlib import Path

from trait_architecture.regime_map import sweep_regimes


if __name__ == "__main__":
    output = sweep_regimes(
        pollinator_service=(0.0, 0.25, 0.5, 0.75, 1.0),
        floral_damage_pressure=(0.0, 0.25, 0.5, 0.75, 1.0),
        leaf_consumer_pressure=(0.0, 0.5, 1.0),
        resolution=21,
    )
    destination = Path("regime_map.csv")
    with destination.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=(
                "pollinator_service",
                "floral_damage_pressure",
                "leaf_consumer_pressure",
                "attraction",
                "defence",
                "assurance",
                "fitness",
                "strategy",
            ),
        )
        writer.writeheader()
        for row in output:
            writer.writerow(
                {
                    "pollinator_service": row.regime.pollinator_service,
                    "floral_damage_pressure": row.regime.floral_damage_pressure,
                    "leaf_consumer_pressure": row.regime.leaf_consumer_pressure,
                    "attraction": row.architecture.attraction,
                    "defence": row.architecture.defence,
                    "assurance": row.architecture.assurance,
                    "fitness": row.fitness,
                    "strategy": row.strategy,
                }
            )
    print(f"wrote {len(output)} rows to {destination}")
