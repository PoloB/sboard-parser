# sboard-parser
Python parser for Storyboard Pro project files.

Storyboard Pro .sboard files are simple xml files.
This parser build a hierarchy of objects that represents all the elements in the
project file.

Usage example:

```python
from sboardparser import SBoardParser

parser = SBoardParser("/path/to/your/sboard/file.sboard")
project = parser.parse()

scenes = project.scenes

for scene in scenes:
    print(scene.id)
```

The classes used to represent the project hierarchy are either get from the 
cls_template module or built at runtime using namedtuple.
This makes sure the parser will keep working even if the Toon Boom team adds
new features.

The parser has been tested on files from the following Storyboard Pro versions:
* 14.20.4

If the parser does not work on your files, please issue a ticket with your 
sboard file.