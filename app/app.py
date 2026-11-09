# app/app.py
"""Aplicación web Flask de la calculadora."""

import os

from flask import Flask, render_template, request
from flask_wtf.csrf import CSRFProtect

from .calculadora import sumar, restar, multiplicar, dividir

app = Flask(__name__)
# Clave aleatoria para firmar el token CSRF. En Docker, Gunicorn usa --preload
# para que todos los workers compartan esta misma clave.
app.config["SECRET_KEY"] = os.urandom(32)
csrf = CSRFProtect(app)


@app.route("/", methods=["GET", "POST"])
def index():
    """Muestra el formulario y, si llega un POST, calcula y muestra el resultado."""
    resultado = None
    if request.method == "POST":
        try:
            num1 = float(request.form["num1"])
            num2 = float(request.form["num2"])
            operacion = request.form["operacion"]

            if operacion == "sumar":
                resultado = sumar(num1, num2)
            elif operacion == "restar":
                resultado = restar(num1, num2)
            elif operacion == "multiplicar":
                resultado = multiplicar(num1, num2)
            elif operacion == "dividir":
                resultado = dividir(num1, num2)
            else:
                resultado = "Operación no válida"
        except ValueError:
            resultado = "Error: Introduce números válidos"
        except ZeroDivisionError:
            resultado = "Error: No se puede dividir por cero"

    return render_template("index.html", resultado=resultado)


if __name__ == "__main__":  # pragma: no cover
    app.run(port=5000)
