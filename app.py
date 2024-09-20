from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, Categorias, Roles, Usuarios, Proveedores, Productos, MovimientosInventario, Ventas, Productos, DetalleVentas
from config import Config
from datetime import datetime
from sqlalchemy import text

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)

@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        sql = db.text("EXEC sp_Login :email, :password")

        try:
            result = db.session.execute(sql, {'email': email, 'password': password})
            rows = result.fetchall()

            if rows:
                user = rows[0]._asdict() 
                rol = user.get('idRol') 
                session['usuarioSesion'] = user
                print(user)
                print(rol, "este es el ROL")
                if rol == 1:
                    return redirect(url_for('gestionar_ventas'))
                elif rol == 2:
                    return redirect(url_for('gestionar_usuarios'))
            else:
                flash("No se encontraron resultados o credenciales incorrectas.")

        except Exception as e:
            flash(f"Error: {e}")

    return render_template('Login.html')
@app.route('/usuarios', methods=['GET', 'POST'])
def gestionar_usuarios():
    if 'usuarioSesion' not in session:
        flash("Debes iniciar sesión para acceder a esta página.")
        return redirect(url_for('login'))

    usuario = session['usuarioSesion']
    idRol = usuario['idRol']

    if request.method == 'POST':
        if idRol == 1:
            action = request.form.get('action')

            # Agregar un usuario
            if action == 'Agregar':
                nombre = request.form.get('nombre')
                email = request.form.get('email')
                password = request.form.get('password')
                idRol = request.form.get('idRol')

                sql = text("EXEC sp_AgregarUsuario :nombre, :email, :password, :idRol")
                try:
                    db.session.execute(sql, {'nombre': nombre, 'email': email, 'password': password, 'idRol': idRol})
                    db.session.commit()
                    flash("Usuario agregado correctamente.")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error al agregar usuario: {e}")

            # Modificar un usuario
            elif action == 'Modificar':
                idUsuario = request.form.get('idUsuario')
                nombre = request.form.get('nombre')
                email = request.form.get('email')
                password = request.form.get('password')
                idRol = request.form.get('idRol')

                sql = text("EXEC sp_ModificarUsuario :idUsuario, :nombre, :email, :password, :idRol")
                try:
                    db.session.execute(sql, {'idUsuario': idUsuario, 'nombre': nombre, 'email': email, 'password': password, 'idRol': idRol})
                    db.session.commit()
                    flash("Usuario modificado correctamente.")
                except Exception as e:
                    db.session.rollback()
                    flash(f"Error al modificar usuario: {e}")

        elif idRol == 1 and request.form.get('action') == 'Eliminar':
            idUsuario = request.form.get('idUsuario')

            sql = text("EXEC sp_EliminarUsuario :idUsuario")
            try:
                db.session.execute(sql, {'idUsuario': idUsuario})
                db.session.commit()
                flash("Usuario eliminado correctamente.")
            except Exception as e:
                db.session.rollback()
                flash(f"Error al eliminar usuario: {e}")

    # Listar usuarios
    usuarios = db.session.execute(text("SELECT * FROM Usuarios")).fetchall()

    return render_template('gestionar_usuarios.html', usuarios=usuarios, idRol=idRol)

@app.route('/ventas', methods=['GET', 'POST'])
def gestionar_ventas():
    if 'usuarioSesion' not in session:
        flash("Debes iniciar sesión para acceder a esta página.")
        return redirect(url_for('login'))

    query = request.args.get('q')
    page = request.args.get('page', 1, type=int) 
    per_page = 5  

    if query:
        productos = Productos.query.filter(
            Productos.nombre.ilike(f'%{query}%') | Productos.descripcion.ilike(f'%{query}%')
        ).order_by(Productos.nombre).paginate(page=page, per_page=per_page)  # Agregamos ORDER BY
    else:
        productos = Productos.query.order_by(Productos.nombre).paginate(page=page, per_page=per_page)  # Agregamos ORDER BY

    usuario = session['usuarioSesion']

    if request.method == 'POST':
        productos_seleccionados = request.form.getlist('productos[]')
        cantidades = request.form.getlist('cantidades[]')
        total_venta = 0

        venta = Ventas(
            idUsuario=usuario['idUsuario'],
            metodoPago=request.form.get('metodoPago'),
            cliente=request.form.get('cliente'),
            observaciones=request.form.get('observaciones'),
            totalVenta=0  # Inicialmente 0, se actualizará más tarde
        )
        db.session.add(venta)
        db.session.commit()

        for i, idProducto in enumerate(productos_seleccionados):
            producto = Productos.query.get(idProducto)
            cantidad = int(cantidades[i])

            if cantidad > producto.cantidadEnStock:
                flash(f"La cantidad solicitada para {producto.nombre} excede el stock disponible.")
                return redirect(url_for('gestionar_ventas'))

            subtotal = producto.precioVenta * cantidad
            total_venta += subtotal

            detalle = DetalleVentas(
                idVenta=venta.idVenta,
                idProducto=producto.idProducto,
                cantidad=cantidad,
                precioUnitario=producto.precioVenta,
                subtotal=subtotal
            )
            db.session.add(detalle)

            producto.cantidadEnStock -= cantidad

        venta.totalVenta = total_venta
        db.session.commit()

        flash("Venta realizada con éxito.")
        return redirect(url_for('gestionar_ventas'))

    return render_template('gestionar_ventas.html', productos=productos)
