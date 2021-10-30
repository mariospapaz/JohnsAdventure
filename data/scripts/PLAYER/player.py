'''
Credits @Marios325346, @ƒkS124
Here is john, our protagonist.
'''


import pygame as p
import math
from copy import copy
from random import random
from ..sound_manager import SoundManager
from ..utils import load, get_sprite, scale, flip_vertical, resource_path, l_path
from .inventory import Inventory
from .player_stats import UpgradeStation
from .camera import Camera, Follow, Border, Auto

p.font.init()
font = p.font.Font(resource_path("data/database/pixelfont.ttf"), 16)
debug_font = p.font.Font(resource_path("data/database/pixelfont.ttf"), 12)

class Player:
    def __init__(self, screen, font, ux, ui, data):
        self.screen, self.InteractPoint = screen, 0
        self.sound_manager = SoundManager(sound_only=True)
        self.velocity = p.Vector2(0, 0) # Player's speed
        self.direction = "left"
        self.move_ability = {
            "left": True,
            "right": True,
            "up": True,
            "down": True
        }

        # Mouse icon for the inventory and some other things
        self.mouse_icon = ui.parse_sprite("mouse.png")
        self.show_mouse = False

        # For displaying npc text
        self.npc_catalog = ux

        # content display (it gets updated by the npcs)
        self.interact_text =  '' 


        self.paused = self.click = self.Interactable = self.is_interacting = False #  Features
        self.Right = self.Down = self.Left = self.Right = self.Up = False # Movement
        
        self.data = data
        self.inventory = Inventory(self.screen, ui, font)

        # States
        self.walking = False

        # Animation
        self.sheet = l_path('data/sprites/john.png')

        self.lvl_up_ring = [scale(get_sprite(self.sheet, 701 + i*27, 29, 27, 21), 4) for i in range(5)]
        self.ring_lu = False
        self.delay_rlu = 0
        self.id_rlu = 0
        self.current_frame_ring = self.lvl_up_ring[0]

        self.a_index = 0

        self.anim = {
            # Right ANIMATION
            'right': [],
            'right_a_1': [],
            'right_a_2': [],
            # Up ANIMATION
            'up': [],
            'up_a_1': [],
            'up_a_2': [],
            # Down ANIMATION
            'down': [],
            'down_a_1': [],
            'down_a_2': [],

            # Dash ANIMATION
            'dash_r': [],
            'dash_u': [],
            'dash_d': []
        }
        
        def get_j(row, col):
            return scale(get_sprite(self.sheet, 46 * row, 52 * col, 46, 52),3)

        # This for loop is reliable only for the current spritesheet
        # W :46
        # H: 52
        x_gap = y_gap = 0
        for key, value in self.anim.items():
            temp_list = [] # Holds the 5 frames
            for i in range(5):
                temp_list.append(get_j(x_gap, y_gap))
                x_gap += 1
            self.anim[key] = temp_list # Update the item key
            # It has reached the end of spritesheet
            if x_gap > 13:
                x_gap = 0
                y_gap += 1

        # Load the reverse frames to the dict for the left animation
        self.anim['left'] = [
            flip_vertical(sprite) for sprite in self.anim['right']
        ]

        self.anim['left_a_1'] = [
            flip_vertical(sprite) for sprite in self.anim['right_a_1']
        ]

        self.anim['left_a_2'] = [
            flip_vertical(sprite) for sprite in self.anim['right_a_2']
        ]

        self.anim['dash_l'] = [
            flip_vertical(sprite) for sprite in self.anim['dash_r']
        ]

        """

            Player Content

        """

        self.rect = self.anim['right'][0].get_rect() # This gets changed later

        # First spawn
        self.rect.x = 510
        self.rect.y = 290

        """

            Camera Settings

        """
        self.camera = Camera(self, screen)
        self.camera_mode = {
            "follow": Follow(self.camera, self),
            "border": Border(self.camera, self),
            "auto": Auto(self.camera, self)
        }

        # Default camera mod
        self.camera.set_method(self.camera_mode['follow'])

        self.looking_down = False
        self.looking_up = False
        self.looking_right = False
        self.looking_left = False

        self.index_attack_animation = 0
        self.delay_attack_animation = 0
        self.restart_animation = True
        self.attacking_frame = self.anim['left_a_2'][self.index_attack_animation]

        ''' Stats'''

        # The width for the UI is 180, but we need to find a way to put less health and keep the width -> width / max_hp * hp
        self.level = 1
        self.health = 180
        self.damage = 10
        self.endurance = 15
        self.critical_chance = 0.051  # The critical change the player has gathered without the weapon
        self.xp = 0 # wtf leveling system in john's adventures!??!?


        # Code for Dash Ability goes here
        self.dash_width = 180 # the pixel width for bars
        self.dash_cd = 750
        self.last_dash_end = 0
        self.dash_start = 0
        self.dashing = False
        self.dashing_direction = None
        self.dash_available = True
        self.delay_increasing_dash = 0
        self.delay_dash_animation = 0
        self.index_dash_animation = 0
        self.current_dashing_frame = None


        # Levelling
        self.experience = 0 # XP
        self.experience_width = 0 # This is for the UI
        self.level_index = 1

        # recalculate the damages, considering the equiped weapon
        self.modified_damages = self.damage + (self.inventory.get_equiped("Weapon").damage if self.inventory.get_equiped("Weapon") is not None else 0)

        self.upgrade_station = UpgradeStation(self.screen, ui, p.font.Font(resource_path("data/database/pixelfont.ttf"), 13), self)

        ''' UI '''
        self.health_box = scale(ui.parse_sprite('health'),5)
        self.heart = scale(ui.parse_sprite('heart'), 4)
        self.hp_box_rect = self.health_box.get_rect(
            topleft = (
                self.screen.get_width() - self.health_box.get_width() - 90,
                20
            )
        )


        '''  Combat System '''
        self.crosshair = ui.parse_sprite("mouse_cursor"),
        self.attack_pointer = l_path('data/ui/attack_pointer.png', True)
        self.attacking = False
        self.current_combo = 0
        # The number of attacks, last is rewarding extra damage
        self.last_attack = 3
        # ticks value in the future
        self.last_attacking_click = 0
        # still to be determined  This is the cooldown of the last attack
        self.attack_speed = 1150
        # still to be determined
        self.attack_cooldown = 450
        self.max_combo_multiplier = 1.025
        self.last_combo_hit_time = 0
        self.next_combo_available = True
        self.attacking = False
        self.attacking_hitbox = None
        # reversed when up or down -> (100, 250)
        self.attacking_hitbox_size = (self.rect.height, self.rect.width)
        self.rooms_objects = []

    def leveling(self):

        # PLAY THE SOUND OF THE LEVEL UPGRADING
        if self.experience >= 180: # <- The max width of the bar
            self.level += 1 # Increase the level
            self.experience = self.experience - 180 # Do the maths in case the exp is more than 180, else its 0
            self.level_index += 1 # a index for multiplying 180(width)    
            self.upgrade_station.new_level()
            self.ring_lu = True # Level UP UI starts
        self.experience_width = self.experience / self.level_index # Player needs more and more exp on each level, therefore we have to cut it

    def get_crit(self):
        crit = random()
        crit_chance = self.inventory.get_equiped("Weapon").critical_chance
        if crit < crit_chance:
            return self.modified_damages*crit_chance
        return 0

    # This should belong in collision system >:(((
    def check_content(self, pos):
        position = (self.rect.topleft - self.camera.offset.xy)
        itr_box = p.Rect(*position, self.rect.w//2, self.rect.h//2)
        # Manual Position tweaks
        itr_box.x -= 17
        itr_box.y += 45

        p.draw.rect(self.screen, (255,255,255), itr_box, 1)
        for obj in self.rooms_objects:
            if hasattr(obj, "IDENTITY"):
                if obj.IDENTITY == "NPC":
                    if itr_box.colliderect(obj.interaction_rect):
                       
                        # If player clicks Interaction key
                        if self.Interactable:
                            # Stop the npcs from moving
                            obj.interacting = True

                            # Turn on interact zone
                            self.is_interacting = True

                            # Get npc's text
                            self.npc_text = obj.tell_story

                            # Stop browsing to reduce calcs
                            break 
                elif obj.IDENTITY == "PROP":
                    if itr_box.colliderect(obj.interaction_rect) and obj.name == "chest":
                        obj.on_interaction(self) # Run Chest opening                      

    def check_for_hitting(self):
        '''
        room_objects is a list containing only the enemies of the current environment,
        for each one, if they are attackable and player hits them, they will lose hp
        '''
        for obj in self.rooms_objects:
            if hasattr(obj, "attackable"):
                if obj.attackable:
                    if self.attacking_hitbox.colliderect(obj.rect):
                        self.sound_manager.play_sound("dummyHit") # This is where it will play the object's hit sound NOT THE SWORD
                        crit = self.get_crit()
                        obj.deal_damage(self.modified_damages+crit, crit>0) if self.current_combo != self.last_attack else obj.deal_damage(self.modified_damages*self.max_combo_multiplier+crit, crit>0)
                        self.inventory.get_equiped("Weapon").start_special_effect(obj)
                    if obj.hp <= 0: # Check if its dead , give xp to the player
                        self.experience += obj.xp_available
                        obj.xp_available = 0

    def attack(self, pos):

        click_time = p.time.get_ticks()


        if not self.attacking and self.inventory.get_equiped("Weapon") is not None:
            self.attacking = True
            self.last_attacking_click = click_time
            self.sound_manager.play_sound("woodenSword") # Play first hit
            self.current_combo += 1
            self.next_combo_available = False
            self.update_attack(pos)
            self.check_for_hitting()

        else:
            if self.next_combo_available:
                if click_time - self.last_attacking_click > self.attack_speed:
                    self.attacking = False
                    self.current_combo = 0
                else:
                    self.sound_manager.play_sound("woodenSword") # Play sound 2
                    self.restart_animation = True
                    self.current_combo += 1
                    self.last_attacking_click = click_time
                    self.update_attack(pos)
                    self.check_for_hitting()
                    self.next_combo_available = False

                    if self.current_combo > self.last_attack:
                        self.last_combo_hit_time = p.time.get_ticks()

    def update_attack(self, pos):
        ''' This function is for updating the players hitbox based on the mouse position and also updating his animation'''

        # print("Up:", self.looking_up, "Down:", self.looking_down, "Left:", self.looking_left, "Right:", self.looking_right)
        # print("Current combo :", self.current_combo, "Time elapsed :", p.time.get_ticks()-self.last_attacking_click, "Cooldown :", p.time.get_ticks()-self.last_attacking_click>self.attack_cooldown, "Index :", self.index_attack_animation)

        if self.attacking:

            # sets the attacking hitbox according to the direction
            rect = p.Rect(self.rect.x - self.camera.offset.x - 50, self.rect.y - self.camera.offset.y - 40, *self.rect.size)
            if self.looking_up:
                self.attacking_hitbox = p.Rect(rect.x, rect.y-self.attacking_hitbox_size[0], self.attacking_hitbox_size[1], self.attacking_hitbox_size[0])
            elif self.looking_down:
                self.attacking_hitbox = p.Rect(rect.x, rect.bottom, self.attacking_hitbox_size[1], self.attacking_hitbox_size[0])
            elif self.looking_left:
                self.attacking_hitbox = p.Rect(rect.x-self.attacking_hitbox_size[1], rect.y, self.attacking_hitbox_size[1], self.attacking_hitbox_size[0])
            elif self.looking_right:
                self.attacking_hitbox = p.Rect(rect.right, rect.y, self.attacking_hitbox_size[1], self.attacking_hitbox_size[0])

            p.draw.rect(self.screen, (255, 0, 0), self.attacking_hitbox, 2)
            p.draw.rect(self.screen, (0, 255, 0), rect, 2)

            # animation delay of 100 ms
            if p.time.get_ticks() - self.delay_attack_animation > 100 and self.restart_animation:

                # select the animation list according to where the player's looking at
                a = self.anim
                if self.looking_right:
                    curr_anim = a['right_a_1'] if self.current_combo == 1 or self.current_combo == 3 else a['right_a_2']
                elif self.looking_left:
                    curr_anim = a['left_a_1'] if self.current_combo == 1 or self.current_combo == 3 else a['left_a_2']
                elif self.looking_down:
                    curr_anim = a['down_a_1'] if self.current_combo == 1 or self.current_combo == 3 else a['down_a_2']
                elif self.looking_up:
                    curr_anim = a['up_a_1'] if self.current_combo == 1 or self.current_combo == 3 else a['up_a_2']

                if self.index_attack_animation + 1 < len(curr_anim):  # check if the animation didn't reach its end
                        self.delay_attack_animation = p.time.get_ticks()  # reset the delay
                        self.attacking_frame = curr_anim[self.index_attack_animation+1]  # change the current animation frame
                        self.index_attack_animation+=1  # increment the animation index
                else:
                    self.restart_animation = False  # don't allow the restart of the animation until a next combo is reached
                    self.index_attack_animation = 0  # reset the animation index, without changing the frame in order to stay in "pause"
                    self.next_combo_available = True  # allow to attack again


            #p.draw.rect(self.screen, (255,255,255), self.Rect)
            self.screen.blit(self.attacking_frame, pos)

            # reset the whole thing if the combo reach his end and the animation of the last hit ended too
            if self.current_combo == self.last_attack and not self.restart_animation and not self.index_attack_animation:
                self.attacking = False  # stop attack
                self.current_combo = 0  # reset combo number
                self.next_combo_available = True  # allow to attack again
                self.restart_animation = True  # allow to restart an animation

            # p.draw.rect(self.screen, (255, 0, 0), self.attacking_hitbox) show hitbox
            if p.time.get_ticks() - self.last_attacking_click > self.attack_speed:
                self.attacking = False
                self.current_combo = 0
                self.next_combo_available = True
                self.restart_animation = True
                # RESET ANIMATION HERE

    def user_interface(self, m, player_pos):

        # Health bar
        p.draw.rect(
        self.screen, (255,0,0),
        p.Rect(
            self.hp_box_rect.x,self.hp_box_rect.y  + 20,
            self.health, 25)
        )

        # Dash Cooldown bar
        p.draw.rect(
            self.screen, (0,255,0),
            p.Rect(
                self.hp_box_rect.x, self.hp_box_rect.y  + 90,
                self.dash_width, 15)
        )

        # Experience bar
        p.draw.rect(
            self.screen, (0,255,255),
            p.Rect(
                self.hp_box_rect.x, self.hp_box_rect.y  + 60,
                self.experience_width, 15
                )
        )

        # Player UI
        self.screen.blit(self.health_box, self.hp_box_rect)

        # Heart Icon
        self.screen.blit(
            self.heart,
            (self.hp_box_rect.x + 3, self.hp_box_rect.y + 15)
        )

         # Level status button goes here
        self.upgrade_station.update(self)

        # Inventory Icon
        self.inventory.update(self)  # sending its own object in order that the inventory can access to the player's damages

        # recalculate the damages, considering the equiped weapon
        self.modified_damages = self.damage + (
            self.inventory.get_equiped("Weapon").damage \
             if self.inventory.get_equiped("Weapon") is not None else 0
        )
        equiped = self.inventory.get_equiped("Weapon")
        if hasattr(equiped, "special_effect"):
            equiped.special_effect(self)

        # if player presses interaction key and is in a interaction zone
        if self.Interactable and self.is_interacting:
            self.npc_catalog.draw(self.npc_text)

        #if not self.inventory
        if self.show_mouse:
            self.screen.blit(self.mouse_icon, self.mouse_icon.get_rect(center=m))

    def set_looking(self, dir_:str, pos):
        '''
            This function is for coordinating the hitbox
            and also playing the looking animation
        '''
        if dir_ == "up":
            self.looking_up, self.looking_down, self.looking_right, self.looking_left = True, False, False, False
        elif dir_ == "down":
            self.looking_up, self.looking_down, self.looking_right, self.looking_left = False, True, False, False
        elif dir_ == "left":
            self.looking_up, self.looking_down, self.looking_right, self.looking_left = False, False, False, True
        elif dir_ == "right":
            self.looking_up, self.looking_down, self.looking_right, self.looking_left = False, False, True, False

        if self.walking:
            self.screen.blit(self.anim[dir_][self.a_index // 7], pos)
        else:
            self.screen.blit(self.anim[dir_][0], pos)

    def start_dash(self):

        if not self.dashing and self.dash_available:
            self.dashing = True
            self.dash_start = p.time.get_ticks()
            self.dash_available = False
            self.delay_increasing_dash = p.time.get_ticks()
            if self.looking_down:
                self.dashing_direction = "down"
            elif self.looking_left:
                self.dashing_direction = "left"
            elif self.looking_right:
                self.dashing_direction = "right"
            else:
                self.dashing_direction = "up"

    def update_dash(self, dt, pos):

        if self.dashing:

            if p.time.get_ticks() - self.delay_dash_animation > 50:
                self.delay_dash_animation = p.time.get_ticks()
                match self.dashing_direction: # lgtm [py/syntax-error]
                    case "left": 
                        anim = self.anim['dash_l']
                    case "right": 
                        anim = self.anim['dash_r']
                    case "up": 
                        anim = self.anim['dash_u']
                    case "down":
                        anim = self.anim['dash_d'] 
                self.index_dash_animation = (self.index_dash_animation + 1) % len(anim)
                self.current_dashing_frame = anim[self.index_dash_animation]
            self.screen.blit(self.current_dashing_frame, pos)

            if p.time.get_ticks() - self.dash_start > 200:
                self.dashing = False
                self.last_dash_end = p.time.get_ticks()
                self.delay_increasing_dash = self.last_dash_end
                self.dash_width = 0

            if p.time.get_ticks() - self.delay_increasing_dash > 2:
                self.delay_attack_animation = p.time.get_ticks()
                freq = 25 # Frequency of the dash
                if self.move_ability[self.dashing_direction]:
                    match self.dashing_direction: # lgtm [py/syntax-error]
                        case "up":
                            self.rect.y -= dt*freq + 12 # 12 = players speed(2) * 2
                        case "down":
                            self.rect.y += dt*freq + 12
                        case "right":
                            self.rect.x += dt*freq + 12
                        case "left":
                            self.rect.x -= dt*freq + 12

        else:
            #  Update the  UI
            
            if p.time.get_ticks() - self.delay_increasing_dash > self.dash_cd / ((11 / 3) * 2):
                self.dash_width += 180/((11 / 3) * 2)
                self.delay_increasing_dash = p.time.get_ticks()

            if p.time.get_ticks() - self.last_dash_end > self.dash_cd:
                self.dash_available = True
                self.dash_width = 180

    def animation_handing(self, dt, m, pos):
        self.update_attack(pos)
        self.update_dash(dt, pos)

        if not self.attacking and not self.dashing:
            angle = math.atan2(
                m[1] - (self.rect.top + 95 - self.camera.offset.y),
                m[0] - (self.rect.left + 10 - self.camera.offset.x),
            )
            angle = abs(math.degrees(angle)) if angle < 0 else 360-math.degrees(angle)
            if 135 >= angle > 45:
                self.set_looking("up", pos)
            elif 225 >= angle > 135:
                self.set_looking("left", pos)
            elif 315 >= angle > 225:
                self.set_looking("down", pos)
            else:
                self.set_looking("right", pos)
        
        # Level UP ring
        self.animate_level_up_ring()

    def movement(self, m, pos):
        # Draw the Ring
        
        angle = math.atan2(
            m[1] - (self.rect.top + 95 - self.camera.offset.y),
            m[0] - (self.rect.left + 10 - self.camera.offset.x),
        )
        x, y = pos[0] - math.cos(angle), pos[1] - math.sin(angle) + 10
        angle = abs(math.degrees(angle))+90 if angle < 0 else 360-math.degrees(angle)+90
        image = p.transform.rotate(self.attack_pointer, angle)
        ring_pos = (x - image.get_width()//2 + 69, y - image.get_height()//2  + 139)
        if not self.ring_lu:
            self.screen.blit(image, ring_pos)

        if not self.inventory.show_menu:
            if not self.attacking: # if he is not attacking, allow him to move
                ''' Movement '''
                if self.Up and self.move_ability["up"]:
                    self.rect.y -= self.velocity[1]
                    dash_vel = -25
                elif self.Down and self.move_ability["down"]:
                    self.rect.y += self.velocity[1]
                    dash_vel = 25
                if self.Left and self.move_ability["right"]:
                    self.rect.x -= self.velocity[0]
                    dash_vel = -25 if not self.Down else 25 # Diagonal
                elif self.Right and self.move_ability["left"]:
                    self.rect.x += self.velocity[0]
                    dash_vel = 25 if not self.Up else -25 # Diagonal
            else: # He is attacking
                dash_vel = 0

            ''' Animation '''
            # fks will get rid of the frame paddding and use frame time
            if self.a_index >= 27:
                self.a_index = 0
            self.a_index += 1
       # Player is looking at the inventory, stop animation
        else:
            self.a_index = 0 # Play only first frame

        if not self.Up and not self.Down and not self.Right and not self.Left:
            self.walking = False

        # Update the camera: ALWAYS LAST LINE
        self.camera.scroll()

    def animate_level_up_ring(self):
        if self.ring_lu:
            if p.time.get_ticks() - self.delay_rlu > 150:
                self.delay_rlu = p.time.get_ticks()
                if self.id_rlu + 1 < len(self.lvl_up_ring):
                    self.id_rlu += 1
                else:
                    self.ring_lu = False
                    self.id_rlu = 0

                self.current_frame_ring = self.lvl_up_ring[self.id_rlu]
            self.screen.blit(self.current_frame_ring, self.current_frame_ring.get_rect(center=self.rect.topleft-self.camera.offset.xy+p.Vector2(15, 80)))

    def handler(self,dt):
        player_p  = (
        # 52 48 are players height and width
        self.rect.x - 52 - self.camera.offset.x,
        self.rect.y - self.camera.offset.y - 48
        )
        m = p.mouse.get_pos()

        self.leveling()
        self.controls(player_p)
        self.movement(m , player_p)
        self.animation_handing(dt, m, player_p)
        self.user_interface(m, player_p)   

    def update(self, dt):
        # Function that handles everything :brain:
        self.handler(dt)

    def controls(self, pos):
        '''
            Getting input from the user
        '''
        for e in p.event.get():
            keys = p.key.get_pressed()
            self.click = False
            a = self.data['controls']

            if not self.inventory.show_menu:
               self.Up = keys[a["up"]]
               self.Down = keys[a["down"]]
               self.Right = keys[a["left"]]
               self.Left = keys[a["right"]]

            interact = a['interact']
            dash = a['dash']
            inv = a['inventory']
            itr = a['interact']
            self.velocity = p.Vector2(-6, 6) if not(self.paused) else p.Vector2(0, 0)

            # Reset Interaction
            if True in [self.Up, self.Down, self.Right, self.Left] or self.InteractPoint == 3:
               self.walking = True
               self.InteractPoint, self.Interactable = 0, False
               self.is_interacting = False   
               self.npc_catalog.reset()
               # It finds for that one NPC that the player interacted with and it goes back to walking
               for obj in self.rooms_objects:
                    if hasattr(obj, "IDENTITY") and obj.IDENTITY == "NPC" and not self.is_interacting:
                        obj.interacting = False
                        break # Stop the for loop to save calculations                   
            match e.type: # lgtm [py/syntax-error]
                case p.QUIT:
                    raise SystemExit

                case p.KEYDOWN:
                    match e.key:

                        case p.K_F12:
                            p.display.toggle_fullscreen()
                        case p.K_ESCAPE:
                            self.paused = True

                       # Temporar until we get a smart python ver
                    if e.key == inv:
                        self.show_mouse = True
                        self.inventory.set_active()
                        if not self.inventory.show_menu:
                           self.show_mouse = False

                    if e.key == dash:
                        self.start_dash()

                    if e.key == itr:
                        self.Interactable = True
                        self.check_content(pos)
                        self.InteractPoint += 1

                case p.MOUSEBUTTONDOWN:
                    match e.button:
                        # left click
                        case 1:
                            click_result1 = self.inventory.handle_clicks(e.pos)
                            click_result2 = self.upgrade_station.handle_clicks(e.pos)
                            # Attack only when player is not in inv
                            if not self.inventory.show_menu and not self.upgrade_station.show_menu and click_result1 != "changed_activity" and click_result2 != "changed_activity":
                                self.attack(pos)
                                self.show_mouse = False
                            self.click = True
                            # scroll up
                        case 4:
                            if self.inventory.show_menu:
                                self.inventory.scroll_up()
                            # scroll down
                        case 5:
                            if self.inventory.show_menu:
                                self.inventory.scroll_down()
