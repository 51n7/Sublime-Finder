import sublime
import sublime_plugin
import os, subprocess, sys
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
    # self.view.settings().set("font_size", 16.0)
    self.view.settings().set("gutter", False)
    # print( self.view.viewport_extent()[0] )

    # self.view.settings().set("font_face", "Anonymous Pro")
    # self.view.settings().set("font_face", "icomoon")
    # self.view.settings().set("color_scheme", "Packages/Finder/Finder.sublime-color-scheme")
    # self.view.settings().set("syntax", "Packages/JavaScript/JSON.sublime-syntax")
    # self.view.set_syntax_file("Packages/Finder/syntax/finder.sublime-syntax")
    
    self.view.run_command("finder_update")
    self.view.set_read_only(True)
  
    window.focus_view(self.view)
    
    return self.view

  def update_phantoms(self):
    print( 'update_phantoms' )


class FinderUpdateCommand(sublime_plugin.TextCommand):

  def run(self, edit, source=None):
    
    # if sys.platform.startswith('darwin'):
      # print('mac')
      # print(os.name)
      # print(sys.platform)
    
    image = "res://Packages/Finder/images/icon-folder.png"
    
    x = self.view.settings().get("finder.x")
    y = self.view.settings().get("finder.y")
    current_path = self.view.settings().get("finder.current_path")

    if source == "up": y -= 1
    if source == "down": y += 1
    if source == "left": x -= 1
    if source == "right": x += 1

    # navigate down
    if source == "nav-down":
      path = expanduser(self.view.settings().get("finder.selected_path"))

      if os.path.isfile(path):
        print( path )
        
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

    # navigate up
    if source == "nav-up":
      x = y = 0
      path = expanduser(os.path.abspath(os.path.join(current_path, os.pardir)))
    
    # if selection is directory
    if os.path.isdir(path) and self.view.size() < 2**20:

      files = [name for index, name in enumerate(os.listdir(path)) if not name.startswith('.')]
      
      gen_obj = self.chunks(files, 4)
      limit = 15
      icon_folder = ""
      icon_file = ""

      html = """
        <body id="finder">
          <style>
            body {
              margin: 0;
              padding: 10px 20px 10px 10px;
              color: #c8c8c8;
            }

            .row.active {  }
            
            .file {
              display: inline;
              margin: 0;
              padding: 0;
              font-size: 16px;
              line-height: 40px;
            }

            .file.active .name {
              text-decoration: underline;
            }
            
            .file img {
              width: 30px;
              height: 20px;
            }

            .file .icon {
              font-family: "devicons";
            }

            .file .name {
              display: inline;
              padding-right: 30px;
            }
          </style>
      """
      
      for index, row in enumerate(gen_obj):
        is_row = " active" if index == y else ""
        tmp = '<div class="row'+is_row+'">'

        for index, col in enumerate(row):
          # is_col = " active" if index == x and is_row == " active" else ""
          # full_path = os.path.join(path, name)

          if index == x and is_row == " active":
            is_col = " active"
            self.view.settings().set("finder.selected_path", os.path.join(path, col))
            # print(os.path.join(path, col))
            # print( os.path.isfile(os.path.join(path, col)) )
            # print( os.path.isdir(os.path.join(path, col)) )
          else:
            is_col = ""
          
          space = limit - len(col)
          
          if space >= 0:
            nbsp = "&nbsp;" * space
          else:
            col = col[:(limit - 3)]+"..."
            nbsp = ""

          tmp += '<div class="file'+ is_col +'"><span class="icon">' + icon_folder + '</span> <span class="name">' + col + '</span>' + nbsp + '</div>'
          # tmp += '<div class="file'+ is_col +'">📁 <span class="name">' + col + '</span>' + nbsp + '</div>'
          # tmp += '<div class="file'+ is_col +'"><img src="' + image + '" width="20" height="20"> <span>' + col + '</span>' + nbsp + '</div>'

        tmp += '</div>'
        html += tmp

      html += '<div><br /><br />'+path+'</div>'
      html += '</body>'
      
      self.view.erase_phantoms("list")
      self.view.add_phantom("list", self.view.sel()[0], html, sublime.LAYOUT_BLOCK)
    
    # print(html)
    self.view.settings().set("finder.x", x)
    self.view.settings().set("finder.y", y)
    self.view.settings().set("finder.current_path", path)
    
  def chunks(self, l, n):
    splitArray = []
    for i in range(0, len(l), n):
      splitArray.append(l[i:i + n])
    return splitArray

