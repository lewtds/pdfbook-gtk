from distutils.core import setup

files = ["data/ui.glade"]

setup(name='pdfbook-gtk',
      version='1.0',
      packages=['pdfbookgtk'],
      package_data={'pdfbookgtk':files},
      data_files=[("share/applications", ["pdfbook-gtk.desktop"])],
      license="GPL",
      scripts=["pdfbookgtk/pdfbook-gtk"]
      )
