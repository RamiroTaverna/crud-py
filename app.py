from flask import Flask, render_template, request, redirect, session, send_from_directory
from flaskext.mysql import MySQL
from datetime import datetime
import os
from PIL import Image  # Importar Pillow para manipulación de imágenes

app = Flask(__name__)
app.secret_key = "rama"
mysql = MySQL()

# Config del server SQL
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = ''
app.config['MYSQL_DATABASE_DB'] = 'sitio'
mysql.init_app(app)

# Función para redimensionar la imagen
def redimensionar_y_recortar_imagen(ruta_imagen, tamaño=(1080, 1080)):
    """
    Redimensiona una imagen a 1080x1080 píxeles.
    - Si la imagen es más pequeña, se estira para llenar el espacio.
    - Si la imagen es más grande, se achica para ajustarse.
    - La imagen siempre se fuerza a ser cuadrada (1080x1080).
    :param ruta_imagen: Ruta de la imagen original.
    :param tamaño: Tupla con el tamaño deseado (ancho, alto).
    """
    with Image.open(ruta_imagen) as img:
        # Forzar la imagen a 1080x1080, estirándola o achicándola
        img = img.resize(tamaño, Image.Resampling.LANCZOS)
        
        # Guardar la imagen redimensionada
        img.save(ruta_imagen)

# INICIO SITIO
@app.route('/')
def inicio():
    return render_template('sitio/index.html')

@app.route('/contacto')
def contacto():
    return render_template('sitio/contacto.html')

# Ruta que renderiza imágenes
@app.route('/img/<imagen>')
def imagenes(imagen):
    print(imagen)
    return send_from_directory(os.path.join('templates/sitio/img'), imagen)

# Renderiza estilos en toda la web
@app.route('/css/<path:filename>')
def css_link(filename):
    return send_from_directory(os.path.join(app.root_path, 'templates/css'), filename)

@app.route('/productos')
def productos():
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `productos` ORDER BY `nombre` ASC")
    productos = cursor.fetchall()
    conexion.commit()
    print(productos)
    
    return render_template('sitio/productos.html', productos=productos)

@app.route('/nosotros')
def nosotros():
    return render_template('sitio/nosotros.html')

@app.route('/templates/<path:filename>')
def serve_static(filename):
    return send_from_directory('templates', filename)

# INICIO ADMIN
@app.route('/admin/')
def admin_index():
    if not 'login' in session:
        return redirect("/admin/login")
    
    return render_template('admin/index.html')

@app.route('/admin/login')
def admin_login():
    return render_template('admin/login.html')

@app.route('/admin/login', methods=['POST'])
def admin_login_post():
    _user = request.form['txtUsuario']
    _password = request.form['txtPassword']
    print(_user)
    print(_password)
    
    if _user == "admin" and _password == "1234":
        session["login"] = True
        session["usuario"] = "Administrador"
        return redirect("/admin")
    
    return render_template("admin/login.html", mensaje="Acceso denegado.")

@app.route('/admin/cerrar')
def admin_login_cerrar():
    session.clear()
    return redirect('/admin/login')

@app.route('/admin/productos')
def admin_productos():
    if not 'login' in session:
        return redirect("/admin/login")
    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT * FROM `productos`")
    productos = cursor.fetchall()
    conexion.commit()
    print(productos)
    
    return render_template('/admin/productos.html', productos=productos)

# Solicitud POST para guardar los productos
@app.route('/admin/productos/guardar', methods=['POST'])
def admin_productos_guardar():
    if not 'login' in session:
        return redirect("/admin/login")
    
    _nombre = request.form['txtNombre'].upper()
    _url = request.form['txtURL']
    _img = request.files['txtImagen']
    
    # Inicializa las alertas
    alertaNombre = ""
    alertaLink = ""
    alertaImg = ""
    
    # Validar campos
    if _nombre == "":
        alertaNombre = "Escribí un nombre para el producto."
    if _url == "":
        alertaLink = "Escribí un link para el producto."
    if _img.filename == "":
        alertaImg = "Selecciona una imagen."
    
    # Si hay alguna alerta, renderiza el template con los valores y las alertas
    if alertaNombre or alertaLink or alertaImg:
        return render_template("admin/productos.html", 
                             alertaNombre=alertaNombre, 
                             alertaLink=alertaLink, 
                             alertaImg=alertaImg,
                             nombre=_nombre,  # Mantener el valor del nombre
                             url=_url)       # Mantener el valor del URL
    
    # Si no hay alertas, procesa la imagen y guarda en la base de datos
    tiempo = datetime.now()
    horaActual = tiempo.strftime('%Y%H%M%S')
    
    if _img.filename != "":
        nuevoNombre = horaActual + "_" + _img.filename
        ruta_temporal = "templates/sitio/img/" + nuevoNombre
        
        # Guardar la imagen temporalmente
        _img.save(ruta_temporal)
        
        # Redimensionar la imagen a 1080x1080
        redimensionar_y_recortar_imagen(ruta_temporal, tamaño=(1080, 1080))
    
    sql = "INSERT INTO `productos` (`id`, `nombre`, `imagen`, `url`) VALUES (NULL, %s, %s, %s);"
    datos = (_nombre, nuevoNombre, _url)
    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute(sql, datos)
    conexion.commit()
    
    return redirect('/admin/productos')

@app.route('/admin/productos/borrar', methods=['POST'])
def admin_productos_borrar():
    if not 'login' in session:
        return redirect("/admin/login")
    
    _id = request.form['txtID']
    print(_id)
    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("SELECT imagen FROM `productos` WHERE id=%s", (_id))
    productos = cursor.fetchall()
    conexion.commit()
    print(productos)
    
    if os.path.exists("templates/sitio/img/" + str(productos[0][0])):
        os.unlink("templates/sitio/img/" + str(productos[0][0]))
    
    conexion = mysql.connect()
    cursor = conexion.cursor()
    cursor.execute("DELETE FROM productos WHERE id=%s", (_id))
    conexion.commit()
    
    return redirect('/admin/productos')

if __name__ == '__main__':
    app.run(debug=True)