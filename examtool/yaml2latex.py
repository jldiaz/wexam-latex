"""Implementa el conversor del diccionario python que contiene un exame
a las cadenas latex que hay que guardar en ficheros para crear el examen"""

import os
import click
from collections import Counter
import ruamel.yaml
yaml = ruamel.yaml.YAML(typ='safe')
yaml.safe_load = yaml.load

from . import converter

@click.command()
@click.argument("yaml_file")
@click.option("--dry/--no-dry", default=False, is_flag=True, show_default=True,
              help="No genera los fichero tex, solo recuenta preguntas y puntos")
@click.option("--skip/--no-skip", default=True, is_flag=True, show_default=True,
              help="No incluye en los resultados las preguntas con un campo 'skip'")
@click.option("--skip_nores/--no-skip_nores", default=True, is_flag=True, show_default=True,
              help="No incluye en los resultados las preguntas que carecen del campo 'resumen'")
@click.option("--onlyok/--no-onlyok", default=False, is_flag=True, show_default=True,
              help="Incluye solo las preguntas con un campo 'ok'")
@click.option("--verbose", default=False, is_flag=True,
              help="Muestra resumen de cada problema incluido en el examen")
def main(yaml_file, dry, skip, skip_nores, onlyok, verbose):
    with open(yaml_file, encoding="utf8") as f_:
        datos = yaml.safe_load(f_)

    main_tex, problemas = (converter.Examen2Tex(to_latex=not dry)
                           .convert_to_exam(datos, skip=skip,
                                            skip_nores=skip_nores, only_ok=onlyok)
    )
    assert len(problemas) > 0, "No ha sido seleccionado ningún problema"
    if verbose:
        for i,p in enumerate(problemas):
            print("{:02} {}".format(i+1, p["resumen"]))
    if not dry:
        for p in problemas:
            with open(p["filename"], "w", encoding="utf8") as f_:
                f_.write(p["latex"])
        fout = os.path.basename(yaml_file).replace("yaml", "tex")
        with open(fout, "w", encoding="utf8") as f_:
            f_.write(main_tex)
        print("Examen generado: {}".format(fout))
    print("  - Preguntas: {}".format(datos["total_preguntas"]))
    print("  - Puntos:    {}".format(datos["total_puntos"]))
    tags = Counter()
    punto_tags = Counter()
    for p in problemas:
        tags.update(p["tags"])
        for tag in p["tags"]:
            punto_tags.update([tag]*p["puntos"])
    if "tags" in datos:
        print("  - Tags:      {}".format(
                ", ".join("%s: %s[%s]" % (tag, tags[tag], punto_tags[tag])
                                          for tag in datos["tags"])))

if __name__ == "__main__":
    main()
