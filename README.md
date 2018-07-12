# Servicio wexam-latex

> Es parte de WeXaM. Para más detalles ver [wexam-main](https://github.com/jldiaz/wexam-main).

Este servicio se ejecuta en un contendor Docker. Ejecuta un "worker" de `rq` que está esperando por tareas en una cola redis llamada `json2latex-task`, para lo que se conecta a una máquina llamada `redis` donde redis debe estar escuchando en el puerto estándar.

Cuando recibe una tarea, carga el correspondiente módulo python y ejecuta la función requerida.

El módulo `tasks.py` contiene dos tareas a las que se puede enviar trabajo:

* `json2latex`: espera como parámetro una cadena con el json del examen, el nombre opcional que le dará al "archivo principal" latex (por defecto `examen.tex`) y el formato en que quiere el resultado (por defecto `"tgz"`, también se puede especificar `"zip"`). Procesa el json para generar un archivo latex separado para cada problema, más otro archivo "principal" que incluye a los anteriores, y empaqueta todos esos ficheros junto con `"examen.sty"` en un solo archivo (tgz o zip). Retorna una tupla con cuatro elementos:

    - El hash md5 del contenido (supérfluo, tenía un cometido inicial pero ahora no sería necesario)
    - El número de problemas (ficheros .tex) del examen
    - El total de puntos del examen
    - Un array de bytes con los contenidos del archivo en cuestión

      La tarea puede tardar, pues por debajo usa `pandoc` para convertir a tex cada problema, pero va actualizando su progreso a través de `redis`, por lo que el cliente que lanzó la tarea puede saber "por donde va".

      Si el mismo examen ya había sido procesado antes, la respuesta será mucho más rápido, pues lo guarda en una caché (en el contenedor, se borrará si el contenedor se reinicia)

* `latex2pdf`: espera como parámetro un array de bytes con formato `tgz` (como el que retorna el servicio anterior en el último elemento) y el nombre del archivo principal a compilar. Utiliza un servidor externo para hacer la compilación. La URL del servidor está de momento prefijada a `http://latex2pdf:2700` porque en mi despliegue tengo este servicio en otro contenedor con ese nombre y ese puerto.

    El valor retornado es un array de bytes con el PDF resultante.

    Si el mismo `tgz` ya había sido compilado y aún está en caché, se retornará inmediatamente, sin hacer uso del servicio mencionado. Si no lo tiene, lo enviará al servicio antes mencionado (el cual a su vez tiene otra caché)

En la carpeta `ejemplos-json` hay un cliente de ejemplo que muestra cómo usar la biblioteca `rq` para enviar trabajos a estas tareas.

# Despliegue

Este servicio se puede "dockerizar" con el `Dockerfile` aquí adjunto. Para lanzarlo se usará:

```
 docker run --rm -d --link some-redis:redis --link latex2pdf:latex2pdf --name json2latex json2latex
```

Lo que requiere que se hayan lanzado antes otros dos contenedores, uno conteniendo `redis` (que la línea anterior asume que ha sido llamado `some-redis`), y otro que conteiene `latex-online` (que la línea anterior supone ha sido llamado `latex2pdf`)


Durante el desarrollo, para no tener que reconstruir siempre la imagen docker, se puede usar este comando:

```
docker run --rm -d --link some-redis:redis --link latex2pdf:latex2pdf --name json2latex -v `pwd`:/usr/src/app json2latex
```


que monta la carpeta actual en el contenedor, para que se pueda modificar el código "en caliente".


# TO-DO

Sólo se cachean actualmente los resultados finales, en base al hash del examen completo. Una buena optimización sería cachear también los resultados parciales de convertir en latex cada uno de los problemas que componen el examen (en base al hash de cada problema). De este modo, al convertir en tex un examen diferente que contenga los mismos problemas el proceso sería más rápido. La compilación a pdf no podría acelerarse por esta vía, pues el .tgz resultante será necesariamente distinto.
