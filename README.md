Made for Superseed Tesla competition by Nexory
@Nexory96 / Discord: nexory

"Rise of Superseed" is a real-time strategy game set in the embattled realm of Ethara, where players muster an army to safeguard their base and raze the enemy’s across 25 progressively tougher levels. Using seeds earned from fallen enemies and passive income linked to locked superseeds, players deploy units—from nimble Peasants to hulking Tanks—that automatically engage waves of Bandits, Zombies, and Undead. Units vary in stats like health (e.g., Peasant: 100, Tank: 300), attack power (e.g., Archer: 20, Warrior: 25), and range (e.g., Melee: 135, Mage: 350). Seeds spawn units (e.g., Peasant: 10, Tank: 60), while superseeds, won from victories, fund upgrades for units (e.g., +25 health) and bases (e.g., +75 HP per level, up to 2500+). Progress persists via a robust savegame system: locally, it writes to player_data.json, and on the web (via Pygbag), it leverages localStorage, preserving superseeds, max level, upgrades, and unlocked units across sessions.
Narrated by David, the story traces Ethara’s rising threats: Bandits rule early levels, with the Bandit King (600 HP, 35 attack) yielding at 25% health in Level 5, granting Archers. Zombies overrun from Level 6, and Undead emerge at Level 16, leading to a climactic battle with the Undead King (700 HP, 40 attack) in Level 25. Towers unlock at Level 6, pitting upgradable Player Tower Archers against enemy Zombie Archers or Undead Mages. With 25 achievements (e.g., "Beat Level 10", "Kill 100 Units"), a sleek UI featuring unit buttons and resource displays, and vivid visuals—animated sprites (14 frames per state) and faction-specific backgrounds—complemented by audio (e.g., bowshot.ogg, toggleable music), the game weaves strategy, resource management, and narrative into a compelling package, enhanced by seamless save functionality for both desktop and web play.
Key Game Aspects by Section (Bullet Points)
Gameplay Overview
Core mechanic: Spawn units with seeds to defend your base and destroy the enemy’s in real-time combat.

Units: 5 player types (Peasant, Spearman, Archer, Warrior, Tank) with auto-fighting AI.

Combat stats: Health (e.g., Peasant: 100, Tank: 300), Attack (e.g., Archer: 20), Speed (e.g., Razor: 2.5), Range (e.g., Melee: 135, Archer: 300).

Resources
Seeds: Gained from kills and passive income (e.g., 84 seeds/sec at 2600 locked superseeds), spent on units (e.g., Tank: 60).

Superseeds: Earned via level wins, used for upgrades, boost passive income when locked (e.g., 0.9 seeds/frame at 1600 locked).

Bases: Player base starts at 1000 HP (upgradable to 2500+), enemy base scales per level (e.g., 1400 HP at Level 5).

Levels and Progression
Levels: 25 total, split across 3 enemy factions.

Factions: Bandits (Levels 1-5), Zombies (Levels 6-15), Undead (Levels 16-25).

Unlocks: Archer at Level 5 (Bandit King surrender), Tank at Level 10 (prison break).

Upgrades
Unit upgrades: Health (+25), Damage (+5), Attack Speed (+0.075), Speed (+0.2), max 20 levels (e.g., Peasant Health: 10 superseeds).

Base upgrades: Base HP (+75/level), Tower stats (Attack +5, Range +50, Speed +0.075), max 20 levels.

Story and Events
Narrator: David guides the story of Ethara’s liberation.

Key events: Bandit King surrenders at Level 5 (600 HP), Zombies rise at Level 6, Undead King falls at Level 25 (700 HP).

Features
Achievements: 25 goals (e.g., "Max Upgrade a Unit") with pop-up notifications.

Towers: Unlock at Level 6—Player Tower Archer (400 range, upgradable) vs. Zombie Archer or Undead Mage.

Savegame: Local play saves to player_data.json; web play (Pygbag) uses localStorage for progress (superseeds, levels, upgrades).

UI
Interface: Unit spawn buttons, seeds/superseeds/XP display, pause menu, and upgrade screens.

Visuals and Audio
Visuals: Animated sprites (idle, run, attack, die; 14 frames each), faction-themed backgrounds (e.g., battlefield_zombies.png).

Audio: Sound effects (e.g., melee_sword.ogg), toggleable music via mouse click.

