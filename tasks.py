import time
import json
import hashlib
import os
import io

from rq import get_current_job
import requests
from examtool import converter, dumper
from diskcache import Index


LATEX2PDF_URL = os.getenv("LATEX_ONLINE_URL", "http://wexam-pdf:2700")

class RQprogress(object):
    """Actualiza el estado de la tarea en redis"""
    def __init__(self):
        self.job = get_current_job()

    def update(self, msg):
        self.job.meta["progress"] = msg
        self.job.save_meta()


def archivar_resultado(main_tex, main_name, problemas, filename, formato):
    """Vuelca el resultado a disco, a un archivo .zip o .tar.gz"""

    nombre = filename
    if formato=="zip":
        dump = dumper.ZipFile(nombre + ".zip")
    else:
        dump = dumper.TarFile(nombre + ".tar.gz")
    with dump as d:
        d.dump(main_tex, problemas)
    return d.name

cache = Index("/tmp/json2latex/cache")

def json2latex(data, main_name="examen.tex", formato="tgz"):
    progress = RQprogress()
    md5 = hashlib.md5("{}{}{}".format(data, main_name, formato).encode("utf8")).hexdigest()
    if md5 in cache:
        return cache[md5]
    datos = json.loads(data)
    main_tex, problemas = (converter.Examen2Tex(to_latex=True, progress=progress)
                           .convert_to_exam(datos, skip=False)
    )
    progress.update("Volcando resultados a fichero")
    f = archivar_resultado(main_tex=main_tex,
                           main_name=main_name,
                           problemas=problemas,
                           filename="{}/{}".format("/tmp", md5),
                           formato=formato)
    with open(f, "rb") as f_tar:
        content = f_tar.read()
    resultado = (md5, datos["total_preguntas"], datos["total_puntos"], content)
    cache[md5] = resultado
    return resultado


def latex2pdf(data, main_name="examen.tex"):
    md5 = hashlib.md5(data).hexdigest()
    if md5 in cache:
        return cache[md5]
    pdf = get_pdf_conversion(data, main_name)
    cache[md5] = pdf
    return pdf


def get_pdf_conversion(data, main_name):
    url = "{}/data?target={}&command=xelatex".format(LATEX2PDF_URL, main_name)
    tgz = io.BytesIO(data)
    files = { 'file': tgz }
    r = requests.post(url, files=files)
    if r.status_code == 200:
        return r.content

def json2pdf(data, main_name="examen.tex", formato="pdf"):
    md5, _, _, tgz = json2latex(data, main_name=main_name, formato="tgz")
    pdf = latex2pdf(tgz, main_name=main_name)
    return pdf
