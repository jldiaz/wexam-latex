import os
import copy
from datetime import datetime

import jinja2
import pypandoc
import simhash


class Examen2Tex:
    """Esta clase implementa los métodos que permiten convertir una
    estructura de datos python continendo un examen, estructurado en
    metadatos, preguntas, etc. a su representación latex lista para
    compilar e imprimir"""

    def __init__(self, to_latex=True, progress=None):
        """Carga los templates latex del examen y las preguntas y asigna
        diferentes parámetros de configuración de jinja2 y pandoc"""
        latex_jinja_env = jinja2.Environment(
            variable_start_string='\\V{',
            variable_end_string='}',
            line_statement_prefix='%%',
            line_comment_prefix='%#',
            trim_blocks=True,
            autoescape=False,
            loader=jinja2.FileSystemLoader(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "templates")))
        )
        self.main_tex_template = latex_jinja_env.get_template('main-examen.template')
        self.problem_template = latex_jinja_env.get_template('problem.template')
        self.pregunta_sola_template = latex_jinja_env.get_template('pregunta-sola.template')
        self.pandoc_extra = ["--listings", "--wrap=preserve"]
        self.ids = 0
        self.to_latex=to_latex
        self.progress = progress

    def markdown_to_latex(self, txt):
        """Convierte cadena markdown a cadena latex, usando pandoc"""
        if self.to_latex:
            result = pypandoc.convert_text(txt, "latex", format="md", extra_args=self.pandoc_extra)
        else:
            result=txt
        return result.replace("\r\n", "\n") # Por si windows

    def unique_id(self, problem, simhash=True):
        """Calcula un id único para el problema. Puede basarse en el campo @id del
        propio problema, o bien en los contenidos del mismo, haciendo un hash (por defecto)
        El hash utilizado es simhash, que produce hashes similares si los contenidos son
        similares"""
        if not simhash:
            if "id" in problem:
                return str(problem["id"])
            if "@id" in problem:
                return problem["@id"].split("/")[-1]
            self.ids += 1
            return self.ids
        else:
            return "%x" % Simhash(problem["latex"]).value

    def convert_to_exam(self, data, simhash=False, only_ok=False, skip=True, skip_nores=True):
        """Recibe un diccionario python que representa el examen y lo convierte
        a LaTeX.

        Args:
            data: El diccionario python que contiene el examen, con campos
                  como "convocatoria", "fecha", "tipo", "autor", etc. Algunos de
                  ellos no son usados. Véanse los ejemplos YAML en la carpeta
                  de ejemplos.
        Returns:
            Una tupla cuyo primer elemento es una cadena que contiene la representación
            LaTeX del "documento principal" y cuyo segundo elemento es un array de
            problemas, siendo cada uno un diccionario con los campos originales presentes
            en "data" y dos campos adicionales: "filename" y "latex". El segundo es la
            representación LaTeX de la pregunta, respuesta, etc. y el primero es el
            nombre del fichero en el que ese latex debe ser guardado (pues es usado
            desde el documento principal en un `\\input`).
        """
        data.update(fecha=datetime.strptime(data["fecha"], "%Y%m%d").date())
        problemas = []
        N = len(data["problemas"])
        for i, p in enumerate(data["problemas"]):
            if self.progress:
                self.progress.update("Procesando problema {}/{}".format(i,N))
            if only_ok and "ok" not in p:
                continue
            if skip and "skip" in p:
                continue
            if skip_nores and "resumen" not in p:
                continue
            if "meta" not in p:
                p["meta"] = {}
                p["meta"]["resumen"] = p["resumen"] if "resumen" in p else "Sin resumen"
                p["meta"]["puntos"] = sum(c["puntos"] if "puntos" in c else 1 for c in p["cuestiones"])
                p["meta"]["n_cuestiones"] = len(p["cuestiones"])
            if "puntos" not in p:
                p["puntos"] = p["meta"]["puntos"]
            if "enunciado" not in p:
                p["enunciado"] = ""
            p["latex"] = self.convert_dict_to_problema(p)
            filename = "{}-{}.tex".format("-".join(p["tags"]),
                                          self.unique_id(p, simhash=simhash))
            p["filename"] = filename.replace(" ", "-").replace("_", "-")
            problemas.append(p)

        if self.progress:
            self.progress.update("Procesando documento principal")
        total_preguntas = len(problemas)
        total_puntos = sum(p["puntos"] for p in problemas)
        if total_puntos == 0:
	        valor_punto = float("inf")
        else:
            valor_punto = 10/total_puntos
        data.update(
            total_preguntas=total_preguntas,
            total_puntos=total_puntos,
            valor_punto=valor_punto
            )
        intro = jinja2.Template(data["intro"]).render(**data)
        data.update(
            intro=self.markdown_to_latex(intro)
            )
        resuelto = data.get("resuelto", "noresuelto")
        main_tex = self.main_tex_template.render(
            fecha=data["fecha"],
            asignatura=data["asignatura"],
            titulacion=data["titulacion"],
            convocatoria=data["convocatoria"],
            tipo=data["tipo"],
            resuelto=resuelto,
            intro=data["intro"],
            problemas=problemas)
        return main_tex, problemas

    def estimar_lineas(self, txt, ancho_linea):
        """Estima cuántas líneas de papel puede utilizar el texto dado,
        contando cuántas líneas lógicas tiene y asumiendo que en cada línea
        física caben `ancho_linea` caracteres."""
        lineas_fisicas = 0
        for linea_logica in txt.split("\n"):
            lineas_fisicas += len(linea_logica)//ancho_linea + 1
        return lineas_fisicas

    def convert_dict_to_problema(self, problem):
        probl = copy.deepcopy(problem)
        probl.update(
            tags=",".join(probl["tags"]),
            puntos=probl["meta"]["puntos"],
            enunciado=self.markdown_to_latex(probl["enunciado"]),
        )

        for q in probl["cuestiones"]:
            if "tam_hueco" not in  q:
                q["tam_hueco"] = 1.2 * (self.estimar_lineas(q.get("respuesta",""), 40) + 1)
            if "puntos" not in q:
                q["puntos"] = 1
            q.update(
                enunciado=self.markdown_to_latex(q["enunciado"]),
                respuesta=self.markdown_to_latex(q.get("respuesta", "")),
                explicacion=self.markdown_to_latex(q.get("explicacion", "")),
            )
        if len(probl["cuestiones"]) < 2:
            txt = self.pregunta_sola_template.render(
                q=probl["cuestiones"][0], **probl)
        else:
            txt = self.problem_template.render(**probl)
        return txt

