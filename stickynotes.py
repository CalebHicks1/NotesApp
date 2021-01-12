#!/usr/bin/python3
"""
A simple program to keep track of sticky notes, stored in the system tray.
--------------
By Caleb Hicks
"""

import os
import gi
import sys
gi.require_version('Gtk', '3.0')
gi.require_version('AppIndicator3', '0.1')
from gi.repository import Gtk as gtk, AppIndicator3 as appindicator, Pango as pango

# Initialize some constants
indicator = appindicator.Indicator.new("customtray", os.path.abspath(sys._MEIPASS+'/icon.png'), appindicator.IndicatorCategory.APPLICATION_STATUS)
notes = gtk.Menu()
exittray = gtk.MenuItem(label='Quit')

# Read the existing notes from file
import ast # Used to read string as a list
if not os.path.exists(os.path.expanduser('~/.stickynotes')):
    os.mkdir(os.path.expanduser('~/.stickynotes'))
try:
    text_file = open(os.path.expanduser('~/.stickynotes/note_titles.txt'), 'r') # reads the saved note titles
except:
    text_file = open(os.path.expanduser('~/.stickynotes/note_titles.txt'), 'w') # Creates the file if it doesn't exist.
    text_file.write('[]')
    text_file.close()
    text_file = open(os.path.expanduser('~/.stickynotes/note_titles.txt'), 'r')

current_notes = ast.literal_eval(text_file.read()) # Reads the string as a list.
text_file.close()
open_notes = []

def main():
    indicator.set_status(appindicator.IndicatorStatus.ACTIVE)
    indicator.set_menu(menu())
    exittray.connect('activate', clicked_quit)
    gtk.main()

# Sets up the menu and restores the saved notes.
def menu():
    main_menu = gtk.Menu()
    command_one = gtk.MenuItem(label='New Note...')
    main_menu.append(command_one)
    note_menu = gtk.MenuItem(label='Notes')
    note_menu.set_submenu(notes)
    main_menu.append(note_menu)
    command_one.connect('activate', new_note)
    if current_notes:
        for note in current_notes:
            notes_submenu = gtk.Menu()
            restore_note(note)
    main_menu.append(exittray)
    notes.show_all()
    main_menu.show_all()
    return main_menu

# Restores the existing notes
def restore_note(note):
    note_label = note
    new_note = gtk.MenuItem(label=note_label)
    new_note.connect('activate', make_stickynote)
    notes.append(new_note)
    notes.show_all()

# Adds a new MenuItem
def new_note(self):
    note_label = 'Untitled Note '
    if note_label in current_notes:
        i=1
        while note_label in current_notes:
            note_label = 'Untitled Note '+str(i)
            i+=1
    new_note = gtk.MenuItem(label=note_label)
    new_note.connect('activate', make_stickynote)
    notes.append(new_note)
    current_notes.append(note_label)
    notes.show_all()
    save_notes()
    new_note.activate()

# Makes a new sticky note, using the label of the note in the tray.
def make_stickynote(self):
    already_open = False
    for note in open_notes:
        if note.label == self.get_label():
            note.present()
            already_open = True
    if not already_open:
        label = self.get_label()
        note = StickyNote(label)
        note.connect("destroy", StickyNote.quit)
        note.show_all()
        note.present()

# The class to act as a sticky note. Takes care of styling and saving
# the note contents.
class StickyNote(gtk.Window):
    def __init__(self, label):
        gtk.Window.__init__(self, title='')
        open_notes.append(self)
        self.label = label
        self.text = gtk.TextView()
        self.label_box = gtk.Entry() #The entry for the label

        # Set the font margins and other style
        self.label_box.set_alignment(xalign=0.5)
        self.label_box.set_text(self.label)
        self.label_box.set_has_frame(False)
        self.label_box.override_font(pango.FontDescription('bold 15'))
        self.text.set_left_margin(10)
        self.text.set_right_margin(10)
        self.text.set_top_margin(10)
        self.text.set_wrap_mode(gtk.WrapMode(2))
        self.resize(300,300)
        # Keep track of text
        self.buffer = self.text.get_buffer()
        self.box = gtk.VBox(homogeneous=False, spacing=0)
        self.box.pack_start(self.label_box, expand=False, fill=False,padding=0)
        self.text_box = gtk.VBox(homogeneous=False, spacing=0)
        self.text_box.pack_end(self.text, expand=True, fill=True,padding=0)
        self.box.pack_end(self.text_box, expand=True, fill=True,padding=0)
        self.add(self.box)
        self.set_icon_from_file(os.path.abspath(sys._MEIPASS+'/icon.png'));
        try:
            # Read text from the saved file.
            text_file = open(os.path.expanduser('~/.stickynotes/')+self.label+'.txt','r')
            self.buffer.set_text(text_file.read())
            text_file.close()
            # Put focus on text box, remove highlighting from label_box
            self.label_box.select_region(0,0)
            self.text_box.set_property('can-focus',True)
            self.text_box.grab_focus()
            self.text.grab_focus()
        except:
            pass

    # Called when the quit button is clicked. Saves the note,
    # and deletes it if the note is blank.
    def quit(self):
        bounds = self.buffer.get_bounds()
        text = self.buffer.get_text(bounds[0],bounds[1],False)
        if self.label_box.get_text() != self.label and self.label_box.get_text() !="":
            if os.path.exists(os.path.expanduser('~/.stickynotes/')+self.label+'.txt'):
                os.remove(os.path.expanduser('~/.stickynotes/')+self.label+'.txt')
            remove_note_label(self.label)
            change_note_label(self, self.label_box.get_text())
        # if there is any text in the file, save it. Otherwise remove the file.
        if text:
            text_file = open(os.path.expanduser('~/.stickynotes/')+self.label+'.txt','w')
            text_file.write(text)
            text_file.close()
        else:
            if os.path.exists(os.path.expanduser('~/.stickynotes/')+self.label+'.txt'):
                os.remove(os.path.expanduser('~/.stickynotes/')+self.label+'.txt')
            remove_note_label(self.label)
        open_notes.remove(self)
        print('Closing note:'+self.label)
        save_notes()
        self.destroy()

# Removes the note with the given name from the system tray menu.
def remove_note_label(name):
    if name in current_notes:
        current_notes.remove(name)
    for note in notes:
        if (note.get_label()) == name:
            notes.remove(note)

# Changes the name of the note to the new label.
def change_note_label(self, new_label):
    self.label = new_label
    new_note = gtk.MenuItem(label=new_label)
    new_note.connect('activate', make_stickynote)
    notes.append(new_note)
    current_notes.append(new_label)
    notes.show_all()
    save_notes()

# Saves the labels in the menu to a file.
def save_notes():
    print('saved!')
    text_file = open(os.path.expanduser('~/.stickynotes/note_titles.txt'), 'w')
    text_file.write(str(current_notes))
    text_file.close()
    notes.show_all()

# Method called when the quit  button is clicked.
def clicked_quit(self):
    for note in open_notes:
        note.quit()
    print('Quit')
    gtk.main_quit()

if __name__ == "__main__":
  main()
