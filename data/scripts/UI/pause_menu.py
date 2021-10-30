import pygame as pg
from ..utils import scale
from copy import copy


class PauseMenu:

    def __init__(self, display, ui):


        self.screen = display
        self.W, self.H = self.screen.get_size()

        self.font = pg.font.Font("data/database/pixelfont.ttf", 25)
        self.background = scale(ui.parse_sprite("catalog_button.png"), 5)

        self.buttons = [
            self.font.render("Resume", True, (0, 0, 0)),
            self.font.render("Settings", True, (0, 0, 0)),
            self.font.render("Save & Quit", True, (0, 0, 0)),
        ]
        self.btn_rects = [
            button.get_rect(center=(self.W//2, ((
                self.H//2-button.get_height()*(len(self.buttons)*2-1)//2)+i*2*button.get_height()+15
            ))) for i, button in enumerate(self.buttons)
        ]
        self.funcs = {
            0: self.resume,  # func that will be executed if button with index 0 is clicked
            1: self.settings,
            2: self.save_and_quit
        }

    def resume(self):
        print("resume")
        return "resume"
    
    def settings(self):
        print("settings")

    def save_and_quit(self):
        print("save & quit")
        return "quit"

    def handle_button_clicks(self, pos):
        for id_, rect in enumerate(self.btn_rects):
            if rect.collidepoint(pos):
                return self.funcs[id_]()

    def handle_events(self):

        for event in pg.event.get():
            match event.type:
                case pg.QUIT:
                    pg.quit()
                    raise SystemExit
                case pg.MOUSEBUTTONDOWN:
                    return self.handle_button_clicks(event.pos)

    def init_pause(self):
        pg.mouse.set_visible(True)
        surf = pg.Surface(self.screen.get_size())
        surf.fill((0, 0, 0))
        surf.set_alpha(200)
        self.screen.blit(surf, (0,0))

    def quit_pause(self):
        pg.mouse.set_visible(False)

    def update(self):

        events = self.handle_events()
        if events is not None:
            return events
        
        self.screen.blit(self.background, self.background.get_rect(center=(self.W//2, self.H//2)))
        for i in range(len(self.buttons)):
            if self.btn_rects[i].collidepoint(pg.mouse.get_pos()):
                r = copy(self.btn_rects[i])
                r = pg.Rect(0, 0, r.w*1.2, r.h*1.2)
                r.center=self.btn_rects[i].center
                pg.draw.rect(self.screen, (255, 255, 255), r, 2)
            self.screen.blit(self.buttons[i], self.btn_rects[i])

        