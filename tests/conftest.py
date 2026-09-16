import os
import sys
from pathlib import Path
import pytest
import pygame

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "src"))
os.chdir(REPO_ROOT / "game")

@pytest.fixture(scope="session", autouse=True)
def pygame_setup():
    """
    Configura Pygame para ejecutarse en modo 'headless' (sin monitor).
    Esto es CRUCIAL para que GitHub Actions y JOSS acepten los tests.
    """
    # Usar el driver 'dummy' para no necesitar tarjeta gráfica
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    os.environ["SDL_AUDIODRIVER"] = "dummy"
    
    pygame.init()
    
    # Creamos una pantalla virtual pequeña para que las funciones de dibujo no fallen
    pygame.display.set_mode((800, 600))
    
    yield  # Aquí corren los tests
    
    pygame.quit()