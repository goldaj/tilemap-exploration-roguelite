"""World chunk seams must not change when the player explores in another order."""
import copy
import unittest

from game.infinite_grid import InfiniteGrid


class InfiniteWorldDeterminismTests(unittest.TestCase):
    def test_generation_order_does_not_change_chunks(self):
        coords = [(-1, 0), (0, 0), (1, 0), (0, 1), (-1, 1), (0, -1)]
        def generate(order):
            world = InfiniteGrid(world_seed=991)
            for x, y in order:
                world.get_cell(x * world.chunk_size + 5, y * world.chunk_size + 5)
            return {key: copy.deepcopy(chunk.cells) for key, chunk in world.chunks.items()}
        self.assertEqual(generate(coords), generate(list(reversed(coords))))

    def test_all_neighbors_share_bidirectional_portals(self):
        grid = InfiniteGrid(world_seed=321)
        grid.get_cell(0, 0)
        grid.get_cell(24, 0)
        grid.get_cell(0, -24)
        middle = grid.chunks[(0, 0)]
        right = grid.chunks[(1, 0)]
        above = grid.chunks[(0, -1)]
        for y in range(grid.chunk_size):
            a, b = middle.cells[y][-1], right.cells[y][0]
            self.assertEqual(bool(a and a['E']), bool(b and b['W']))
        for x in range(grid.chunk_size):
            a, b = above.cells[-1][x], middle.cells[0][x]
            self.assertEqual(bool(a and a['S']), bool(b and b['N']))

    def test_small_invalid_chunks_rejected(self):
        with self.assertRaises(ValueError):
            InfiniteGrid(chunk_size=5)


if __name__ == "__main__":
    unittest.main()
