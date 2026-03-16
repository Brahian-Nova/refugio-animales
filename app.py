import os

from flask import Flask, render_template, request, redirect, flash, session
import psycopg2
import re

app = Flask(__name__)
app.secret_key = "clave_secreta"


# -----------------------------------------
# CONEXIÓN A LA BASE DE DATOS
# -----------------------------------------


def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])
        
    


# -----------------------------------------
# LOGIN
# -----------------------------------------
@app.route("/")
def login():

    # si ya inició sesión no mostrar login
    if "usuario" in session:
        return redirect("/menu")

    return render_template("login.html")


# -----------------------------------------
# VALIDAR LOGIN
# -----------------------------------------
@app.route("/validar", methods=["POST"])
def validar():

    email = request.form["email"].strip()
    password = request.form["password"].strip()

    if email == "" or password == "":
        flash("Todos los campos son obligatorios")
        return redirect("/")

    patron_email = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    if not re.match(patron_email, email):
        flash("Formato de correo inválido")
        return redirect("/")

    if len(password) < 4:
        flash("La contraseña debe tener al menos 4 caracteres")
        return redirect("/")

    try:

        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT * 
            FROM usuarios
            WHERE LOWER(email)=LOWER(%s)
            AND password=%s
            AND activo=TRUE
        """, (email, password))

        usuario = cur.fetchone()

        cur.close()
        conn.close()

        if usuario:
            session["usuario"] = usuario[1]
            return redirect("/menu")
        else:
            flash("Usuario o contraseña incorrectos")
            return redirect("/")

    except Exception as e:
        print(e)
        flash("Error de conexión con la base de datos")
        return redirect("/")


# -----------------------------------------
# MENÚ PRINCIPAL
# -----------------------------------------
@app.route("/menu")
def menu():

    if "usuario" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) FROM usuarios")
    total_usuarios = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM animales")
    total_animales = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM animales WHERE adoptado = TRUE")
    adoptados = cur.fetchone()[0]

    cur.close()
    conn.close()

    return render_template(
        "menu.html",
        usuario=session["usuario"],
        total_usuarios=total_usuarios,
        total_animales=total_animales,
        adoptados=adoptados
    )


# -----------------------------------------
# CERRAR SESIÓN
# -----------------------------------------
@app.route("/logout")
def logout():
    session.pop("usuario", None)
    return redirect("/")


# -----------------------------------------
# ANIMALES
# -----------------------------------------
@app.route("/animales")
def animales():

    if "usuario" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT animales.id,
           animales.nombre,
           animales.especie,
           animales.edad,
           usuarios.nombre
    FROM animales
    JOIN usuarios
    ON animales.usuario_id = usuarios.id
    """)

    animales = cur.fetchall()

    cur.execute("SELECT id, nombre FROM usuarios")
    usuarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template(
        "animales.html",
        animales=animales,
        usuarios=usuarios
    )


# -----------------------------------------
# INSERTAR ANIMAL
# -----------------------------------------
@app.route("/insertar_animal", methods=["POST"])
def insertar_animal():

    if "usuario" not in session:
        return redirect("/")

    nombre = request.form["nombre"].strip()
    especie = request.form["especie"].strip()
    edad = request.form["edad"]
    usuario_id = request.form["usuario_id"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "CALL insertar_animal(%s,%s,%s,%s)",
        (nombre, especie, edad, usuario_id)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/animales")


# -----------------------------------------
# ELIMINAR ANIMAL
# -----------------------------------------
@app.route("/eliminar_animal/<int:id>")
def eliminar_animal(id):

    if "usuario" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("CALL eliminar_animal(%s)", (id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/animales")


# -----------------------------------------
# USUARIOS
# -----------------------------------------
@app.route("/usuarios")
def usuarios():

    if "usuario" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios")
    usuarios = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("usuarios.html", usuarios=usuarios)


# INSERTAR USUARIO
@app.route("/usuarios/insertar", methods=["POST"])
def insertar_usuario():

    if "usuario" not in session:
        return redirect("/")

    nombre = request.form["nombre"]
    email = request.form["email"]
    password = request.form["password"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "CALL insertar_usuario(%s,%s,%s)",
        (nombre, email, password)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/usuarios")


# ELIMINAR USUARIO
@app.route("/usuarios/eliminar/<int:id>")
def eliminar_usuario(id):

    if "usuario" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("CALL eliminar_usuario(%s)", (id,))
    conn.commit()

    cur.close()
    conn.close()

    return redirect("/usuarios")


# EDITAR USUARIO
@app.route("/usuarios/editar/<int:id>")
def editar_usuario(id):

    if "usuario" not in session:
        return redirect("/")

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM usuarios WHERE id=%s", (id,))
    usuario = cur.fetchone()

    cur.close()
    conn.close()

    return render_template("editar_usuario.html", usuario=usuario)


# ACTUALIZAR USUARIO
@app.route("/usuarios/actualizar", methods=["POST"])
def actualizar_usuario():

    if "usuario" not in session:
        return redirect("/")

    id = request.form["id"]
    nombre = request.form["nombre"]
    email = request.form["email"]

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
        "CALL actualizar_usuario(%s,%s,%s)",
        (id, nombre, email)
    )

    conn.commit()

    cur.close()
    conn.close()

    return redirect("/usuarios")


# -----------------------------------------
# PÁGINA PÚBLICA DE ADOPCIONES
# -----------------------------------------
@app.route("/adopciones")
def adopciones():

    conn = get_connection()
    cur = conn.cursor()

    cur.execute("""
    SELECT id,nombre,especie,edad
    FROM animales
    WHERE adoptado = FALSE
    """)

    animales = cur.fetchall()

    cur.close()
    conn.close()

    return render_template("adopciones.html", animales=animales)


# -----------------------------------------
# EJECUTAR APP
# -----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
