import sublime, sublime_plugin  
import subprocess
import re
import threading

class CloudCodeDeployOnSaveCommand(sublime_plugin.EventListener):
  # Deploy automatically on save
  def on_post_save(self, view):
    # TODO Filter to only run this in cloud code directories
    # Extract path
    m = re.search('^(.+)/([^/]+)$', view.file_name())
    path = m.group(1)

    # Create and start thread
    thread = CloudCodeDeployThread(path)
    thread.start()

    # Start polling thread status
    self.handle_thread(thread, view)

  def handle_thread(self, thread, view, i=0, direction=1):
    # Check if thread is done
    if not thread.is_alive():
      # If no error show completed message
      if thread.result['return_code'] == 0: # success
        view.set_status("cloud_code", "Cloud Code Deployed")
        erase = lambda: view.erase_status("cloud_code")
        sublime.set_timeout(erase, 2000)
      # If we get an error just fail silently
      # TODO Better way to handle errors
      else:
        view.erase_status("cloud_code")

      # Print out stdout/stderr to console
      for line in thread.result['pipes'].stdout:
          print("stdout: " + line.rstrip())
      for line in thread.result['pipes'].stderr:
          print("stderr: " + line.rstrip())
    else:
      # Animate the loading
      before = i % 4  
      after = (3) - before  
      if not after:  
          direction = -1  
      if not before:  
          direction = 1  
      i += direction
      view.set_status('cloud_code', 'Deploying Cloud Code [%s=%s]' % (' ' * before, ' ' * after)) 

      # Check again in 100ms
      sublime.set_timeout(lambda: self.handle_thread(thread, view, i, direction), 100)
    return
    

class CloudCodeDeployThread(threading.Thread):
  def __init__(self, path):
    self.path = path
    threading.Thread.__init__(self)

  def run(self):
    # TODO I don't think this could be more brittle!
    #   - Use python to change directory
    #   - Add /usr/local/bin to PATH and just use parse deploy
    proc = subprocess.Popen("cd '" + self.path + "';/usr/local/bin/parse deploy", shell=True, stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    return_code = proc.wait()
    self.result = {}
    self.result['return_code'] = return_code
    self.result['pipes'] = proc
