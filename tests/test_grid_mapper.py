"""Headless tests for the tilemap/grid contract."""
import unittest
from types import SimpleNamespace

from game.grid_mapper import GridMapper


class GridMapperRegressionTests(unittest.TestCase):
    def test_empty_map_can_be_rebuilt_after_a_populated_map(self):
        mapper = GridMapper()
        first = SimpleNamespace(
            nodes={1: SimpleNamespace(x=0, y=0)},
            neighbors=lambda node_id: [],
        )
        mapper.rebuild(first)
        self.assertEqual(mapper.node_at(0, 0), 1)

        mapper.rebuild(SimpleNamespace(nodes={}))
        self.assertEqual((mapper.cols, mapper.rows), (0, 0))
        self.assertEqual(mapper.grid, [])
        self.assertIsNone(mapper.node_at(0, 0))
        self.assertFalse(mapper.can_step(0, 0, 1, 0))

    def test_invalid_tile_size_is_rejected(self):
        with self.assertRaises(ValueError):
            GridMapper(tile_size=0)
        with self.assertRaises(ValueError):
            GridMapper(tile_size=-8)

    def test_corridor_requires_bidirectional_adjacency(self):
        mapper = GridMapper()
        graph = SimpleNamespace(
            nodes={1: SimpleNamespace(x=0, y=0), 2: SimpleNamespace(x=128, y=0)},
            neighbors=lambda node_id: [2] if node_id == 1 else [1],
        )
        mapper.rebuild(graph)
        self.assertTrue(mapper.can_step(0, 0, 1, 0))
        self.assertTrue(mapper.can_step(1, 0, 0, 0))
        self.assertFalse(mapper.can_step(0, 0, 2, 0))


if __name__ == "__main__":
    unittest.main()
