# Grupo 129:
# 110020 Diogo Pan

from sys import stdin
from pathlib import Path
import matplotlib.pyplot as plt
import imageio
from search import *

_str_to_piece = {
    "I": [((1,), (1,), (1,), (1,)), ((1, 1, 1, 1),)],
    "S": [((1, -1), (1, 1), (-1, 1)), ((-1, 1, 1), (1, 1, -1)),
          ((-1, 1), (1, 1), (1, -1)), ((1, 1, -1), (-1, 1, 1))],
    "T": [((-1, 1, -1), (1, 1, 1)), ((1, 1, 1), (-1, 1, -1)),
          ((-1, 1), (1, 1), (-1, 1)), ((1, -1), (1, 1), (1, -1))],
    "L": [((1, 1, 1), (1, -1, 0)), ((1, 1, 1), (0, -1, 1)),
          ((0, -1, 1), (1, 1, 1)), ((1, 0), (1, -1), (1, 1)),
          ((1, -1, 0), (1, 1, 1)), ((0, 1), (-1, 1), (1, 1)),
          ((1, 1), (-1, 1), (0, 1)), ((1, 1), (1, -1), (1, 0))],
}

# Normalized coordinates for each piece shape
_piece_to_str = {
    ((0, 0), (1, 0), (2, 0), (2, 1)): "L", ((0, 0), (0, 1), (0, 2), (1, 0)): "L",
    ((0, 0), (0, 1), (1, 1), (2, 1)): "L", ((0, 2), (1, 0), (1, 1), (1, 2)): "L",
    ((0, 0), (1, 0), (1, 1), (1, 2)): "L", ((0, 0), (0, 1), (1, 0), (2, 0)): "L",
    ((0, 1), (1, 1), (2, 0), (2, 1)): "L", ((0, 0), (0, 1), (0, 2), (1, 2)): "L",
    ((0, 0), (1, 0), (2, 0), (3, 0)): "I", ((0, 0), (0, 1), (0, 2), (0, 3)): "I",
    ((0, 1), (1, 0), (1, 1), (1, 2)): "T", ((0, 0), (0, 1), (0, 2), (1, 1)): "T",
    ((0, 0), (1, 0), (1, 1), (2, 0)): "T", ((0, 1), (1, 0), (1, 1), (2, 1)): "T",
    ((0, 1), (0, 2), (1, 0), (1, 1)): "S", ((0, 0), (1, 0), (1, 1), (2, 1)): "S",
    ((0, 0), (0, 1), (1, 1), (1, 2)): "S", ((0, 1), (1, 0), (1, 1), (2, 0)): "S"
}

_pieces = ("L", "I", "T", "S")
_id = 0
_regions = dict()

def create_gif(fps=2):
    frames = []
    filenames = sorted(Path("nuruomino_graphs/current").iterdir())  # Ensure correct order

    for path in filenames:
        name = str(path)
        if name.endswith(".png"):
            frames.append(imageio.v2.imread(name))

    imageio.mimsave("nuruomino_graphs/current/solution.gif", frames, fps=fps, loop=0)

def draw_board(board):
    """Draws a vizualization of a state of a nuruomino board."""
    N = board.size
    fig, ax = plt.subplots(figsize=(N/2, N/2))
    ax.set_facecolor('white')
    fig.patch.set_facecolor('white')

    # Define fixed colors for pieces
    piece_colors = {
        'L': '#ADD8EA',   # blue
        'T': '#CBC3EA',   # purple
        'I': '#ffea00',   # yellow
        'S': '#90EE90',   # green
    }

    # Draw each cell
    for r in range(N):
        for c in range(N):
            val = board.get_value(r, c)
            color = piece_colors.get(val, '#ffffff')

            #if isinstance(val, str) and val not in _pieces:
            #    color = "#ff0000"

            #if len(board.regions[board.initial[r][c]]) == 0 and val not in _pieces:
            #    color = "#808080"

            #if board.initial[r][c] in (6, 7) and val not in _pieces:
            #    color = "#ff0000"

            rect = plt.Rectangle(
                (c, N - 1 - r), 1, 1,
                facecolor=color,
                edgecolor='#000000',  # light grey cell border
                linewidth=0.5
            )
            ax.add_patch(rect)

    # Draw black borders around each region
    for r in range(N):
        for c in range(N):
            current = board.initial[r][c]
            # Check neighbors: if neighbor has a different region ID, draw a line
            if r > 0 and board.initial[r-1][c] != current:
                ax.plot([c, c+1], [N-r, N-r], color='black', linewidth=3)
            if r < N-1 and board.initial[r+1][c] != current:
                ax.plot([c, c+1], [N-1-r, N-1-r], color='black', linewidth=3)
            if c > 0 and board.initial[r][c-1] != current:
                ax.plot([c, c], [N-1-r, N-r], color='black', linewidth=3)
            if c < N-1 and board.initial[r][c+1] != current:
                ax.plot([c+1, c+1], [N-1-r, N-r], color='black', linewidth=3)

    ax.add_patch(plt.Rectangle(
        (0, 0), N, N,
        fill=False,
        edgecolor='black',
        linewidth=7
    ))

    ax.set_xlim(0, N)
    ax.set_ylim(0, N)
    ax.set_aspect('equal')
    ax.axis('off')
    plt.savefig(f"nuruomino_graphs/current/board{_id:03d}.png", bbox_inches='tight')


class NuruominoState:
    state_id = 0

    def __init__(self, board):
        self.board = board
        self.id = NuruominoState.state_id
        NuruominoState.state_id += 1

    def __lt__(self, other):
        """This method is used in case of a tie when managing the frontier of an informed search algorithm."""
        return self.id < other.id


class Board:
    """Internal representation of a Nuruomino board."""

    def __init__(self, configuration: dict, regions: dict):
        self.size = len(configuration)
        self.configuration = configuration
        self.regions = regions
        self.valid = True

    def set_initial(self):
        """Places the only placeable piece into regions with 4 cells and returns the board."""
        self.initial = {r: v.copy() for r, v in self.configuration.items()}
        self.open_cells_counter = {r: len(self.regions[r]) for r in self.regions}
        self.last_placed = None
        self.closed_regions = {r: [] for r in self.regions}
        self.region_restriction = dict()
        self.adj_regions = dict()
        self.islands = []

        for region in self.regions:
            adj_regions = set()

            for row, col in self.regions[region]:
                for adj_region in self.adjacent_values(row, col):
                    if adj_region != region:
                        adj_regions.add(adj_region)

            self.adj_regions[region] = list(adj_regions)

        global _id
        draw_board(self)
        _id += 1

        self.place_initial()
        self.placeables = dict()

        for region in self.regions:
            if self.regions[region]:
                self.compute_placeable_shapes(region)

        return self

    def place_initial(self):
        """Places pieces into all regions with 4 cells in the initial board."""
        for region, region_coords in self.regions.items():
            if len(region_coords) == 4:
                print(region)
                min_row, min_col = region_coords[0][0], min([col for row, col in region_coords])
                normalized_region = tuple((row - min_row, col - min_col) for row, col in region_coords)
                piece = _piece_to_str[normalized_region]

                for row, col in region_coords:
                    self.configuration[row][col] = piece

                for row, col in region_coords:
                    self.check_2x2(row, col)

                self.closed_regions[region] = region_coords
                self.open_cells_counter[region] = 0
                self.isolated_island(region)
                self.regions[region] = []
                self.last_placed = region

                global _id
                draw_board(self)
                _id += 1

    def get_value(self, row: int, col: int):
        """Returns the value from a cell."""
        return self.configuration[row][col]

    def get_num_open_cells(self):
        """Returns the number of open cells in the current board."""
        return sum(self.open_cells_counter[r] for r in self.regions)

    def get_num_islands(self):
        """Returns the number of islands in the current board."""
        return len(self.islands)

    def get_next_region(self):
        """Returns the next regions to place a piece and updates the list containing the following regions.
        If there's no region to return, returns None"""
        next_region = min(self.placeables, key=lambda region: len(self.placeables[region]), default=None)
        return next_region

    def close(self, row: int, col: int) -> bool:
        """Closes a cell for any piece placements.
        When cloasing a cell, if any invalid region is found, returns False, True otherwise."""
        region = self.get_value(row, col)

        if not isinstance(region, str):
            self.configuration[row][col] = str(self.configuration[row][col])
            self.regions[region].remove((row, col))
            self.open_cells_counter[region] -= 1

            open_regions = [region for region in self.regions if self.regions[region]]

            if any(self.open_cells_counter[r] + len(self.closed_regions[r]) < 4 for r in open_regions):
                self.valid = False
                return False
        return True

    def adjacent_positions(self, row: int, col: int) -> list:
        """Returns a list containing all the orthogonally adjacent positions of the given position."""
        positions = [(-1, 0), (0, -1), (0, 1), (1, 0)]

        return [(row + x, col + y) for x, y in positions
                if 0 <= row + x < self.size and 0 <= col + y < self.size]

    def adjacent_values(self, row: int, col: int) -> list:
        """Returns a list containing all the adjacent cell values of the given position."""
        return [self.get_value(adj_row, adj_col) for adj_row, adj_col in self.adjacent_positions(row, col)]

    def isolated_island(self, region: int) -> bool:
        """Returns True if the given region is isolated from the other regions, False otherwise.
        Stores the region in an island, if connected to another, or turns itself into one."""
        if len(self.closed_regions[region]) < 4 or len(self.regions[region]) == 0:
            return False

        region_piece = self.get_value(self.closed_regions[region][0][0], self.closed_regions[region][0][1])

        if region_piece not in _pieces:
            return False

        check_pieces = list(_pieces)
        check_pieces.remove(region_piece)

        isolated = True
        not_closed = set()
        connected_regions = set()
        connected_indices = set()
        for row, col in self.closed_regions[region]:
            for adj_row, adj_col in self.adjacent_positions(row, col):
                adj_region = self.initial[adj_row][adj_col]

                if adj_region == region:
                    continue

                if self.get_value(adj_row, adj_col) in check_pieces:
                    isolated = False
                    connected_regions.add(adj_region)

                    for ind, island in enumerate(self.islands):
                        if region in island:
                            return False

                        if adj_region in island:
                            if ind in connected_indices:
                                break

                            connected_indices.add(ind)
                elif len(self.regions[adj_region]) > 0:
                    connected_regions.add(adj_region)
                    not_closed.add(adj_region)
                    isolated = False

        if isolated:
            self.valid = False
            return True

        for adj_r in self.adj_regions[region]:
            if adj_r not in connected_regions:
                self.adj_regions[adj_r].remove(region)

        if len(not_closed) == 1 and len(connected_regions) == 1:
            rest = next(iter(not_closed))
            self.region_restriction.setdefault(rest, set()).add(region)

        if connected_indices:
            connected_indices_sorted = sorted(list(connected_indices), reverse=True)
            fixed = connected_indices_sorted.pop()
            for ind in connected_indices_sorted:
                self.islands[fixed].update(self.islands[ind])
                self.islands.pop(ind)

            self.islands[fixed].add(region)
        else:
            self.islands.append({region, })

        self.adj_regions[region] = list(connected_regions)
        return False

    def check_all_isolated_islands(self):
        """Returns True if any current island is isolated, False otherwise."""
        visited = [False for _ in range(len(self.regions))]

        frontier = []

        for r in self.regions:
            if not self.regions[r]:
                frontier.append(r)
                break

        while frontier:
            curr = frontier.pop(0)
            visited[curr - 1] = True
            frontier.extend([region for region in self.adj_regions[curr] if not visited[region - 1]])

        if not all(visited):
            return True
        return False

    def check_2x2(self, row: int, col: int) -> bool:
        """Returns True if the given cell is part of a 2x2 square formed by pieces or
        whenever the current board is invalidated during the execution of this function, False otherwise.
        If a quasi square (a square where only 1 cell is missing a piece) is found, closes the remaining open cell.
        If a square is found, invalidates the current board."""
        for x in range(-1, 1):
            for y in range(-1, 1):
                r, c = row + x, col + y

                if 0 <= r < self.size - 1 and 0 <= c < self.size - 1:
                    square_coords = [(r, c), (r, c + 1), (r + 1, c), (r + 1, c + 1)]
                    square_values = [self.get_value(sr, sc) for sr, sc in square_coords]

                    if all(val in _pieces for val in square_values):
                        self.valid = False
                        return True
                    else:
                        open_cells = [square_coords[i] for i, val in enumerate(square_values)
                                      if not isinstance(val, str) or val not in _pieces]

                        if len(open_cells) == 1:  # a quasi square
                            if not self.close(open_cells[0][0], open_cells[0][1]):  # invalidated by invalid regions
                                return True

        return False

    def placeable_shape(self, piece: str, shape: tuple, cell: tuple, region: int) -> bool:
        """Returns True if the given piece shape is placeable in the given cell."""
        row, col = cell
        start = 0

        if shape[0][0] in (-1, 0):
            start -= 1

            if len(shape) > 1 and shape[1][0] in (-1, 0):
                start -= 1

        check_rest = set()
        coords = []
        encounter = False
        for i in range(len(shape)):
            for j in range(len(shape[0])):
                r, c = row + i + start, col + j

                if 0 <= r < self.size and 0 <= c < self.size:
                    curr_val = self.get_value(r, c)

                    if shape[i][j] == 1:

                        if curr_val != region or any(val == piece for val in self.adjacent_values(r, c)):
                            return False

                        coords.append((r, c))

                        for adj_row, adj_col in self.adjacent_positions(r, c):
                            if self.initial[adj_row][adj_col] != region:
                                encounter = True

                            if region in self.region_restriction:
                                if self.initial[adj_row][adj_col] in self.region_restriction[region]:
                                    check_rest.add(self.initial[adj_row][adj_col])
                    elif shape[i][j] == -1:
                        if curr_val in _pieces:
                            return False
                else:
                    return False

        if not encounter:
            return False

        if region in self.region_restriction and len(check_rest) != len(self.region_restriction[region]):
            return False

        return True

    def compute_placeable_shapes(self, region):
        """Searches for all placeable piece shapes for each coordinate of the given region."""
        piece_restriction = []
        self.closed_regions[region] = self.closed_regions[region].copy()
        if region in self.region_restriction:
            for r in self.region_restriction[region]:
                piece_restriction.append(self.get_value(self.closed_regions[r][0][0], self.closed_regions[r][0][1]))

        for piece, shapes in _str_to_piece.items():
            if piece_restriction and piece in piece_restriction:
                continue

            for shape in shapes:
                for region_coord in self.regions[region]:
                    if self.placeable_shape(piece, shape, region_coord, region):
                        self.placeables.setdefault(region, []).append((piece, shape, region_coord))

        if region in self.region_restriction:
            del self.region_restriction[region]

    def update_placeables(self, region):
        """Updates the placeables of the given region.
        Invalidates the current board if there are no placeables of an open region."""
        if not self.regions[region]:
            return

        self.placeables[region] = self.placeables[region].copy()
        updated_placebles = []

        for placeable in self.placeables[region]:
            piece, shape, region_coord = placeable
            if self.placeable_shape(piece, shape, region_coord, region):
                updated_placebles.append(placeable)

        if region in self.region_restriction:
            del self.region_restriction[region]

        if not updated_placebles:
            self.valid = False

        self.placeables[region] = updated_placebles

    def place_piece(self, piece: str, shape: tuple, cell: tuple):
        """Places the piece with given shape into the region, with cell as the anchor.
        Returns the result as an instance of a Board."""
        region = self.initial[cell[0]][cell[1]]
        closed_region = []
        new_configuration = {r: cells.copy() for r, cells in self.configuration.items()}
        new_regions = dict()

        for i in self.regions:
            if i == region:
                for row, col in self.regions[i]:
                    new_configuration[row][col] = str(self.configuration[row][col])

            new_regions[i] = self.regions[i].copy()

        start = 0

        if shape[0][0] in (-1, 0):
            start -= 1
            if len(shape) > 1 and shape[1][0] in (-1, 0):
                start -= 1

        for i in range(len(shape)):
            for j in range(len(shape[0])):
                r, c = cell[0] + i + start, cell[1] + j
                if shape[i][j] == 1:
                    if self.get_value(r, c) == region:
                        new_configuration[r][c] = piece
                        closed_region.append((r, c))
                    else:
                        new_board = Board(new_configuration, new_regions)
                        new_board.open_cells_counter = self.open_cells_counter
                        new_board.islands = self.islands
                        new_board.valid = False
                        return new_board

        new_board = Board(new_configuration, new_regions)
        new_board.region_restriction = {r: rest.copy() for r, rest in self.region_restriction.items()}
        new_board.adj_regions = {r: adj.copy() for r, adj in self.adj_regions.items()}
        new_board.initial = self.initial
        new_board.open_cells_counter = {r: self.open_cells_counter[r] for r in self.regions}
        new_board.open_cells_counter[region] += len(self.closed_regions[region]) - len(self.regions[region])
        new_closed_regions = dict()
        new_closed_regions[region] = closed_region
        new_board.closed_regions = new_closed_regions
        new_board.islands = [i.copy() for i in self.islands]

        for r in self.closed_regions:
            if r == region:
                continue

            new_closed_regions[r] = self.closed_regions[r]

        if new_board.isolated_island(region):
            new_board.valid = False
            return new_board

        new_board.regions[region] = []

        if new_board.check_all_isolated_islands():
            new_board.valid = False
            return new_board

        for row, col in closed_region:
            if new_board.check_2x2(row, col):
                new_board.valid = False
                return new_board

        new_board.placeables = {r: placeable for r, placeable in self.placeables.items() if r != region}

        for adj_region in new_board.adj_regions[region]:
            new_board.update_placeables(adj_region)
        return new_board

    @staticmethod
    def parse_instance():
        """Reads from the standard input (stdin) and returns an object of the class Board."""
        configuration = dict()
        regions = dict()

        for line, content in enumerate(stdin):
            col = 0
            configuration[line] = list(map(int, content.split()))

            for region in configuration[line]:
                regions.setdefault(region, []).append((line, col))
                col += 1

        return Board(configuration, regions).set_initial()

    def __str__(self):
        out = ""

        for row in range(self.size):
            for col in range(self.size):
                if col != self.size - 1:
                    out += f"{self.get_value(row, col)}\t"
                else:
                    out += f"{self.get_value(row, col)}\n"

        return out[:-1]


class Nuruomino(Problem):
    def __init__(self, board: Board):
        """The constructor specifies the initial state."""
        super().__init__(NuruominoState(board))

    def actions(self, state: NuruominoState):
        """Returns a list containing all the actions that can be executed from the given state."""
        if not state.board.valid:
            return []

        region = state.board.get_next_region()
        if region is None:
            return []

        placeables = state.board.placeables[region]
        if not placeables:
            return []

        return placeables

    def result(self, state: NuruominoState, action):
        """Returns the state resulting from executing a 'action' on the given 'state'.
        The action to be executed must be one of those present in the list given by executing self.actions(state)."""
        piece, shape, cell = action
        s = NuruominoState(state.board.place_piece(piece, shape, cell))

        """global _id
        draw_board(s.board)
        _id += 1"""
        return s

    def goal_test(self, state: NuruominoState):
        """Returns True if and only if the given state is a goal state.
        It must verify if all positions on the board are filled according to the problem's rules."""
        return (state.board.valid and
                state.board.get_next_region() is None)

    def h(self, node: Node):
        """Heuristic function used for A* search."""
        return (node.state.board.get_num_open_cells() / 4) + 3*(node.state.board.get_num_islands() - 1)

if __name__ == "__main__":
    create_gif(3)
    exit()
    for file in Path("nuruomino_graphs/current").iterdir():
        if file.is_file():
            file.unlink()

    b = Board.parse_instance()
    problem = Nuruomino(b)
    """s0 = NuruominoState(b)
    s1 = problem.result(s0, ("T", ((0, 1, 0), (1, 1, 1)), (2, 0)))
    s2 = problem.result(s1, ("L", ((1, 1, 1), (1, 0, 0)), (0, 0)))
    print(s2.board)"""

    """draw_board(b)"""
    goal_node = depth_first_tree_search(problem)
    """print(goal_node.state.board, end="")"""
    """draw_board(goal_node.state.board)"""

    for i in range(1, len(goal_node.path())):
        node = goal_node.path()[i]
        draw_board(node.state.board)
        _id += 1

    """draw_board(goal_node.state.board)
    _id+=1"""
