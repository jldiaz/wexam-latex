"""Implementa el conversor del diccionario python que contiene un exame
a las cadenas latex que hay que guardar en ficheros para crear el examen"""

import os
import click
from collections import Counter
import json

from . import converter
from . import dumper


class Consola(object):
    def update(self, msg):
        print(msg)


def archivar_resultado(main_tex, problemas, json_file, output):
    """Vuelca el resultado a disco, ya sea a una carpeta o a un archivo
    .zip o .tar.gz"""

    # Quitar una o dos extensiones del fichero
    fout = os.path.splitext(os.path.splitext(json_file)[0])[0]
    if output is None:
        dump = dumper.Folder(fout, fout + ".tex")
    elif output.endswith(".tar.gz") or output.endswith(".tgz"):
        dump = dumper.TarFile(output, fout + ".tex")
    elif output.endswith(".zip"):
        dump = dumper.ZipFile(output, fout + ".tex")
    else:
        dump = dumper.Folder(output, fout + ".tex")

    with dump as d:
        d.dump(main_tex, problemas)
    print("Examen generado: {}".format(dump.name))

@click.command()
@click.argument("json_file")
@click.option("--dry/--no-dry", default=False, is_flag=True, show_default=True,
              help="No genera los fichero tex, solo recuenta preguntas y puntos")
@click.option("--verbose", default=False, is_flag=True,
              help="Muestra resumen de cada problema incluido en el examen")
@click.option("--progress", default=False, is_flag=True,
              help="Muestra progreso de la conversión a latex")
@click.option("--output", "-o", default=None, show_default=False,
              help="Nombre del resultado. Si la extensión es .tgz, .tar.gz o .zip se creará "\
                   "un archivo. En caso contrario una carpeta de ese nombre que contendrá los "\
                   "ficheros resultantes")
def main(json_file, dry, verbose, progress, output):
    with open(json_file) as f_:
        datos = json.load(f_)

    if progress:
        progress = Consola()

    main_tex, problemas = (converter.Examen2Tex(to_latex=not dry, progress=progress)
                           .convert_to_exam(datos, skip=False)
    )
    # assert len(problemas) > 0, "No hay problemas en el examen"
    if verbose:
        for i,p in enumerate(problemas):
            print("{:02} {}".format(i+1, p["resumen"]))
    if progress:
        progress.update("Volcando resultados a fichero")
    if not dry:
        archivar_resultado(main_tex, problemas, json_file, output)
    print("  - Preguntas: {}".format(datos["total_preguntas"]))
    print("  - Puntos:    {}".format(datos["total_puntos"]))

if __name__ == "__main__":
    main()
