from gi.repository import GLib, Gtk, Gdk, GObject
import subprocess
import signal
import os
import threading
import time

ui_file = os.path.join(os.path.dirname(__file__), 'data/ui.glade')

class CommandThread(threading.Thread) :
    def __init__(self, command, args, widget, cwd=None) :
        threading.Thread.__init__(self)
        self.cmdline = []
        self.cmdline.append(command)
        self.cmdline.extend(args)
        self.widget = widget
        self.cwd = cwd
    
    def run(self) :
        process = subprocess.Popen(self.cmdline,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd = self.cwd)
        
        GObject.idle_add(self.__start, process)
        
        process.poll()
        while process.returncode == None :
            message = process.stderr.readline()
            GObject.idle_add(self.__updateGUI, message)
            process.poll()
        
        GObject.idle_add(self.__stop, process)
        
    def __updateGUI(self, message) :
        self.widget._output_text.get_buffer().insert_at_cursor(message, -1)
        return False
        
    def __start(self, process) :
        self.widget._output_text.get_buffer().insert_at_cursor("PID=" +
            str(process.pid) +
            " -- " + 
            " ".join(self.cmdline) +
            " -- \n")
        return False

    def __stop(self, process) :
        self.widget._progress_spinner.stop()
        self.widget._progress_spinner.hide()
        self.widget._run_button.set_sensitive(True)

        if process.returncode == 0 :
            self.widget._ok_image.show()
        else :
            self.widget._error_image.show()

        self.widget._output_text.get_buffer().insert_at_cursor(
            "\n-- Finished -- Returncode=" +
            str(process.returncode) +
            " --\n")
        return False

class Wrapper(Gtk.Dialog) :
        
    def __init__(self) :
        
        builder = Gtk.Builder()
        builder.add_from_file(ui_file)
        
        this = builder.get_object("dialog1")
        this.connect("destroy", Gtk.main_quit)
        
        quit_button = builder.get_object("quit-button")
        quit_button.connect("clicked", Gtk.main_quit)
        
        self._run_button = builder.get_object("run-button")
        self._run_button.connect("clicked", lambda x : self.run())
        
        self.signatures = 16
        adj = Gtk.Adjustment(self.signatures, 4, 32, 4)
        
        def set_signature(adj) :
            self.signatures = int(adj.get_value())
            
        adj.connect("value-changed", set_signature)
        signature_spin = builder.get_object("signature-spin")
        signature_spin.set_adjustment(adj)
        
        self._src_file = ""
        file_button = builder.get_object("choose-file-button")
        file_button.connect("clicked", self.on_file_clicked)
    
        folder_button = builder.get_object("choose-folder-button")
        folder_button.connect("clicked", self.on_folder_clicked)
    
        self._file_entry = builder.get_object("file-entry")
        self._file_entry.connect("icon-press", self.on_entry_icon_clicked)
        
        self._folder_entry = builder.get_object("folder-entry")
        self._folder_entry.connect("icon-press", self.on_folder_icon_clicked)
        self._folder_entry.set_text(os.getcwd())
        
        self._pagespec_entry = builder.get_object("pagespec-entry")
        self._pagespec_entry.connect("icon-press", self.on_entry_icon_clicked)
        
        self._output_text = builder.get_object("output-text")
        output_buffer = Gtk.TextBuffer()
        self._output_text.set_buffer(output_buffer)
                
        self._optional_args_entry = builder.get_object("optional-args-entry")
        self._optional_args_entry.connect("icon-press", self.on_entry_icon_clicked)        
                
        self._progress_spinner = builder.get_object("progress-spinner")
        
        self._ok_image = builder.get_object("ok-image")
        self._error_image = builder.get_object("error-image")
        
        this.show_all()
       
    def run(self) :
    
        if self._file_entry.get_text() == "" :
            self._file_entry.set_placeholder_text("Please choose a file first!")
            self._error_image.show()
            return
            
        self._progress_spinner.show()
        self._progress_spinner.start()
        self._run_button.set_sensitive(False)
        
        self._ok_image.hide()
        self._error_image.hide()

        args = []
        optional_opt = self._optional_args_entry.get_text().split()      
        if optional_opt != [] :
            try :
                i = optional_opt.index("--short-edge")
                print(i)
                shortedge = optional_opt.pop(i)
                optional_opt.insert(0, shortedge)
            except ValueError :
                pass
            args.extend(optional_opt)

        args.extend(["--signature", str(self.signatures)])
        args.append(self._file_entry.get_text())
        args.append(self._pagespec_entry.get_text())
        
        cwd = self._folder_entry.get_text()
        if cwd == "" :
            cwd = None
        workerThread = CommandThread("/usr/bin/pdfbook", args, self, cwd)        
        workerThread.start()

    def on_file_clicked(self, button) :
        file_dialog = Gtk.FileChooserDialog("",
            self,
            Gtk.FileChooserAction.OPEN,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        
        filter_pdf = Gtk.FileFilter()
        filter_pdf.set_name("PDF Files")
        filter_pdf.add_mime_type("application/pdf")
        
        file_dialog.add_filter(filter_pdf)
        
        respond = file_dialog.run()
        if respond == Gtk.ResponseType.OK :
            self._src_file = file_dialog.get_filename()
            self._file_entry.set_text(self._src_file)
            
            self._file_entry.set_placeholder_text("")
            self._error_image.hide()
        file_dialog.destroy()
    
    def on_folder_clicked(self, widget) :
        folder_dialog = Gtk.FileChooserDialog("",
            self,
            Gtk.FileChooserAction.SELECT_FOLDER,
            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
            
        respond = folder_dialog.run()
        if respond == Gtk.ResponseType.OK :
            self._output_folder = folder_dialog.get_filename()
            self._folder_entry.set_text(self._output_folder)
        folder_dialog.destroy()
    
    def on_folder_icon_clicked(self, widget, icon_pos, event) :
        widget.set_text(os.getcwd())
    
    def on_entry_icon_clicked(self, widget, icon_pos, event) :
        widget.set_text("")

def main() :
    GObject.threads_init()
	# Quit when Control-C is received
    signal.signal(signal.SIGINT, signal.SIG_DFL)
    
    app = Wrapper()
    Gtk.main()
    
if __name__ == '__main__':
    main()
