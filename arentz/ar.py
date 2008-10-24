
import shutil, time, os, StringIO

class Archive(object):

    def __init__(self):
        self.files = []

    def add(self, name, path):
        self.files.append({ 'path': path, 'name': name })

    def write(self, path, mode):
        now = int(time.time())
        fp = open(path, mode)
        fp.write("!<arch>\n")
        for file in self.files:
            if isinstance(file['path'], str):
                header = "%-16s%10d  %-6d%-6d%-8o%-10d\140\012" % (file['name'], now, 0, 0,
                    0100644, os.path.getsize(file['path']))
                fp.write(header)
                shutil.copyfileobj(open(file['path']), fp, 8192)
                if fp.tell() & 1:
                    fp.write("\n")
            elif isinstance(file['path'], StringIO.StringIO):
                header = "%-16s%10d  %-6d%-6d%-8o%-10d\140\012" % (file['name'], now, 0, 0,
                    0100644, len(file['path'].getvalue()))
                fp.write(header)
            fp.write(file['path'].getvalue())
            if fp.tell() & 1:
                fp.write("\n")
        fp.close()
                    
