# levels.py
from units import (
    Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank,
    Zombie_Archer, Zombie_Assassin, Zombie_Farmer, Zombie_Melee, Zombie_Tank,
    Undead_Axeman, Undead_King, Undead_Mage, Undead_Samurai, Undead_Warrior
)
import random

class Level:
    """Class to manage level data."""
    def __init__(self, level_number):
        self.level_number = level_number
        self.faction, self.units = self.define_level_units()

    def define_level_units(self):
        """Return faction and unit list based on level number."""
        if 1 <= self.level_number <= 3:
            return "Bandits", [Bandit_Razor, Bandit_Madman]
        elif 4 <= self.level_number <= 5:
            return "Bandits", [Bandit_Razor, Bandit_Madman, Bandit_Archer, Bandit_Tank]
        elif 6 <= self.level_number <= 15:
            return "Zombies", [Zombie_Archer, Zombie_Assassin, Zombie_Farmer, Zombie_Melee, Zombie_Tank]
        elif 16 <= self.level_number <= 24:
            return "Undead", [Undead_Axeman, Undead_Mage, Undead_Samurai, Undead_Warrior]  # No King here, spawned separately
        elif 25 <= self.level_number <= 25:
            return "Undead", [Undead_Axeman, Undead_Mage, Undead_Samurai, Undead_Warrior, Undead_King]  # No King here, spawned separately
        else:
            raise ValueError(f"Invalid level number: {self.level_number}")

    def get_next_enemy_unit(self):
        """Return a random unit class from the level's unit list."""
        return random.choice(self.units) if self.units else None