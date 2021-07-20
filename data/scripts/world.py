
import sys, random, json
import pygame as pg
from pygame import mixer
from pygame import mouse
from pygame.constants import KEYDOWN, MOUSEBUTTONDOWN
from .backend import *
from .player import *

pg.init(), pg.display.set_caption("iBoxStudio Engine")
DISPLAY = pg.display.set_mode((1280, 720))

#  Uncomment the below when you stop debugging
#DISPLAY = pg.display.set_mode((1280, 720), flags=pg.RESIZABLE | pg.SCALED)  # pg.NOFRAME for linux :penguin:
#pg.display.toggle_fullscreen()

if '--debug' in sys.argv:
    print("Oh you sussy you're trying to debug me huh?")
    debug = True
else:
    debug = False

# INITIALIZE
framerate = pygame.time.Clock()
UIspriteSheet = UI_Spritesheet('data/ui/UI_spritesheet.png')
get_screen_w, get_screen_h = DISPLAY.get_width(), DISPLAY.get_height()
mouse_icon = UIspriteSheet.parse_sprite('mouse_cursor.png').convert()  # Game's exclusive mouse icon!
scroll = [0, 0]  # player "camera"
dt = framerate.tick(35) / 1000 # Delta time :D
font = pg.font.Font("data/database/pixelfont.ttf", 24)
blacksword = pg.font.Font("data/database/Blacksword.otf", 113) # I use this only for the logo

class Interface(object): 
    def __init__(self):
        self.icon = scale(UIspriteSheet.parse_sprite('interface_button.png').convert(), 8)
        self.current_text_index = self.timer = 0
        self.text_pos = (get_screen_w // 2 - 420, get_screen_h // 2 + 110) # Position of the first sentence
        with open('data/database/language.json') as f: self.data = json.load(f); f.close() # Read Json and close it     
        self.sound = pg.mixer.Sound('data/sound/letter_sound.wav'); self.sound.set_volume(0.2) # Insert music and change sound     
        self.text_display = ['' for i in range(4)] # Create 4 empty text renders
        self.text_surfaces = [font.render(self.text_display[i], True, (0,0,0)) for i in range(4)] # font render each of them

    def reset(self): self.current_text_index  =  0  # Resets text
    
    def draw(self, path):
        if path: # If string is not empty
            DISPLAY.blit(self.icon, (155 , get_screen_h // 2 + 80)) # UI
            text = self.data[path]['text'] # Import from Json the AI/UI 's text
            self.timer += dt # Speed of text/delta_time
            if self.timer > 0.030:
                    self.current_text_index += 1 # Next letter
                    if self.current_text_index < len(text):
                        self.current_text_index += 1 
                        if not (text[self.current_text_index] == ' '):  self.sound.play()  # if there isn't space            
                    # --- UPDATE CONTENT ---
                    self.text_display = [text[44 * i : min(self.current_text_index, 44 * (i + 1))] for i in range(4)] # Update letters strings
                    self.text_surfaces = [font.render(text, True, (0,0,0)) for text in self.text_display]  # Transform them into a surface                        
                    self.timer = 0 # Reset timer /  End of if statement                 
            for i, surface in enumerate(self.text_surfaces): # Blits the text 
                DISPLAY.blit(surface, (self.text_pos[0], self.text_pos[1] + i * 30))          

# Classes
class MainMenu(object):
    def __init__(self):
        # ------------ Background and Animation  -------------
        self.background = pg.transform.scale(load('data/ui/background.png'), (1280,720))
        self.event = None # event for keys
        self.logo = [blacksword.render("John's Adventure", True, (255 * i, 255 * i,255 * i)) for i in range(2)]

        # ------------- Music Playlist -------------
        self.button_font = pg.font.Font("data/database/pixelfont.ttf", 28)
        self.music = [mixer.Sound("data/sound/forest_theme_part1.flac"), mixer.Sound("data/sound/Select_UI.wav")]
        for music in self.music:  music.set_volume(0.2)
        # --------- GUI ----------
        self.buttons = [[scale(UIspriteSheet.parse_sprite('button.png'), 4),scale(UIspriteSheet.parse_sprite('button_hover.png'), 4)] for i in range(3)]
        self.gui_text = [self.button_font.render("Play", True, (255,255,255)), self.button_font.render("Controls", True, (255,255,255)),self.button_font.render("Quit", True, (255,255,255))]
        
        # --------- DATA LOAD/SAVE -------
        self.save = self.get_data('data/database/data.json') # Get data from json
        self.settings_bg = scale(UIspriteSheet.parse_sprite('catalog_button.png'), 11)
        self.show_settings = self.changing = self.controls_error = self.blank_keys = False # blits gui, user clicks on a keybind button
        self.change_key_index = None # The index of the key we're changing
        self.keybinds = [scale(UIspriteSheet.parse_sprite("keybind.png"),5) for i in range(len(self.save["controls"]))]
        self.settings_text = [font.render('Up', True, (0,0,0)), font.render('Down',True, (0,0,0)),font.render('Left',True, (0,0,0)),font.render('Right',True, (0,0,0)),font.render('Interact',True, (0,0,0))]

    def get_data(self, path):
        with open(path, 'r') as f: return json.load(f)

    def save_data(self):
        with open('data/database/data.json', 'w+') as f: return json.dump(self.save, f)

    def draw_txt(self, txt, pos):
        render = font.render(txt, True, (0, 0, 0))
        rect = render.get_rect()
        rect.centerx = get_screen_w // 2 - 7
        rect.centery = pos.centery - 2
        return DISPLAY.blit(render, rect)

    def update(self, mouse_p):  
        DISPLAY.blit(self.background,(0,0)) # Background          
        ''' Settings '''
        if self.show_settings:
            DISPLAY.blit(self.settings_bg, self.settings_bg.get_rect(center=(get_screen_w//2, get_screen_h//2)))    
            if self.controls_error: DISPLAY.blit(font.render("Please put another key!", True, (0,0,0)), (get_screen_w //2 - 220, get_screen_h //2 - 200))
            elif self.blank_keys: DISPLAY.blit(font.render("Please fill the keys!", True, (0,0,0)), (get_screen_w //2 - 220, get_screen_h //2 - 200))

            #  Key Button    
            for i, key in enumerate(self.keybinds):
                rect = key.get_rect(center= pg.Vector2(get_screen_w //2,  get_screen_h //2 - 110 +  60 * i))
                DISPLAY.blit(key, rect), DISPLAY.blit(self.settings_text[i], (rect[0] - 180, rect[1] + 10))

                if rect.collidepoint(mouse_p) and self.event.type == MOUSEBUTTONDOWN and self.event.button == 1:  
                    self.changing = True
                    self.controls_error = False
                    self.save['controls'][i] = '' # User Feedback that he is changing 
                    self.change_key_index = i # Save index
                
                # Checking the lenth of the key  
                try:
                    bind = str(pg.key.name(self.save['controls'][i]))
                    kb = self.draw_txt(bind, rect) #if len(bind) >= 5 else  draw_txt (DISPLAY, bind, rect)
                except Exception as e:
                    print(e) 

        else:

            ''' Show again the buttons'''
            for i, text in enumerate(self.logo):  DISPLAY.blit(text, (get_screen_w//6+20, get_screen_h//2 - 190 - (2 * i)))

            ''' Buttons '''
            for i, button in enumerate(self.buttons):     
                rect = button[0].get_rect(topleft=((get_screen_w//2 - 115, get_screen_h//2 + 75 * (i + 1)))) # Rect of image in sublist              
                btn = DISPLAY.blit(button[1], rect) if rect.collidepoint(mouse_p) else DISPLAY.blit(button[0], rect)     
                txt = DISPLAY.blit(self.gui_text[i], (rect[0] + self.gui_text[0].get_width()//4, rect[1] + 5)) if i == 1 else  DISPLAY.blit(self.gui_text[i], (rect[0] + self.gui_text[0].get_width()//2 + 15, rect[1] + 5))

        ''' Controls '''
        for event in pg.event.get():
            self.event = event
            if event.type == pg.MOUSEBUTTONDOWN and self.buttons[1][0].get_rect(center=((get_screen_w//2, get_screen_h//2 + 150))).collidepoint(mouse_p):
                self.show_settings = True
            if event.type == pg.QUIT: pg.quit(), sys.exit()     
            if event.type == pg.KEYDOWN:
                if self.changing:
                    if event.key not in self.save['controls']: # Check for Unique keys
                        if event.key != pg.K_ESCAPE:
                            self.save['controls'][self.change_key_index] = event.key # Sets new key       
                            self.controls_error = self.changing = self.blank_keys = False # Change the button and close it       
                        else:
                            self.blank_keys = True
                    else:
                        self.controls_error = True                 

                if self.show_settings and event.key == pg.K_ESCAPE:
                    if '' in self.save['controls']: # If there are empty boxes
                        self.blank_keys = True
                    else: # Every box is filled
                        self.blank_keys = False
                        self.save_data() # Update Json File
                        self.show_settings = False
                    
                if event.key == pg.K_F12: pg.display.toggle_fullscreen()
class Game:
    def __init__(self):
        self.menu = MainMenu()
        self.Menu = True # If False , the adventure starts
        #------- World -----
        self.worlds = [
            pg.transform.scale(load('data/sprites/world/Johns_room.png'), (1280,720)), # 0 John's Room
            pg.transform.scale(load('data/sprites/world/kitchen.png'), (1280,720))  # 1 Kitchen Room
        ]
        self.world = self.worlds[0]  # Current world      
        self.PlayerRoom = self.Kitchen = self.Forest = False  # Worlds   
        self.Player = Player(get_screen_w // 2, get_screen_h // 2, DISPLAY, debug, Interface(), self.menu.save) # The player
            
        #------- Objects -----
        self.o_index = 0 # Index for the sublists below
        self.objects = [
            [Mau(150,530), pg.Rect(10,90, 430,360), pg.Rect(5,500, 72, 214), pg.Rect(450, 40, 410, 192)], # John's Room     
            [Cynthia(570, 220, load('data/sprites/npc_spritesheet.png')), pg.Rect(0,0, 250,350), pg.Rect(0,0, 64, 256), pg.Rect(0,0, 860, 230), pg.Rect(0,0, 256, 200)] # Kitchen Room
        ] 

        self.object_p = [
            [None, pg.Vector2(10,90), pg.Vector2(5,500), pg.Vector2(450, 40)], # John's Room     
            [None,pg.Vector2(20, 250), pg.Vector2(280,300), pg.Vector2(10,0), pg.Vector2(1020, 440)]       
        ] # pygame.Rect.x .y is stupid so im forced to use this bloated list
              
    # Αλγόριθμος Παγκόσμιας Σύγκρουσης Οντοτήτων / Player Collision System with Object&Entities
    def collision_system(self, index):
        for i, object in enumerate(self.objects[index]):
            collision = False # No collision
            try: # OBJECT
                object.topleft = (self.object_p[index][i].x - scroll[0], self.object_p[index][i].y - scroll[1])
                collision = self.Player.Rect.colliderect(object)
                top = abs(object.bottom - self.Player.Rect.top)
                bottom = abs(object.top - self.Player.Rect.bottom)
                left = abs(object.right - self.Player.Rect.left)
                right = abs(object.left - self.Player.Rect.right)
                if debug: pg.draw.rect(DISPLAY, (255,255,255), object, width = 1) 
            except: # NPC
                object.topleft = (object.x - scroll[0], object.y - scroll[1])
                collision = self.Player.Rect.colliderect(object.Rect)
                top = abs(object.Rect.bottom - self.Player.Rect.top)
                bottom = abs(object.Rect.top - self.Player.Rect.bottom)
                left = abs(object.Rect.right - self.Player.Rect.left)
                right = abs(object.Rect.left - self.Player.Rect.right)
                if self.Player.Rect.colliderect(object.interact_rect):
                   self.Player.is_interacting = True
                   self.Player.interact_text = object.interact_text

                if debug: pg.draw.rect(DISPLAY, (255,255,255), object.Rect, width = 1)   
                         
            # Collision happen
            if collision:                       
                if self.Player.Up or self.Player.Down:  # Up / Down borders
                    if top < 10:
                        self.Player.y = self.Player.y + self.Player.speedY
                    elif bottom < 10:
                        self.Player.y = self.Player.y - self.Player.speedY # Clunky             
                if self.Player.Left or self.Player.Right:  # Left / Right borders
                    if left < 10:
                        self.Player.x = self.Player.x + self.Player.speedX
                    elif right < 10:
                        self.Player.x = self.Player.x - self.Player.speedX # Clunky

    def pause(self, mouse):
        if self.Player.paused:
            surface = pygame.Surface((get_screen_w,get_screen_h), pygame.SRCALPHA)
            surface.fill((0,0,0)); surface.set_alpha(235); DISPLAY.blit(surface, (0,0)) # Draws black screen with opacity
            for character in self.Characters: character.speed = 0 # Stop characters frog
            # -----v TEMPORARY v-----
            DISPLAY.blit(font.render("(GAME UNDER CONSTRUCTION)", True, (255,255,255)), (get_screen_w//2 - 220, get_screen_h//2 - 140))
            DISPLAY.blit(blacksword.render("Paused", True, (255,255,255)), (get_screen_w//2 - 190, get_screen_h//2 - 120))
            DISPLAY.blit(font.render("PRESS ESQ TO UNPAUSE", True, (255,255,255)), (get_screen_w//2 - 190, get_screen_h//2 + 100))
            DISPLAY.blit(font.render("THINGS ARE GOING TO BE CHANGED IN THE FUTURE", True, (255,255,255)), (256, get_screen_h//2 + 140))
    
    # When in a room
    def room_borders(self, up = get_screen_h - get_screen_h, down = get_screen_h, left = get_screen_w - get_screen_w, right = get_screen_w):        
        if self.Player.y < up + 150: self.Player.y = up + 150      
        elif self.Player.y > down - 40: self.Player.y = down - 40     
        if self.Player.x < left + 40: self.Player.x = left + 40         
        elif self.Player.x > right - 40: self.Player.x = right - 40

    def update(self): 
        while True:
            dt, mouse_p = framerate.tick(35) / 1000, pg.mouse.get_pos() # Framerate Indepence and Mouse position
            DISPLAY.fill((0, 0, 0))
            if self.Menu:
                self.menu.update(mouse_p) # Show Menu Screen  
                # Position of the buttons
                menu_rect  = self.menu.buttons[0][0].get_rect(center=((get_screen_w//2, get_screen_h//2 + 75)))
                quit_rect = self.menu.buttons[2][0].get_rect(center=((get_screen_w//2, get_screen_h//2 + 225)))
                if self.menu.event.type == pg.MOUSEBUTTONDOWN and not self.menu.show_settings:
                     if menu_rect.collidepoint(mouse_p):  self.Menu = False; self.PlayerRoom = True
                     if quit_rect.collidepoint(mouse_p): pg.quit(), sys.exit()
            else: # The game
                scroll[0] += (self.Player.x - scroll[0] - get_screen_w // 2)
                scroll[1] += (self.Player.y - scroll[1] - get_screen_h // 2)
                DISPLAY.blit(self.world, (0 - scroll[0], 0 - scroll[1]))  # World Background Image
                ''' John's Room '''
                if self.PlayerRoom:                  
                    self.objects[0][0].update(DISPLAY, scroll, self.Player), self.room_borders() # Mau                   
                    if self.Player.y < 270:
                        self.Player.is_interacting = True
                        if self.Player.x >= 680 and self.Player.x <= 870:
                             self.Player.interact_text = 'computer'
                        elif self.Player.x >= 490 and self.Player.x < 650:
                             self.Player.interact_text = 'desk'
                    # Stairs
                    if self.Player.Rect.colliderect(pygame.Rect(get_screen_w // 2 + 334 - scroll[0], 150 - scroll[1], 195, 130)):
                         self.Player.interact_text = 'stairs'
                         self.Player.is_interacting = True
                         if self.Player.InteractPoint == 2:
                             self.PlayerRoom, self.world, self.Kitchen, self.Player.x , self.Player.y, self.Player.is_interacting, self.o_index = False, self.worlds[1], True, 1080, 250, False, 1
                     # End of John's Room               
                elif self.Kitchen: 
                    self.room_borders()
                    self.objects[1][0].update(DISPLAY, scroll, self.Player)
                    if self.Player.y < 270 and self.Player.x >= 420 and self.Player.x <= 810:
                        self.Player.is_interacting = True
                        self.Player.interact_text = 'kitchen' if self.Player.x < 570 else 'sink'
                    ''' Stairs '''
                    if self.Player.x >= 1005 and self.Player.y < 240 and self.Player.Interactable:
                        self.Player.interact_text = 'stairs_up'
                        self.Player.is_interacting = True
                        if self.Player.InteractPoint == 2:
                            self.PlayerRoom, self.world, self.Kitchen, self.Player.x, self.Player.y, self.Player.is_interacting, self.o_index = True, self.worlds[0], False, 1080, 320, False, 0
                # Global stuff that all worlds share
                self.Player.update()  # Draw player
                self.collision_system(self.o_index)
                self.pause(mouse_p)  # Pause menu
            # General Function         
            pg.display.update()



