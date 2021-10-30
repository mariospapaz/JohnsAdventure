from copy import copy
import pygame as pg
from .backend import UI_Spritesheet
from .PLAYER.player import Player
from .PLAYER.inventory import *
from .AI.enemies import Dummy
from .sound_manager import SoundManager
from .AI import npc
from .UI.mainmenu import Menu
from .UI.interface import Interface
from .UI.loading_screen import LoadingScreen
from .UI.pause_menu import PauseMenu
from .utils import resource_path, l_path

from .levels import (
    PlayerRoom,
    Kitchen
)

def main(debug=False):
    GameManager(debug=debug).update()


class GameManager:

    """

    Game class -> handles everything of the game.

    """
    pg.init()

    # FONTS

    pg.mixer.pre_init(44100, 32, 2, 4096) # Frequency, 32 Bit sound, channels, buffer
    pg.display.set_caption("iBoxStudio Engine Pre Alpha 0.23")
    pg.mouse.set_visible(False)
    # CONSTS
   
    DISPLAY = pg.display.set_mode((1280, 720), flags= pg.SRCALPHA | pg.SCALED | pg.DOUBLEBUF) # Add no frame for linux wayland 
    pg.display.set_icon(l_path("data/ui/logo.png"))
    W, H = DISPLAY.get_size()
    
    FPS = 35


    def __init__(self, debug=False):

        # ------------- SPRITESHEET ---------------
        self.ui = UI_Spritesheet("data/ui/UI_spritesheet.png")

        # ------------ FRAMERATE ------------------
        self.framerate = pg.time.Clock()
        self.dt = self.framerate.tick(self.FPS) / 1000

        # ----------- GAME STATE VARIABLES --------
        self.menu = True
        self.loading = False

        # 
        self.font = pg.font.Font(resource_path("data/database/pixelfont.ttf"), 24)
        self.blacksword = pg.font.Font(resource_path("data/database/Blacksword.otf"), 113)

        # ---------- GAME MANAGERS ----------------
        self.sound_manager = SoundManager()
        self.loading_screen = LoadingScreen(self.DISPLAY)
        self.menu_manager = Menu(self.DISPLAY, self.blacksword, self.ui)
        self.interface = Interface(self.DISPLAY, self.ui, self.font, self.dt)
        self.pause_menu = PauseMenu(self.DISPLAY, self.ui)

        # ------------- PLAYER ----------------
        self.player = Player(
        self.DISPLAY, # Screen surface
        self.font, # Font
        self.interface,
        self.ui, # Other UI like Inventory
        self.menu_manager.save, # controls
        )

        # ----------- GAME STATE ------------------
        self.state = "player_room"
        self.state_manager = {
            "player_room": PlayerRoom(self.DISPLAY, self.player),
            "kitchen": Kitchen(self.DISPLAY, self.player)
        }

        # ------------ DEBUG ----------------------
        self.debug = debug
        self.debugger = Debugging(self.DISPLAY, self)

    def pause(self):
        if self.player.paused:
            self.pause_menu.init_pause()
            while True:
                upd = self.pause_menu.update()

                if upd == "quit":
                    self.pause_menu.quit_pause()
                    self.loading = True
                    self.loading_screen.start("menu", duration=1000, text=True, cat=True, key_end=False)
                    self.player.paused = False
                    self.menu_manager.start_game = False
                    break
                elif upd == "resume":
                    self.pause_menu.quit_pause()
                    self.player.paused = False
                    break

                pg.display.update()

    def routine(self):

        """Method called every frame of the game.
        (Created to simplify the game loop)"""

        self.dt = self.framerate.tick(self.FPS) / 1000

        if not self.menu and not self.loading:  # if the game is playing
            self.player.update(self.dt)
            self.pause()

        if self.debug:
            self.debugger.update()

        pg.display.update()

    def update(self):

        while True:

            if self.menu:  # menu playing

                self.menu_manager.update(pg.mouse.get_pos())

                if self.menu_manager.start_game:  # start the game
                    self.menu = False
                    self.loading = True
                    self.loading_screen.start("player_room", duration=2500, main_loading=True, cat=True, text=False, key_end=True)

            elif self.loading:  # update the loading screen

                update_return = self.loading_screen.update()
                if update_return is not None:
                    print(update_return["next_state"])
                    if update_return["next_state"] != "menu":
                        self.state = update_return["next_state"]
                        self.loading = False
                        if update_return["next_music"] is not None:
                            self.sound_manager.play_music(update_return["next_music"])
                    else:
                        self.menu = True
                        self.loading = False

            else:
                self.DISPLAY.fill((0, 0, 0))
                update = self.state_manager[self.state].update(self.player.camera, self.dt)
                if update is not None:  # if a change of state is detected
                    self.loading = True  # start a loading screen (update="next_state_name")
                    self.loading_screen.start(update, text=True, duration=750, key_end=False)
                    if self.state in self.state_manager[update].spawn:
                        self.player.rect.topleft = self.state_manager[update].spawn[self.state]

            self.routine()


class Debugging:

    def __init__(self, display, game_instance):

        self.screen = display
        self.game = game_instance
        self.player = self.game.player

        self.colors = {
            "interaction_rect": (255, 255, 0),
            "collision_rect": (0, 255, 0),
            "attacking_rect": (255, 0, 0),
            "exit_rect": (255, 255, 0)
        }

        self.font = pg.font.Font("data/database/pixelfont.ttf", 15)

    def draw_text(self, txt, color, pos, bottomleft=False):
        text = self.font.render(txt, True, color)
        rect = text.get_rect(topleft=pos)
        if bottomleft:
            rect.bottomleft=pos
        self.screen.blit(text, rect)

    def update(self):

        """Primitive debugging system showing rects.
        
        TODO: Improve it to show stats. And make it more readable."""
        
        if not self.game.menu and not self.game.loading:
            scroll = self.player.camera.offset.xy
            objects = copy(self.game.state_manager[self.game.state].objects)
            objects.append(self.player)

            for obj in objects:
                if type(obj) is pg.Rect:
                    pg.draw.rect(self.screen, self.colors["collision_rect"], pg.Rect(obj.topleft-self.player.camera.offset.xy, obj.size), 2)
                else:
                    for key, color in self.colors.items():
                        if hasattr(obj, key):
                            attr = (getattr(obj, key))
                            if type(attr) is pg.Rect:
                                pg.draw.rect(self.screen, color, attr, 1)

                    col_rect = copy(obj.rect)
                    if hasattr(obj, "IDENTITY"):
                        if obj.IDENTITY in ["NPC", "PROP"]:
                            col_rect.topleft -= scroll
                        pg.draw.rect(self.screen, self.colors["collision_rect"], col_rect, 2)

            exit_rects = self.game.state_manager[self.game.state].exit_rects
            for exit_rect in exit_rects:
                r = copy(exit_rects[exit_rect])
                r.topleft -= scroll
                pg.draw.rect(self.screen, self.colors["exit_rect"], r, 2)
                self.draw_text(str('To:'+exit_rect), self.colors["exit_rect"], r.topleft, bottomleft=True)

            pl_col_rect = copy(self.player.rect)
            pl_col_rect.topleft -= scroll
            pl_col_rect.topleft -= pg.Vector2(15, -70)
            pl_col_rect.w -= 70
            pl_col_rect.h -= 115
            pg.draw.rect(self.screen,self.colors["collision_rect"], pl_col_rect, 1)