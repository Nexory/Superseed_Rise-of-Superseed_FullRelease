class Faction:
    def __init__(self, name, health_mod, attack_mod, speed_mod):
        self.name = name
        self.health_mod = health_mod
        self.attack_mod = attack_mod
        self.speed_mod = speed_mod

class Player(Faction):
    def __init__(self):
        super().__init__("Player", health_mod=1.0, attack_mod=1.0, speed_mod=1.0)

class Bandits(Faction):
    def __init__(self):
        super().__init__("Bandits", health_mod=1.1, attack_mod=1.2, speed_mod=0.9)

class Undead(Faction):
    def __init__(self):
        super().__init__("Undead", health_mod=1.2, attack_mod=0.9, speed_mod=0.8)

class Zombies(Faction):
    def __init__(self):
        super().__init__("Zombies", health_mod=0.9, attack_mod=1.0, speed_mod=1.1)