import sublime
import sublime_plugin
import os, subprocess, sys
from urllib import parse
from os.path import expanduser

class FinderCommand( sublime_plugin.TextCommand ):

  def run(self, edit):
    
    window = sublime.active_window()
    self.view = window.new_file()

    self.view.set_name('Finder')
    self.view.set_scratch(True)
    self.view.settings().set("finder.is_open", True)
    self.view.settings().set("finder.x", 0)
    self.view.settings().set("finder.y", 0)
    self.view.settings().set("finder.selected_path", expanduser("~"))
    self.view.settings().set("finder.current_path", expanduser("~"))
    self.view.settings().set("font_size", 16.0)
    self.view.settings().set("gutter", False)
    self.view.settings().set("finder.has_loaded", False)
    
    # self.view.settings().set("font_face", "Anonymous Pro")
    # self.view.settings().set("font_face", "icomoon")
    # self.view.settings().set("color_scheme", "Packages/Finder/Finder.sublime-color-scheme")
    # self.view.settings().set("syntax", "Packages/JavaScript/JSON.sublime-syntax")
    # self.view.set_syntax_file("Packages/Finder/syntax/finder.sublime-syntax")
    
    self.view.run_command("finder_update")
    # self.view.set_read_only(True)
  
    window.focus_view(self.view)
    
    return self.view

class FinderUpdateCommand(sublime_plugin.TextCommand):

  def run(self, edit, source=None):
    
    image = "res://Packages/Finder/images/icon-folder.png"
    
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

      files = [name for index, name in enumerate(os.listdir(path)) if not name.startswith('.')]
      
      char_limit = 17
      icon_width = 40

      em_width = self.view.em_width()
      width_bug = 0 if has_loaded else 46 # my guess is the gutter causing issues
      width = (self.view.viewport_extent()[0] + width_bug) - (em_width * 2)
      
      file_width = (em_width * (char_limit + 1)) + icon_width
      col_count = int( width / file_width )
      pad = (width - (file_width * col_count)) / col_count
      
      icon_folder = ""
      icon_file = ""
      
      html = """
        <body id="finder">
          <style>
            body {
              margin: 0;
              padding: 0 """ + str( em_width ) + """;
              width: """ + str( width ) + """px;
              font-size: """ + str( self.view.settings().get("font_size") ) + """px;
            }

            a {
              text-decoration: none;
              color: #fff;
            }
            
            .file {
              display: inline;
              margin: 0;
              padding: 10px """ + str( pad / 2 ) + """;
              line-height: 35px;
            }

            .file .icon {
              font-family: "devicons";
              display: inline;
              position: relative;
              top: 10px;
              font-size: """ + str( icon_width ) + """px;
            }
            
            .file .name {
              display: inline;
              padding: 0;
              position: relative;
              left: """ + str( em_width ) + """px;
            }

            .file.active {
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
            }

            .footer {
              margin-top: 40px;
            }
          </style>
      """

      if x >= col_count: x = 0
      if x < 0: x = (col_count - 1)

      # if y >= len(file_array): y = 0
      # if y < 0: y = (len(file_array) - 1)
      
      # FOR EACH ROW
      for index, file in enumerate(files):

        is_active = ""
        space = char_limit - len(file)
        
        if space >= 0:
          # nbsp = "-" * space
          nbsp = "&nbsp;" * space
        else:
          file = file[:(char_limit - 3)]+"..."
          nbsp = ""
        
        pos_x = self.get_xy(col_count, index)[0]
        pos_y = self.get_xy(col_count, index)[1]

        if y == pos_y and x == pos_x:
          is_active = " active"
          self.view.settings().set("finder.selected_path", os.path.join(path, file))
        
        tmp = '<a href="?x='+ str( pos_x ) +'&y='+ str( pos_y ) +'" class="file'+ is_active +'"><span class="icon">'+ icon_folder +'</span><span class="name">'+ file.replace(" ", "&nbsp;") +'</span>'+ nbsp +' </a>'
        
        html += tmp

      html += '<div class="footer">'+path+'</div>'
      html += '</body>'
      
      self.view.erase_phantoms("list")
      self.view.add_phantom("list", self.view.sel()[0], html, sublime.LAYOUT_BLOCK, self.on_navigate)
    
    self.view.settings().set("finder.x", x)
    self.view.settings().set("finder.y", y)
    self.view.settings().set("finder.current_path", path)
    self.view.settings().set("finder.has_loaded", True)
  
  def get_xy(self, col_count, index):
    return (index % col_count, int( index / col_count ))

  def on_navigate(self, href):
    
    get_x = parse.parse_qs(parse.urlparse(href).query)['x'][0]
    get_y = parse.parse_qs(parse.urlparse(href).query)['y'][0]
    
    self.view.settings().set("finder.x", int(get_x))
    self.view.settings().set("finder.y", int(get_y))
    
    self.view.run_command("finder_update")
