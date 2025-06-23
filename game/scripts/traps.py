"""
File with the traps of the game - moving spikes, disappearing blocks
"""
import math
import pygame

class Spike:
    """Class representing a moving spike"""
    def __init__(self, pos, variant, game, tile_size=16):
        self.pos = pos
        self.variant = variant
        self.game = game
        self.tile_size = tile_size
        self.dashing = False
        self.speed = 7

    def update(self, player_pos, player_size):
        """Updates position if moving, starts movement if not moving and player is around"""
        if not self.dashing:
            player_center = (player_pos[0] + player_size[0] / 2, player_pos[1] + player_size[1] / 2)
            spike_center = (self.pos[0] + self.tile_size / 2, self.pos[1] + self.tile_size / 2)
            match self.variant:
                case 0: # up
                    if (abs(player_center[0] - spike_center[0]) < self.tile_size / 2 + player_size[0] / 2) and (-self.tile_size / 4 <= spike_center[1] - player_center[1] < 5 * self.tile_size):
                        self.dashing = True
                case 1: # right
                    if (abs(player_center[1] - spike_center[1]) < 3 * self.tile_size / 4 + player_size[1] / 2) and (-self.tile_size / 4 < player_center[0] - spike_center[0] < 5 * self.tile_size):
                        self.dashing = True
                case 2: # down
                    if (abs(player_center[0] - spike_center[0]) < self.tile_size / 2 + player_size[0] / 2) and (-self.tile_size / 4 < player_center[1] - spike_center[1] < 5 * self.tile_size):
                        self.dashing = True
                case 3: # left
                    if (abs(player_center[1] - spike_center[1]) < 3 * self.tile_size / 4 + player_size[1] / 2) and (-self.tile_size / 4 < spike_center[0] - player_center[0] < 5 * self.tile_size):
                        self.dashing = True
        else:
            match self.variant:
                case 0: # up
                    self.pos[1] -= self.speed
                case 1: # right
                    self.pos[0] += self.speed
                case 2: # down
                    self.pos[1] += self.speed
                case 3: # left
                    self.pos[0] -= self.speed

    def render(self, surf):
        """Renders spike on surf"""
        surf.blit(self.game.assets["textures"]["spikes"][self.variant], self.pos)

    def rect(self):
        """Returns the rectangle of the spike"""
        return pygame.Rect(self.pos[0], self.pos[1], self.tile_size, self.tile_size)

    def mask(self):
        """Returns the mask of the spike"""
        return pygame.mask.from_surface(self.game.assets["textures"]["spikes"][self.variant])

class Block:
    """Class representing a disappearing block"""
    def __init__(self, pos, info, game, tile_size=16):
        self.pos = pos
        self.type = info[0]
        self.variant = info[1]
        self.game = game
        self.tile_size = tile_size

    def update(self, player_pos, player_size):
        """Returns True if player is around so the block should disappear, returns False otherwise"""
        player_center = (player_pos[0] + player_size[0] / 2, player_pos[1] + player_size[1] / 2)
        block_center = (self.pos[0] + self.tile_size / 2, self.pos[1] + self.tile_size / 2)
        if math.sqrt((player_center[0] - block_center[0]) ** 2 + (player_center[1] - block_center[1]) ** 2) < self.tile_size * 1.2:
            return True
        return False

    def render(self, surf):
        """Renders block on surf"""
        surf.blit(self.game.assets["textures"][self.type][self.variant], self.pos)

class Traps:
    """Class representing all the moving spikes and disappearing blocks of the game"""
    def __init__(self, game, spikes, blocks):
        self.game = game
        self.spikes = spikes
        self.blocks = blocks

    def update(self, player_pos, player_size):
        """Updates all traps"""
        remove_indices = []
        for i, spike in enumerate(self.spikes):
            spike.update(player_pos, player_size)
            if (
                (spike.pos[0] < 0 - spike.tile_size)
                or (spike.pos[1] < 0 - spike.tile_size)
                or (spike.pos[0] > self.game.display_settings.display.get_width() + spike.tile_size)
                or (spike.pos[1] > self.game.display_settings.display.get_height() + spike.tile_size)
            ):
                remove_indices.append(i)
        for i in sorted(remove_indices, reverse=True):
            self.spikes.pop(i)

        remove_indices = []
        for i, block in enumerate(self.blocks):
            remove = block.update(player_pos, player_size)
            if remove:
                remove_indices.append(i)
        for i in sorted(remove_indices, reverse=True):
            self.blocks.pop(i)

    def render(self, surf):
        """Renders all traps on surf"""
        for spike in self.spikes:
            spike.render(surf)

        for block in self.blocks:
            block.render(surf)
