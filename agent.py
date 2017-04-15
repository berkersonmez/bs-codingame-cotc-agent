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
            self.owner = arg1  # type: int
            self.turns = arg2  # type: int

    def hex(self):
        return Hex(self.x, self.y)


class Ship:
    def __init__(self, entity):
        self.entity = entity  # type: Entity
        old_ship = next(iter([x for x in Global.ships if x.entity.id == self.entity.id]), None)
        if old_ship is not None:
            self.cannon_cd = old_ship.cannon_cd  # type: int
            self.mine_cd = old_ship.mine_cd  # type: int
            self.old_spd = old_ship.entity.spd  # type: int
            self.old_action = old_ship.action  # type: str
        else:
            self.cannon_cd = 0  # type: int
            self.mine_cd = 0  # type: int
            self.old_spd = -1  # type: int
            self.old_action = ""  # type: str

    def think(self):
        self.cooldown()
        self.action = "WAIT"

        enemy_ships = [x for x in Global.entities if x.type == "SHIP" and not x.me]
        enemy_ship = min(enemy_ships, key=lambda ship: distance(self.entity, ship)) \
            if len(enemy_ships) > 0 else None  # type: Entity
        barrels = [x for x in Global.entities if x.type == "BARREL"]
        mines = [x for x in Global.entities if x.type == "MINE"]
        cannonballs = [x for x in Global.entities if x.type == "CANNONBALL"]

        # Hunt for barrels
        while len(barrels) > 0:
            barrels = heapq.nsmallest(1, barrels, key=lambda barrel: distance(self.entity, barrel))
            target = max(barrels, key=lambda barrel: barrel.rum)
            if is_obstacle(target.hex()):
                barrels.remove(target)
                continue
            path = find_path(self.entity.hex(), target.hex(), self)
            if path is None:
                barrels.remove(target)
                continue
            self.move(path)
            break

        should_attack = self.action == "WAIT" or (self.old_spd == 0 and self.entity.spd == 0)
        # Fire at enemy
        if should_attack and self.cannon_cd == 0 and enemy_ship is not None and distance(self.entity, enemy_ship) < 10:
            self.target = enemy_ship
            self.action = "FIRE"
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
        if self.action == "WAIT":
            print("WAIT")
        elif self.action == "FIRE":
            self.cannon_cd = 2
            print("FIRE " + str(self.target.x) + " " + str(self.target.y))
        elif self.action == "MOVE":
            print("MOVE " + str(self.target.x) + " " + str(self.target.y))
        elif self.action == "MINE":
            self.mine_cd = 5
            print("MINE")
        elif self.action == "PORT":
            print("PORT")
        elif self.action == "STARBOARD":
            print("STARBOARD")
        elif self.action == "FASTER":
            print("FASTER")
        elif self.action == "SLOWER":
            print("SLOWER")
        else:
            print("WAIT")

    def move(self, path):
        self.action = "WAIT"
        next_hex = path[self.entity.hex()]
        next_dir = direction_between(self.entity.hex(), next_hex)
        second_hex = path[next_hex] if next_hex in path else None
        second_dir = direction_between(next_hex, second_hex) if second_hex is not None else None
        third_hex = path[second_hex] if second_hex is not None and second_hex in path else None
        third_dir = direction_between(second_hex, third_hex) if third_hex is not None else None
        if self.entity.spd == 0:
            # If we are stationary, turn if next dir is different, else get faster
            if next_dir != self.entity.ori:
                self.action = "PORT" if required_rotation(self.entity.ori, next_dir) == 1 else "STARBOARD"
            else:
                self.action = "FASTER"
        elif self.entity.spd == 1:
            # If our speed is one:
            # - Slow down if need to turn immediately
            # - Turn if need to turn with distance 1
            # - Wait if need to turn with distance 2
            # - Get faster if no need to turn
            if next_dir != self.entity.ori:
                print("NEXT_DIR:" + str(next_dir) + " NOW_ORI:" + str(self.entity.ori), file=sys.stderr)
                self.action = "SLOWER"
            elif second_dir is not None and second_dir != next_dir:
                self.action = "PORT" if required_rotation(next_dir, second_dir) == 1 else "STARBOARD"
            elif third_dir is not None and third_dir != second_dir:
                self.action = "WAIT"
            elif third_dir is not None:
                self.action = "FASTER"
        elif self.entity.spd == 2:
            # If our speed is two:
            # - Slow down if need to turn immediately or with distance 1
            # - Turn if need to turn with distance 2
            # - Wait if no need to turn
            if next_dir != self.entity.ori or (second_dir is not None and second_dir != next_dir):
                self.action = "SLOWER"
            elif third_dir is not None and third_dir != second_dir:
                self.action = "PORT" if required_rotation(second_dir, third_dir) == 1 else "STARBOARD"
            elif third_dir is not None:
                self.action = "WAIT"
            else:
                self.action = "SLOWER"
        return


# region HEX GRID LOGIC


class PriorityQueue:
    def __init__(self):
        self.elements = []

    def empty(self):
        return len(self.elements) == 0

    def put(self, item, priority):
        heapq.heappush(self.elements, (priority, item))

    def get(self):
        return heapq.heappop(self.elements)[1]


class Hex:
    def __init__(self, x, y):
        self.x = x
        self.y = y

    def neighbor(self, direction):
        parity = abs(self.y) % 2
        dirn = Global.dir_to_hex[parity][direction]
        return Hex(self.x + dirn.x, self.y + dirn.y)

    def neighbors(self):
        return [nbr for nbr in [self.neighbor(dirn) for dirn in range(6)] if in_grid(Global.grid, nbr)]

    def __eq__(self, other):
        return self.x == other.x and self.y == other.y

    def __ne__(self, other):
        return self.x != other.x or self.y != other.y

    def __hash__(self):
        return hash((self.x, self.y))

    def __lt__(self, other):
        return self.x < other.x or self.y < other.y

    def __str__(self):
        return "(" + str(self.x) + "," + str(self.y) + ")"


def in_grid(grid, target):
    return len(grid) > target.x and len(grid[0]) > target.y


def distance(target1, target2):
    """
    :type target1: Entity
    :type target2: Entity
    """
    x1, y1, z1 = offset_to_cube(target1.x, target1.y)
    x2, y2, z2 = offset_to_cube(target2.x, target2.y)
    return cube_distance(x1, y1, z1, x2, y2, z2)


def cost(from_hex, to_hex, came_from, current_ori):
    dist = distance(from_hex, to_hex)
    if came_from[from_hex] is None:
        prev_dir = current_ori
    else:
        prev_dir = direction_between(came_from[from_hex], from_hex)
    now_dir = direction_between(from_hex, to_hex)
    turn_cost = turning_cost(prev_dir, now_dir)
    return dist + turn_cost


def direction_between(from_hex, to_hex):
    difx = to_hex.x - from_hex.x
    dify = to_hex.y - from_hex.y
    return Global.hex_to_dir[from_hex.y % 2][(difx, dify)]


def turning_cost(from_dir, to_dir):
    cost1 = abs(from_dir - to_dir)
    if cost1 <= 3:
        return cost1
    return 6 - cost1


def required_rotation(from_dir, to_dir):
    # Returns 0 for right, 1 for left
    diff_dir = abs(to_dir - from_dir)
    if diff_dir < 3:
        return 1 if to_dir > from_dir else 0
    else:
        return 0 if to_dir > from_dir else 1


def offset_to_cube(x, y):
    ox = x - (y - (abs(y) % 2)) / 2
    oz = y
    oy = -ox - oz
    return ox, oy, oz


def cube_distance(x1, y1, z1, x2, y2, z2):
    return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) / 2


def heuristic(a, b):
    return distance(a, b)


def find_path(beg, tar, ship):
    """
    A* path-finding implementation
    :type beg: Hex
    :type tar: Hex
    """
    frontier = PriorityQueue()
    frontier.put(beg, 0)
    came_from = {beg: None}
    cost_so_far = {beg: 0}
    found = False

    while not frontier.empty():
        cur = frontier.get()
        if cur == tar:
            found = True
            break
        for nxt in [neighbor for neighbor in cur.neighbors() if not is_obstacle(neighbor)]:
            new_cost = cost_so_far[cur] + cost(cur, nxt, came_from, ship.entity.ori)
            if nxt not in cost_so_far or new_cost < cost_so_far[nxt]:
                cost_so_far[nxt] = new_cost
                priority = new_cost + heuristic(tar, nxt)
                frontier.put(nxt, priority)
                came_from[nxt] = cur
    if not found:
        return None
    # Construct path
    path = {}
    cur = tar
    while cur != beg:
        path[came_from[cur]] = cur
        cur = came_from[cur]
    if ship.entity.id == 2:
        print("TARGET: " + str(tar), file=sys.stderr)
        print("---PATH----", file=sys.stderr)
        for key, value in path.items():
            print(str(key) + " -> " + str(value), file=sys.stderr)
        print("-----------", file=sys.stderr)
    return path


def is_obstacle(target):
    """
    :type target: Hex
    """
    entity = Global.grid[target.x][target.y]
    if entity is not None and entity.type == "MINE":
        return True
    for neighbor in target.neighbors():
        if Global.grid[neighbor.x][neighbor.y] is not None and Global.grid[neighbor.x][neighbor.y].type == "MINE":
            return True
    return False


# endregion

class Global:
    me_ship_cnt = 0
    entity_cnt = 0
    entities = []  # type: List[Entity]
    ships = []  # type: List[Ship]
    grid = [[None for x in range(21)] for y in range(23)]  # type: List[List[Entity]]
    dir_to_hex = [
        [Hex(+1, 0), Hex(0, -1), Hex(-1, -1),
         Hex(-1, 0), Hex(-1, +1), Hex(0, +1)],
        [Hex(+1, 0), Hex(+1, -1), Hex(0, -1),
         Hex(-1, 0), Hex(0, +1), Hex(+1, +1)]
    ]
    hex_to_dir = [{(+1, 0):0, (0, -1):1, (-1, -1):2, (-1, 0):3, (-1, +1):4, (0, +1):5},
                  {(+1, 0):0, (+1, -1):1, (0, -1):2, (-1, 0):3, (0, +1):4, (+1, +1):5}]


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
    Global.grid = [[None for _ in range(21)] for _ in range(23)]
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
        Global.grid[x][y] = entity
        if entity.type == "SHIP" and entity.me:
            ships.append(Ship(entity))
    Global.entities = entities
    Global.ships = ships


def main():
    play()


if __name__ == "__main__":
    main()
