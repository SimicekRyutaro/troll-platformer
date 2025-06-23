"""
File with the level editor
"""
import sys
import pygame
from scripts.tilemap import Tilemap
from scripts.utils import load_images

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 800
RENDER_SCALE = 2.0
LOAD_MAP_LOCATION = "4.json"
SAVE_MAP_LOCATION = "4.json"

class Editor:
    """The main class of the level editor"""
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Level Editor")
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.display = pygame.Surface((int(SCREEN_WIDTH // RENDER_SCALE), int(SCREEN_HEIGHT // RENDER_SCALE)))
        self.clock = pygame.time.Clock()

        self.assets = {
            "textures": {
                "grass": load_images("tiles/grass/"),
                "stone": load_images("tiles/stone/"),
                "spawners": load_images("tiles/spawners/"),
                "goal": load_images("tiles/goal/"),
                "spikes": load_images("tiles/spikes/"),
            },
            "sfx": {

            },
        }

        self.tilemap = Tilemap(self, tile_size=16)
        try:
            self.tilemap.load(LOAD_MAP_LOCATION)
        except FileNotFoundError:
            print(f"File {LOAD_MAP_LOCATION} not found, starting with an empty map")
        except IsADirectoryError:
            print("You provided a directory, starting with an empty map")

        self.tile_selection = {
            "list": list(self.assets["textures"]),
            "group": 0,
            "variant": 0
        }

        self.input_state = {
            "clicking": False,
            "right_clicking": False,
            "shift": False,
            "ongrid": True
        }


    def handle_quit(self, event):
        """Exits the level editor after pressing ESC or closing window"""
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            pygame.quit()
            sys.exit()

    def handle_mbdown(self, event, mpos):
        """Handles pressing mouse buttons"""
        if event.button == 1:
            self.input_state["clicking"] = True
            if not self.input_state["ongrid"]:
                self.tilemap.offgrid_tiles.append({"type": self.tile_selection["list"][self.tile_selection["group"]], "variant": self.tile_selection["variant"], "pos": mpos})
        if event.button == 3:
            self.input_state["right_clicking"] = True

    def handle_mscroll(self, event):
        """Changes tiles while scrolling"""
        if self.input_state["shift"]:
            self.tile_selection["variant"] = 0
            if event.button == 4:
                self.tile_selection["group"] = (self.tile_selection["group"] - 1) % len(self.tile_selection["list"])
            if event.button == 5:
                self.tile_selection["group"] = (self.tile_selection["group"] + 1) % len(self.tile_selection["list"])
        else:
            if event.button == 4:
                self.tile_selection["variant"] = (self.tile_selection["variant"] - 1) % len(self.assets["textures"][self.tile_selection["list"][self.tile_selection["group"]]])
            if event.button == 5:
                self.tile_selection["variant"] = (self.tile_selection["variant"] + 1) % len(self.assets["textures"][self.tile_selection["list"][self.tile_selection["group"]]])

    def handle_mbup(self, event):
        """Handles releasing the mouse buttons"""
        if event.button == 1:
            self.input_state["clicking"] = False
        if event.button == 3:
            self.input_state["right_clicking"] = False

    def handle_key_down(self, event):
        """Handles key presses"""
        if event.key == pygame.K_LSHIFT:
            self.input_state["shift"] = True
        if event.key == pygame.K_LCTRL:
            self.input_state["ongrid"] = not self.input_state["ongrid"]
        if event.key == pygame.K_o:
            self.tilemap.save(SAVE_MAP_LOCATION)
        if event.key == pygame.K_t:
            self.tilemap.autotile()

    def handle_key_up(self, event):
        """Handles releasing key presses"""
        if event.key == pygame.K_LSHIFT:
            self.input_state["shift"] = False

    def process_events(self, mpos):
        """Processes all keyboard and mouse events"""
        for event in pygame.event.get():
            self.handle_quit(event)

            if event.type == pygame.MOUSEBUTTONDOWN:
                self.handle_mbdown(event, mpos)
                self.handle_mscroll(event)

            if event.type == pygame.MOUSEBUTTONUP:
                self.handle_mbup(event)

            if event.type == pygame.KEYDOWN:
                self.handle_key_down(event)

            if event.type == pygame.KEYUP:
                self.handle_key_up(event)

    def run(self):
        """Runs the level editor, the main loop is here"""
        while True:
            self.display.fill((162, 242, 252))
            self.tilemap.render(self.display)

            current_tile_img = self.assets["textures"][self.tile_selection["list"][self.tile_selection["group"]]][self.tile_selection["variant"]].copy()
            current_tile_img.set_alpha(100)

            mpos = pygame.mouse.get_pos()
            mpos = (mpos[0] // RENDER_SCALE, mpos[1] // RENDER_SCALE)
            tile_pos = (int(mpos[0] // self.tilemap.tile_size), int(mpos[1] // self.tilemap.tile_size))

            if self.input_state["ongrid"]:
                self.display.blit(current_tile_img, (tile_pos[0] * self.tilemap.tile_size, tile_pos[1] * self.tilemap.tile_size))
            else:
                self.display.blit(current_tile_img, mpos)

            self.display.blit(current_tile_img, (5, 5))

            if self.input_state["clicking"] and self.input_state["ongrid"]:
                self.tilemap.tilemap[str(tile_pos[0]) + ";" + str(tile_pos[1])] = {"type": self.tile_selection["list"][self.tile_selection["group"]], "variant": self.tile_selection["variant"], "pos": tile_pos}
            if self.input_state["right_clicking"]:
                tile_loc = str(tile_pos[0]) + ";" + str(tile_pos[1])
                self.tilemap.tilemap.pop(tile_loc, None)
                for tile in self.tilemap.offgrid_tiles.copy():
                    tile_img = self.assets["textures"][tile["type"]][tile["variant"]]
                    tile_r = pygame.Rect(tile["pos"][0], tile["pos"][1], tile_img.get_width(), tile_img.get_height())
                    if tile_r.collidepoint(mpos):
                        self.tilemap.offgrid_tiles.remove(tile)

            self.process_events(mpos)

            self.screen.blit(pygame.transform.scale(self.display, self.screen.get_size()), (0, 0))
            pygame.display.update()
            self.clock.tick(60)

Editor().run()
