import heapq
import random
import sys
import math
from typing import List


# To debug: print("Debug messages...", file=sys.stderr)
class Entity:
    def __init__(self, no, typ, x, y, arg1, arg2, arg3, arg4):
        self.id = no  # type: int
        self.type = typ  # type: str
        self.x = x  # type: int
        self.y = y  # type: int
        if typ == "SHIP":
            self.ori = arg1  # type: int
            self.spd = arg2  # type: int
            self.rum = arg3  # type: int
            self.me = True if arg4 == 1 else False  # type: bool
        elif typ == "BARREL":
            self.rum = arg1  # type: int
        elif typ == "CANNONBALL":
            self.owner = arg1  #type: int
            self.turns = arg2  #type: int

class Global:
    me_ship_cnt = 0
    entity_cnt = 0
    entities = []  # type: List[Entity]
    ships = []  # type: List[Ship]

class Ship:
    def __init__(self, entity):
        self.entity = entity  # type: Entity
        old_ship = next(iter([x for x in Global.ships if x.entity.id == self.entity.id]), None)
        if old_ship is not None:
            self.cannon_cd = old_ship.cannon_cd  # type: int
            self.mine_cd = old_ship.mine_cd  # type: int
        else:
            self.cannon_cd = 0  # type: int
            self.mine_cd = 0  # type: int

    def think(self):
        self.cooldown()
        self.move = "WAIT"

        enemy_ships = [x for x in Global.entities if x.type == "SHIP" and not x.me]
        enemy_ship = min(enemy_ships, key= lambda ship: distance(self.entity, ship))  # type: Entity
        barrels = [x for x in Global.entities if x.type == "BARREL"]
        mines = [x for x in Global.entities if x.type == "MINE"]
        cannonballs = [x for x in Global.entities if x.type == "CANNONBALL"]

        if self.cannon_cd == 0 and enemy_ship is not None and distance(self.entity, enemy_ship) < 10:
            self.target = enemy_ship
            self.move = "FIRE"
            return

        if len(barrels) > 0:
            barrels = heapq.nsmallest(2, barrels, key=lambda barrel: distance(self.entity, barrel))
            self.target = max(barrels, key=lambda barrel: barrel.rum)
            self.move = "MOVE"
            return

        # self.target = Entity("99", "-", self.entity.x + random.randint(0,1), self.entity.y + random.randint(0,1), "", "", "", "")
        # self.move = "MOVE"

        # if self.mine_cd == 0:
        #     self.move = "MINE"
        #     return

    def cooldown(self):
        self.cannon_cd = self.cannon_cd - 1 if self.cannon_cd > 0 else 0
        self.mine_cd = self.mine_cd - 1 if self.mine_cd > 0 else 0

    def act(self):
        if self.move == "WAIT":
            print("WAIT")
        elif self.move == "FIRE":
            self.cannon_cd = 2
            print("FIRE " + str(self.target.x) + " " + str(self.target.y))
        elif self.move == "MOVE":
            print("MOVE " + str(self.target.x) + " " + str(self.target.y))
        elif self.move == "MINE":
            self.mine_cd = 5
            print("MINE")

def distance(target1, target2):
    """
    :type target1: Entity
    :type target2: Entity
    """
    x1, y1, z1 = offset_to_cube(target1.x, target1.y)
    x2, y2, z2 = offset_to_cube(target2.x, target2.y)
    return cube_distance(x1, y1, z1, x2, y2, z2)

def offset_to_cube(x, y):
    ox = y - (x - (x % 2)) / 2
    oz = x
    oy = -ox - oz
    return ox, oz, oy

def cube_distance(x1, y1, z1, x2, y2, z2):
    return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) / 2

def play():
    # game loop
    while True:
        get_inputs()
        for ship in Global.ships:
            ship.think()
            ship.act()


def get_inputs():
    Global.me_ship_cnt = int(input())  # the number of remaining ships
    Global.entity_cnt = int(input())  # the number of entities (e.g. ships, mines or cannonballs)
    entities = []
    ships = []
    for i in range(Global.entity_cnt):
        entity_id, entity_type, x, y, arg_1, arg_2, arg_3, arg_4 = input().split()
        entity_id = int(entity_id)
        x = int(x)
        y = int(y)
        arg_1 = int(arg_1)
        arg_2 = int(arg_2)
        arg_3 = int(arg_3)
        arg_4 = int(arg_4)
        entity = Entity(entity_id, entity_type, x, y, arg_1, arg_2, arg_3, arg_4)
        entities.append(entity)
        if entity.type == "SHIP" and entity.me:
            ships.append(Ship(entity))
    Global.entities = entities
    Global.ships = ships


def main():
    play()

if __name__ == "__main__":
    main()