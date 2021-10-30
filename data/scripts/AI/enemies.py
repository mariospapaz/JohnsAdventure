from types import coroutine
import pygame as pg
from ..utils import load, get_sprite, scale, resource_path
from .damage_popups import DamagePopUp
from math import ceil


class Enemy:

    """Designed to be the parent class of every enemy.
    
    It should help creating new ennemies, faster.
    
    There are a lot of docstrings to ease the comprehension of it, 
    as it can be a bit complicated sometimes."""

    def __init__(self, screen:pg.Surface, pos:tuple[int,int], hp:int=100, xp_drop = int):

        self.IDENTITY = "ENEMY"

        self.sheet = load(resource_path("data/sprites/dummy.png"), alpha=True)
        self.attackable = True
        self.screen = screen
        self.idle = scale(get_sprite(self.sheet, 0, 0, 34, 48), 4)
        self.hit_anim = [scale(get_sprite(self.sheet, i * 34, 48, 34, 48), 4) for i in range(4)]
        self.x, self.y = pos
        self.rect = self.idle.get_rect(topleft=pos)

        self.dead = False  # dead or not
        self.attackable = True  # if false, player can't damage the enemy

        # COORDINATES MANAGEMENT
        self.pos = pos
        self.x, self.y = pos

        # LIFE
        self.hp = self.MAX_HP = self.show_hp = hp
        self.xp_available = xp_drop
        self.xp_drop = xp_drop
        self.endurance = 0
        self.show_life_bar = True

        # DAMAGE POPUPS
        self.damages_texts = []

        # ANIMATION
        self.current_sprite = None
        #self.rect = None
        self.id_anim = self.delay = 0
        self.hitted = False
        self.idling = False

        # IMAGES & SPRITES MANAGEMENT

        # defines if the part is animated, useful for managing animation
        self.animating = { 
            "hit": [False, "hitted", "hit_anim", "single"],
            "walk": [False, "moving", "walk_anim_manager", "loop"],
            "attack": [False, "attacking", "attack_anim_manager", "single"],
            "idle": [False, "idling", "idle", "loop"],
            "death": [False, "dead", "death_anim", "single"],
        }
        # FORM EXPLANATION :
        # "state": [animating (T or F), "variable_of_animation_name", "animation_var_name" or "dict_managing_anim", "loop" or "single"]
        # "state" -> eg.: "hit" for the hit animation (default False)
        # animating -> tell if an animation is loaded and has to be played
        # "variable_of_animation_name" -> name of the variable that track if this currently has to be animated -> eg. : walking = True or False for walking animation
        # "animation_var_name" -> basically where the animation is stored or where the dict that manages it is stored (dicts are useful for multiple directions)
        # "loop" if the animation has to be played in a loop, "single" otherwise

        self.sheet = pg.Surface((10, 10))
        self.idle = self.hit_anim = self.death_anim = self.walk_right = self.walk_left = self.walk_down = self.walk_up = self.attack_right = self.attack_left = self.attack_down = self.attack_up = []

        # MOVEMENT
        self.moving = False
        self.direction = "right"
        self.walk_anim_manager = {
            "right": self.walk_right,
            "left": self.walk_left,
            "down": self.walk_down,
            "up": self.walk_up
        }

        # ATTACK
        self.attacking = False
        self.attack_anim_manager = {
            "right": self.attack_right,
            "left": self.attack_left,
            "down": self.attack_down,
            "up": self.attack_up
        }


    def load_animation(self,
                       sheet_path:str,
                       idle:str="None",
                       hit_anim:str="None",
                       walk_anim:str="None",
                       death_anim:str="None",
                       attack_anim:str="None",
                       idle_coo=None,  # idle sprites
                       hit_coo=None,  # hit sprites
                       walk_l_coo=None,  # left
                       walk_r_coo=None,  # right
                       walk_u_coo=None,  # up
                       walk_d_coo=None,  # downs
                       death_coo=None,  # death sprites
                       attack_l_coo=None,
                       attack_r_coo=None,
                       attack_u_coo=None,
                       attack_d_coo=None,
                       ):

        """
        coordinates form : [x, y, width, height, iterations, scale]
        eg.: [0 (left), 0 (top), 34 (34 px width), 48 (48 px height), 5 (5 sprites), 4 (scale original sprite by 4)]
        
        Function to setup the enemy's animation, usually called in __init__ method of the child
        class, after the super class's init.

        eg.:

        class NewEnemy(Enemy):
            def __init__(self):
                super().__init__(self, screen, pos, hp)
                self.load_animation(...)
        
        """

        # update sheet
        self.sheet = load(sheet_path, alpha=True)

        if idle in ["static", "animated"] and idle_coo is not None:  # check if there is an animation passed as an arg
            self.animating["idle"][0] = True  # specify that there is an idle animation
            self.idle = self.load_sheet(idle_coo)  # load it
        
        if hit_anim in ["static", "animated"] and hit_coo is not None:
            self.animating["hit"][0] = True  
            self.hit_anim = self.load_sheet(hit_coo)
        
        if walk_anim in ["static", "animated"] and None not in [walk_d_coo, walk_l_coo, walk_r_coo, walk_u_coo]:
            self.animating["walk"][0] = True  
            self.walk_down = self.load_sheet(walk_d_coo)
            self.walk_right = self.load_sheet(walk_r_coo)
            self.walk_up = self.load_sheet(walk_u_coo)
            self.walk_left = self.load_sheet(walk_l_coo)

        if death_anim in ["static", "animated"] and death_coo is not None:
            self.animating["death"][0] = True  
            self.death_anim = self.load_sheet(death_coo)

        if attack_anim in ["static", "animated"] and None not in [attack_d_coo, attack_l_coo, attack_r_coo, attack_u_coo]:
            self.animating["attack"][0] = True  
            self.attack_down = self.load_sheet(walk_d_coo)
            self.attack_right = self.load_sheet(walk_r_coo)
            self.attack_up = self.load_sheet(walk_u_coo)
            self.attack_left = self.load_sheet(walk_l_coo)

    def load_sheet(self, coo):

        """Load an animation sequence (of sprites) on a sprites,
        you obviously have to pass the coordinates of the sprites."""

        x, y, width, height = coo[:4]
        if coo[-1] != 0:  # check for scale
            return [scale(get_sprite(self.sheet, x+width*i, y, width, height), coo[-1]) for i in range(coo[-2])]
        else:
            return [get_sprite(self.sheet, x+width*i, y, width, height) for i in range(coo[-2])]
    
    def animate(self):

        """Animate the enemy considering all its states, it's designed to be generic,
        reusable and modifiable."""

        for key in self.animating:
            if self.animating[key][0]:  # check if an animation is loaded
                val = self.animating[key]
                if getattr(self, val[1]):
                    animation = getattr(self, val[2])
                    if type(animation) is dict:
                        animation = animation[self.direction]

                    if pg.time.get_ticks() - self.delay > 100:
                        match val[-1]:
                            case "loop":
                                self.id_anim = (self.id_anim + 1) % len(animation)
                            case "single":
                                if self.id_anim + 1 < len(animation):
                                    self.id_anim += 1
                        self.delay = pg.time.get_ticks()
                        self.current_sprite = animation[self.id_anim] 

                        # Update Enemy's rect
        self.rect = self.current_sprite.get_rect(topleft=self.pos)  

    def deal_damage(self, value:int, crit:bool, endurance_ignorance:bool=False):

        """Deal damages to its own instance, also triggers animations of hits,
        include critics and endurance ignorance."""

        self.hp -= ceil(value - self.endurance) if not endurance_ignorance else ceil(value)
        if self.hitted:
            self.id_anim = 0
        self.hitted = True
        # -> crit : dmg_type="crit" -> health ; dmg_type="health" ...
        if not endurance_ignorance:
            self.damages_texts.append(DamagePopUp(self.screen, self.rect, ceil(value-self.endurance), dmg_type=("default" if not crit else "crit"))) 
        else:
            self.damages_texts.append(DamagePopUp(self.screen, self.rect, ceil(value), dmg_type="health"))
        if self.hp <= 0:
            self.attackable = False
            self.dead = True
            self.hp = 0
    

    def life_bar(self):

        """Draw a life bar if the enemy is not at its max hp"""
        if self.MAX_HP != self.hp:
            # Outline
            pg.draw.rect(self.screen, (0, 0, 0), [self.pos[0], self.pos[1] - 12, self.current_sprite.get_width(), 10])
            
            # Health Bar
            pg.draw.rect(self.screen, (255, 0, 0), [self.pos[0], self.pos[1] - 12, int((self.current_sprite.get_width()/self.MAX_HP)*self.show_hp) - 2, 8])

            pg.draw.rect(self.screen, (255,255,255), self.rect, 1)

    def update_dmg_popups(self, scroll):

        """Update all the damages popups, including the removing."""

        for dmg_txt in self.damages_texts:
            kill = dmg_txt.update(scroll)
            if kill == "kill":
                self.damages_texts.remove(dmg_txt)

    def update_states(self):

        """Defines the priorities of states, for eg, if the enemy is dead,
        it forbid any actions for the enemy. It helps for animation coordination
        and fix bugs."""

        if self.dead:
            self.show_life_bar = False
            self.moving = False
            self.attacking = False
            return

        if self.attacking:
            self.moving = False
            self.idling = False
        
        if self.moving:
            self.idling = False
        else:
            self.idling = True

    def logic(self):

        """Here we pass all the behavior of the enemy, movement,
        attacks, spells..."""

        self.update_states()
        self.animate()

    def update(self, scroll, dt):

        """We gather all the methods needed to make the enemy work here.
        We pass the scroll."""

        # update the life bar if it's shown
        if self.show_life_bar:
            if self.show_hp >= self.hp:
                self.show_hp -= dt*16*abs((self.show_hp-self.hp)//3+1)
            self.life_bar()

        # update the damage pop ups
        self.update_dmg_popups(scroll)

        # update the pos of the enemy
        self.pos = self.x-scroll[0], self.y-scroll[1]

        # call logic method
        self.logic()       
        self.screen.blit(self.current_sprite, self.pos)


class Dummy(Enemy):

    def __init__(self, screen:pg.Surface, pos:tuple[int, int], hp:int=100, xp_drop = 9000):
        super().__init__(screen, pos, hp=100, xp_drop=210)
        self.load_animation(
            resource_path("data/sprites/dummy.png"),
            idle="static",
            hit_anim="animated",
            idle_coo=[0, 0, 34, 48, 1, 4],
            hit_coo=[0, 48, 34, 48, 4, 4]
        )
        self.xp_drop = self.xp_available = xp_drop