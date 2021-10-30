import pygame as pg
from pygame import Rect
from copy import copy

#from .PLAYER.items import Chest
from .PLAYER.player import *
from .PLAYER.inventory import *
from .AI.enemies import Dummy
from .AI import npc
from .utils import resource_path, load, l_path
from .props import Chest
from .PLAYER.items import Training_Sword

class GameState:

    """Parent class of every level.
    It handles every objects and handle their update method's arguments.
    (These args can of course be different than other objects of the list)"""

    def __init__(self, DISPLAY:pg.Surface, player_instance):

        # ------- SCREEN -----------------
        self.display, self.screen = DISPLAY, DISPLAY
        self.W, self.H = self.display.get_size()
        self.dt = 0  # wil be updated in update method

        # -------- WORLD's OBJECTS ----------
        self.player = player_instance  # get player to pass it as an argument in certain func of obj

        self.objects = []
        self.world = pg.Surface((1, 1))  # set default values for world -> supposed to be replaced

        # eg. -> "next_state_name" : pg.Rect(0, 0, 100, 100)
        self.exit_rects = {}  # the rects that lead to exit the current room

        # ----------- COLLISION SYSTEM ---------

        self.points_side = {  # -> lambda functions to get the coordinates of the colliding points
            "left": lambda rect, vel: [
                rect.topleft + pg.Vector2(vel[0], vel[1]),
                rect.midleft - pg.Vector2(-vel[0], 0),
                rect.bottomleft - pg.Vector2(-vel[0], vel[1])
            ],
            "right": lambda rect, vel: [
                rect.topright + pg.Vector2(-vel[0], vel[1]),
                rect.midright - pg.Vector2(vel[0], 0),
                rect.bottomright - pg.Vector2(vel[0], vel[1])
            ],
            "up": lambda rect, vel: [
                rect.topright - pg.Vector2(-vel[0], vel[1]),
                rect.midtop - pg.Vector2(0, vel[1]),
                rect.topleft - pg.Vector2(vel[0], vel[1])
            ],
            "down": lambda rect, vel: [
                rect.bottomright + pg.Vector2(vel[0], vel[1]),
                rect.midbottom + pg.Vector2(0, vel[1]),
                rect.bottomleft + pg.Vector2(-vel[0], vel[1])
            ]
        }

        self.spawn = {}
        # previous_state : coords

    def check(self, moving_object, col_obj, side):
        """Given a side of the moving object,
        this function detects the collision between
        the moving object and the collider.
        
        It handles the change of dictionary of the moving object.
        
        During the whole func, we use copy to get rects. It's not always useful, 
        but it's necessary sometimes, so to prevent from eventual assignement bugs
        we do it by default."""

        vel = copy(moving_object.velocity)  # gets velocity of the moving object
        obj_rect = copy(moving_object.rect)  # gets rect from the moving object
        obj_rect.topleft-=self.scroll  # applying scroll

        # apply a few modifications from the original player's rect to fit better to the collision system
        if type(moving_object) is Player: 
            obj_rect.topleft -= pg.Vector2(15, -70)
            obj_rect.w -= 70
            obj_rect.h -= 115

        if type(col_obj) is not pg.Rect:
            col_rect = copy(col_obj.rect)
            if hasattr(col_obj, "IDENTITY"):
                if col_obj.IDENTITY in ["NPC", "PROP"]:
                    col_rect.topleft -= self.scroll  # apply scroll to NPCs because it's not defaultly applied to rect
            # apply a few modifications from the original player's rect to fit better to the collision system
            if type(col_obj) is Player:
                col_rect.topleft -= self.scroll
                col_rect.topleft -= pg.Vector2(15, -70)
                col_rect.w -= 70
                col_rect.h -= 115
        else:
            col_rect = copy(col_obj)  # if it's a rect, just copy it
            col_rect.topleft -= self.scroll
  
        # pg.draw.rect(self.screen, (0, 255, 0), col_rect, 1)   ------ DO NOT ERASE : USEFUL FOR DEBUGGING -----

        # colliding points
        points = self.points_side[side](obj_rect, vel)

        changed = False  # -> gets if a change has been done
        for point in points:
            # pg.draw.circle(self.screen, (0, 255, 255), point, 5)   ------ DO NOT ERASE : USEFUL FOR DEBUGGING -----
            if col_rect.collidepoint(point):
                changed = True
                moving_object.move_ability[side] = False 
        if not changed:
            moving_object.move_ability[side] = True  # if no change have been done, resets the value
        if not moving_object.move_ability[side]:
            return "kill"  
            # -> tell the "parent script" to break the loop because a collision has already occured on this side

    def collision_system(self, obj_moving, objects_to_collide):

        """Basically the function that handles every object and every direction
        of the collide system."""

        for direction in ["left", "right", "down", "up"]:
            for obj in objects_to_collide:
                check = self.check(obj_moving, obj, direction)
                if check == "kill":  # a collision has occured on this side, no need to check more, so break
                    if hasattr(obj_moving, "switch_directions"):
                        obj_moving.switch_directions(blocked_direction=direction)  # switch NPCs direction for eg.
                    break

    def update(self, camera, dt):

        # update the game values
        self.player.rooms_objects = self.objects 
        self.dt = dt

        # display background
        self.display.blit(self.world, -camera.offset.xy)
        self.scroll = camera.offset.xy

        """ Collision Algorithm and Entity Updater """
        self.changes = {}  # reset the changes
        for obj in self.objects:
            """
            method.__code__.co_varnames -> ("arg1", "arg2", "var1", "var2", "var...") of the method
            so we remove self argument (useless) using [1:x]
            and we stop when we reach arguments' count gotten by : method.__code__.co_argcount
            get all the arguments of the func in a list -> the arguments must be found inside this class (GameState)
            for eg. : def update(self, screen, scroll)
            self is ignored, screen and scroll are found by getattr(self, "screen") and getattr(self, "scroll")
            """

            if type(obj) is not pg.Rect:
                obj.update(*[getattr(self, arg) for arg in obj.update.__code__.co_varnames[1:obj.update.__code__.co_argcount]])
            
            if hasattr(obj, "move_ability"):
                objects = copy(self.objects)  # gets all objects
                objects.remove(obj)  # remove the object that we are currently checking for collisions
                objects.append(self.player)  # add the player in the object list bc it's still a collider 
                self.collision_system(obj, objects)  # handle collisions
        
        # handle collisions for the player
        self.collision_system(self.player, self.objects)

        # MUST BE REWORKED -> supposed to track if the player is interacting with exit rects
        for exit_state, exit_rect in self.exit_rects.items():
            exit_rect = pg.Rect(exit_rect.x, exit_rect.y, *exit_rect.size)
            if self.player.rect.colliderect(exit_rect):
                if self.player.InteractPoint == 2:
                    return exit_state


class PlayerRoom(GameState):

    def __init__(self, DISPLAY:pg.Surface, player_instance):

        super().__init__(DISPLAY, player_instance)

        self.objects = [
            # Wall borders
            Rect(0,0, 1280,133), # Left
            Rect(1270,134,10,586), # Right
            Rect(0,0,1280,133), # Up
            Rect(0,711, 1280,9), # Down
            #################
            npc.Mau((150,530), (300, 100)),
            Rect(10,90, 430,360),
            Rect(5,500, 72, 214),
            Rect(450, 40, 410, 192),
            Rect(36,400, 77,94), 
            Dummy(DISPLAY, (1050, 300)),
            Chest((750, 250), {"items":Training_Sword(), "coins": 50})
        ]

        self.world = pg.transform.scale(l_path('data/sprites/world/Johns_room.png'), (1280, 720))

        self.exit_rects = {
            "kitchen": pg.Rect(self.W // 2 + 353, 150, 155, 130)
        }

        self.spawn = {
            "kitchen": (self.exit_rects["kitchen"].bottomleft+pg.Vector2(0, 50))
        }


class Kitchen(GameState):

    def __init__(self, DISPLAY:pg.Surface, player_instance):

        super().__init__(DISPLAY, player_instance)

        self.world = pg.transform.scale(load(resource_path('data/sprites/world/kitchen.png')), (1280,720))  # 1 Kitchen Room
        self.objects = [
            # Wall borders
            Rect(0,0, 1280,133), # Left
            Rect(1270,134,10,586), # Right
            Rect(0,0,1280,133), # Up
            Rect(0,711, 1280,9), # Down
            #################
            npc.Cynthia((570, 220)),
            Rect(20, 250, 250,350),
            Rect(280,300, 64, 256),
            Rect(10,0, 990, 230),
            Rect(1020, 440, 256, 200)
        ]

        self.exit_rects = {
            "player_room": pg.Rect(1005, 0, 1280-1005, 240)
        }

        self.spawn = {
            "player_room": (self.exit_rects["player_room"].bottomleft+pg.Vector2(25, 50))
        }
