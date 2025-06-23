"""
File with entity classes - PhysicsEntity, Player
"""
from dataclasses import dataclass, field
import pygame
from scripts.traps import Traps

@dataclass
class Transform:
    """Dataclass storing position and movement related variables"""
    pos: list[float | int]
    size: tuple[int, int]
    velocity: list[float | int] = field(default_factory=lambda: [0, 0])
    flip: bool = False

@dataclass
class CollisionState:
    """Dataclass storing if collision occurred"""
    up: bool = False
    down: bool = False
    right: bool = False
    left: bool = False

@dataclass
class AnimationState:
    """Dataclass storing the animation state"""
    action: str = None
    animation = None

class PhysicsEntity:
    """Base class for entities with physics"""
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.transform = Transform(pos=list(pos), size=size)
        self.collision = CollisionState()
        self.anim = AnimationState()
        self.dead = 0
        self.set_action("idle")

    def set_action(self, action):
        """Sets the animation based on action"""
        if action != self.anim.action:
            self.anim.action = action
            self.anim.animation = self.game.assets["animations"][self.type + "/" + action].copy()

    def rect(self):
        """Returns the rectangle of the entity"""
        return pygame.Rect(self.transform.pos[0], self.transform.pos[1], self.transform.size[0], self.transform.size[1])

    def clip_horizontal_pos(self):
        """Disables leaving the screen from the left and right side"""
        if self.transform.pos[0] < 0:
            self.transform.pos[0] = 0
        if self.transform.pos[0] + self.transform.size[0] > self.game.display_settings.display.get_width():
            self.transform.pos[0] = self.game.display_settings.display.get_width() - self.transform.size[0]

    def update_horizontal_pos(self, frame_movement, tilemap):
        """Ensures the movement to the left and right"""
        self.transform.pos[0] += frame_movement[0] * 1.6
        self.clip_horizontal_pos()

        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.transform.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collision.right = True
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collision.left = True
                self.transform.pos[0] = entity_rect.x

    def update_vertical_pos(self, frame_movement, tilemap):
        """Ensures the movement up and down"""
        self.transform.pos[1] += frame_movement[1]

        if self.transform.pos[1] > self.game.display_settings.display.get_height():
            self.dead = 1

        entity_rect = self.rect()
        for rect in tilemap.physics_rects_around(self.transform.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collision.down = True
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collision.up = True
                self.transform.pos[1] = entity_rect.y

    def update_flip(self, movement):
        """Updates flip (direction the entity is facing) based on movement"""
        if movement[0] > 0:
            self.transform.flip = False
        elif movement[0] < 0:
            self.transform.flip = True

    def update_physics(self):
        """Updates up/down velocity"""
        self.transform.velocity[1] = min(5, self.transform.velocity[1] + 0.2)
        if self.collision.down or self.collision.up:
            self.transform.velocity[1] = 0

    def update(self, tilemap, movement=(0, 0)):
        """Updates the position of the entity"""
        self.collision = CollisionState(up=False, down=False, right=False, left=False)

        frame_movement = (movement[0] + self.transform.velocity[0], movement[1] + self.transform.velocity[1])

        self.update_horizontal_pos(frame_movement, tilemap)
        self.update_vertical_pos(frame_movement, tilemap)
        self.update_flip(movement)
        self.update_physics()
        self.anim.animation.update()

    def render(self, surf):
        """Renders entity image on surf"""
        surf.blit(pygame.transform.flip(self.anim.animation.img(), self.transform.flip, False), self.transform.pos)

class Player(PhysicsEntity):
    """Class for the player entity"""
    def __init__(self, game, pos, size):
        super().__init__(game, "player", pos, size)
        self.air_time = 0
        self.jumps = 2

    def check_goal_collision(self, tilemap):
        """Checks if player reached goal"""
        player_tile = (int((self.transform.pos[0] + self.transform.size[0] // 2) // tilemap.tile_size), int((self.transform.pos[1] + self.transform.size[1] // 2) // tilemap.tile_size))
        player_tile_str = str(player_tile[0]) + ";" + str(player_tile[1])
        if player_tile_str in tilemap.tilemap and tilemap.tilemap[player_tile_str]["type"] == "goal":
            goal = tilemap.tilemap[player_tile_str]
            goal_pos = (int(goal["pos"][0] * tilemap.tile_size + tilemap.tile_size // 2), int(goal["pos"][1] * tilemap.tile_size + tilemap.tile_size // 2))
            if self.rect().collidepoint(goal_pos):
                self.game.assets["sfx"]["start_level"].play()
                self.game.level_info.level_up = True

    def check_static_spike_collision(self, tilemap):
        """Checks if player ran into a static spike"""
        entity_rect = self.rect()
        entity_mask = pygame.mask.from_surface(self.anim.animation.img())
        for variant, rect in tilemap.spikes_rects_around(self.transform.pos):
            if not entity_rect.colliderect(rect):
                continue
            spike_mask = pygame.mask.from_surface(self.game.assets["textures"]["spikes"][variant])
            if entity_mask.overlap(spike_mask, (rect.x - self.transform.pos[0], rect.y - self.transform.pos[1])):
                self.dead = 1

    def check_dynamic_spike_collision(self, traps):
        """Checks if player ran into a moving spike"""
        entity_rect = self.rect()
        entity_mask = pygame.mask.from_surface(self.anim.animation.img())
        for spike in traps.spikes:
            if not spike.dashing:
                continue
            spike_rect = spike.rect()
            if not entity_rect.colliderect(spike_rect):
                continue
            spike_mask = spike.mask()
            if entity_mask.overlap(spike_mask, (spike_rect.x - self.transform.pos[0], spike_rect.y - self.transform.pos[1])):
                self.dead = 1

    def update_air_state(self):
        """Updates air time, resets jumps if standing on the ground"""
        self.air_time += 1
        if self.collision.down:
            self.air_time = 0
            self.jumps = 2

    def update_animation(self, movement):
        """Changes animation based on state (jump, walk, idle)"""
        if self.air_time > 4:
            self.set_action("jump")
        elif movement[0] != 0:
            self.set_action("walk")
        else:
            self.set_action("idle")

    def update(self, tilemap, movement=(0, 0), traps=Traps(None, [], [])):
        """Updates player position and animation, checks goal and spike collision"""
        super().update(tilemap, movement=movement)
        self.check_goal_collision(tilemap)
        self.check_static_spike_collision(tilemap)
        self.check_dynamic_spike_collision(traps)
        if self.dead:
            self.game.assets["sfx"]["death"].play()
        self.update_air_state()
        self.update_animation(movement)

    def jump(self):
        """Jumps if has jumps left"""
        if self.jumps:
            self.game.assets["sfx"]["jump"].play()
            self.transform.velocity[1] = -4
            self.jumps -= 1
            self.air_time = 5
