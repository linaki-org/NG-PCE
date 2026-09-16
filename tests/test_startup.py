import pygame
import pytest

import ng_pce.engine as engine
from ng_pce.classes.commons import TRANSITION_FADE
from ng_pce.scenes.variables import GameState


@pytest.fixture(scope="module")
def running_engine():
    engine.cfg.CONFIG["ENABLE_SOUND"] = False
    engine.init()
    engine.load_scripts("scripts")
    return engine


def count_visible_pixels(surface):
    width, height = surface.get_size()
    return sum(
        surface.get_at((x, y))[:3] != (0, 0, 0)
        for x in range(0, width, 8)
        for y in range(0, height, 8)
    )


def test_engine_starts_in_title_and_draws(running_engine):
    assert running_engine.CURRENT_STATE == GameState.TITLE
    assert running_engine.screen.get_size() == (
        running_engine.cfg.CONFIG["GAME_WIDTH"],
        running_engine.cfg.CONFIG["GAME_HEIGHT"],
    )

    running_engine.screen.fill((0, 0, 0))
    running_engine.title_menu.draw(running_engine.screen)

    assert count_visible_pixels(running_engine.screen) > 0


def test_startup_scripts_register_scenes_and_content(running_engine):
    assert {"peace_avenue", "town_hall", "panoramic"}.issubset(
        running_engine.scene_manager.scenes
    )

    peace_avenue = running_engine.scene_manager.scenes["peace_avenue"]
    assert len(peace_avenue.hotspot_data) == 2
    assert len(peace_avenue.exits) == 2


def test_scene_activation_and_rendering_at_different_steps(running_engine):
    scene = running_engine.scene_manager.change_scene("peace_avenue")
    running_engine.set_state(GameState.EXPLORE)

    assert scene is not None
    assert scene.walkable_area is not None
    assert scene.pathfinder is not None
    assert scene.parallax_layers

    for camera_x in (0, 120):
        scene.camera_x = camera_x
        running_engine.screen.fill((0, 0, 0))
        running_engine.draw_explore_mode(running_engine.screen)
        assert count_visible_pixels(running_engine.screen) > 0


def test_scene_transition_progresses_through_fade_steps(running_engine):
    running_engine.scene_manager.change_scene("peace_avenue")
    running_engine.scene_manager.change_scene_with_effect(
        "town_hall", (50, 400), forced_effect=TRANSITION_FADE
    )

    assert running_engine.scene_manager.transition_mode == "FADE_OUT"

    running_engine.scene_manager.update_transition(0.1)
    assert running_engine.scene_manager.transition_mode == "FADE_OUT"
    assert running_engine.scene_manager.progress == 60

    running_engine.scene_manager.update_transition(1.0)
    assert running_engine.scene_manager.current_scene.id == "town_hall"
    assert running_engine.scene_manager.transition_mode == "FADE_IN"

    running_engine.scene_manager.update_transition(1.0)
    assert running_engine.scene_manager.transition_mode == "IDLE"
    assert running_engine.scene_manager.progress == 0