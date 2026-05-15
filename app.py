import os
import re
from datetime import datetime, timezone, timedelta
from io import BytesIO

import psycopg2
from pymongo import MongoClient
from openpyxl import Workbook
from werkzeug.security import generate_password_hash, check_password_hash
from flask import Flask, render_template, request, redirect, flash, session, send_file

app = Flask(__name__)
app.secret_key = "clave_secreta"


# -----------------------------------------
# CONEXIÓN A LA BASE DE DATOS
# -----------------------------------------


def get_connection():
    return psycopg2.connect(os.environ["DATABASE_URL"])

def get_mongo():
    client = MongoClient(os.environ["MONGO_URL"])
    db = client["refugio"]
    return db
    


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
        AND activo=TRUE
""", (email,))
        
        usuario = cur.fetchone()

        cur.close()
        conn.close()

        if usuario and check_password_hash(usuario[3], password):
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
    LEFT JOIN usuarios
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
    edad = int(request.form["edad"])
    usuario_id = int(request.form["usuario_id"])

    conn = get_connection()
    cur = conn.cursor()

    
    cur.execute(
"""
INSERT INTO animales(nombre, especie, edad, usuario_id)
VALUES (%s,%s,%s,%s)
""",
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

    cur.execute("DELETE FROM animales WHERE id=%s", (id,))
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
    
    #encriptar contraseña
    password_hash = generate_password_hash(password)

    conn = get_connection()
    cur = conn.cursor()

    cur.execute(
"""
INSERT INTO usuarios(nombre,email,password)
VALUES(%s,%s,%s)
""",
(nombre,email,password_hash)
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

    cur.execute("DELETE FROM usuarios WHERE id=%s",(id,))
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
"""
UPDATE usuarios
SET nombre=%s,email=%s
WHERE id=%s
""",
(nombre,email,id)
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

@app.route("/test-mongo")
def test_mongo():

    try:
        db = get_mongo()

        db.adoptados.insert_one({
            "nombre": "Prueba",
            "especie": "Perro",
            "edad": 1
        })

        return "Mongo funcionando 🚀"

    except Exception as e:
        return f"Error Mongo: {e}"
    
@app.route("/adoptar/<int:id>", methods=["POST"])

def adoptar_animal(id):

    conn = None
    cur = None

    try:
        conn = get_connection()
        cur = conn.cursor()

        cur.execute("""
            SELECT id, nombre, especie, edad, adoptado
            FROM animales
            WHERE id = %s
            FOR UPDATE
        """, (id,))
        animal = cur.fetchone()

        if not animal:
            flash("El animal no existe")
            return redirect("/adopciones")

        if animal[4]:
            flash("Este animal ya fue adoptado")
            return redirect("/adopciones")

        cur.execute("""
            UPDATE animales
            SET adoptado = TRUE
            WHERE id = %s
        """, (id,))

        db = get_mongo()
        db.adoptados.insert_one({
            "animal_id": animal[0],
            "nombre": animal[1],
            "especie": animal[2],
            "edad": animal[3],
            "fecha_adopcion": datetime.now(timezone.utc)
        })

        conn.commit()
        flash(f"{animal[1]} fue adoptado exitosamente")

    except Exception as e:
        if conn:
            conn.rollback()
        print(e)
        flash("No se pudo completar la adopción. Intenta nuevamente.")
    finally:
        if cur:
            cur.close()
        if conn:
            conn.close()

    return redirect("/adopciones")

@app.route("/adoptados")
def adoptados():

    if "usuario" not in session:
        return redirect("/")

    try:
        db = get_mongo()
        adoptados_data = list(
            db.adoptados.find({}, {"_id": 0}).sort("fecha_adopcion", -1)
        )

        # 🔥 AJUSTE DE ZONA HORARIA
        for item in adoptados_data:
            fecha = item.get("fecha_adopcion")
            if fecha:
                fecha = fecha - timedelta(hours=5)
                item["fecha_adopcion"] = fecha.strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        print(e)
        flash("No se pudieron cargar los adoptados desde MongoDB")
        adoptados_data = []

    return render_template("adoptados.html", adoptados=adoptados_data)

@app.route("/adoptados/exportar")
def exportar_adoptados():

    if "usuario" not in session:
        return redirect("/")

    try:
        db = get_mongo()
        adoptados_data = list(
            db.adoptados.find({}, {"_id": 0}).sort("fecha_adopcion", -1)
        )

        wb = Workbook()
        ws = wb.active
        ws.title = "Adoptados"
        ws.append(["ID Animal", "Nombre", "Especie", "Edad", "Fecha Adopción"])

        for item in adoptados_data:
            fecha = item.get("fecha_adopcion")
            
            if fecha:
                fecha = fecha - timedelta(hours=5)

            if hasattr(fecha, "strftime"):
                fecha = fecha.strftime("%Y-%m-%d %H:%M:%S")

            ws.append([
                item.get("animal_id", ""),
                item.get("nombre", ""),
                item.get("especie", ""),
                item.get("edad", ""),
                fecha or ""
            ])

        output = BytesIO()
        wb.save(output)
        output.seek(0)

        return send_file(
            output,
            as_attachment=True,
            download_name="animales_adoptados.xlsx",
            mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        print(e)
        flash("No se pudo exportar el archivo Excel de adoptados")
        return redirect("/adoptados")
# -----------------------------------------
# EJECUTAR APP
# -----------------------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
