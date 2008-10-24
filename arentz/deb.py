#!/usr/bin/python

import ar, md5, os, StringIO, shutil, tarfile, time

class Deb(object):
    
    def __init__(self, package, version, revision, arch, maintainer):
        self.package = package
        self.version = version
        self.revision = revision
        self.arch = arch
        self.maintainer = maintainer
        self.section = "unknown"
        self.priority = "extra"
        self.description = "No description."
        self.data_files = []
        self.control_files = []
        self.directories = []
        self.dependencies = []
        self.now = int(time.time())
        self.conffiles = []

    def add_file(self, src, dst, mode = 0644, conf = False):
        self.data_files.append({ 'src': src, 'dst': dst, 'mode': mode })
        if conf:
            self.conffiles.append(dst)

    def add_executable(self, src, dst, mode = 0755, conf = False):
        self.add_file(src, dst, mode)
        if conf:
            self.conffiles.append(dst)

    def add_startup_script(self, src, name):
        self.add_executable(src, "./etc/init.d/%s" % name)

    def add_dependency(self, package, match = None, version = None):
        self.dependencies.append({ 'package': package, 'match': match, 'version': version })

    def _add_control_file(self, src, name):
        self.control_files.append({ 'src': src, 'dst': name, 'mode': 0644 })

    def set_prerm(self, src):
        self.control_files.append({ 'src': src, 'dst': "prerm", 'mode': 0755 })

    def set_postrm(self, src):
        self.control_files.append({ 'src': src, 'dst': "postrm", 'mode': 0755 })

    def set_preinst(self, src):
        self.control_files.append({ 'src': src, 'dst': "preinst", 'mode': 0755 })

    def set_postinst(self, src):
        self.control_files.append({ 'src': src, 'dst': "postinst", 'mode': 0755 })

    def write(self, path):
        self._add_control_file(self._create_control_file(), "control")
        self._add_control_file(self._create_md5sums_file(), "md5sums")
        if len(self.conffiles):
            self._add_control_file(self._create_conffiles_file(), "conffiles")

        archive = ar.Archive()
        archive.add("debian-binary", StringIO.StringIO("2.0\n"))
        archive.add("control.tar.gz", self._create_tar_file("control.tar.gz", self.control_files))
        archive.add("data.tar.gz", self._create_tar_file("data.tar.gz", self.data_files))
        
        packageName = "%s_%s-%s_%s.deb" % (self.package, self.version, self.revision, self.arch)
        packagePath = path + "/" + packageName

        archive.write(packagePath, "w")

        return packageName

    def _calculate_installed_size(self):
        total = 0
        for file in self.data_files:
            total += os.path.getsize(file['src'])
        return total

    def _calculate_depends(self):
        a = []
        for d in self.dependencies:
            s = d['package']
            if d['match'] and d['version']:
                s += " (%s %s)" % (d['match'], d['version'])
            a.append(s)
        return ', '.join(a)

    def _create_control_file(self):
        control = StringIO.StringIO()
        control.write("Package: %s\n" % self.package)
        control.write("Version: %s-%s\n" % (self.version, self.revision))
        control.write("Architecture: %s\n" % self.arch)
        control.write("Maintainer: %s\n" % self.maintainer)
        control.write("Installed-Size: %s\n" % self._calculate_installed_size())
        control.write("Depends: %s\n" % self._calculate_depends())
        control.write("Section: %s\n" % self.section)
        control.write("Priority: %s\n" % self.priority)
        control.write("Description: %s\n" % self.description)
        #print control.getvalue()
        return control

    def _create_conffiles_file(self):
        conffiles = StringIO.StringIO()
        for f in self.conffiles:
            conffiles.write("%s\n" % f)
        return conffiles

    def _get_md5sum(self, path):
        return md5.new(open(path).read()).hexdigest()

    def _create_md5sums_file(self):
        fp = StringIO.StringIO()
        for f in self.data_files:
            fp.write("%s\t%s\n" % (self._get_md5sum(f['src']), f['dst']))
        return fp

    def _create_tar_file(self, name, files):
        data = StringIO.StringIO()
        tar = tarfile.open(name, "w:gz", data)
        for f in files:
            if isinstance(f['src'], str):
                #print "Adding regular file %s as %s" % (f['src'], f['dst'])
                tarinfo = tar.gettarinfo(f['src'], f['dst'])
                tarinfo.uid = 0
                tarinfo.gid = 0
                tarinfo.uname = "root"
                tarinfo.gname = "root"
                tarinfo.mode = f['mode']
                tarinfo.mtime = self.now
                tar.addfile(tarinfo, file(f['src']))
            elif isinstance(f['src'], StringIO.StringIO):
                #print "Adding in-memory file as %s" % (f['dst'])
                tarinfo = tarfile.TarInfo(f['dst'])
                tarinfo.uid = 0
                tarinfo.gid = 0
                tarinfo.uname = "root"
                tarinfo.gname = "root"
                tarinfo.mode = f['mode']
                tarinfo.mtime = self.now
                tarinfo.size = len(f['src'].getvalue())
                f['src'].seek(0)
                tar.addfile(tarinfo, f['src'])
        tar.close()
        return data

