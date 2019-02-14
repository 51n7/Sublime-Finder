import sublime
import sublime_plugin
import os, subprocess, sys
from urllib import parse
from os.path import expanduser

# todo:
# import win32api, win32con
# https://stackoverflow.com/questions/19799990/sublime-text-plugin-adding-python-libraries

class FinderCommand( sublime_plugin.TextCommand ):

  def run(self, edit):
    
    settings = sublime.load_settings("Finder.sublime-settings")
    
    window = sublime.active_window()
    self.view = window.new_file()
    
    self.view.set_name('Finder')
    self.view.set_scratch(True)
    self.view.set_read_only(True)
    self.view.window().set_minimap_visible(False)
    self.view.settings().set("finder.is_open", True)
    self.view.settings().set("finder.inline", settings.get("files_inline"))
    self.view.settings().set("finder.x", 0)
    self.view.settings().set("finder.y", 0)
    self.view.settings().set("finder.selected_path", expanduser("~"))
    self.view.settings().set("finder.current_path", expanduser("~"))
    self.view.settings().set("font_size", settings.get("font_size"))
    self.view.settings().set("gutter", False)
    self.view.settings().set("finder.has_loaded", False)
    self.view.settings().set("is_widget", True)
    
    self.view.run_command("finder_update")
    
    window.focus_view(self.view)
    
    return self.view

class FinderUpdateCommand(sublime_plugin.TextCommand):

  def run(self, edit, source=None):
    
    inline = self.view.settings().get("finder.inline")
    x = self.view.settings().get("finder.x")
    y = self.view.settings().get("finder.y")
    current_path = self.view.settings().get("finder.current_path")
    has_loaded = self.view.settings().get("finder.has_loaded")

    if source == "up": y -= 1
    if source == "down": y += 1
    if source == "left": x -= 1
    if source == "right": x += 1

    # NAVIGATE DOWN
    if source == "nav-down":
      path = expanduser(self.view.settings().get("finder.selected_path"))
      
      if os.path.isfile(path):
        
        # OPEN FILE
        if sys.platform.startswith('darwin'):
          subprocess.call(('open', path))
        elif os.name == 'nt': # For Windows
          os.startfile(path)
        elif os.name == 'posix': # For Linux, Mac, etc.
          subprocess.call(('xdg-open', path))

        path = expanduser(current_path)
      else:
        x = y = 0
    else:
      path = expanduser(current_path)

    # NAVIGATE UP
    if source == "nav-up":
      x = y = 0
      path = expanduser(os.path.abspath(os.path.join(current_path, os.pardir)))
      
    # IF SELECTION IS DIRECTORY
    if os.path.isdir(path) and self.view.size() < 2**20:

      # files = [name for index, name in enumerate(os.listdir(path)) if not folder_is_hidden(name)]
      files = sorted([name for index, name in enumerate(os.listdir(path)) if not name.startswith('.')], reverse = False)
      
      if len(files) == 0: files = ['..']
      
      char_limit = 17
      icon_width = 40 if inline == True else 50
      em_space = 3

      em_width = self.view.em_width()
      width_bug = 0 if has_loaded else 46 # my guess is the gutter causing issues
      width = (self.view.viewport_extent()[0] + width_bug) - (em_width * em_space)
      
      file_width = (em_width * (char_limit + em_space)) + icon_width
      col_count = int( width / file_width )
      row_count = self.ceil( len(files) / col_count )
      pad = (width - (file_width * col_count)) / col_count
      
      if inline == True:
        icon_x = 0
        icon_y = 10
        name_x = 0
        name_y = 0
        line_height = 35
      else:
        icon_x = (file_width / 2) - (icon_width / 2) - (em_width / 2)
        icon_y = 0
        name_x = -(icon_width / 2)
        name_y = 25
        line_height = 80

      html = """
        <body id="finder">
          <style>
            body {
              margin: 0;
              padding: 0 """ + str( em_width ) + """;
            }

            a {
              text-decoration: none;
              color: #fff;
            }
            
            .file {
              display: inline;
              margin: 0;
              padding: 0 """ + str( pad / 2 ) + """;
            }

            .file .wrapper {
              padding: 10px """ + str( em_width ) + """;
              line-height: """ + str( line_height ) + """px;
            }

            .file .icon {
              font-family: "devicons";
              display: inline;
              position: relative;
              top: """ + str( icon_y ) + """px;
              left: """ + str( icon_x ) + """px;
              font-size: """ + str( icon_width ) + """px;
              padding-right: """ + str( em_width ) + """;
            }
            
            .file .name {
              position: relative;
              left: """ + str( name_x ) + """px;
              top: """ + str( name_y ) + """px;
            }

            .file.active .wrapper {
              background-color: rgba(255, 255, 255, 0.15);
            }

            .file.active .name {
              text-decoration: underline;
            }

            .tester {
              background-color: #b1dc1c;
              display: block;
              margin-top: 40px;
              width: """ + str( file_width ) + """px;
              padding: 0 """ + str( pad / 2 ) + """;
              height: 20px;
              display: none;
            }

            .footer {
              margin-top: 40px;
            }
          </style>
      """

      # LOOP NAVIGATION
      x = x % col_count
      y = y % row_count

      if ((y * col_count) + x > (len(files) - 1)):
        x = ((len(files) - 1) % col_count)

      # FOR EACH ROW
      for index, file in enumerate(files):

        is_active = ""
        file_path = os.path.join(path, file)
        file = file[:(char_limit - 3)]+"..." if len(file) > char_limit else file
        spacer = int(file_width - ( em_width * (len(file) + em_space) + icon_width ))
        padding = "0 "+ str(spacer) +" 0 0" if inline == True else "0 "+ str(spacer / 2)
        
        pos_x = self.get_xy(col_count, index)[0]
        pos_y = self.get_xy(col_count, index)[1]
        
        br = '<br />' if (index + 1) and ((index + 1) % col_count == 0) else ''

        icon = "" if os.path.isdir(file_path) else ""
        
        if y == pos_y and x == pos_x:
          is_active = " active"
          
          if not file == "..":
            self.view.settings().set("finder.selected_path", file_path)

        tmp = '<a href="?x='+ str( pos_x ) +'&y='+ str( pos_y ) +'" class="file'+ is_active +'"><span class="wrapper"><span class="icon">'+ icon +'</span><span class="name" style="padding: '+ padding +';">'+ file.replace(" ", "&nbsp;") +'</span></span></a>' + br
        
        html += tmp

      html += '<div class="tester"></div><div class="footer">'+path+'</div>'
      html += '</body>'
      
      self.view.erase_phantoms("list")
      self.view.add_phantom("list", self.view.sel()[0], html, sublime.LAYOUT_BLOCK, self.on_navigate)
    
    self.view.settings().set("finder.x", x)
    self.view.settings().set("finder.y", y)
    self.view.settings().set("finder.current_path", path)
    self.view.settings().set("finder.has_loaded", True)
  
  def get_xy(self, col_count, index):
    return (index % col_count, int( index / col_count ))

  def ceil(self, num):
    return int(num + 1) if int(num) < num else num

  def on_navigate(self, href):
    
    get_x = parse.parse_qs(parse.urlparse(href).query)['x'][0]
    get_y = parse.parse_qs(parse.urlparse(href).query)['y'][0]
    
    self.view.settings().set("finder.x", int(get_x))
    self.view.settings().set("finder.y", int(get_y))
    
    self.view.run_command("finder_update")

  
  # def folder_is_hidden(p):
  #   if os.name== 'nt':
  #     attribute = win32api.GetFileAttributes(p)
  #     return attribute & (win32con.FILE_ATTRIBUTE_HIDDEN | win32con.FILE_ATTRIBUTE_SYSTEM)
  #   else:
  #     return p.startswith('.') #linux-osx


# CONTEXT MENU - COPY PATH
class finderCopyPathCommand(sublime_plugin.TextCommand):

  def run(self, edit, event):
    sublime.set_clipboard(self.view.settings().get("finder.current_path"))
    
  def is_visible(self, event):
    return self.view.settings().get("finder.is_open") is not None
  
  def want_event(self): return True


# CONTEXT MENU - MOUNT PROJECT
class finderMountProjectCommand(sublime_plugin.TextCommand):

  def run(self, edit, event):
    path = self.view.settings().get("finder.current_path")

    sublime.run_command("new_window")
    window = sublime.active_window()

    data = window.project_data()
    data = {'folders': [{'follow_symlinks': True, 'path': path}] }

    window.set_project_data(data)
    
  def is_visible(self, event):
    return self.view.settings().get("finder.is_open") is not None
  
  def want_event(self): return True
