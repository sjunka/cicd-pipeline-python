# cicd-pipeline-python

Taller Entregable 2 del curso Integración y Entrega Continua de Software (SI6008), Universidad EAFIT.

Pipeline de CI para una calculadora web en Flask: Black, Pylint y Flake8, pruebas unitarias y de componente con cobertura, pruebas de aceptación con Selenium contra la imagen Docker, análisis en SonarCloud y publicación de la imagen en Docker Hub.

## Integrantes

Texto usado en `AUTOR`: `Sergio Junca`

| Nombre completo | Usuario de GitHub | Rol |
|---|---|---|
| Sergio Junca | [sjunka](https://github.com/sjunka) | Propietario del repositorio |

## Fases del pipeline

El workflow está en `.github/workflows/ci.yml` (job `build-and-test`).

| Fase | Herramientas |
|---|---|
| Disparo | GitHub Actions: `push` y `pull_request` a `main`, y `workflow_dispatch` |
| Checkout | `actions/checkout` con historial completo (`fetch-depth: 0`) para SonarCloud |
| Entorno | `actions/setup-python` (Python 3.13) y `pip install -r requirements-dev.txt` con versiones fijas |
| Análisis estático | Black (`--check`), Pylint y Flake8 |
| Pruebas unitarias y de componente | pytest y pytest-cov, con cobertura mínima del 80 % |
| Build | Imagen Docker (`python:3.13-slim`, Flask servido con Gunicorn) etiquetada con el SHA del commit |
| Pruebas de aceptación | Contenedor en ejecución y pruebas con Selenium; reporte con pytest-html |
| Reportes | `actions/upload-artifact` con cobertura, reportes de pruebas, Pylint y Flake8 |
| Quality gate | SonarCloud; si el quality gate no pasa, el pipeline falla |
| Publicación | Login con `DOCKERHUB_TOKEN` (GitHub Secrets) y push a Docker Hub con las etiquetas `sha` y `latest`, solo en push a `main` |
| Notificación | Estado del check en el PR; la protección de `main` exige `build-and-test` |

## Evidencias

- Pull Request de la sección 9: https://github.com/sjunka/cicd-pipeline-python/pull/1
- Ejecución fallida por el error intencional: https://github.com/sjunka/cicd-pipeline-python/actions/runs/42651209389
- Ejecución en verde del PR #1 después de corregir el error: https://github.com/sjunka/cicd-pipeline-python/actions/runs/42651370201
- Ejecución en verde por push a `main`: https://github.com/sjunka/cicd-pipeline-python/actions/runs/42650378808
- Proyecto en SonarCloud: https://sonarcloud.io/project/overview?id=sjunka_cicd-pipeline-python
- Imagen en Docker Hub: `sjunka/cicd-pipeline-python` (https://hub.docker.com/r/sjunka/cicd-pipeline-python)

## Respuestas

### 1. Ventajas de usar un pipeline de CI

- **Los errores se detectan apenas se suben.** Cada push y cada Pull Request corre las pruebas sin que nadie tenga que acordarse. En el PR de la sección 9 el error intencional en `restar` se detectó en unos 30 segundos, antes de llegar a `main`. Mientras más rápido aparece un error, más barato es corregirlo, porque todavía se sabe qué cambio lo causó.
- **Las mismas reglas de calidad para todos.** Black, Pylint, Flake8 y SonarCloud revisan el código igual sin importar quién lo escribió. SonarCloud encontró cosas que a simple vista pasaban, como la falta de protección CSRF y que la aplicación escuchaba en todas las interfaces de red. Eso evita discusiones de estilo en las revisiones y deja un registro objetivo de la calidad.
- **Lo que se entrega es exactamente lo que se probó.** La imagen se construye una vez, pasa las pruebas de aceptación y esa misma imagen se publica con la etiqueta del SHA del commit. Así se sabe qué versión del código hay en cada imagen y se puede volver a una anterior si algo falla.
- **`main` siempre queda en un estado que funciona.** Con la regla `proteger-main`, nada entra sin el pipeline en verde y la aprobación de otra persona, así que cualquiera puede partir de `main` sin heredar errores de otros.

### 2. Prueba unitaria, de componente y de aceptación

Como ejemplo tomo una aplicación web de pedidos para un restaurante: el cliente elige los platos, el sistema calcula el total con el impuesto al consumo y la propina, y envía el pedido a la cocina.

- **Unitaria:** prueba una función aislada, sin servidor, base de datos ni navegador. Probaría la función que calcula el total: con un subtotal de 50.000, impuesto del 8% y propina del 10%, el total debe ser 59.000, y un subtotal negativo debe lanzar un error.
- **De componente:** prueba una parte de la aplicación con sus piezas reales juntas (rutas, lógica y plantilla), pero sin levantar un servidor ni abrir un navegador. Probaría la ruta que recibe el pedido con el cliente de pruebas de Flask: con un pedido válido debe responder 201 y mostrar el total, y con un plato que no existe debe responder 400.
- **De aceptación:** prueba la aplicación como la usaría una persona, con un navegador real sobre la aplicación en ejecución. Con Selenium abriría la página, agregaría dos platos, confirmaría el pedido y verificaría que aparece "Pedido recibido" con el total correcto.

### 3. Pasos del workflow

| Paso | Qué hace | Para qué |
|---|---|---|
| Checkout | Descarga el código del repositorio con el historial completo (`fetch-depth: 0`). | Tener el código en el runner. SonarCloud usa el historial para saber qué código es nuevo. |
| Set up Python | Instala Python 3.13. | Usar la misma versión que el `Dockerfile` y evitar diferencias entre entornos. |
| Install dependencies | Instala `requirements-dev.txt`, que incluye `requirements.txt`. | Tener la aplicación, los linters y las herramientas de prueba con las versiones fijadas. |
| Run Black | Verifica el formato con `black app --check`. | Detener el pipeline si hay código sin formatear. |
| Run Pylint y Run Flake8 | Generan `pylint-report.txt` y `flake8-report.txt` con `--exit-zero`. | Pasar los hallazgos a SonarCloud, que decide con el Quality Gate. Solo fallan si la herramienta no puede ejecutarse. |
| Run Unit and Component Tests | Corre las pruebas unitarias y de componente con cobertura mínima del 80%. Genera `coverage.xml`. | Detener el pipeline si una prueba falla o si baja la cobertura. |
| Build Docker image | Construye la imagen una sola vez, etiquetada con el SHA del commit. | Tener un artefacto único e identificable para probar y publicar. |
| Start container | Ejecuta la imagen y espera hasta 30 segundos a que responda. | Probar la aplicación empaquetada, no solo el código. |
| Run Acceptance Tests | Corre las pruebas de Selenium contra el contenedor (`APP_BASE_URL=http://localhost:8000`). | Verificar que la aplicación funciona como la usaría una persona. |
| Show container logs on failure | Muestra los logs del contenedor si algo falló. | Facilitar el diagnóstico. |
| Upload Test Reports Artifacts | Sube los reportes aunque el pipeline falle. | Poder revisar cobertura, pruebas y linters después de la ejecución. |
| SonarCloud Scan | Envía el código y los reportes a SonarCloud y espera el Quality Gate. | Detener el pipeline si el código no cumple la calidad. |
| Login to Docker Hub | Inicia sesión con la variable `DOCKERHUB_USERNAME` y el secreto `DOCKERHUB_TOKEN`. Solo en push a `main`. | Poder publicar sin dejar credenciales en el código. |
| Push Docker image | Agrega la etiqueta `latest` a la imagen ya probada y publica las etiquetas SHA y `latest`. Solo en push a `main`. | Publicar exactamente la imagen que pasó todas las validaciones. |

### 4. Problemas y aprendizajes

**Sergio Junca:**

- El Python de Homebrew en mi Mac no podía crear entornos virtuales ni instalar paquetes: `pyexpat` no cargaba con la versión de `libexpat` de macOS 26.2. Lo resolví creando el entorno con el Python 3.13 que gestiona `uv` (`uv venv --python 3.13`).
- SonarCloud no mostró como *Security Hotspots* el modo debug, la falta de CSRF ni el `host="0.0.0.0"`, como describe el taller, sino como vulnerabilidades (issues). Como los issues se deben corregir en el código, quité `debug=True`, dejé `app.run` escuchando solo en localhost y activé la protección CSRF con `CSRFProtect` de Flask-WTF. Para eso agregué el token oculto al formulario y desactivé CSRF solo en el cliente de pruebas de Flask, que no envía el token.
- La protección CSRF necesita una `SECRET_KEY`. Al generarla aleatoria, cada uno de los 4 workers de Gunicorn tendría una clave distinta y el token fallaría según qué worker atendiera la petición. Lo resolví con `--preload` en el `Dockerfile`, que carga la aplicación una sola vez antes de crear los workers. Comprobé que un POST sin token responde 400 y que las pruebas de aceptación pasan contra el contenedor.
- Aprendí que un Quality Gate en verde no significa 0 issues: la primera ejecución pasó el Quality Gate con 14 issues abiertos, porque el Quality Gate evalúa el código nuevo. Hay que revisar también la vista **Overall Code**.

### 5. Construir, probar y publicar la misma imagen

- **Lo que se prueba es lo que se entrega.** Si la imagen se volviera a construir para publicarla, podría cambiar la imagen base o la versión de alguna dependencia, y lo publicado no sería lo que pasó las pruebas.
- **Se encuentran errores de empaquetado que las pruebas del código no ven.** Por ejemplo, si `flask-wtf` estuviera solo en `requirements-dev.txt`, las pruebas unitarias pasarían, pero la imagen fallaría al arrancar porque solo instala `requirements.txt`. Lo mismo con un archivo que no se copia en el `Dockerfile` o un comando de inicio mal escrito.
- **Trazabilidad.** Cada imagen tiene la etiqueta del SHA del commit, así se sabe qué código corre en cada entorno y se puede volver a una versión anterior conocida.

### 6. Pull Request de la sección 9

En el PR se agregaron tres pruebas:

- `test_sumar_decimales`: verifica `sumar(0.1, 0.2) == pytest.approx(0.3)`. Detectaría que la suma convierta a entero o redondee (`int(0.1) + int(0.2)` da 0).
- `test_restar_dos_negativos`: verifica `restar(-5, -3) == -2` y `restar(-3, -5) == 2`. Detectaría errores de signo, como que la resta sume o devuelva el valor absoluto.
- `test_index_post_un_numero_invalido`: envía el formulario con `2` y `abc`. Detectaría que la aplicación solo valide cuando los dos números son inválidos, o que falle con un error 500 en lugar de mostrar "Error: Introduce números válidos".

Con el error intencional (`restar` sumando), el pipeline falló en el paso **Run Unit and Component Tests**: fallaron `test_restar`, `test_restar_dos_negativos` y `test_index_post_restar`. No se ejecutaron *Build Docker image*, *Start container*, *Run Acceptance Tests*, *SonarCloud Scan*, *Login to Docker Hub* ni *Push Docker image*. Sí se ejecutaron *Show container logs on failure* y *Upload Test Reports Artifacts*, por sus condiciones `failure()` y `always()`.

El error no pudo llegar a `main` porque la regla `proteger-main` exige que el check `build-and-test` pase y que otra persona apruebe el PR, así que GitHub bloqueó el merge. Tampoco pudo llegar a Docker Hub: el pipeline se detuvo antes de construir la imagen, y la publicación solo ocurre en un push a `main`, es decir, después de un merge que no se podía hacer.
