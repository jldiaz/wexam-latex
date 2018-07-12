import tarfile
import zipfile
import io
import os

class Dumper(object):
    def __init__(self, name, main_name="examen.tex"):
        self.name =  name
        self.main_name = main_name

    def dump(self, main_tex, problemas):
        for p in problemas:
            self.dump_file(filename=p["filename"], content=p["latex"])
        self.dump_file(filename=self.main_name, content=main_tex)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if exc_type is not None:
            print(traceback)
        # Añadir estilos, etc.
        extradir = os.path.abspath(os.path.join(os.path.dirname(__file__), "extra_files"))
        for filename in os.listdir(extradir):
            with open(os.path.join(extradir, filename), "r") as f:
                content = f.read()
            self.dump_file(filename, content)


class Folder(Dumper):
    def __enter__(self):
        if not os.path.exists(self.name):
            os.mkdir(self.name)
        return self

    def dump_file(self, filename, content):
        with open(os.path.join(self.name, filename), "w", encoding="utf-8") as f:
            f.write(content)


class TarFile(Dumper):
    def __enter__(self):
        self.tarfile = tarfile.open(self.name, "w:gz")
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        self.tarfile.close()

    def dump_file(self, filename, content):
        tarinfo = tarfile.TarInfo(name=filename)
        content = content.encode("utf-8")
        tarinfo.size = len(content)
        # info.mtime = time.time()
        f = io.BytesIO(content)
        self.tarfile.addfile(tarinfo=tarinfo, fileobj=f)


class ZipFile(Dumper):
    def __enter__(self):
        self.zipfile = zipfile.ZipFile(self.name, "w", compression=zipfile.ZIP_DEFLATED)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        super().__exit__(exc_type, exc_value, traceback)
        self.zipfile.close()

    def dump_file(self, filename, content):
        self.zipfile.writestr(filename, content)