"""
The main file of the game with Game class
"""
import sys
import json
from dataclasses import dataclass, field
import pygame
from scripts.entities import Player
from scripts.tilemap import Tilemap
from scripts.utils import load_images, Animation
from scripts.clouds import Clouds
from scripts.traps import Traps, Spike, Block

DISAPPEARING_BLOCKS = [
    ("grass", 9), ("grass", 10), ("grass", 11), ("grass", 12), ("grass", 13), ("grass", 14), ("grass", 15), ("grass", 16), ("grass", 17),
    ("stone", 9), ("stone", 10), ("stone", 11), ("stone", 12), ("stone", 13), ("stone", 14), ("stone", 15), ("stone", 16), ("stone", 17),
]

MAX_LEVEL = 4

SCREEN_WIDTH = 960
SCREEN_HEIGHT = 800
RENDER_SCALE = 2.0

@dataclass
class DisplaySettings:
    """Dataclass storing display related variables of the game"""
    screen: pygame.Surface
    display: pygame.Surface
    clock: pygame.time.Clock
    transition: int = -30

@dataclass
class GameComponents:
    """Dataclass storing the components of the game"""
    player: Player
    tilemap: Tilemap
    clouds: Clouds
    traps: Traps

@dataclass
class LevelInfo:
    """Dataclass storing information about levels"""
    level: int = 0
    level_up: bool = False
    time: int = 0
    deaths: int = 0
    start_game: bool = False
    restart_game: bool = False
    current_slot: int = 2
    data: dict = field(default_factory=lambda: {
        "slot1": {"level": 0, "time": 0, "deaths": 0},
        "slot2": {"level": 0, "time": 0, "deaths": 0},
        "slot3": {"level": 0, "time": 0, "deaths": 0},
        "best": {"time": None, "deaths": None},
        "last": {"time": None, "deaths": None},
    })

class Game:
    """The main class of the game"""
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Troll Platformer")

        self.display_settings = DisplaySettings(
            screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT)),
            display = pygame.Surface((int(SCREEN_WIDTH // RENDER_SCALE), int(SCREEN_HEIGHT // RENDER_SCALE))),
            clock = pygame.time.Clock()
        )
        self.assets = {
            "textures": {
                "grass": load_images("tiles/grass/"),
                "stone": load_images("tiles/stone/"),
                "clouds": load_images("clouds/"),
                "goal": load_images("tiles/goal/"),
                "spikes": load_images("tiles/spikes/"),
            },
            "animations": {
                "player/idle": Animation(load_images("entities/player/idle/"), img_dur=30),
                "player/walk": Animation(load_images("entities/player/walk/"), img_dur=8),
                "player/jump": Animation(load_images("entities/player/jump/"), img_dur=5),
                "player/death": Animation(load_images("entities/player/death/"), img_dur=5),
            },
            "sfx": {
                "jump": pygame.mixer.Sound("data/sfx/jump.wav"),
                "select": pygame.mixer.Sound("data/sfx/select.wav"),
                "start_level": pygame.mixer.Sound("data/sfx/start.wav"),
                "death": pygame.mixer.Sound("data/sfx/death.wav"),
            },
            "fonts": {
                "small": pygame.font.Font("data/fonts/ThaleahFat.ttf", 16),
                "medium": pygame.font.Font("data/fonts/ThaleahFat.ttf", 32),
                "large": pygame.font.Font("data/fonts/ThaleahFat.ttf", 48),
            }
        }
        self.assets["sfx"]["jump"].set_volume(0.6)
        self.assets["sfx"]["select"].set_volume(0.6)
        self.assets["sfx"]["start_level"].set_volume(0.4)
        self.assets["sfx"]["death"].set_volume(0.6)
        self.components = GameComponents(
            player = Player(self, (0, 0), (13, 16)),
            tilemap = Tilemap(self, tile_size=16),
            clouds = Clouds(self.assets["textures"]["clouds"], self.display_settings.display.get_width(), self.display_settings.display.get_height()),
            traps = Traps(self, [], [])
        )
        self.level_info = LevelInfo()
        self.movement = [False, False]
        self.current_state = "main_menu"
        try:
            self.load_game()
        except FileNotFoundError:
            pass

    def save_game(self):
        """Saves game to data/saves/save.json"""
        with open("data/saves/save.json", "wt", encoding="utf-8") as f:
            json.dump(self.level_info.data, f)

    def load_game(self):
        """Loads game from data/saves/save.json"""
        with open("data/saves/save.json", "rt", encoding="utf-8") as f:
            data = json.load(f)
        self.level_info.data = data

    def load_level(self, level_id):
        """Loads level number level_id"""
        self.components.player = Player(self, (0, 0), (13, 16))
        self.components.tilemap.load(str(level_id) + ".json")

        for spawner in self.components.tilemap.extract([("spawners", 0), ("spawners", 1)], keep=False):
            if spawner["variant"] in {0, 1}:
                self.components.player.transform.pos = spawner["pos"]
                if spawner["variant"] == 1:
                    self.components.player.transform.flip = True

        self.components.traps.spikes = []
        for moving_spike in self.components.tilemap.extract([("spikes", 4), ("spikes", 5), ("spikes", 6), ("spikes", 7)], keep=False):
            self.components.traps.spikes.append(Spike(moving_spike["pos"], moving_spike["variant"] % 4, self, tile_size=self.components.tilemap.tile_size))

        self.components.traps.blocks = []
        for disappearing_block in self.components.tilemap.extract(DISAPPEARING_BLOCKS, keep=False):
            self.components.traps.blocks.append(Block(disappearing_block["pos"], (disappearing_block["type"], disappearing_block["variant"] % 9), self, tile_size=self.components.tilemap.tile_size))

        self.level_info.level_up = False
        self.display_settings.transition = -30

    def draw_text(self, surf, string, pos, size="medium", color=(255, 255, 255)):
        """Draws text on surface surf at position pos."""
        text_surface = self.assets["fonts"][size].render(string, False, color)
        text_surface_outline = self.assets["fonts"][size].render(string, False, (0, 0, 0))
        for shift in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
            surf.blit(text_surface_outline, (pos[0] + shift[0], pos[1] + shift[1]))
        surf.blit(text_surface, pos)

    def handle_gameplay_input(self):
        """Handles pressed keys while in the gameplay state."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_a:
                    self.movement[0] = True
                if event.key == pygame.K_d:
                    self.movement[1] = True
                if (event.key in {pygame.K_w, pygame.K_SPACE}) and (not self.display_settings.transition) and (not self.components.player.dead):
                    self.components.player.jump()
                if event.key == pygame.K_r and (not self.display_settings.transition) and (not self.components.player.dead):
                    self.assets["sfx"]["death"].play()
                    self.components.player.dead = 10
            if event.type == pygame.KEYUP:
                if event.key == pygame.K_a:
                    self.movement[0] = False
                if event.key == pygame.K_d:
                    self.movement[1] = False
        return True

    def update_level_up_transition(self):
        """Updates transition while leveling up or finishing last level"""
        self.display_settings.transition += 1
        if self.display_settings.transition > 30:
            self.level_info.level = self.level_info.level + 1
            if self.level_info.level > MAX_LEVEL:
                self.current_state = "end_screen"
                self.display_settings.transition = -30
                self.level_info.level_up = False
                self.level_info.data["last"] = {"time": self.level_info.time, "deaths": self.level_info.deaths}
                if (self.level_info.data["best"]["time"] is None) or (self.level_info.data["best"]["time"] > self.level_info.time):
                    self.level_info.data["best"] = {"time": self.level_info.time, "deaths": self.level_info.deaths}
                self.level_info.data["slot" + str(self.level_info.current_slot)] = {"level": 0, "time": 0, "deaths": 0}
            else:
                self.load_level(self.level_info.level)

    def update_level_restart_transition(self):
        """Updates transition while restarting level"""
        self.components.player.dead += 1
        if self.components.player.dead >= 10:
            self.display_settings.transition += 1
        if self.display_settings.transition > 30:
            self.level_info.deaths += 1
            self.load_level(self.level_info.level)

    def update_game_start_transition(self):
        """Updates transition while starting the game"""
        self.display_settings.transition += 1
        if self.display_settings.transition > 30:
            self.level_info.start_game = False
            self.current_state = "gameplay"
            self.level_info.time = self.level_info.data["slot" + str(self.level_info.current_slot)]["time"]
            self.level_info.deaths = self.level_info.data["slot" + str(self.level_info.current_slot)]["deaths"]
            self.level_info.level = self.level_info.data["slot" + str(self.level_info.current_slot)]["level"]
            self.load_level(self.level_info.level)

    def update_game_restart_transition(self):
        """Updates transition while restarting the game from end screen"""
        self.display_settings.transition += 1
        if self.display_settings.transition > 30:
            self.level_info.restart_game = False
            self.current_state = "main_menu"
            self.display_settings.transition = -30

    def update_transition(self):
        """Updates transition"""
        # Loading level
        if self.display_settings.transition < 0:
            self.display_settings.transition += 1

        # Level up + last level finish
        if self.level_info.level_up:
            self.update_level_up_transition()

        # Level restart
        if self.components.player.dead:
            self.update_level_restart_transition()

        # Start game
        if self.level_info.start_game:
            self.update_game_start_transition()

        # Restart game from end screen
        if self.level_info.restart_game:
            self.update_game_restart_transition()

    def draw_transition(self, surf):
        """Draws the transition circle"""
        transition_surf = pygame.Surface(surf.get_size())
        pygame.draw.circle(
            transition_surf,
            (255, 255, 255),
            (surf.get_width() // 2, surf.get_height() // 2),
            (30 - abs(self.display_settings.transition)) * 12
        )
        transition_surf.set_colorkey((255, 255, 255))
        surf.blit(transition_surf, (0, 0))

    def draw_gameplay(self):
        """Draws the gameplay screen"""
        self.display_settings.display.fill((162, 242, 252))

        self.components.clouds.update()
        self.components.clouds.render(self.display_settings.display)

        self.components.tilemap.render(self.display_settings.display)

        if (not self.display_settings.transition) and (not self.components.player.dead):
            self.components.traps.update(self.components.player.transform.pos, self.components.player.transform.size)
        self.components.traps.render(self.display_settings.display)

        if (not self.display_settings.transition) and (not self.components.player.dead):
            self.components.player.update(self.components.tilemap, (self.movement[1] - self.movement[0], 0), self.components.traps)
        self.components.player.render(self.display_settings.display)

        seconds = self.level_info.time // 60
        minutes = seconds // 60
        seconds = seconds % 60
        self.draw_text(self.display_settings.display, f"time: {minutes:02}:{seconds:02}", (5, 5), size="small")
        self.draw_text(self.display_settings.display, f"deaths: {self.level_info.deaths}", (5, 21), size="small")
        self.draw_text(self.display_settings.display, "restart - r", (self.display_settings.display.get_width() - 90, 5), size="small")

        if self.display_settings.transition:
            self.draw_transition(self.display_settings.display)

        self.display_settings.screen.blit(pygame.transform.scale(self.display_settings.display, self.display_settings.screen.get_size()), (0, 0))

    def handle_menu_input(self):
        """Handles pressed keys while in the main menu state"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False
            if event.type == pygame.KEYDOWN and (not self.level_info.start_game):
                if event.key == pygame.K_SPACE:
                    self.assets["sfx"]["start_level"].play()
                    self.level_info.start_game = True
                if event.key == pygame.K_a:
                    old_slot = self.level_info.current_slot
                    self.level_info.current_slot = max(self.level_info.current_slot - 1, 1)
                    if self.level_info.current_slot != old_slot:
                        self.assets["sfx"]["select"].play()
                if event.key == pygame.K_d:
                    old_slot = self.level_info.current_slot
                    self.level_info.current_slot = min(self.level_info.current_slot + 1, 3)
                    if self.level_info.current_slot != old_slot:
                        self.assets["sfx"]["select"].play()
                if event.key == pygame.K_DELETE:
                    self.level_info = LevelInfo()
                if event.key == pygame.K_p:
                    self.level_info.data["slot" + str(self.level_info.current_slot)] = {"level": 0, "time": 0, "deaths": 0}
        return True

    def draw_menu_slot(self, slot, x_positions):
        """Draws save slot information on the main menu"""
        white_color = (255, 255, 255)
        yellow_color = (245, 221, 100)
        seconds = self.level_info.data["slot" + str(slot)]["time"] // 60
        minutes = f"{seconds // 60:02}"
        seconds = f"{seconds % 60:02}"
        deaths = f"{self.level_info.data['slot' + str(slot)]['deaths']}"
        level = self.level_info.data["slot" + str(slot)]["level"] + 1
        color = yellow_color if self.level_info.current_slot == slot else white_color
        self.draw_text(self.display_settings.display, f"Slot {slot}", (x_positions[0], 111), size="large", color=color)
        self.draw_text(self.display_settings.display, f"Level: {level}", (x_positions[1], 148), size="medium", color=color)
        self.draw_text(self.display_settings.display, f"Time: {minutes}:{seconds}", (x_positions[2], 178), size="medium", color=color)
        self.draw_text(self.display_settings.display, f"Deaths: {deaths}", (x_positions[3], 208), size="medium", color=color)

    def draw_menu(self):
        """Draws main menu"""
        self.display_settings.display.fill((162, 242, 252))

        if self.level_info.data["best"]["time"] is not None:
            seconds = self.level_info.data["best"]["time"] // 60
            minutes = f"{seconds // 60:02}"
            seconds = f"{seconds % 60:02}"
            deaths = f"{self.level_info.data['best']['deaths']}"
        else:
            seconds = "XX"
            minutes = "XX"
            deaths = "XX"
        self.draw_text(self.display_settings.display, f"Best time: {minutes}:{seconds}", (27, 33), size="small")
        self.draw_text(self.display_settings.display, f"Deaths: {deaths}", (27, 49), size="small")

        if self.level_info.data["last"]["time"] is not None:
            seconds = self.level_info.data["last"]["time"] // 60
            minutes = f"{seconds // 60:02}"
            seconds = f"{seconds % 60:02}"
            deaths = f"{self.level_info.data['last']['deaths']}"
        else:
            seconds = "XX"
            minutes = "XX"
            deaths = "XX"
        self.draw_text(self.display_settings.display, f"Last time: {minutes}:{seconds}", (347, 33), size="small")
        self.draw_text(self.display_settings.display, f"Deaths: {deaths}", (347, 49), size="small")

        self.draw_menu_slot(1, (19, 26, 9, 16))
        self.draw_menu_slot(2, (174, 186, 169, 176))
        self.draw_menu_slot(3, (334, 346, 329, 336))

        self.draw_text(self.display_settings.display, "< A   D >", (191, 253), size="medium")

        self.draw_text(self.display_settings.display, "Move - WASD     Restart level - R", (14, 298), size="medium")

        self.draw_text(self.display_settings.display, "Reset slot - P     Reset all - DEL", (10, 328), size="medium")

        self.draw_text(self.display_settings.display, "Space to start", (85, 354), size="large")

        if self.display_settings.transition:
            self.draw_transition(self.display_settings.display)

        self.display_settings.screen.blit(pygame.transform.scale(self.display_settings.display, self.display_settings.screen.get_size()), (0, 0))

    def handle_end_screen_input(self):
        """Handles pressed keys while in the end screen state"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.level_info.restart_game = True
        return True

    def draw_end_screen(self):
        """Draws end screen"""
        self.display_settings.display.fill((162, 242, 252))

        self.draw_text(self.display_settings.display, "You won!", (156, 134), size="large")

        seconds = self.level_info.time // 60
        minutes = seconds // 60
        seconds = seconds % 60
        self.draw_text(self.display_settings.display, f"Time: {minutes:02}:{seconds:02}", (138, 178), size="large", color=(245, 221, 100))

        self.draw_text(self.display_settings.display, f"Deaths: {self.level_info.deaths}", (144, 222), size="large", color=(245, 221, 100))

        self.draw_text(self.display_settings.display, "Space - main menu", (121, 290), size="medium")

        self.draw_text(self.display_settings.display, "ESC - exit", (175, 320), size="medium")

        if self.display_settings.transition:
            self.draw_transition(self.display_settings.display)

        self.display_settings.screen.blit(pygame.transform.scale(self.display_settings.display, self.display_settings.screen.get_size()), (0, 0))

    def run(self):
        """Runs the game, the game loop is here"""
        pygame.mixer.music.load("data/music.ogg")
        pygame.mixer.music.set_volume(0.2)
        pygame.mixer.music.play(-1)

        running = True
        while running:
            self.update_transition()
            if self.current_state == "main_menu":
                running = self.handle_menu_input()
                self.draw_menu()
            elif self.current_state == "gameplay":
                running = self.handle_gameplay_input()
                self.draw_gameplay()
                self.level_info.time += 1
            elif self.current_state == "end_screen":
                running = self.handle_end_screen_input()
                self.draw_end_screen()

            pygame.display.flip()
            self.display_settings.clock.tick(60)

        if self.current_state == "gameplay":
            self.level_info.data["slot" + str(self.level_info.current_slot)]["level"] = self.level_info.level
            self.level_info.data["slot" + str(self.level_info.current_slot)]["time"] = self.level_info.time
            self.level_info.data["slot" + str(self.level_info.current_slot)]["deaths"] = self.level_info.deaths

        self.save_game()

        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
