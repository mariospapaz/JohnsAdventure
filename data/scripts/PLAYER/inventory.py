import pygame as pg
from .items import ItemSorter
from ..utils import scale, get_sprite


class Inventory:

    def __init__(self, screen, sprite_sheet, font):

        # unpack variables
        self.spr_sh = sprite_sheet
        self.screen, self.w, self.h = screen, screen.get_width(), screen.get_height()

        # invetory button
        self.button_inv = scale(self.spr_sh.parse_sprite("inventory"), 5)
        self.bi_rect = self.button_inv.get_rect(right=self.w-10, y=80)
        # the menu where all the items in the inventory will be displayed
        # only if the player is currently in this state
        self.inv_menu = pg.Surface((self.w // 3, self.h // 3), pg.SRCALPHA)
        self.im_rect = self.inv_menu.get_rect(right=self.bi_rect.x-5, y=140)  # center

        # ui piece for the inventory
        self.ui_inv = scale(self.spr_sh.parse_sprite("catalog_button.png"), 5)
        self.uii_rect = self.ui_inv.get_rect(right=self.inv_menu.get_width(), y=0)

        self.show_menu = False # Inventory is shown if it's True

        # Player's items:
        self.item_sorter = ItemSorter  # put this to avoid unused import
        self.items = [] # -> self.item_sorter.weapons["Knight_Sword"]()
        self.index_scroll = 0 # Useful to track the scrolling
        self.font = font


    def scroll_down(self):
        self.index_scroll += 1 * (self.index_scroll < len(self.items) - 3)

    def scroll_up(self):
        self.index_scroll -= 1 * (self.index_scroll > 0)

    def update(self, parent_class):
        item_l = len(self.items) # Lenth of the items 
        self.screen.blit(self.button_inv, self.bi_rect) # blit the inventory button
       
        if self.show_menu: # if it shows the menu, then it does not show the down bar      
            self.inv_menu.blit(self.ui_inv, self.uii_rect) # blit the inventory ui
          
            for index in range(item_l): # loop through the items
                # avoid errors where the scroll applied is too far away 
                if index + self.index_scroll > item_l - 1:
                    break

                # getting the item, the first item is 0 + scroll
                item = self.items[index+self.index_scroll]

                # track if the item is blitted outside of the ui, if so it breaks the loop
                if index*item.image.get_height()+16 > self.uii_rect.height - 15:
                    break
                
            
                damages = parent_class.inventory.get_equiped("Weapon").damage if parent_class.inventory.get_equiped("Weapon") is not None else 0
                # display the item on the screen
                item.update(self.inv_menu, (self.uii_rect.x+25, index*item.image.get_height()+12), damages)

            # showing a scroll bar
            #h = self.uii_rect.height / item_l
            #step = h / item_l * self.index_scroll * item_l
            #pg.draw.rect(self.inv_menu, (255, 0, 0), [self.uii_rect.right-10, step+10, 5, h * 1.5])
            self.screen.blit(self.inv_menu, self.im_rect) # Show menu
            self.screen.blit(self.font.render(f"{item_l}/32", True, (0,0,0)), (self.im_rect[0] + 340, self.im_rect[1] + 175)) # Show menu
    
    def reset_equipement(self, type_: str, instance: object):

        for item in self.items:
            if item.type == type_ and item != instance:
                item.equiped = False

    def get_equiped(self, type_:str):

        for item in self.items:
            if item.type == type_ and item.equiped:
                return item

    def handle_clicks(self, pos):
        # check if the inventory button is clicked if the inventory is not active
        if not self.show_menu and self.bi_rect.collidepoint(pos) or self.show_menu and not self.im_rect.collidepoint(pos):
            self.set_active()
            return "changed_activity"
        
        if self.show_menu:
            pos -= pg.Vector2(*self.im_rect.topleft) # get the pos of the click on the surface
            for item in self.items: 
                changes = item.handle_clicks(pos)  # Handle the clicks for all items
                if changes is not None:
                    if changes[0]:
                        self.reset_equipement(changes[1], changes[2])

    def set_active(self): # Switch state of the invetory
        self.show_menu = not self.show_menu