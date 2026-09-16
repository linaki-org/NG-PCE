from unittest.mock import MagicMock, patch

import pygame

from ng_pce.config import CONFIG, TEXT_CONFIG
from ng_pce.classes.resources import ResourceManager
from ng_pce.scenes.variables import GAME_STATE, GameState

def test_configuracion_basica():
    assert "GAME_WIDTH" in CONFIG
    assert isinstance(CONFIG["GAME_WIDTH"], int)
    assert CONFIG["GAME_WIDTH"] > 0
    assert "SPEED_MEDIUM" in TEXT_CONFIG

def test_game_state_inicial():
    assert GAME_STATE["campana_recogida"] is False
    assert GameState.EXPLORE == "EXPLORE"

@patch('os.path.exists')
@patch('pygame.image.load')
def test_resource_manager(mock_load, mock_exists):
    mock_exists.return_value = True
    
    fake_surface = MagicMock()
    mock_load.return_value = fake_surface
    
    manager = ResourceManager()
    
    img = manager.get_image("test_image.png", subfolder="assets")
    
    mock_load.assert_called()
    assert img is not None
    
    img2 = manager.get_image("test_image.png", subfolder="assets")
    assert mock_load.call_count == 1
    assert img is img2


def test_resource_manager_returns_none_for_missing_file():
    manager = ResourceManager()

    with patch("ng_pce.classes.resources.os.path.exists", return_value=False):
        assert manager.get_image("missing.png") is None

    assert manager.image_cache == {}


def test_resource_manager_returns_none_when_loader_fails():
    manager = ResourceManager()

    with (
        patch("ng_pce.classes.resources.os.path.exists", return_value=True),
        patch("ng_pce.classes.resources.pygame.image.load", side_effect=pygame.error("bad image")),
    ):
        assert manager.get_image("broken.png") is None

    assert manager.image_cache == {}


def test_resource_manager_clear_cache():
    manager = ResourceManager()
    manager.image_cache[("assets", "test.png")] = object()

    manager.clear_cache()

    assert manager.image_cache == {}

def test_calculo_fuentes():
    assert TEXT_CONFIG["SIZE_LARGE"] > TEXT_CONFIG["SIZE_SMALL"]