import sys
import pygame
import time
import re
from time import localtime
import os.path
import random
from random import shuffle

from tile import *

COLOR_BLACK = (0,0,0)
COLOR_WHITE = (255,255,255)
def is_in(x,y, rect):
  if x >= rect[0] and x <= rect[0]+rect[2] and \
     y >= rect[1] and y <= rect[1]+rect[3]:
    return True

  return False

def render_black_bars(screen):
  pygame.draw.rect(screen,(0,0,0), (0,0,800,80))
  pygame.draw.rect(screen,(0,0,0), (0,520,800,80)) 
  
def get_string_surf(font, text, color=COLOR_BLACK):
  "Used in lazy-man text-writing :)"
  return font.render(text, True, color)
  
def render_text(screen, font, text, x,y,w,h, color=COLOR_BLACK):
  "Lazy-man text-writing."
  screen.blit(get_string_surf(font, text, color=color), (x,y,w,h))

def load_level(filename, rnd=False, enforceTwo=False):
  "Loads a level from a text file. If the random flag is set to True \
   then all tiles are simply random, otherwise use the files data. "
   
  try:
    fh = open(os.path.abspath('levels/' + filename), 'r')
  except IOError as e:
    open(os.path.abspath('levels/' + filename), 'a')
  
  fh = open(os.path.abspath('levels/' + filename), 'r')
  if fh:
    text = fh.read()
    tiles = []
    for no,x,y,z in re.findall('[(](\d+),(\d+),(\d+),(\d+)[))]', text):
     tiles.append(Tile(int(no),int(x),int(y),int(z)))
    
    if enforceTwo and len(tiles) % 2 == 0:
      print ('You are enforcing divisible by two tile rule, and there are an uneven amount of tiles.')
      return []
    
    if rnd:
      random.seed()
      for tile in range(0,len(tiles)-1,2):
        no = random.choice(range(1,16,1))
        tiles[tile] = Tile(no, tiles[tile].x, tiles[tile].y, tiles[tile].z)
        tiles[tile+1] = Tile(no, tiles[tile+1].x, tiles[tile+1].y, tiles[tile+1].z)
      
      
      shuffle_tiles(tiles)
    
    return tiles
      
  return []
  
class Game:    
  def __init__(self, player_name='Player', editor=False, sound=True, filename=None):
  
    # If true, editor is running, if not then 
    # we begin in the menu like normal.
    if editor:  
      self.state = 'playing'
      self.filename = filename
      self.tiles = load_level(filename, rnd=(not editor))
      self.start_piece_count = len(self.tiles)
    else:
      self.state = 'menu' 
      
    self.pieces_removed = 0                         
    self.selected = None                             
    self.time_started = pygame.time.get_ticks()     
    self.m_selector = 0                             
    self.sound_on = sound                           
    self.editor = editor                            
    self.viewing_highscores_for = None              
    self.player_name = player_name                  

    self.resources = { 'pause'      : pygame.image.load(os.path.abspath('res/icons/pause.png')),     \
                       'back'       : pygame.image.load(os.path.abspath('res/icons/back.png')),      \
                       'play'       : pygame.image.load(os.path.abspath('res/icons/play.png')),      \
                       'sound_on'   : pygame.image.load(os.path.abspath('res/icons/sound_on.png')),  \
                       'sound_off'  : pygame.image.load(os.path.abspath('res/icons/sound_off.png')), \
                       'sfx_select' : pygame.mixer.Sound( os.path.abspath('res/sfx/select.wav')),    \
                       'sfx_back'   : pygame.mixer.Sound( os.path.abspath('res/sfx/back.wav')),      \
                       'sfx_switch' : pygame.mixer.Sound( os.path.abspath('res/sfx/switch.wav'))     \
    }
    
    self.render_func = { 'playing'        : self.render_playing,         \
                         'menu'           : self.render_menu,            \
                         'level_select'   : self.render_level_select,    \
                         'paused'         : self.render_paused,          \
                         'level_complete' : self.render_level_complete,  \
                         'highscores'     : self.render_highscores       \
    }


    self.input_handlers = { 'playing'        : self.handle_playing_input,        \
                            'menu'           : self.handle_menu_input,           \
                            'level_select'   : self.handle_level_select_input,   \
                            'paused'         : self.handle_paused_input,         \
                            'level_complete' : self.handle_level_complete_input, \
                            'highscores'     : self.handle_highscores_input      \
    }

    
    self.fontpath = os.path.abspath('res/C_BOX.TTF')   
    self.font = pygame.font.Font(self.fontpath, 30, bold=True)    
     
  def write_score(self):
    "Writes player score to file for the current level they just completed. "
    scorepath = os.path.abspath('levels/scores/' + self.filename)
    scores = []
    
    try:
      fh = open(scorepath, 'r')
      scores = fh.read()
      scores = re.findall('[(](\w*),(\w*)[)]', scores)
      fh.close()
    except IOError:
      print ("Score file doesn't yet exist, creating...")
      
    scores.append((self.player_name,(pygame.time.get_ticks() - self.time_started)/1000))
    if scores:
      scores = sorted(scores, key=lambda s: int(s[01]))
      
    fh = open(scorepath, 'w')
    i = 0
    for score in scores:
      fh.write('('+str(score[0])+','+str(score[1])+')')
      if i < 4:
        i += 1
      else:
        fh.close()
        return
        
    fh.close()      
          
  def handle_input(self, event):
    "Based on the games current state, manage our mouse input."
    if self.editor:
      if  event.type == pygame.MOUSEBUTTONDOWN:
        self.place_tile(event)
      elif event.type == pygame.MOUSEMOTION:
        self.move_tile_cursor(event)
      elif event.type == pygame.KEYDOWN:
        self.select_cursor_tile(event)
        
      return
    

    if self.state in self.input_handlers:
      self.input_handlers[self.state](event)
         
  def render(self, screen):
    "Based on the games state, call the appropriate drawing methods"
    if self.state in self.render_func:     
      screen.fill((255,255,255))
      self.render_func[self.state](screen)
      
    if self.editor:
      self.draw_tile_cursor(screen)  


  def handle_menu_input(self, event):
    if event.type == pygame.MOUSEMOTION:
      x,y = pygame.mouse.get_pos()
      for i in range(4):
        if is_in(x,y,(310, 200+42*i, 250, 30)):
          if not i == self.m_selector:
            if self.sound_on:
             self.resources['sfx_switch'].play()
            self.m_selector = i

    if event.type == pygame.MOUSEBUTTONDOWN:
      x,y = pygame.mouse.get_pos()
      self.sound_toggle_check(event)
      for i in range(5):
        if is_in(x,y,(310, 200+42*i, 250, 30)):
          if self.sound_on:
            self.resources['sfx_select'].play()
          self.m_selector = i
          if i == 0:
            self.state = 'level_select'
            return
          elif i == 1:
            self.state = 'highscores'
            return
          elif i == 4:
            sys.exit()
            return
      
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_DOWN:
        if self.sound_on:   
          self.resources['sfx_switch'].play()
        if self.m_selector == 3:
          self.m_selector = 0
        else:
          self.m_selector += 1
          
      if event.key == pygame.K_UP:
        if self.sound_on:
          self.resources['sfx_switch'].play()
        if self.m_selector == 0:
          self.m_selector = 3
        else:
          self.m_selector -= 1
        
      if event.key == pygame.K_RETURN:
        if self.sound_on:
          self.resources['sfx_select'].play()
        if self.m_selector == 0:
          self.state = 'level_select'
          self.m_selector = 0
        if self.m_selector == 1:
          self.state = 'highscores'
          self.m_selector = 0
          
        if self.m_selector == 3:
          sys.exit()
        
      if event.key == pygame.K_ESCAPE:
        if self.sound_on:
          self.resources['sfx_back'].play()
        sys.exit()
          
  def handle_playing_input(self, event):
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        if self.sound_on:
          self.resources['sfx_back'].play()
        if not self.editor:
          self.state = 'level_select'
        else:
          sys.exit()
        return
      
    if event.type == pygame.MOUSEBUTTONDOWN:
      backrect  = (720, 16, 32, 32)
      pauserect = (760, 16, 32, 32)
      x,y = event.pos
      if is_in(x,y,backrect):
        if self.sound_on:
          self.resources['sfx_back'].play()
        self.state = 'level_select'
        return
      if is_in(x,y,pauserect):
        self.state = 'paused'
        self.paused_at = pygame.time.get_ticks()
        return

      self.sound_toggle_check(event)


      for tile in sorted(self.tiles, key=byTopRight, reverse=True) :
          x,y = event.pos
          if x >= tile.x - tile.z * 3 and x <= tile.x + 40 - tile.z * 3 and \
             y >= tile.y - tile.z * 3 and y <= tile.y + 60 - tile.z * 3:
             if self.selected == tile: 
              self.selected = None
              return
             if self.selected: 
              if self.selected.tileno == tile.tileno:     
                if not tile.is_blocked(self.tiles) and not self.selected.is_blocked(self.tiles):
                  self.tiles.remove(self.selected)
                  self.tiles.remove(tile)
                  self.pieces_removed += 2
                  
                  # If we won!
                  if len(self.tiles) == 0:
                    self.state = 'level_complete'
                    self.score = str((pygame.time.get_ticks()-self.time_started)/1000)
                    pygame.event.clear()
                    
                    self.write_score()
                    return
                self.selected = None
                return
              else:
                self.selected = None
                return
             else:
              if not tile.is_blocked(self.tiles):
                self.selected = tile       
             return
             
             
      self.selected = None    
   
  def handle_level_select_input(self, event):

    levels = os.listdir(os.path.abspath('levels/'))
    max = len(levels)-1 
    
    if 'scores' in levels:
      levels.remove('scores')

    if event.type == pygame.MOUSEMOTION:
      for i in range(len(levels)):
        x,y = pygame.mouse.get_pos()        
        if is_in(x,y,(310, 200 + i * 50, 300, 30)):
          if not i == self.m_selector:
            if self.sound_on:
              self.resources['sfx_switch'].play()
            self.m_selector = i
            return
      if is_in(x,y,(310, 100, 300, 30)):
        if not self.m_selector == len(levels):
          if self.sound_on:
            self.resources['sfx_switch'].play()
          self.m_selector = len(levels)

    if event.type == pygame.MOUSEBUTTONDOWN:
      for i in range(len(levels)):
        x,y = pygame.mouse.get_pos()        
        if is_in(x,y,(310, 200 + i * 50, 300, 42)):
          if self.sound_on:
            self.resources['sfx_select'].play()
          self.state = 'playing'     
          self.time_started = pygame.time.get_ticks()
          self.pieces_removed = 0
          self.tiles = load_level(filename=levels[self.m_selector], rnd=True)
          self.filename = levels[self.m_selector]
          self.start_piece_count = len(self.tiles)

      if is_in(x,y,(310, 100, 300, 84)):
        if self.sound_on:
          self.resources['sfx_back'].play()
        self.state = 'menu'
        self.m_selector = 0
        return

      self.sound_toggle_check(event)

    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        if self.sound_on:
          self.resources['sfx_back'].play()
        self.state = 'menu'
        self.m_selector = 0
        return
      elif event.key == pygame.K_UP:
        if self.sound_on:
          self.resources['sfx_switch'].play()
        if self.m_selector == 0:
          self.m_selector = max
        else:
          self.m_selector -= 1
      elif event.key == pygame.K_DOWN:
        self.resources['sfx_switch'].play()
        if self.m_selector == max:
          self.m_selector = 0
        else:
          self.m_selector += 1  
      elif event.key == pygame.K_RETURN:
        if self.m_selector == max:
          if self.sound_on:
            self.resources['sfx_back'].play()
          self.state = 'menu'
          self.m_selector = 0
          return
        
        if self.sound_on:
          self.resources['sfx_select'].play()
        self.state = 'playing'     
        self.time_started = pygame.time.get_ticks()
        self.pieces_removed = 0
        self.tiles = load_level(filename=levels[self.m_selector], rnd=True)
        self.filename = levels[self.m_selector]
        self.start_piece_count = len(self.tiles)        
  
  def handle_level_complete_input(self, event):
    if event.type == pygame.MOUSEBUTTONDOWN:
      self.state = 'level_select'
      self.selected = None
  
  def handle_paused_input(self, event):
    if event.type == pygame.MOUSEBUTTONDOWN:
      backrect  = (720, 16, 32, 32)
      pauserect = (760, 16, 32, 32)
      x,y = event.pos

      self.sound_toggle_check(event)

      if is_in(x,y,backrect):
        self.state = 'level_select'
        
      if is_in(x,y,pauserect):
        self.state = 'playing'
        self.time_started += (pygame.time.get_ticks() - self.paused_at)
      
    
    
  def handle_highscores_input(self, event):
    if event.type == pygame.KEYDOWN:
      if event.key == pygame.K_ESCAPE:
        self.state = 'menu'
        
      if event.key == pygame.K_LEFT or \
         event.key == pygame.K_RIGHT:
      
        levels = os.listdir(os.path.abspath('levels/scores'))
        max = len(levels)
        if self.viewing_highscores_for:
          selected = levels.index(self.viewing_highscores_for)
          if not selected == None:
            if event.key == pygame.K_LEFT:
              if selected == 0:
                selected = max-1
              else:
                selected -= 1
            elif event.key == pygame.K_RIGHT:
              if selected == max-1:
                selected = 0
              else:
                selected += 1

            self.viewing_highscores_for = levels[selected]
  
  def render_highscores(self, screen):
    pygame.draw.rect(screen,(0,0,0), (0,0,800,80))
    pygame.draw.rect(screen,(0,0,0), (0,520,800,80))   
    render_text(screen, self.font, "Vanessa's Mahjong", (20,20,300,300), color=(255,74,203))
    render_text(screen, self.font, "Highscores...", (20,540,200,100), color=(255,74,203))
    render_text(screen, self.font, "Left/Right to Cycle", (450,20,300,300), color=(255,74,203))
    
    if self.viewing_highscores_for:
      scorepath = os.path.abspath('levels/scores/' + self.viewing_highscores_for)
      fh = open(scorepath, 'r')
      if fh:
        text = fh.read()
        scores = re.findall('[(](\w+),(\d+)[)]', text)
        
        render_text(screen, self.font, self.viewing_highscores_for,( 300,125,300,300))
        i = 1
        for score in scores:
          render_text(screen, self.font, score[0]+' - '+score[1] + ' seconds...',( 325,125+i*50,350,300))
          i += 1
    else:
      levels = os.listdir(os.path.abspath('levels/scores/'))
      
      if 'scores' in levels:
        levels.remove('scores')
      
      if len(levels) > 0:
        self.viewing_highscores_for = levels[0]
      else:
        render_text(screen, self.font, "You have no high scores yet.", (200,255,30,300))
      
  def render_level_complete(self, screen):
    rose = pygame.image.load('res/rose.jpg')
    roserect = (220,120,318,350)
    screen.blit(rose,roserect)
    render_black_bars(screen)

    render_text(screen, self.font,"Click for next level...", (450,540,200,100), color=(255,74,203))
    render_text(screen, self.font,  str(self.score) + " seconds, sweet!", (20,20,300,300), color=(255,74,203))
      
  def render_playing(self,screen):
    render_black_bars(screen)
    
    if self.editor:
      render_text(screen, self.font, "Level Editor", (20,20,300,300), color=(255,74,203))
      render_text(screen, self.font, "S = save, U = undo", (500,20,300,300), color=(255,74,203))
      render_text(screen, self.font, "Editing: " + self.filename, (20,520,200,100), color=(255,74,203))
      render_text(screen, self.font, "Pieces Placed: " + str(len(self.tiles)), (20,560,200,100), color=(255,255,255,))
    else:
      render_text(screen, self.font, "Vanessa's Mahjong", (20,20,300,300), color=(255,74,203))
      render_text(screen, self.font, "Pieces Removed: ", (20,540,200,100), color=(255,74,203))
      render_text(screen, self.font, str(self.pieces_removed) + ' of ' + str(self.start_piece_count), (300,540,200,50), color=(255,255,255))
      screen.blit(self.resources['back'], (720, 16, 32, 32))
      if self.state == 'playing':
        screen.blit(self.resources['pause'], (760, 16, 32, 32))
        render_text(screen, self.font, "Time Elapsed: ", (470, 540, 100,100), color=(255,74,203))
        render_text(screen, self.font, str(int((pygame.time.get_ticks()  - self.time_started) / 1000)), \
                    (705, 540, 100,100), color=(255,255,255))
      elif self.state == 'paused':
        screen.blit(self.resources['play'], (760, 16, 32, 32))
        render_text(screen, self.font, "Paused", (470, 540, 100,100), color=(255,255,255))

    self.blit_sound_icon(screen)

    for tile in self.tiles:
      if self.state == 'paused':
        tile.draw(screen, paused=True)
      else:
        tile.draw(screen)
 
      if self.selected: 
        pygame.draw.rect(screen, (255,0,0), (self.selected.x - self.selected.z * 3, \
                                             self.selected.y - self.selected.z * 3, 40-2, 60-2),2)

  def blit_sound_icon(self, screen):
    if self.sound_on:
      screen.blit(self.resources['sound_on'], (680, 16))
    else:
      screen.blit(self.resources['sound_off'], (680, 16))

  def sound_toggle_check(self, event):
    x,y = event.pos
    if x >= 680 and x <= 712 and y >= 16 and y <= 48:
      self.sound_on = not self.sound_on

  def render_menu(self, screen):
    pygame.draw.rect(screen,(0,0,0), (0,0,800,80))
    pygame.draw.rect(screen,(0,0,0), (0,520,800,80))   
    render_text(screen, self.font, "Vanessa's Mahjong", (20,20,300,300), color=(255,74,203))
    render_text(screen, self.font, "New Game", (310, 200, 300, 300))
    render_text(screen, self.font, "High Scores", (310, 250, 300, 300))
    render_text(screen, self.font, "Settings", (310, 300, 300, 300))
    render_text(screen, self.font, "Exit Game", (310, 350, 300, 300))
    render_text(screen, self.font, "-", (280, 200 + self.m_selector * 50, 300, 300))
    self.blit_sound_icon(screen)
    
  def render_level_select(self, screen):
    render_black_bars(screen)  
    render_text(screen, self.font, "Vanessa's Mahjong", (20,20,300,300), color=(255,74,203))
    render_text(screen, self.font, "Select a level...", (20,540,200,100), color=(255,74,203))
    i = 0
    levels = os.listdir(os.path.abspath('levels/'))
    for level in levels:
      if level == 'scores':
        continue
      render_text(screen, self.font, level, (310, 200 + i * 50, 300, 300))
      i += 1
    render_text(screen, self.font, "BACK", (310, 100, 300, 300))
    if self.m_selector == len(levels)-1:
      render_text(screen, self.font, "-", (280, 100, 300, 300 ))
    else:
      render_text(screen, self.font, "-", (280, 200 + self.m_selector * 50, 300, 300 ))
    self.blit_sound_icon(screen)

  def render_paused(self,screen):
    self.render_playing(screen)
    
    pass
    