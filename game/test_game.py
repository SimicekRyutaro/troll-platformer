"""
File with tests
"""
import json
import pytest
import pygame
from scripts.entities import Player
from scripts.tilemap import Tilemap
from scripts.clouds import Cloud, Clouds
from scripts.traps import Spike, Block, Traps
from game import Game

@pytest.fixture
def game():
    """Fixture that provides a game instance"""
    game_fixture = Game()
    yield game_fixture
    pygame.quit()

def test_game_initialization(game):
    """Test if game initializes with correct default values"""
    assert game.current_state == "main_menu"
    assert game.movement == [False, False]
    assert game.level_info.level == 0
    assert game.level_info.deaths == 0
    assert isinstance(game.components.player, Player)
    assert isinstance(game.components.tilemap, Tilemap)
    assert isinstance(game.components.clouds, Clouds)
    assert isinstance(game.components.traps, Traps)

def test_player_physics(game):
    """Test player physics behavior"""
    player = game.components.player

    # Test gravity
    player.update(game.components.tilemap)
    assert player.transform.velocity[1] > 0  # Should fall due to gravity

    # Test jump
    player.jumps = 2  # Reset jumps
    player.jump()
    assert player.transform.velocity[1] < 0  # Should move upward
    assert player.jumps == 1  # Should use one jump

def test_collision_detection(game):
    """Test basic collision detection"""
    player = game.components.player
    tilemap = game.components.tilemap

    # Create a floor tile
    floor_pos = (0, player.transform.pos[1] + player.transform.size[1])
    tile_key = f"{floor_pos[0]//16};{floor_pos[1]//16}"
    tilemap.tilemap[tile_key] = {
        "type": "grass",
        "variant": 0,
        "pos": [floor_pos[0]//16, floor_pos[1]//16]
    }

    # Test floor collision
    player.jumps = 0
    for _ in range(60):
        player.update(tilemap)
    assert player.collision.down  # Should detect floor collision
    assert player.jumps == 2  # Should reset jumps when on floor

def test_cloud_movement():
    """Test cloud movement behavior"""
    cloud = Cloud((100, 100), pygame.Surface((32, 32)), 0.5)
    initial_x = cloud.pos[0]

    cloud.update()
    assert cloud.pos[0] > initial_x  # Cloud should move right
    assert cloud.pos[1] == 100  # Y position should remain unchanged

def test_spike_activation(game):
    """Test spike activation behavior"""
    spike = Spike([100, 100], 0, game)  # Upward facing spike
    player_pos = [100, 50]  # Player above spike
    player_size = (13, 16)

    # Test spike activation
    spike.update(player_pos, player_size)
    assert spike.dashing  # Spike should activate when player is in range

def test_disappearing_block(game):
    """Test disappearing block behavior"""
    block = Block([100, 100], ("grass", 0), game)
    player_pos = [90, 90]  # Player near block
    player_size = (13, 16)

    # Test block disappearance
    should_disappear = block.update(player_pos, player_size)
    assert should_disappear  # Block should disappear when player is close

def test_save_load_game(game, tmp_path):
    """Test game save/load functionality"""
    # Setup test data
    game.level_info.level = 1
    game.level_info.data["slot1"]["level"] = 1

    # Save game
    test_save_path = tmp_path / "test_save.json"
    with open(test_save_path, "wt", encoding="utf-8") as f:
        json.dump(game.level_info.data, f)

    # Modify data
    game.level_info.level = 0
    game.level_info.data["slot1"]["level"] = 0

    # Load game
    with open(test_save_path, "rt", encoding="utf-8") as f:
        game.level_info.data = json.load(f)

    # Verify data
    assert game.level_info.level == 0
    assert game.level_info.data["slot1"]["level"] == 1
    assert isinstance(game.level_info.data["slot1"]["deaths"], int)

def test_level_loading(game):
    """Test level loading functionality"""
    game.load_level(1)
    assert not game.level_info.level_up
    assert game.display_settings.transition == -30
    assert isinstance(game.components.player, Player)
    assert len(game.components.tilemap.tilemap) > 0

def test_animation_state(game):
    """Test player animation states"""
    player = game.components.player

    # Test idle animation
    player.set_action("idle")
    assert player.anim.action == "idle"
    assert player.anim.animation is not None

    # Test walk animation
    player.set_action("walk")
    assert player.anim.action == "walk"
    assert player.anim.animation is not None

def test_transition_system(game):
    """Test game transition system"""
    game.display_settings.transition = -30

    # Test transition increment
    game.update_transition()
    assert game.display_settings.transition == -29

    # Test level up transition
    game.level_info.level_up = True
    game.display_settings.transition = 29
    game.update_transition()
    assert game.display_settings.transition == 30
    assert game.level_info.level_up
    game.update_transition()
    assert game.display_settings.transition == -30
    assert not game.level_info.level_up
