import heapq
import random
import sys
import math

from copy import deepcopy
from typing import List, Dict


# TODO: Division of labor between ships
# TODO: Ship behaviour types (attacker, guard, collector)
# TODO: Avoidance of other ships
# INPR: Detection and resolution of stuck ships
# TODO: Avoidance of enemy cannonballs (don't be stationary)
# TODO: Hunt other ships when no barrels left
# TODO: (Maybe) Don't hit reward barrel
# TODO: Don't hit yourself when shooting mines
# DONE: Fix halting problem when going with speed 2 and need to turn after 3 nodes

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

    def front(self):
        return Hex(self.x, self.y).neighbor(self.ori)

    def back(self):
        return Hex(self.x, self.y).neighbor(abs(3 - self.ori))


class Ship:
    def __init__(self, entity):
        self.entity = entity  # type: Entity
        old_ship = next(iter([x for x in Global.ships if x.entity.id == self.entity.id]), None)
        if old_ship is not None:
            self.cannon_cd = old_ship.cannon_cd  # type: int
            self.mine_cd = old_ship.mine_cd  # type: int
            self.old_spd = old_ship.entity.spd  # type: int
            self.old_action = old_ship.action  # type: str
            self.old_ori = old_ship.entity.ori  # type: int
        else:
            self.cannon_cd = 0  # type: int
            self.mine_cd = 0  # type: int
            self.old_spd = -1  # type: int
            self.old_action = ""  # type: str
            self.old_ori = -1  # type: int
        self.path = None  # type: Dict[AStarAdv.Node, AStarAdv.Node]

    def think(self):
        self.cooldown()
        self.action = "WAIT"

        enemy_ships = [x for x in Global.entities if x.type == "SHIP" and not x.me]
        enemy_ship = min(enemy_ships, key=lambda ship: distance(self.entity, ship)) \
            if len(enemy_ships) > 0 else None  # type: Entity
        barrels = [x for x in Global.entities if x.type == "BARREL"]
        mines = [x for x in Global.entities if x.type == "MINE"]
        cannonballs = [x for x in Global.entities if x.type == "CANNONBALL"]

        # Turn if we are stuck
        if self.old_spd == 0 and self.entity.spd == 0:
            if self.old_action == "FASTER":
                self.action = "STARBOARD" if random.randint(0, 1) == 0 else "PORT"
            elif self.old_action == "STARBOARD":
                self.action = "PORT" if self.old_ori == self.entity.ori else "FASTER"
            elif self.old_action == "PORT":
                self.action = "STARBOARD" if self.old_ori == self.entity.ori else "FASTER"
            return

        # Hunt for barrels
        while len(barrels) > 0 and self.entity.spd == 2:
            barrels = heapq.nsmallest(1, barrels, key=lambda barrel: distance(self.entity, barrel))
            target = max(barrels, key=lambda barrel: barrel.rum)
            astar = AStarAdv(self.entity.hex(), target.hex(), self.entity.ori)
            astar.find_path()
            if not astar.found:
                barrels.remove(target)
                continue
            self.move(astar)
            break

        if self.entity.spd != 2:
            self.action = "FASTER"

        # Clear mines near the path
        if self.path is not None:
            for from_hex, to_hex in self.path.items():
                if distance(self.entity, to_hex.pos) > 10:
                    break
                nearby_mine = find_nearby_mine(to_hex.pos)
                if nearby_mine is not None:
                    self.target = nearby_mine
                    self.action = "FIRE"
                    break

        should_attack = self.action == "WAIT" or (self.old_spd == 0 and self.entity.spd == 0)
        # Fire at enemy
        if should_attack and self.cannon_cd == 0 and enemy_ship is not None and distance(self.entity, enemy_ship) < 15:
            attack_point = calculate_attack(enemy_ship, self.entity)
            if attack_point is not None and distance(self.entity, attack_point) < 10:
                self.target = attack_point
                self.action = "FIRE"
            return

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

    def move(self, astar):
        """
        :type astar: AStarAdv
        """
        self.action = "WAIT"
        next_node = astar.path[astar.beg]
        if next_node.ori != self.entity.ori:
            self.action = "PORT" if required_rotation(self.entity.ori, next_node.ori) else "STARBOARD"
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

    def front(self, ori):
        return Hex(self.x, self.y).neighbor(ori)

    def back(self, ori):
        return Hex(self.x, self.y).neighbor(abs(3 - ori))

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


class AStarAdv:
    class Node:
        def __init__(self, pos, ori, astar):
            self.pos = pos  # type: Hex
            self.ori = ori  # type: int
            self.expanded = False
            self.astar = astar  # type: AStarAdv
            self.neighbors = []  # type: List[AStarAdv.Node]

        def expand(self):
            pos = self.pos
            for i in range(self.astar.spd):
                pos = self.pos.front(self.ori)
            if in_grid(Global.grid, pos):
                self.neighbors.append(AStarAdv.Node(pos, self.ori, self.astar))
                self.neighbors.append(AStarAdv.Node(pos, rotate(self.ori, 1), self.astar))
                self.neighbors.append(AStarAdv.Node(pos, rotate(self.ori, -1), self.astar))

        def __eq__(self, other):
            return self.pos == other.pos

        def __ne__(self, other):
            return self.pos != other.pos

        def __hash__(self):
            return hash(self.pos)

        def __lt__(self, other):
            return self.pos < other.pos

    def __init__(self, beg, end, ori):
        self.beg = AStarAdv.Node(beg, ori, self)  # type: AStarAdv.Node
        self.end = end  # type: Hex
        self.spd = 2  # type: int
        self.frontier = PriorityQueue()
        self.frontier.put(self.beg, 0)
        self.came_from = {self.beg: None}
        self.cost_so_far = {self.beg: 0}
        self.found = False
        self.path = None

    def h(self, from_node):
        if from_node.pos.front(from_node.ori) == self.end or from_node.pos.back(from_node.ori) == self.end:
            return 0
        next_hex = from_node.pos
        for i in range(self.spd):
            next_hex = next_hex.front(from_node.ori)
        return distance(from_node.pos, self.end) + distance(next_hex, self.end)

    def find_path(self):
        last = None
        while not self.frontier.empty():
            cur = self.frontier.get()  # type: AStarAdv.Node
            if cur.pos == self.end or cur.pos.front(cur.ori) == self.end or cur.pos.back(cur.ori) == self.end:
                self.found = True
                last = cur
                break
            if not cur.expanded:
                cur.expand()
            for nxt in [nbr for nbr in cur.neighbors]:
                new_cost = self.cost_so_far[cur] + self.spd
                if nxt not in self.cost_so_far or new_cost < self.cost_so_far[nxt]:
                    self.cost_so_far[nxt] = new_cost
                    priority = new_cost + self.h(nxt)
                    self.frontier.put(nxt, priority)
                    self.came_from[nxt] = cur
        if not self.found:
            return
        # Construct the path
        self.path = {}
        cur = last
        while cur != self.beg:
            self.path[self.came_from[cur]] = cur
            cur = self.came_from[cur]


def in_grid(grid, target):
    return len(grid) > target.x > 0 and len(grid[0]) > target.y > 0


def distance(target1, target2):
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


def rotate(from_ori, direction):
    to_ori = from_ori + direction
    while to_ori > 5:
        to_ori = to_ori - 6
    while to_ori < 0:
        to_ori = to_ori + 6
    return to_ori


def offset_to_cube(x, y):
    ox = x - (y - (abs(y) % 2)) / 2
    oz = y
    oy = -ox - oz
    return ox, oy, oz


def cube_distance(x1, y1, z1, x2, y2, z2):
    return (abs(x1 - x2) + abs(y1 - y2) + abs(z1 - z2)) / 2


def heuristic(a, b):
    return distance(a, b)


def find_path(beg, tar, ship_entity):
    """
    A* path-finding implementation
    :type ship_entity: Entity
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
        for nxt in [neighbor for neighbor in cur.neighbors()]:
            new_cost = cost_so_far[cur] + cost(cur, nxt, came_from, ship_entity.ori)
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
    if ship_entity.id == 2:
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


def find_nearby_mine(target):
    entity = Global.grid[target.x][target.y]
    if entity is not None and entity.type == "MINE":
        return entity
    for neighbor in target.neighbors():
        if Global.grid[neighbor.x][neighbor.y] is not None and Global.grid[neighbor.x][neighbor.y].type == "MINE":
            return Global.grid[neighbor.x][neighbor.y]
    return None


def calculate_attack(target_ship, self_ship):
    # Calculate where to attack to hit the enemy.
    # - If enemy is near a barrel, find the enemy's approximate path and attack.
    # - Else, assume enemy will move straight and attack.
    barrels = [x for x in Global.entities if x.type == "BARREL" and distance(target_ship, x) <= 5]
    if len(barrels) > 0:
        barrel = min(barrels, key=lambda x: distance(target_ship, x))
        path = find_path(target_ship.hex(), barrel.hex(), target_ship)
        impact_point = calculate_impact_point(target_ship, self_ship.front(), path)
        if impact_point is not None:
            return impact_point
    impact_point = calculate_impact_point_straight(target_ship, self_ship.front())
    if impact_point is not None:
        return impact_point
    return None


def calculate_impact_point(target_ship, fire_point, path):
    turn = 0
    cur_hex = target_ship.hex()
    while cur_hex in path and turn < 5:
        turn = turn + 1
        cur_hex = path[cur_hex]
        cball_duration = round(1 + (distance(fire_point, cur_hex)) / 2)
        if cball_duration == turn:
            return cur_hex
    return None


def calculate_impact_point_straight(target_ship, fire_point):
    turn = 0
    cur_hex = target_ship.hex()
    while turn < 5:
        turn = turn + 1
        next_hex = cur_hex
        for i in range(target_ship.spd):
            next_hex = next_hex.front(target_ship.ori)
        cur_hex = next_hex if in_grid(Global.grid, next_hex) else cur_hex
        cball_duration = round(1 + (distance(fire_point, cur_hex)) / 2)
        if cball_duration == turn:
            return cur_hex
    return None


# endregion


class Mcts:
    class Node:
        def __init__(self, parent_node=None):
            """
            :type parent_node: Mcts.Node
            """
            self.entities = deepcopy(parent_node.entities) if parent_node is not None else None  # type: Mcts.Node
            self.children = []  # type: List[Mcts.Node]
            self.total_score = 0  # type: int
            self.max_score = 0  # type: int

    def __init__(self):
        self.root = Mcts.Node()


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
