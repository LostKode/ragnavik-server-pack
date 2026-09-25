"""Reject missing or free costs in the maintained Warfare weapon recipes."""
from __future__ import annotations

import configparser
from pathlib import Path

RESTORED_WEAPONS = (
    "Buckshot", "Cranium Basher", "Doombringer", "Heartrender",
    "Hunger", "Skullcrusher", "Skystrike", "Viper",
)
# Old case-sensitive section names retained from the server configuration.
# Warfare 1.9.4 binds Blood Drinker and Hellblade Cleavers instead; both are paid.
LEGACY_SECTIONS = {"Blood drinker", "Hellblade cleavers"}


def validate_recipe_costs(path: Path) -> None:
    config = configparser.ConfigParser(interpolation=None)
    config.optionxform = str
    with path.open(encoding="utf-8") as source:
        config.read_file(source)
    for name in RESTORED_WEAPONS:
        if not config.has_option(name, "Crafting Costs"):
            raise ValueError(f"missing Warfare crafting costs: {name}")
    for name in config.sections():
        if name in LEGACY_SECTIONS:
            continue
        section = config[name]
        if "Crafting Costs" not in section:
            continue
        value = section["Crafting Costs"].strip()
        if not value:
            raise ValueError(f"empty Warfare crafting costs: {name}")
        for ingredient in value.split(","):
            fields = ingredient.split(":")
            if (len(fields) not in (2, 3) or not fields[0].strip()
                    or (len(fields) == 3 and fields[2].lower() not in ("true", "false"))):
                raise ValueError(f"invalid Warfare ingredient for {name}: {ingredient}")
            try:
                amount = int(fields[1])
            except ValueError as error:
                raise ValueError(f"invalid Warfare quantity for {name}: {ingredient}") from error
            if amount <= 0:
                raise ValueError(f"nonpositive Warfare quantity for {name}: {ingredient}")


if __name__ == "__main__":
    validate_recipe_costs(Path(__file__).resolve().parents[1] / "config/Therzie.Warfare.cfg")
    print("Warfare recipe costs validated")
