#!/usr/bin/env python3

import gi

gi.require_version("Gtk", "3.0")

import os  # noqa: E402
from os.path import isfile  # noqa: E402
from gi.repository import Gtk, GdkPixbuf  # noqa: E402


class MainWindow(Gtk.Window):

    def __init__(self):
        super().__init__(title="imgclean")
        Gtk.Window.set_default_size(self, 640, 480)

        header_bar = Gtk.HeaderBar(title="imgclean")
        header_bar.set_show_close_button(True)
        self.set_titlebar(header_bar)
        self.header_bar = header_bar

        self.btn_open = Gtk.Button(label="open")
        self.btn_open.connect("clicked", self.btn_open_clicked)
        self.header_bar.pack_start(self.btn_open)

        self.btn_prev = Gtk.Button(label="previous")
        self.btn_prev.connect("clicked", self.btn_prev_clicked)
        self.header_bar.pack_start(self.btn_prev)

        self.btn_next = Gtk.Button(label="next")
        self.btn_next.connect("clicked", self.btn_next_clicked)
        self.header_bar.pack_start(self.btn_next)

        self.page_counter = Gtk.Label(label="0/0")
        self.header_bar.pack_start(self.page_counter)

        self.content_container = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.add(self.content_container)

        self.preview_container = Gtk.Paned()
        self.image = Gtk.Image(margin=10)
        self.metadata = Gtk.Box()
        self.preview_container.add(self.image)
        self.preview_container.add(self.metadata)
        self.content_container.pack_start(
            self.preview_container, True, True, 0
        )

        self.liststore = Gtk.ListStore(bool, str, str, str, str, str, str)
        self.treeview = Gtk.TreeView(model=self.liststore)

        treeview_headers = [
            'Selected',
            'Data Checksum',
            'Metadata Checksum',
            'Date Original',
            'Date Created',
            'File Size',
            'File Path',
        ]

        self.treeview = Gtk.TreeView(model=self.liststore)
        for n, header in enumerate(treeview_headers):
            if n == 0:
                checkbox = Gtk.CellRendererToggle()
                column = Gtk.TreeViewColumn(
                    "Selected", checkbox
                )
                column.add_attribute(checkbox, "active", n)
            else:
                column = Gtk.TreeViewColumn(
                    header, Gtk.CellRendererText(), text=n
                )
            self.treeview.append_column(column)

        self.treeview.connect('row-activated', self.treeview_on_row_activated)
        self.select = self.treeview.get_selection()
        self.select.connect('changed', self.treeview_on_selection_changed)

        self.content_container.pack_start(self.treeview, True, True, 0)

        self.btn_delete = Gtk.Button(label="Delete Selected Files")
        self.btn_delete.connect("clicked", self.btn_delete_clicked)

        self.content_container.pack_start(self.btn_delete, True, True, 0)

        self.record_index = 0

    def treeview_on_selection_changed(self, selection):
        """Update content in the upper pane when the row
           selection has changed
        """
        model, treeiter = selection.get_selected()
        if treeiter is not None:
            self.img_content_update(model[treeiter][-1])

    def treeview_on_row_activated(self, widget, row_id, column_id):
        """Toggle selection field boolean (True/False) on the activated row
        """
        path = Gtk.TreePath(row_id)
        treeiter = self.liststore.get_iter(path)

        # Toggles True/False of the selected field
        self.liststore.set_value(
            treeiter,
            0,
            [True, False][self.liststore.get_value(treeiter, 0)]
        )

    def btn_open_clicked(self, widget):
        try:
            dialog = Gtk.FileChooserDialog(
                title="Please choose a data file...",
                parent=self,
                action=Gtk.FileChooserAction.OPEN,
            )
            dialog.add_buttons(
                    Gtk.STOCK_OPEN, Gtk.ResponseType.OK,
                    Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
            )
            response = dialog.run()
            if response == Gtk.ResponseType.OK:
                file = dialog.get_filename()
            else:
                dialog.destroy()
                return

            dialog.destroy()

            # self.img_content_update(file)
            self.open_file(file)

        except Exception as e:
            self.msg_display("Error", "ERROR: \n\n" + str(e))

    def btn_prev_clicked(self, widget):
        if not hasattr(self, 'records_list'):
            return
        if self.record_index == 0:
            self.record_index = len(self.records_list) - 1
        else:
            self.record_index -= 1
        self.update_liststore(self.records_list[self.record_index])

    def btn_next_clicked(self, widget):
        if not hasattr(self, 'records_list'):
            return
        if self.record_index == len(self.records_list) - 1:
            self.record_index = 0
        else:
            self.record_index += 1
        self.update_liststore(self.records_list[self.record_index])

    def btn_delete_clicked(self, widget):
        """Grabs data from the liststore and groups the filepaths
           in either files_to_keep or files_to_delete based on
           if they were or were not selected in the application

           files that were active/selected (checkbox checked)
           are kept, while the rest is deleted
        """
        if not hasattr(self, 'records_list'):
            return
        treeiter = self.liststore.get_iter_first()

        files_to_delete, files_to_keep = [], []
        while treeiter is not None:
            selected = self.liststore.get_value(treeiter, 0)
            if selected:
                files_to_delete.append(self.liststore.get_value(treeiter, 6))
            else:
                files_to_keep.append(self.liststore.get_value(treeiter, 6))

            treeiter = self.liststore.iter_next(treeiter)

        for file in files_to_delete:
            print(f'DELETING FILE "{file}"')
            os.remove(file)

    def img_content_update(self, file):
        """Updates The image preview content
        """
        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
            file,
            800,
            600,
            True,
        )
        self.image.set_from_pixbuf(pixbuf)

    def msg_display(self, title, message):
        dialog = Gtk.MessageDialog(
            flags=None,
            text=message,
        )
        dialog.add_buttons(
            Gtk.STOCK_OK, Gtk.ResponseType.OK,
        )
        dialog.run()
        dialog.destroy()

    def open_file(self, file):
        """Parses data within the log file and sorts it by the image data hash
           Image files that do not exist on disk are skipped.

           This sets self.hash_records_list to a list of
           [
           { HASH: [record, ...] }
           ,
           ...
           ]
        """
        # Sort file records by imagedata hash
        _hash_records_map = {}
        with open(file, 'r') as f:
            for line in f.readlines():
                r = line.rstrip().split('|')
                r = [0] + r  # prepend 'active' bool

                hash_key = _hash_records_map.setdefault(r[1], [])
                if isfile(r[6]):
                    hash_key.append(r)

        # Create a set or records through which the program
        # can cycle through. We only care about the values
        # here and not the hash it was sorted with since
        # that information is already within the records
        self.records_list = []
        for k, v in _hash_records_map.items():
            if len(v) > 1:
                self.records_list.append(v)

        self.update_liststore(self.records_list[0])
        self.record_index = 0
        self.page_counter.set_label(
            f'{self.record_index+1}/{len(self.records_list)}'
        )

    def update_liststore(self, records):
        """Updates (clean + replace) the liststore and subsequently
           the treeview container With the new records that are
           passed to the function
        """
        self.liststore.clear()

        for r in records:
            if isfile(r[6]):
                print(r[6])
                self.liststore.append(r)

        # Select the first element of the new data and grab Window
        # focus to the list view (for keyboard controls)
        path = Gtk.TreePath(0)
        self.select = self.treeview.get_selection()
        self.select.select_path(path)
        self.treeview.grab_focus()

        self.page_counter.set_label(
            f'{self.record_index+1}/{len(self.records_list)}'
        )


def main():
    w = MainWindow()
    w.connect("destroy", Gtk.main_quit)
    w.show_all()
    Gtk.main()


if __name__ == '__main__':
    main()
