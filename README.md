# sboard-parser
Python parser for Toon Boom Storyboard Pro project files.

Storyboard Pro .sboard files are simple xml files.
This parser build a hierarchy of objects that represents all the elements in the
project file.

Usage example:

```python
from sboardparser import parse

parser = parse("/path/to/your/sboard/file.sboard")
project = parser.root

scenes = project.scenes

for scene in scenes:
    print(scene.id)
```

The parser has been tested on files from the following Storyboard Pro versions:
* 14.20.4

If the parser does not work on your files, please issue a ticket with your 
sboard file.
