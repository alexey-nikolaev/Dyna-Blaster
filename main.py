from random import choice, shuffle, randint, seed
from math import sin, cos, atan, pi, ceil
from datetime import datetime
from os.path import join
from functools import partial

import kivy
kivy.require('1.9.1')

from kivy.app import App
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.image import Image
from kivy.graphics import Color, Rectangle, Line
from kivy.uix.button import Button
from kivy.uix.togglebutton import ToggleButton
from kivy.uix.label import Label
from kivy.uix.widget import Widget
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, NoTransition, Screen
from kivy.core.audio import SoundLoader
from kivy.storage.jsonstore import JsonStore

# window properties
from kivy.core.window import Window
Window.clearcolor = [25/255., 25/255., 112/255., 1]

# load fonts
from kivy.core.text import LabelBase
LabelBase.register(name="PressStart2P", 
                   fn_regular=join("fonts", "PressStart2P.ttf"))

#load sounds
s_intro = SoundLoader.load(join('sounds', 'intro.mp3'))
s_select = SoundLoader.load(join('sounds', 'menu-select.mp3'))
s_game = SoundLoader.load(join('sounds', 'loop.mp3'))
s_fire = SoundLoader.load(join('sounds', 'explosion.mp3'))
s_sword = SoundLoader.load(join('sounds', 'sword.mp3'))
s_potion = SoundLoader.load(join('sounds', 'potion.mp3'))
s_hit = SoundLoader.load(join('sounds', 'hit.mp3'))
s_spikes = SoundLoader.load(join('sounds', 'spikes.mp3'))
s_heal = SoundLoader.load(join('sounds', 'heal.mp3'))
s_score = SoundLoader.load(join('sounds', 'score.mp3'))
s_evil = SoundLoader.load(join('sounds', 'evil.mp3'))
s_kill_enemy = SoundLoader.load(join('sounds', 'kill_enemy.mp3'))
s_wind = SoundLoader.load(join('sounds', 'wind.mp3'))

# storage file
storage = JsonStore('storage_file.json')

mflag = False # hero movement flag (including waiting list)
anim_flag = False # hero animation flag
waiting = [] # command waiting list
game_ended = False # game end flag
tutorial_mode = False # tutorial mode flag

# world frame
a = min(Window.width, Window.height)
b = max(Window.width, Window.height)
world_top = b-0.15*a
world_bottom = b-1.05*a-2*0.09*a
world_left = 0.05*a
world_right = 0.95*a

# controller size
# determine width or height limitations
if a >= ((b-1.25*a)*388.)/164.: # height limitation
    c_pos_x = (a-(b-1.25*a)*(388./164.))/(2.*Window.width)
    c_pos_y = 0.01*a/Window.height
    c_size_x = ((b-1.25*a)*388.)/(164.*Window.width)
    c_size_y = (b-1.25*a)/Window.height
else: # width limitation
    c_pos_x = 0
    c_pos_y = (b-1.3*a-(Window.width*164.)/388.)/(2.*Window.height)
    c_size_x = 1
    c_size_y = (Window.width*164.)/(388.*Window.height)
    
Builder.load_string('''
<MainFrame>:
    
    Screen:
        id: start_screen
        name: 'start screen'
        
        StartLayout:
            id: start_layout
            name: 'start_layout'
            
            Image:
                source: 'logo.png'
                size_hint: 1, 240./320.
                pos_hint: {'center_y': .8, 'center_x':.5}
                allow_stretch: True
            
            BoxLayout:
                id: start_box
                size_hint: (1, .5)
                pos_hint: {'x': 0, 'y': .25}
                orientation: 'vertical'
                    
                StartText:
                    id: start_text
                    size_hint: 1, .5
    
    BlankScreen:
        id: blank_screen
        name: 'blank screen'
                    
    GameScreen:
        id: game_screen
        name: 'game screen'
        
        Game:
            id: game
            name: 'game'
    
    HighscoreScreen:
        id: highscore_screen
        name: 'highscore'
        
        StartText:
            id: highscore
            text: 'highscore'
            on_touch_down: root.current = 'start screen'
''')

class TutorialLabel(Widget):
    def __init__(self, text, **kwargs):
        super(TutorialLabel, self).__init__(**kwargs)
        self.size_hint=(1.,.2)
        self.pos_hint={'center_x':.5, 'center_y': .5}
        self.bind(size=self.draw, pos=self.draw, center_x=self.draw, center_y=self.draw)
        self.name='tutorial label'
        self.text=text
    def draw(self, *args):
        self.canvas.clear()
        self.clear_widgets()
        with self.canvas:
            self.color = Color(0,192./255.,235./255.,1)
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.add_widget(Label(text=self.text, size=self.size, pos=self.pos, font_name='PressStart2P', font_size='14sp'))
    
class StartText(Label):
    def __init__(self, **kwargs):
        super(StartText, self).__init__(**kwargs)
        self.text = '\n\n\n\nPress F to start\n\n\nPress P to watch\nthe tutorial\n\n\nPress RIGHT to see\nthe highscore'
        self.font_name = 'PressStart2P'
        self.font_size = '14sp'
        #self.size = self.texture_size
        #self.text_size = self.size
        self.markup = True
        
# blank screens used to avoid text blinking
class BlankScreen(Screen):
    def __init__(self, **kwargs):
        super(BlankScreen, self).__init__(**kwargs)
    def on_enter(self, *args):
        self.parent.current = 'game screen'
        
class GameScreen(Screen):
    def __init__(self, **kwargs):
        super(GameScreen, self).__init__(**kwargs)
    def on_enter(self, *args):
        if tutorial_mode:
            self.children[0].restart(True) # restart in fixed layout mode
            m = 0.05*a
            hero1.pos_hint = {'x': (m+0.09*a)/Window.width, 'y': (b-0.24*a)/Window.height}
            hero2.pos_hint = {'x': (m+0.09*a*3)/Window.width, 'y': (b-0.24*a)/Window.height}
            Clock.schedule_once(self.children[0].show_tutorial, 1.)
        else:
            self.children[0].restart(False) # restart in random layout mode
        
class HighscoreScreen(Screen):
    def __init__(self, **kwargs):
        super(HighscoreScreen, self).__init__(**kwargs)
    def on_pre_enter(self, *args):
        try: 
            storage.get('highscore')
        except KeyError:
            storage.put('highscore', score = 0, datetime = 'no highscores yet')
        score = storage.get('highscore')['score']
        datetime = storage.get('highscore')['datetime']
        text = "highscore: %s\n\n\n%s" % (score, datetime)
        label = self.children[0]
        label.text = text

class Wall(Image):
    def __init__(self, pos_x, pos_y, p1, p2, **kwargs):
        super(Wall, self).__init__(**kwargs)
        self.source='wall.png'
        self.allow_stretch=True
        self.mipmap=True
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(p1,p2)
        self.name='wall'

class Container(Image):
    def __init__(self, pos_x, pos_y, p1, p2, **kwargs):
        super(Container, self).__init__(**kwargs)
        self.source=''
        self.color=(0,0,0,0)
        self.allow_stretch=True
        self.mipmap=True
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(p1,p2)
        self.name='container'
        
class HomeTile(Image):
    def __init__(self, pos_x, pos_y, p1, p2, **kwargs):
        super(HomeTile, self).__init__(**kwargs)
        self.source='wall.png'
        self.allow_stretch=True
        self.mipmap=True
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(p1,p2)
        self.color=(170/255.,1,0,1)
        self.name='home'
        
class Spikes(Image):
    def __init__(self, pos_x, pos_y, p1, p2, **kwargs):
        super(Spikes, self).__init__(**kwargs)
        self.source='spikes_blue_short.png'
        self.allow_stretch=True
        #self.mipmap=True
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(p1,p2)
        self.name='spikes'
        
class HomeLabel(Image):
    def __init__(self, pos_x, pos_y, p1, p2, **kwargs):
        super(HomeLabel, self).__init__(**kwargs)
        self.source='home.png'
        self.allow_stretch=True
        self.mipmap=True
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(p1,p2)
        self.name='home_label'
        
class GameOverLabel(Label):
    def __init__(self, **kwargs):
        super(GameOverLabel, self).__init__(**kwargs)
        self.name='game over'
        self.markup=True
        self.text='[size=24sp]Game Over[/size]\n\nPress F to restart\n\nPress P to quit'
        self.font_name='PressStart2P'
        self.halign='center'
        self.pos_hint={'center_x': (world_right+world_left)/(2.*Window.width), 'center_y': (world_top+world_bottom)/(2.*Window.height)}
        self.font_size='14sp'
            
class Item(Image):
    def __init__(self, model, pos_x, pos_y, **kwargs):
        super(Item, self).__init__(**kwargs)
        self.model=model
        self.allow_stretch=True
        self.source=join('items',model+'.png')
        self.size_hint=(0.05*a/Window.width, 0.05*a/Window.height)
        self.pos_hint={'center_x':pos_x, 'center_y':pos_y}
        self.x=self.pos_hint['center_x']*Window.width-0.045*a
        self.y=self.pos_hint['center_y']*Window.height-0.045*a
        self.size=(0.05*a, 0.05*a)
        self.name='item'
        if not game_ended:
            # correct item's position if it is not of the grid
            cx, cy = (self.x - world_left)/(0.09*a), (self.y-world_bottom)/(0.09*a)
            if not ((cx == int(cx)) and (cy == int(cy))): # if hero's poisition is not in the grid
                # find closest tile on which hero will be returned
                min_dist = 10**6
                for wid in firebttn.parent.children:
                    if wid.name in ['container', 'forest', 'home']:
                        dist = ((self.y-wid.y)**2+(self.x-wid.x)**2)**0.5
                        if dist < min_dist:
                            min_dist = dist
                            closest_tile = wid
                self.pos_hint = {'center_x': (closest_tile.x+0.045*a)/Window.width, 'center_y': (closest_tile.y+0.045*a)/Window.height}
    def update(self, *args):
        self.x=self.pos_hint['center_x']*Window.width-0.045*a
        self.y=self.pos_hint['center_y']*Window.height-0.045*a
        self.size=(0.05*a, 0.05*a)
    def take_action(self, hero, *args):
        if self.model == 'medikit':
            # add 2 lives if possible
            s_heal.play()
            if hero.life<6:
                if hero.life<5:
                    for i in range(2):
                        hero.life+=1
                        num = int(ceil(hero.life/2.))-1
                        hero.hearts[num].st-=1
                        hero.hearts[num].update()
                else:
                    hero.life+=1
                    num = int(ceil(hero.life/2.))-1
                    hero.hearts[num].st-=1
                    hero.hearts[num].update()
        elif self.model == 'star':
            s_score.play()
            scorer.score += 3
            scorer.update()
        elif self.model == 'sword':
            s_sword.play()
            hero.expanded_fire = True # expand fire for 1 to 2 in each direction for 1 minute
            def shrink_fire(*args):
                hero.expanded_fire = False
                hero.events['shrink_fire'] = None # delete restoring event
            if not hero.events['shrink_fire'] == None: # cancel not completed restoring event
                hero.events['shrink_fire'].cancel()
            hero.events['shrink_fire'] = Clock.schedule_once(shrink_fire, 60.)
        elif self.model == 'potion':
            hero.invisible = True # make hero invisible for 30 seconds
            hero.color = (0, 0, 1, .5)
            s_potion.play()
            def make_visible(*args):
                hero.invisible = False
                hero.color = (1,1,1,1)
                hero.events['make_visible'] = None # delete restoring event
            if not hero.events['make_visible'] == None: # cancel not completed restoring event
                hero.events['make_visible'].cancel()
            hero.events['make_visible'] = Clock.schedule_once(make_visible, 30.)
        elif self.model == 'boots':
            hero.speed = 2
            s_wind.play()
            def slow_down(*args):
                hero.speed = 1
                hero.events['slow_down'] = None # delete restoring event
            if not hero.events['slow_down'] == None: # cancel not completed restoring event
                hero.events['slow_down'].cancel()
            hero.events['slow_down'] = Clock.schedule_once(slow_down, 30.)
        self.die()
    def die(self, *args):
        firebttn.parent.remove_widget(self)
        
class Flame(Image):
    def __init__(self, creator, base, target, **kwargs):
        super(Flame, self).__init__(**kwargs)
        self.st=0 # state for image changes
        self.fst=0 # state for flying
        if creator.level == 0:
            self.model = 'flame'
        elif creator.level == 1:
            self.model = 'blue_flame'
        self.source=join(self.model,self.model+'_'+str(self.st)+'.png')
        self.allow_stretch=True
        self.calculate_path(base, target)
        self.pos_hint={'center_x': self.path[self.fst][0]/Window.width, 'center_y': self.path[self.fst][1]/Window.height}
        self.size_hint=(0.06*a/Window.width,0.06*a/Window.height)
        self.name='flame'
        self.used=False # flag to exclude double life decrease
        self.creator=creator # object property, enemy which created this flame
        Clock.schedule_interval(self.update, .1)
        for i in range(1,100):
            Clock.schedule_once(self.fly_to_target, i/20.)
        Clock.schedule_once(self.die, 5.)
    def update(self, *args):
        if self.st == 3: self.st = 0
        else: self.st+=1
        self.source=join(self.model,self.model+'_'+str(self.st)+'.png')
    def calculate_path(self, base, target, *args):
        # calculate path to fly along hyperbolic spiral from base to target: x = a*cost/t, y=a*sint/t, t -> 0: y -> a
        # hyperbolic spiral can't shoot targets on horizontal or vertical, rotation needed (rotate first quadrant diagonal 45 to vector and back)
        tar0, tar1 = target[0]-base[0], target[1]-base[1]
        if tar0 == 0: phi0 = pi/2.
        else: phi0 = atan(tar1*1./tar0)
        phi = pi/4 - phi0 # rotation angle
        tar0_rotated, tar1_rotated = tar0*cos(phi)+tar1*sin(phi), -tar0*sin(phi)+tar1*cos(phi)
        # fit curve to target
        # calculate atan correction
        if tar0_rotated*tar1_rotated>=0: corr=0
        else: corr=pi
        # fit parameters
        try:
            t_tar = atan(tar1_rotated*1./tar0_rotated)+corr
        except ZeroDivisionError:
            firebttn.parent.remove_widget(self) # remove flames with path that can't be calculated
        a = tar0_rotated*t_tar/cos(t_tar)
        # calculate path
        t_range = [t_tar+(99-i)/10. for i in range(100)]
        path_rotated = [(a*cos(t)/t, a*sin(t)/t) for t in t_range]
        # rotate back
        self.path = [(base[0]+p[0]*cos(phi)-p[1]*sin(phi), base[1]+p[0]*sin(phi)+p[1]*cos(phi)) for p in path_rotated]
    def fly_to_target(self, *args):
        self.fst+=1
        self.pos_hint={'center_x': self.path[self.fst][0]/Window.width, 'center_y': self.path[self.fst][1]/Window.height}
        self.hit()
    def hit(self, *args):
        for i, hero in enumerate([hero1, hero2]):
            # destroy flames in protected area
            if hero.protected:
                c_pos = (self.pos_hint['center_x']*Window.width, self.pos_hint['center_y']*Window.height)
                if c_pos[0]<=hero.center_x+0.135*a and c_pos[0]>=hero.center_x-0.135*a and c_pos[1]<=hero.center_y+0.135*a and c_pos[1]>=hero.center_y-0.135*a:
                    firebttn.parent.remove_widget(self)
                    break
            elif self.collide_widget(hero) and not self.used:
                s_hit.play()
                self.used = True
                firebttn.parent.remove_widget(self)
                 # make changes in hero's hearts
                num = int(ceil(hero.life/2.))-1
                hero.hearts[num].st+=1
                hero.hearts[num].update()
                hero.life -= 1
                # end game
                if hero.life == 0: 
                    firebttn.parent.end_game(i+1)
    def die(self, *args):
        if not game_ended:
            firebttn.parent.remove_widget(self)

class Heart(Image):
    def __init__(self, num, hero, **kwargs):
        super(Heart, self).__init__(**kwargs)
        self.st=0 # zero means full life for one heart, 1 - half and 2 - no life
        self.num=num # ordering number from 0 to 2
        self.name='heart'
        self.hero=hero # hero number (1 or 2)
        self.allow_stretch=True
        self.source=join('hearts', str(self.st)+'.png')
        self.size_hint = (a*(0.36/10.)/Window.width, a*(0.32/10.)/Window.height)
        if self.hero == 1: shift=0
        elif self.hero == 2: shift=(world_left+world_right)/2.
        self.pos_hint = {'x': (0.05*a+0.08*a*self.num+shift)/Window.width, 'y': (b-0.05*a-a*(0.32/10.))/Window.height}
    def update(self, *args):
        self.source=join('hearts', str(self.st)+'.png')
            
class Hero(Image):
    def __init__(self, model, pos_x, pos_y, p1, p2, **kwargs):
        super(Hero, self).__init__(**kwargs)
        self.source=join('sprites', model, model+choice(['-0-1.png', '-0-3.png']))
        self.allow_stretch=True
        #self.mipmap=True
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(p1,p2)
        self.st=0
        self.life=6 # 2 lives make 1 heart
        self.drct='2'
        self.name='hero'
        self.model=model
        self.hearts=[] # hearts with hero lives
        self.expanded_fire=False
        self.invisible=False
        self.protected=False
        self.speed=1
        self.events = {'shrink_fire': None, 'make_visible': None, 'slow_down': None}
    def update(self, *args):
        if self.st == 7: # bats while biting
            self.source = join('sprites', self.model, self.model+'-7-'+self.drct+'.png')
        else:
            self.source = join('sprites', self.model, self.model+'-'+str(int(self.st%3))+'-'+self.drct+'.png')
        self.x, self.y = self.pos_hint['x']*Window.width, self.pos_hint['x']*Window.height
        self.center_x, self.center_y = self.x+0.0045*a, self.y+0.0045*a
    def move(self, drct):
        if not game_ended and not self.protected:
            dkeys = {'up':'0', 'right':'1', 'down':'2', 'left':'3'}
            dmoves = {'up':(0,1), 'right':(1,0), 'down':(0,-1), 'left':(-1,0)}
            self.drct = dkeys[drct]
            stop = False
            fut_center_x = self.x+dmoves[drct][0]*0.09*a+0.045*a # future hero widget center
            fut_center_y = self.y+dmoves[drct][1]*0.09*a+0.045*a
            # stop going up in empty space
            if drct == 'up':
                esaflag = True # empty space above hero flag
                for wid in firebttn.parent.children:
                    if wid.name in ['forest', 'item', 'home']:
                        if wid.collide_point(fut_center_x, fut_center_y):
                            esaflag = False
                            break
                if esaflag: stop = True
            if not stop: 
                for wid in firebttn.parent.children:
                    if wid.name == 'wall':
                        if wid.collide_point(fut_center_x, fut_center_y): # check whether future hero widget center collides with any wall
                            stop = True
                            break
            if not stop:
                if (fut_center_x > world_right) or (fut_center_x < world_left) or (fut_center_y > world_top) or (fut_center_y < world_bottom+0.09*a): # check wheter future hero widget center is inside the world frame and avoid going to spikes
                    stop = True
            # avoid going up from the wall with empty space above
            if not stop:
                for wid in firebttn.parent.children:
                    if wid.name == 'wall':
                        if wid.collide_point(self.center_x-0.09*a, self.center_y-0.09*a): # wall under a hero
                            esflag = True # empty space at hero position flag
                            for wid in firebttn.parent.children:
                                if wid.name in ['forest', 'home']:
                                    if wid.collide_point(self.center_x, self.center_y): 
                                        esflag = False
                                        break
                            if esflag and drct == 'up': stop = True
                            break
            if not stop:
                global anim_flag
                anim_flag = True
                anim = Animation(pos_hint={'x':self.pos_hint['x']+dmoves[drct][0]*0.09*a/Window.width, 'y':self.pos_hint['y']+dmoves[drct][1]*0.09*a/Window.height}, st=10, t='linear', duration=1./self.speed)
                anim.bind(on_start=self.activate_update, on_complete=self.before_move_next)
                anim.start(self)
            else:
                self.before_move_next()
    def activate_update(self, *args):
        global mflag
        mflag = True
        for i in range(10):
            Clock.schedule_once(self.update, i/10.)
    def before_move_next(self, *args):
        if not game_ended and not self.protected:
            global anim_flag
            anim_flag = False
            self.st = 0
            # die on spikes (minus one heart and return home)
            if self.y < world_bottom+0.09*a:
                s_spikes.play()
                def die_on_spikes(*args):
                    # make changes in hero's hearts
                    for i in range(2):
                        num = int(ceil(self.life/2.))-1
                        self.hearts[num].st+=1
                        self.hearts[num].update()
                        self.life -= 1
                        if self.life == 0:
                            if self.model == 'warrior-m': hero_num = 1
                            else: hero_num = 2
                            firebttn.parent.end_game(hero_num)
                            break
                    else: 
                        self.pos_hint['y'] = (world_top-0.09*a)/Window.height
                        self.y = world_top-0.09*a
                        global waiting
                        waiting = [] # clear command waiting list
                        # cancel all temporary abilities
                        self.invisible = False
                        self.expanded_fire = False
                        self.speed = 1
                        self.color = (1,1,1,1)
                        self.events = {'shrink_fire': None, 'make_visible': None, 'slow_down': None}
                        self.move_next()
                Clock.schedule_once(die_on_spikes, 1.)
            else:
                # collect items
                for wid in firebttn.parent.children:
                    if wid.name == 'item' and wid.collide_point(self.center_x, self.center_y):
                        wid.take_action(self)
                        break
                if firebttn.fire_waiting:
                    Clock.schedule_once(self.move_next, 1./self.speed)
                else: self.move_next()
    def move_next(self, *args):
        if not game_ended and not self.protected:
            # correct hero's position if it is not of the grid
            cx, cy = (self.x - world_left)/(0.09*a), (self.y-world_bottom)/(0.09*a)
            if not ((cx == int(cx)) and (cy == int(cy))): # if hero's poisition is not in the grid
                # find closest tile on which hero will be returned
                min_dist = 10**6
                for wid in firebttn.parent.children:
                    if wid.name in ['container', 'forest', 'home']:
                        dist = ((self.y-wid.y)**2+(self.x-wid.x)**2)**0.5
                        if dist < min_dist:
                            min_dist = dist
                            closest_tile = wid
                self.pos_hint = {'x': closest_tile.x/Window.width, 'y': closest_tile.y/Window.height}
            res = self.check_fall()
            if res[0]:
                if len(waiting) == 0: # check for commands in waiting list
                    global mflag
                    mflag = False
                else:
                    cur = waiting.pop(0)
                    self.move(cur)
            else:
                self.fall(res[1])
    def check_fall(self, *args): # check whether to fall or not
        if not game_ended:
            stay_flag = False
            depth = 0
            if self.y < world_bottom: 
                stay_flag = True
            else:
                for wid in firebttn.parent.children:
                    if wid.name in ['forest', 'item', 'home']:
                        if wid.collide_point(self.x+0.045*a, self.y+0.045*a):
                            stay_flag = True
                            break
                    elif wid.name == 'wall':
                        if wid.collide_point(self.x+0.045*a, self.y+0.045*a-0.09*a):
                            stay_flag = True
                            break
            if not stay_flag:
                max_depth = int((self.y-world_bottom)/(0.09*a)) # maximum fall depth to spikes level
                dsflag = True # active fall depth search flag
                for i in range(1, max_depth+1):
                    if not dsflag: break
                    for wid in firebttn.parent.children:
                        if wid.name in ['forest', 'item', 'home', 'spikes']:
                            if wid.collide_point(self.x+0.045*a, self.y+0.045*a-0.09*a*i):
                                dsflag = False
                                depth = i
                                break
                        elif wid.name == 'wall':
                            if wid.collide_point(self.x+0.045*a, self.y+0.045*a-0.09*a*(i+1)):
                                dsflag = False
                                depth = i
                                break
                else: 
                    depth = max_depth
            return (stay_flag, depth)
    def fall(self, depth, *args): # fall down for variable depth
        global anim_flag
        anim_flag = True
        old_y = self.y
        def after_fall(*args):
            self.y = old_y-0.09*a*depth # update self.y before position correction
            self.before_move_next()
        anim = Animation(pos_hint={'x':self.pos_hint['x'], 'y':self.pos_hint['y']-0.09*depth*a/Window.height}, t='in_cubic', duration=.5*(depth**0.5))
        anim.bind(on_complete=after_fall)
        anim.start(self)

class Enemy(Hero): # based on Hero class
    def __init__(self, model, level, pos_x, pos_y, p1, p2, **kwargs):
        super(Enemy, self).__init__(model, pos_x, pos_y, p1, p2, **kwargs)
        self.name='enemy'
        self.level=level # level 1 expands vision field and make movement more unpredictable, level -1 is bat
        if self.level == -1: # bat
            self.used = False
            self.speed = 2
    def check_vision_field(self, *args): # check triangular vision field 3*4 in movement direction
        # functions to check if point is in a triangle
        def sign(p1, p2, p3):
            return (p1[0] - p3[0]) * (p2[1] - p3[1]) - (p2[0] - p3[0]) * (p1[1] - p3[1])
        def PointInTriangle(pt, v1, v2, v3):
            b1 = sign(pt, v1, v2) < 0
            b2 = sign(pt, v2, v3) < 0
            b3 = sign(pt, v3, v1) < 0
            return ((b1 == b2) and (b2 == b3))
        # determine vision field depending on enemy's level
        if self.level == 0:
            front = 3
            side = 2
        elif self.level == 1:
            front = 4
            side = 3
        dkeys = {'0':(0,1), '1':(1,0), '2':(0,-1), '3':(-1,0)}
        front_point = (self.center_x + dkeys[self.drct][0]*front*0.09*a, self.center_y + dkeys[self.drct][1]*front*0.09*a)
        upper_or_right_point = (front_point[0] + ((abs(dkeys[self.drct][0])+1)%2)*side*0.09*a, front_point[1] + ((abs(dkeys[self.drct][1])+1)%2)*side*0.09*a) # change 0 to 1 and +-1 to 0
        lower_or_left_point = (front_point[0] - ((abs(dkeys[self.drct][0])+1)%2)*side*0.09*a, front_point[1] - ((abs(dkeys[self.drct][1])+1)%2)*side*0.09*a) # change 0 to 1 and +-1 to 0
        # look for heroes in vision field in random order
        heroes = [hero1, hero2]
        shuffle(heroes)
        for hero in heroes:
            pt, v1, v2, v3 = (hero.center_x, hero.center_y), (self.center_x, self.center_y), upper_or_right_point, lower_or_left_point
            if PointInTriangle(pt, v1, v2, v3) and not hero.center_y > world_top - 0.09*a and not (hero.invisible or hero.protected): # enemy can't see heroes at home and invisible/protected heroes
                return (True, pt)
                break
        else:
            return (False, pt)
    def move(self, drct, *args):
        self.st = 0
        dkeys = {'up':'0', 'right':'1', 'down':'2', 'left':'3'}
        dmoves = {'up':(0,1), 'right':(1,0), 'down':(0,-1), 'left':(-1,0)}
        self.drct = dkeys[drct]
        anim = Animation(pos_hint={'x':self.pos_hint['x']+dmoves[drct][0]*0.09*a/Window.width, 'y':self.pos_hint['y']+dmoves[drct][1]*0.09*a/Window.height}, st=10, t='linear', duration=1./self.speed)
        anim.bind(on_start=self.activate_update, on_complete=self.move_next)
        anim.start(self)
        self.creation_flag = 0
    def move_next(self, *args):
        if not game_ended:
            dkeys = {'0':'up', '1':'right', '2':'down', '3':'left'}
            dmoves = {'0':(0,1), '1':(1,0), '2':(0,-1), '3':(-1,0)}
            if (self.center_x > world_right) or (self.center_x < world_left) or (self.center_y > world_top-2*0.09*a) or (self.center_y < world_bottom+2*0.09*a):
                for i, hero in enumerate([hero1, hero2]):
                    if hero.collide_point(self.center_x, self.center_y) and not self.used:
                        if self.level == -1:
                            s_hit.play()
                            self.used = True
                            self.st = 7
                            self.update()
                            # make changes in hero's hearts
                            num = int(ceil(hero.life/2.))-1
                            hero.hearts[num].st+=1
                            hero.hearts[num].update()
                            hero.life -= 1
                            # end game
                            if hero.life == 0: 
                                firebttn.parent.end_game(i+1)
                            break
                # recreate enemy if it leaves playing field
                level = self.level
                firebttn.parent.remove_widget(self)
                firebttn.parent.add_enemy(level)
            elif self.level == -1:
                # check for protected heroes as obstacles
                for hero in [hero1, hero2]:
                    if hero.protected:
                        future_pos = (self.center_x+0.09*a*dmoves[self.drct][0], self.center_y+0.09*a*dmoves[self.drct][1])
                        # check if future position is in protected area
                        if future_pos[0]<=hero.center_x+0.135*a and future_pos[0]>=hero.center_x-0.135*a and future_pos[1]<=hero.center_y+0.135*a and future_pos[1]>=hero.center_y-0.135*a:
                            if self.drct in ['0','2']:
                                new_drct = choice(['1','3'])
                            else:
                                new_drct = choice(['0','2'])
                            self.drct = new_drct
                            self.move(dkeys[self.drct])
                            break
                else:
                    for i, hero in enumerate([hero1, hero2]):
                        if hero.collide_point(self.center_x, self.center_y) and not self.used:
                            s_hit.play()
                            self.used = True
                            self.st = 7
                            self.update()
                            # make changes in hero's hearts
                            num = int(ceil(hero.life/2.))-1
                            hero.hearts[num].st+=1
                            hero.hearts[num].update()
                            hero.life -= 1
                            # end game
                            if hero.life == 0: 
                                firebttn.parent.end_game(i+1)
                            def move_after_biting(*args):
                                self.update()
                                self.move(dkeys[self.drct])
                            Clock.schedule_once(move_after_biting, 1.) # stay for 1 second
                            break
                    else:
                        self.move(dkeys[self.drct])
            elif self.check_vision_field()[0]: # target detected
                # create flame
                flame = Flame(self, (self.center_x, self.center_y), self.check_vision_field()[1])
                firebttn.parent.add_widget(flame)
                # change direction by 90 grad
                if self.drct in ['0','2']:
                    new_drct = choice(['1','3'])
                else:
                    new_drct = choice(['0','2'])
                self.drct = new_drct
                # move after 5 second when flame animation is completed
                Clock.schedule_once(partial(self.move, dkeys[self.drct]), 5.)
            else:
                # check for protected heroes as obstacles
                for hero in [hero1, hero2]:
                    if hero.protected:
                        future_pos = (self.center_x+0.09*a*dmoves[self.drct][0], self.center_y+0.09*a*dmoves[self.drct][1])
                        # check if future position is in protected area
                        if future_pos[0]<=hero.center_x+0.135*a and future_pos[0]>=hero.center_x-0.135*a and future_pos[1]<=hero.center_y+0.135*a and future_pos[1]>=hero.center_y-0.135*a:
                            if self.drct in ['0','2']:
                                new_drct = choice(['1','3'])
                            else:
                                new_drct = choice(['0','2'])
                            self.drct = new_drct
                            break
                else:
                    # change direction by 90 grad with probabilty depending on enemy's level
                    if self.level == 0:
                        chance = choice(range(30)) # 1/30
                    elif self.level == 1:
                        chance = choice(range(5)) # 1/5
                    if chance == 0:
                        if self.drct in ['0','2']:
                            new_drct = choice(['1','3'])
                        else:
                            new_drct = choice(['0','2'])
                        self.drct = new_drct
                self.move(dkeys[self.drct])
    def activate_update(self, *args):
        for i in range(10):
            Clock.schedule_once(self.update, i/10.)

class CtrlBttn(Button):
    def __init__(self, drct, **kwargs):
        super(CtrlBttn, self).__init__(**kwargs)
        self.name = drct
        if drct == 'left':
            self.pos_hint={'x':c_pos_x, 'y':c_pos_y+(65./164.)*c_size_y}
            self.size_hint = ((26./388.)*c_size_x+(42./164.)*c_size_y*Window.height/Window.width,(32./164.)*c_size_y) # 42*32 button, determine through y, extended
        elif drct == 'right':
            self.pos_hint={'x':c_pos_x+(97./388.)*c_size_x, 'y':c_pos_y+(65./164.)*c_size_y}
            self.size_hint = ((26./388.)*c_size_x+(44./164.)*c_size_y*Window.height/Window.width,(32./164.)*c_size_y) # 44*32 button, determine through y, extended
        elif drct == 'up':
            self.pos_hint={'x':c_pos_x+(65./388.)*c_size_x, 'y':c_pos_y+(97./164.)*c_size_y}
            self.size_hint = ((33./164.)*c_size_y*Window.height/Window.width,(44./164.)*c_size_y+(22./164.)*c_size_y) # 33*44 button, determine through y, extended
        elif drct == 'down':
            self.pos_hint={'x':c_pos_x+(65./388.)*c_size_x, 'y':c_pos_y}
            self.size_hint = ((33./164.)*c_size_y*Window.height/Window.width,(45./164.)*c_size_y+(22./164.)*c_size_y) # 33*45 button, determine through y, extended
        self.bind(on_press=self.append_moves) #call move_hero every 1. until touch_up
    def append_moves(self, *args):
        if self.parent.name == 'start_layout': # alternative actions on start screen
            if self.name == 'right':
                self.parent.parent.parent.current = 'highscore' # change current screenmanager's screen
            else: pass
        else:
            self.move_hero()
            Clock.schedule_interval(self.move_hero, 1./active_hero.speed) #append new moves every 1 second
    def move_hero(self, *args):
        if self.state == 'down':
            if not mflag:
                active_hero.st = 0
                active_hero.move(self.name)
            else:
                dkeys = {'0':'up', '1':'right', '2':'down', '3':'left'}
                if not dkeys[active_hero.drct] == 'down': # don't append commands if they lead down
                    if len(waiting) < 2: # maximal command waiting list length is 2
                        global waiting
                        waiting.append(self.name)
                    else:
                        pass
        else:
            return False # unschedule event

class BaseBttn(Button):
    def __init__(self, **kwargs):
        super(BaseBttn, self).__init__(**kwargs)
        self.size_hint = ((35./164.)*c_size_y*Window.height/Window.width,(35./164.)*c_size_y) # 36*36 button, determine through y
        self.pos_hint={'x':c_pos_x+(65./388.)*c_size_x, 'y':c_pos_y+(64./164.)*c_size_y}
        self.background_down = self.background_normal # disable color change
        self.name='basebttn'
        self.border=[0,0,0,0]
            
class Controller(Image):
    def __init__(self, **kwargs):
        super(Controller, self).__init__(**kwargs)
        self.source='controller.png'
        self.allow_stretch=True
        self.pos_hint={'x':c_pos_x, 'y':c_pos_y}
        self.size_hint=(c_size_x, c_size_y)
        self.name='controller'
    
class Cell(Widget):
    def __init__(self, pos_x, pos_y, p1, p2, color, **kwargs):
        super(Cell,self).__init__(**kwargs)
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(p1,p2)
        self.name = 'cell'
        if not hasattr(self, 'color'):
            with self.canvas:
                self.color = Color(color[0], color[1], color[2], 1)
                self.rect = Rectangle(size=(p1*Window.width, p2*Window.height), pos=(pos_x*Window.width,pos_y*Window.height))
        self.color.a = 1
        anim = Animation(a=0, t='in_quad', duration=.5)
        anim.start(self.color)
        Clock.schedule_once(self.die, .5) # vanishes after fade-out animation finishes
    def die(self, dt):
        active_hero.parent.remove_widget(self)
        
class FireBttn(Button):
    def __init__(self, **kwargs):
        super(FireBttn, self).__init__(**kwargs)
        self.size_hint = ((46./164.)*c_size_y*Window.height/Window.width,(41./164.)*c_size_y) #almost square button, determine size through y
        self.name = 'fire'
        self.fire_waiting = False # fire queue flag
        self.text = 'F'
        self.font_name = 'PressStart2P'
        self.font_size = '9sp'
        self.pos_hint={'x':c_pos_x+((279./388.)*c_size_x), 'y':c_pos_y+((106./164.)*c_size_y)}
        self.bind(on_press=self.schedule_fire)
    def schedule_fire(self, *args):
        if self.parent.name == 'start_layout': # alternative actions on start screen
            s_intro.stop()
            s_select.play()
            def play_sound(*args):
                s_game.play()
            def loop_sound(*args):
                Clock.schedule_interval(play_sound, .001)
            Clock.schedule_once(loop_sound, 2.)
            self.parent.parent.parent.current = 'blank screen' # change current screenmanager's screen
        elif game_ended:
            self.parent.restart(False)
        else:
            if not self.fire_waiting and not (active_hero.model == 'warrior_m' and active_hero.center_y > world_top - 0.09*a): # red fire prohibited at home
                self.fire_waiting = True
                for i in range(int(10./active_hero.speed)+1):
                    Clock.schedule_once(self.fire, i/10.)
                Clock.schedule_once(self.release_fire, 1./active_hero.speed)
    def release_fire(self, *args):
        self.fire_waiting = False
    def fire(self, *args):
        if tutorial_mode or (self.fire_waiting and active_hero.st == 0 
        and not anim_flag and not (active_hero.model == 'warrior_m' and 
        active_hero.y < world_bottom + 0.09*a) and not active_hero.protected): 
        # red fire prohibited at home and under protection
            if active_hero.model == 'warrior_m':
                color = [1, 0, 0]
            else: color = [0, 1, 0]
            def add(shifts_x, shifts_y):
                for shift_x, shift_y in zip(shifts_x, shifts_y):
                    # burn or grow trees, destroy enemies
                    if active_hero.model == 'warrior_m':
                        for wid in self.parent.children:
                            if wid.name == 'forest' or wid.name == 'enemy':
                                    if wid.collide_point(active_hero.x+shift_x*0.09*a+0.045*a, active_hero.y+shift_y*0.09*a+0.045*a):
                                        if wid.name == 'enemy':
                                            # remove flame produced by this enemy if it exists
                                            for w in firebttn.parent.children:
                                                if w.name == 'flame' and w.creator == wid:
                                                    firebttn.parent.remove_widget(w)
                                                    break
                                            # destroy enemy
                                            s_kill_enemy.play()
                                            firebttn.parent.remove_widget(wid)
                                            # add score
                                            scorer.score += 1
                                            scorer.update()
                                        elif wid.name == 'forest':
                                            wid.name = 'container' # turn forest into container
                                            wid.color = (0,0,0,0)
                                            wid.source = ''
                                            if not (shift_x == 0 and shift_y == 0): # disclose items with 1/2 probabilty when burning forest, not at hero's position
                                                chance = choice(range(2))
                                                if tutorial_mode: 
                                                    model = 'sword'
                                                else:
                                                    model = choice(['star','medikit', 'sword', 'potion', 'boots'])
                                                if chance == 0:
                                                    item = Item(model,(active_hero.x+shift_x*0.09*a+0.045*a)/Window.width, (active_hero.y+shift_y*0.09*a+0.045*a)/Window.height)
                                                    firebttn.parent.add_widget(item)
                                                    item.update()
                    else: # green fire
                        stop = False
                        for wid in self.parent.children:
                            if wid.name in ['forest', 'wall', 'home']:
                                if wid.collide_point(active_hero.x+shift_x*0.09*a+0.045*a, active_hero.y+shift_y*0.09*a+0.045*a):
                                    stop = True
                                    break
                        if not stop:
                            if active_hero.y+shift_y*0.09*a+0.045*a > world_top or active_hero.y+shift_y*0.09*a+0.045*a < world_bottom+0.09*a or active_hero.x+shift_x*0.09*a+0.045*a > world_right or active_hero.x+shift_x*0.09*a+0.045*a < world_left:
                                stop = True # creating forest outside playing field is forbidden
                        if not stop:
                            if active_hero.protected:
                                stop = True # hero can't do anything while protected
                        if not stop:
                            for wid in firebttn.parent.children:
                                if wid.name == 'container' and wid.collide_point(active_hero.x+shift_x*0.09*a+0.045*a, active_hero.y+shift_y*0.09*a+0.045*a): # turn container into forest
                                    wid.source = 'wall.png'
                                    wid.color=(0,.5,0,1)
                                    wid.name = 'forest'
                    cell = Cell(active_hero.pos_hint['x']+shift_x*0.09*a/Window.width, active_hero.pos_hint['y']+shift_y*0.09*a/Window.height, active_hero.size_hint[0], active_hero.size_hint[1], color)
                    active_hero.parent.add_widget(cell)
            s_fire.play()
            if active_hero.expanded_fire:
                add([-2,-1,0,1,2,0,0,0,0], [0,0,0,0,0,2,1,-1,-2]) # add light cross around a hero
            else:
                add([0,-1,1,0,0], [0,0,0,-1,1]) # add light cross around a hero
            self.fire_waiting = False
            # move active hero futher
            active_hero.before_move_next()
            # check fall for other hero
            for hero in [hero1, hero2]:
                if not hero == active_hero:
                    res = hero.check_fall()
                    if not res[0]: hero.fall(res[1])
                        
class ProtectBttn(Button):
    def __init__(self, **kwargs):
        super(ProtectBttn, self).__init__(**kwargs)
        self.size_hint = ((46./164.)*c_size_y*Window.height/Window.width,(41./164.)*c_size_y) #almost square button, determine size through y
        self.name = 'protect button'
        self.text = 'P'
        self.font_name = 'PressStart2P'
        self.font_size = '9sp'
        self.pos_hint={'x':c_pos_x+((236./388.)*c_size_x), 'y':c_pos_y+((64./164.)*c_size_y)}
        self.protect_waiting = False
        self.bind(on_press=self.schedule_protect)
    def schedule_protect(self, *args):
        if self.parent.name == 'start_layout': # alternative actions on start screen
            s_intro.volume = 0
            s_intro.stop()
            s_select.play()
            def play_sound(*args):
                s_game.play()
            def loop_sound(*args):
                Clock.schedule_interval(play_sound, .001)
            Clock.schedule_once(loop_sound, 2.)
            self.parent.parent.parent.current = 'blank screen' # change current screenmanager's screen
            global tutorial_mode
            tutorial_mode = True
        elif game_ended:
            App.get_running_app().stop() # quit game
        else:
            # schedule hero protection
            if not self.protect_waiting:
                self.protect_waiting = True
                for i in range(int(10./active_hero.speed)+1):
                    Clock.schedule_once(self.protect, i/10.)
    def protect(self, *args):
        if tutorial_mode or (self.protect_waiting and active_hero.st == 0 and not anim_flag):
            # 2 heroes can't be protected at the same time
            for hero in [hero1, hero2]:
                if hero.protected:
                    break
            else:
                # protect hero
                firebttn.parent.add_widget(ProtectionFrame(active_hero.pos_hint['x'], active_hero.pos_hint['y']))
                target_hero = active_hero
                target_hero.protected = True
                def unprotect_hero(*args):
                    target_hero.protected = False
                Clock.schedule_once(unprotect_hero, 5.) # unprotect hero after 5 seconds
                self.protect_waiting = False
    
class ProtectionFrame(Widget):
    def __init__(self, pos_x, pos_y, **kwargs):
        super(ProtectionFrame,self).__init__(**kwargs)
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(0.09*a/Window.width,0.09*a/Window.height)
        self.name = 'protection'
        self.center_x, self.center_y = pos_x*Window.width+0.045*a, pos_y*Window.height+0.045*a
        with self.canvas:
            self.color = Color(102./255.,217./255.,1.,1)
            Line(points=[self.center_x-0.09*a, self.center_y+0.09*a, self.center_x+0.09*a, self.center_y+0.09*a, self.center_x+0.09*a, self.center_y-0.09*a, self.center_x-0.09*a, self.center_y-0.09*a], width=5, cap='square', joint='miter', close=True)
        Clock.schedule_once(self.die, 5.) # protection ends after 5 seconds
    def die(self, dt):
        active_hero.parent.remove_widget(self)
            
class HeroSelector(ToggleButton):
    def __init__(self, pos_x, pos_y, **kwargs):
        super(HeroSelector, self).__init__(**kwargs)
        self.group = 'hero'
        self.size_hint = ((46./164.)*c_size_y*Window.height/Window.width,(41./164.)*c_size_y) #same size as firebttn
        self.name = 'selector'
        self.font_name = 'PressStart2P'
        self.disabled_color = (1,1,1,1)
        self.background_disabled_normal = self.background_normal
        self.font_size = '9sp'
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.bind(on_press=self.set_active_hero)
        self.allow_no_selection=False # one of heroes should always be chosen
    def set_active_hero(self, *args):
        if self.parent.name == 'start_layout': # alternative actions on start screen
            pass
        else:
            global waiting
            waiting = []
            global active_hero
            if self.text == 'H1':
                active_hero = hero1
            else:
                active_hero = hero2
            
class Scorer(Label):
    def __init__(self, **kwargs):
        super(Scorer, self).__init__(**kwargs)
        c_pos_x = (a-(b-1.25*a)*(388./164.))/(2.*Window.width)
        c_pos_y = 0.01*a/Window.height
        c_size_x = ((b-1.25*a)*388.)/(164.*Window.width)
        c_size_y = (b-1.25*a)/Window.height
        self.score=0 # game score
        self.name='scorer'
        self.text='score: '+str(self.score)
        self.font_name='PressStart2P'
        self.color=(0,0,0,1)
        self.pos_hint={'center_x': c_pos_x + c_size_x/2., 'center_y': c_pos_y + c_size_y*(130./164.)}
        self.font_size = '9sp'
    def update(self, *args):
        self.text='score: '+str(self.score)
        
class StartLayout(FloatLayout):
    def __init__(self, **kwargs):
        super(StartLayout, self).__init__(**kwargs)
        # add controls
        for i, drct in zip(range(4), ['up','down','left','right']):
            self.add_widget(CtrlBttn(drct))
        self.add_widget(BaseBttn())
        firebttn = FireBttn()
        self.add_widget(firebttn)
        hero1_selector = HeroSelector(text='H1', state='down', pos_x=c_pos_x+(279./388.)*c_size_x, pos_y=c_pos_y+(23./164.)*c_size_y)
        self.add_widget(hero1_selector)
        hero2_selector = HeroSelector(text='H2', pos_x=c_pos_x+(321./388.)*c_size_x, pos_y=c_pos_y+(64./164.)*c_size_y)
        self.add_widget(hero2_selector)
        protectbttn = ProtectBttn()
        self.add_widget(protectbttn)
        self.add_widget(Controller())

class TutorialHighlighter(Widget):
    def __init__(self, pos_x, pos_y, size_x, size_y, **kwargs):
        super(TutorialHighlighter, self).__init__(**kwargs)
        self.pos_hint={'x':pos_x, 'y':pos_y}
        self.size_hint=(size_x, size_y)
        self.name = 'highlighter'
        p_x, p_y, s_x, s_y = self.pos_hint['x']*Window.width, self.pos_hint['y']*Window.height, self.size_hint[0]*Window.width, self.size_hint[1]*Window.height
        with self.canvas:
            self.color = Color(102./255.,217./255.,1.,1)
            Line(points=[p_x, p_y, p_x, p_y+s_y, p_x+s_x, p_y+s_y, p_x+s_x, p_y], width=2, cap='square', joint='miter', close=True) # draw rectangle of lines
    def die(self, dt):
        firebttn.parent.remove_widget(self)
        
class Game(FloatLayout):
    def restart(self, fixed, *args):
        self.clear_widgets()
        self.__init__(fixed)
        global game_ended
        game_ended = False
        global mflag
        mflag = False
        global anim_flag
        anim_flag = False
        global waiting
        waiting = []
        s_game.volume = 1
        s_game.play()
    def __init__(self, fixed=True, **kwargs):
        super(Game, self).__init__(**kwargs)
        self.name = 'game layout'
        p1, p2 = a*0.18/Window.width, a*0.18/Window.height
        m = a*0.05
        if fixed: 
            seed(1) # set 0 random seed for reproducible results in random numbers generator
        else:
            seed()
        # add landscape containers for area where forest can emerge (10x10)
        for i in range(10):
            for j in range(10):
               pos_x = (m + 0.09*a*i)/Window.width 
               pos_y = (b-(3*m + 0.18*a + 0.09*a*j))/Window.height
               c = Container(pos_x, pos_y, p1/2., p2/2.)
               self.add_widget(c)
        # add landscape
        for i in range(3):
            for j in range(3): 
                pos_x = (m + 0.36*a*i)/Window.width
                pos_y = (b-(3*m + 0.27*a + 0.36*a*j))/Window.height
                l = Wall(pos_x, pos_y, p1, p2)
                self.add_widget(l)
        for n in range(50):
            c = []
            while True:
                i, j = choice(range(10)), choice(range(10))
                if i in [2,3,6,7] or (i in [0,1,4,5,8,9] and j in [2,3,6,7]):
                    if not (i,j) in c:
                        c.append((i,j))
                        break
            for wid in self.children: # turn container to forest
                if wid.name == 'container' and wid.pos_hint['x'] == (m+0.09*a*i)/Window.width and wid.pos_hint['y'] == (b-(3*m+0.18*a+0.09*a*j))/Window.height:
                    wid.source = 'wall.png'
                    wid.color=(0,.5,0,1)
                    wid.name = 'forest'
        for i in range(10):
            self.add_widget(HomeTile((m+0.09*a*i)/Window.width, (b-0.24*a)/Window.height, p1/2., p2/2.))
            self.add_widget(HomeLabel(m/Window.width, (b-0.2775*a)/Window.height, p1/2., (p2*(15/27.))/2.))
            self.add_widget(Spikes((m+0.09*a*i)/Window.width, (b-(3*m+1.08*a))/Window.height, p1/2., p2/2.))
        # add heroes and place them on home tiles randomly
        c1 = choice(range(10)) # avoid placing place heroes at the same position
        c2 = c1
        while c1 == c2:
            c2 = choice(range(10))
        global hero1 
        hero1 = Hero('warrior_m', (m+0.09*a*c1)/Window.width, (b-0.24*a)/Window.height, p1/2., p2/2.)
        self.add_widget(hero1)
        global hero2
        hero2 = Hero('healer_f_green', (m+0.09*a*c2)/Window.width, (b-0.24*a)/Window.height, p1/2., p2/2.)
        self.add_widget(hero2)
        # set active hero
        global active_hero
        active_hero = hero1
        # add controls
        global up_bttn
        up_bttn = CtrlBttn('up')
        global down_bttn
        down_bttn = CtrlBttn('down')
        global left_bttn
        left_bttn = CtrlBttn('left')
        global right_bttn
        right_bttn = CtrlBttn('right')
        for bttn in [up_bttn, down_bttn, left_bttn, right_bttn]:
            self.add_widget(bttn)
        self.add_widget(BaseBttn())
        global firebttn
        firebttn = FireBttn() # anchor widget to determine Game class instance as its parent
        self.add_widget(firebttn)
        global hero1_selector
        hero1_selector = HeroSelector(text='H1', state='down', pos_x=c_pos_x+(279./388.)*c_size_x, pos_y=c_pos_y+(23./164.)*c_size_y)
        self.add_widget(hero1_selector)
        global hero2_selector 
        hero2_selector = HeroSelector(text='H2', pos_x=c_pos_x+(321./388.)*c_size_x, pos_y=c_pos_y+(64./164.)*c_size_y)
        self.add_widget(hero2_selector)
        global protectbttn
        protectbttn = ProtectBttn()
        self.add_widget(protectbttn)
        # add new enemy every 10 seconds if conditions are met
        if not tutorial_mode:
            Clock.schedule_interval(self.control_enemies_number, 10.)
        # add hearts
        for i in range(6):
            if i<3: 
                hero_num = 1
                hero_obj = hero1
            else: 
                hero_num = 2
                hero_obj = hero2
            heart = Heart(i%3, hero_num)
            hero_obj.hearts.append(heart)
            self.add_widget(heart)
        # add controller
        global controller
        controller = Controller()
        self.add_widget(controller)
        # add scorer
        global scorer
        scorer = Scorer()
        self.add_widget(scorer)
    def add_enemy(self, level, *args):
        p1, p2 = a*0.18/Window.width, a*0.18/Window.height
        free_pos = choice(['x','y'])
        for hero in [hero1, hero2]:
            if hero.protected:
                p = (hero.center_x, hero.center_y)
                break
        else:
            p = (0,0)
        if free_pos == 'x':
            border = choice([(world_bottom+0.09*a)/Window.height, (world_top-2*0.09*a)/Window.height])
            while True:
                pos_x, pos_y = (0.05*a+randint(0,9)*0.09*a)/Window.width, border
                center_x, center_y = pos_x*Window.width+0.045*a, pos_y*Window.height+0.045*a
                if p == (0,0):
                    break
                elif not ((center_x >= p[0]-0.135*a) and (center_x <= p[0]+0.135*a) and (center_y <= p[1]+0.135*a) and (center_y >= p[1]-0.135*a)): # check if starting position goes into protected area
                    break
            if border == (world_top-2*0.09*a)/Window.height: 
                drct = 'down'
            else: 
                drct = 'up'
        else:
            border = choice([(world_left-0.09*a)/Window.width, world_right/Window.width])
            while True:
                pos_x, pos_y = border, (world_top-randint(2,10)*0.09*a)/Window.height
                center_x, center_y = pos_x*Window.width+0.045*a, pos_y*Window.height+0.045*a
                if p == (0,0):
                    break
                elif not ((center_x >= p[0]-0.135*a) and (center_x <= p[0]+0.135*a) and (center_y <= p[1]+0.135*a) and (center_y >= p[1]-0.135*a)): # check if starting position goes into protected area
                    break
            if border == (world_left-0.09*a)/Window.width: 
                drct = 'right'
            else: 
                drct = 'left'
        if level == 0:
            model = 'firehead'
        elif level == 1:
            model = 'gashead'
        else:
            model = 'bat'
        enemy = Enemy(model, level, pos_x, pos_y, p1/2., p2/2.)
        self.add_widget(enemy)
        enemy.move(drct)
    def control_enemies_number(self, *args):
        if (not game_ended) and (not tutorial_mode):
            c=0 # enemies counter
            for wid in self.children:
                if wid.name == 'enemy':
                    c+=1
            if c<3+int(scorer.score/20.): # max 3 enemies simultaneously (and then more)
                chances = [(50, 10), (70, 5), (100, 4), (120, 3), (150, 2)] # upper bound - prob range
                if scorer.score < 30:
                    level =  choice([0,-1]) # zero level 1 probability
                elif scorer.score >= 150:
                    level = 1 # always create level 1 enemies
                else:
                    for e in chances:
                        if scorer.score < chances[0]:
                            chance = choice(range(chances[1]))
                            if chance == 0:
                                level = 1
                            else:
                                level = choice([0,-1])
                            break
                self.add_enemy(level)
        else:
            return False # unschedule event
    def end_game(self, hero_num, *args):
        global game_ended
        game_ended = True
        self.export_to_png('endscreen.png')
        self.clear_widgets()
        self.add_widget(Image(source='endscreen.png', color=(0,1,0,0.99)))
        heart = Heart(0, hero_num)
        heart.source = join("hearts","2.png")
        heart.color=(0,1,0,0.99)
        self.add_widget(heart)
        self.add_widget(GameOverLabel())
        # add controls
        for i, drct in zip(range(4), ['up','down','left','right']):
            self.add_widget(CtrlBttn(drct))
        self.add_widget(BaseBttn())
        firebttn = FireBttn()
        self.add_widget(firebttn)
        hero1_selector = HeroSelector(text='H1', state='down', pos_x=c_pos_x+(279./388.)*c_size_x, pos_y=c_pos_y+(23./164.)*c_size_y)
        self.add_widget(hero1_selector)
        hero2_selector = HeroSelector(text='H2', pos_x=c_pos_x+(321./388.)*c_size_x, pos_y=c_pos_y+(64./164.)*c_size_y)
        self.add_widget(hero2_selector)
        protectbttn = ProtectBttn()
        self.add_widget(protectbttn)
        self.add_widget(Controller(color=(0,1.,0,1.)))
        s_game.volume=0
        s_game.stop()
        s_evil.play()
        # save highscore
        timestamp = datetime.strftime(datetime.now(), '%Y-%m-%d %H:%M')
        score = str(scorer.score)
        storage.put('highscore', score = score, datetime = timestamp)
    def show_tutorial(self, *args):
        global tutorial_label
        tutorial_label = TutorialLabel('hero 1 (male)\nis set active\nwhen game starts')
        firebttn.parent.add_widget(tutorial_label)
        def step_0(*args):
            tutorial_label.text='you can see his life\nindicators (hearts) in\nthe upper left corner'
            tutorial_label.draw()
            m_x, m_y = 5./Window.width, 5./Window.height # margins
            pos_x = hero1.hearts[0].pos_hint['x']-m_x
            pos_y = hero1.hearts[0].pos_hint['y']-m_y
            size_x = hero1.hearts[2].pos_hint['x']-hero1.hearts[0].pos_hint['x']+hero1.hearts[2].size_hint[0]+2*m_x
            size_y = hero1.hearts[0].size_hint[1]+2*m_y
            highlighter = TutorialHighlighter(pos_x, pos_y, size_x, size_y)
            self.add_widget(highlighter)
            Clock.schedule_once(highlighter.die, 5.) # remove highlighter
        def step_1(*args):
            tutorial_label.text='you start at home\n(upper green row)\nwhere you are safe'
            tutorial_label.draw()
            m_x, m_y = 5./Window.width, 5./Window.height
            pos_x = hero1.pos_hint['x']-(0.09*a/Window.width)-m_x
            pos_y = hero1.pos_hint['y']-m_y
            size_x = 0.9*a/Window.width+2*m_x
            size_y = hero1.size_hint[1]+2*m_y
            highlighter = TutorialHighlighter(pos_x, pos_y, size_x, size_y)
            self.add_widget(highlighter)
            Clock.schedule_once(highlighter.die, 5.) # remove highlighter
        def step_2(*args):
            tutorial_label.text='use gamepad arrow\nkeys to move hero'
            tutorial_label.draw()
        def step_3(*args):
            right_bttn.state='down'
            hero1.move('right')
        def step_4(*args):
            right_bttn.state='normal'
            down_bttn.state='down'
            hero1.move('down')
        def step_5(*args):
            down_bttn.state='normal'
            tutorial_label.text='press F to create\nred fire around hero'
            tutorial_label.draw()
            firebttn.state='down'
        def step_6(*args):
            firebttn.fire()
            firebttn.state='normal'
        def step_7(*args):
            tutorial_label.text='red fire destroys\nenemies and burns\ntrees. you cannot\nuse it at home'
            tutorial_label.draw()
        def step_8(*args):
            tutorial_label.text='items can be\ndiscovered when\nburning trees\n(now a sword)'
            tutorial_label.draw()
        def step_9(*args):
            tutorial_label.text='press H2 to activate\nhero 2 (female)\nher life indicators\nare now highlighted'
            tutorial_label.draw()
            m_x, m_y = 5./Window.width, 5./Window.height # margins
            pos_x = hero2.hearts[0].pos_hint['x']-m_x
            pos_y = hero2.hearts[0].pos_hint['y']-m_y
            size_x = hero2.hearts[2].pos_hint['x']-hero2.hearts[0].pos_hint['x']+hero2.hearts[2].size_hint[0]+2*m_x
            size_y = hero2.hearts[0].size_hint[1]+2*m_y
            highlighter = TutorialHighlighter(pos_x, pos_y, size_x, size_y)
            self.add_widget(highlighter)
            Clock.schedule_once(highlighter.die, 5.) # remove highlighter
            hero1_selector.state='normal'
            hero2_selector.state='down'
            global active_hero
            active_hero = hero2
        def step_10(*args):
            tutorial_label.text='grab items to gain\nextra powers\n(a sword expands\nyour fire range)'
            tutorial_label.draw()
            down_bttn.state='down'
            hero2.move('down')
        def step_11(*args):
            tutorial_label.text='hero 2 produces\ngreen fire which\ncan grow forests'
            tutorial_label.draw()
            down_bttn.state='normal'
            firebttn.state='down'
            firebttn.fire()
        def step_12(*args):
            firebttn.state='normal'
            tutorial_label.text='forests are used\nby both heroes\nfor walking'
            tutorial_label.draw()
        def step_13(*args):
            tutorial_label.text='hero falls while\nnot in a forest\nand does not stand\non a rock'
            tutorial_label.draw()
        def step_14(*args):
            tutorial_label.text='press P to protect\nactive hero from\nenemies for some time'
            tutorial_label.draw()
            protectbttn.state='down'
            protectbttn.protect()
        def step_15(*args):
            protectbttn.state='normal'
            tutorial_label.text='you can only protect\none hero at any\ngiven moment'
            tutorial_label.draw()
        def step_16(*args):
            tutorial_label.text='avoid falling on\nspikes or you\nlose one life'
            tutorial_label.draw()
            m_x, m_y = 5./Window.width, 5./Window.height
            pos_x = hero1.pos_hint['x']-(2*0.09*a/Window.width)-m_x
            pos_y = hero1.pos_hint['y']-m_y-(0.72*a/Window.height)
            size_x = 0.9*a/Window.width+2*m_x
            size_y = hero1.size_hint[1]+2*m_y
            highlighter = TutorialHighlighter(pos_x, pos_y, size_x, size_y)
            self.add_widget(highlighter)
            Clock.schedule_once(highlighter.die, 5.) # remove highlighter
        def step_17(*args):
            tutorial_label.text='if one of the heroes\ndies the game is over'
            tutorial_label.draw()
        def step_18(*args):
            tutorial_label.text='you can increase\nyou score by\nkilling enemies'
            tutorial_label.draw()
        def step_19(*args):
            tutorial_label.text='when you reach 100\nscore points you win\nand you land is\nfree again!'
            tutorial_label.draw()
        def step_20(*args):
            tutorial_label.text='you are now ready\nto play. the game\nwill start in\na few seconds'
            tutorial_label.draw()
        def step_21(*args):
            global tutorial_mode
            tutorial_mode = False
            self.restart(False)
        steps = [(5, step_0), (8, step_1), (3, step_2), (3, step_3),
                 (3, step_4), (3, step_5), (3, step_6), (8, step_7), 
                 (8, step_8), (8, step_9), (8, step_10), (6, step_11),
                 (4, step_12), (8, step_13), (8, step_14), 
                 (6, step_15), (8, step_16), (5, step_17), (5, step_18),
                 (8, step_19), (6, step_20), (0, step_21)]
        time = 5
        for step in steps:
            Clock.schedule_once(step[1], time)
            time += step[0]
               
class MainFrame(ScreenManager):
    def __init__(self, **kwargs):
        super(MainFrame, self).__init__(**kwargs)
        self.transition = NoTransition()
        if s_intro:
            s_intro.play()

class Dyna(App):
    def build(self):
        return MainFrame()
    # pause/restore application
    def on_pause(self):
        s_game.volume = 0
        s_evil.volume = 0
        s_intro.volume = 0
        return True
    def on_resume(self):
        s_game.volume = 1
        s_evil.volume = 1
        s_intro.volume = 1
        pass
    def on_stop(self):
        exit()

if __name__ == '__main__':
    Dyna().run()