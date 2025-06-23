"""
File with the Tilemap class
"""
import json
import pygame

AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 7,
    tuple(sorted([(-1, 0), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, -1), (0, -1), (1, -1), (-1, 0), (0, 0), (1, 0), (-1, 1), (0, 1), (1, 1)]
PHYSICS_TILES = {"grass", "stone"}
AUTOTILE_TILES = {"grass", "stone"}
BASE_TILEMAP_PATH = "data/maps/"

class Tilemap:
    """Class used for storing and rendering the level maps"""
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []

    def extract(self, id_pairs, keep=False):
        """Returns all tiles with corresponding id_pairs"""
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile["type"], tile["variant"]) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
        for loc, tile in self.tilemap.copy().items():
            if (tile["type"], tile["variant"]) in id_pairs:
                matches.append(tile.copy())
                matches[-1]["pos"] = matches[-1]["pos"].copy()
                matches[-1]["pos"][0] *= self.tile_size
                matches[-1]["pos"][1] *= self.tile_size
                if not keep:
                    self.tilemap.pop(loc, None)
        return matches

    def tiles_around(self, pos):
        """Returns the 9 tiles around pos"""
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ";" + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles

    def physics_rects_around(self, pos):
        """Returns the rects of physics tiles around pos"""
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile["pos"][0] * self.tile_size, tile["pos"][1] * self.tile_size, self.tile_size, self.tile_size))
        return rects

    def spikes_rects_around(self, pos):
        """Returns the rects of spike tiles around pos"""
        rects = []
        for tile in self.tiles_around(pos):
            if tile["type"] == "spikes":
                rects.append((tile["variant"], pygame.Rect(tile["pos"][0] * self.tile_size, tile["pos"][1] * self.tile_size, self.tile_size, self.tile_size)))
        return rects

    def autotile(self):
        """Changes tile variant based on tiles around it"""
        for tile in self.tilemap.values():
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile["pos"][0] + shift[0]) + ";" + str(tile["pos"][1] + shift[1])
                if check_loc not in self.tilemap:
                    continue
                if self.tilemap[check_loc]["type"] == tile["type"]:
                    neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile["type"] in AUTOTILE_TILES) and (neighbors in AUTOTILE_MAP):
                tile["variant"] = AUTOTILE_MAP[neighbors]

    def save(self, path):
        """Saves the tilemap to directory path"""
        with open(BASE_TILEMAP_PATH + path, "wt", encoding="utf-8") as f:
            json.dump({"tilemap": self.tilemap, "tile_size": self.tile_size, "offgrid": self.offgrid_tiles}, f)

    def load(self, path):
        """Loads the tilemap from directory path"""
        with open(BASE_TILEMAP_PATH + path, "rt", encoding="utf-8") as f:
            map_data = json.load(f)
        self.tilemap = map_data["tilemap"]
        self.tile_size = map_data["tile_size"]
        self.offgrid_tiles = map_data["offgrid"]

    def render(self, surf):
        """Renders the tilemap on surf"""
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets["textures"][tile["type"]][tile["variant"]], tile["pos"])

        for tile in self.tilemap.values():
            surf.blit(self.game.assets["textures"][tile["type"]][tile["variant"]], (tile["pos"][0] * self.tile_size, tile["pos"][1] * self.tile_size))
