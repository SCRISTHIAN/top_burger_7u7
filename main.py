
from dp_algorithm import bellman_algorithm
from flask import Flask, Response, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
from flask_cors import CORS
import pymysql
import aiomysql
from contextlib import asynccontextmanager

app = Flask(__name__)
app.config['JWT_SECRET_KEY'] = 'IJDLZQVMpvbnBAuOsGBg'
jwt = JWTManager(app)
CORS(app, resources={r"/*": {"origins": "*"}}, supports_credentials=True)

#ufa

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', '*')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response

@asynccontextmanager
async def connect_to_database():
    connection = await aiomysql.connect(
        # host='containers-us-west-24.railway.app',
        # port=5828,
        # user='root',
        # password='IJDLZQVMpvbnBAuOsGBg',
        # db='railway',
        # cursorclass=aiomysql.DictCursor
        host='containers-us-west-174.railway.app',
        port=6897,
        user='root',
        password='zV5wnoVB2E935xu6LqKk',
        db='railway',
        cursorclass=aiomysql.DictCursor
    )
    try:
        yield connection
        print("Conexión establecida")
    finally:
        connection.close()


@app.route('/login', methods=['POST'])
async def login():
    data = request.get_json()
    user = data.get('user')
    password = data.get('password')

    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT Usuario, Contrasena, Rol FROM Empleado WHERE Usuario = %s"
                await cursor.execute(sql, (user,))
                empleado = await cursor.fetchone()
                print(empleado)
                if not empleado or not check_password_hash(empleado['Contrasena'], password):
                    return jsonify({"error": "Invalid user or password"}), 401
                # RuntimeError: JWT_SECRET_KEY or flask SECRET_KEY must be set when using symmetric algorithm "HS256"

                access_token = create_access_token(identity={"user": user, "role": empleado["Rol"]})
                return jsonify(access_token=access_token), 200           
        except pymysql.Error as e:
            return jsonify({"error":"Login failed! :{}".format(e)}),500
        finally:
            connection.close()



@app.route('/ingresar_ingrediente', methods=['POST'])
async def ingresar_ingrediente():
    data = request.get_json()
    nombre_proveedor = data['nombre_proveedor']
    ingredientes = data['ingredientes']

    async with connect_to_database() as connection:
        try:
            # Buscar el ID del proveedor
            id_proveedor = await get_proveedor_id(connection, nombre_proveedor)

            for ingrediente in ingredientes:
                nombre_ingrediente = ingrediente['nombre']
                fecha_adquisicion = ingrediente['fecha_adquisicion']
                fecha_caducidad = ingrediente['fecha_caducidad']
                cantidad = ingrediente['cantidad']

                # Buscar el ID del ingrediente
                id_ingrediente = await get_ingrediente_id(connection, nombre_ingrediente)

                # Crear una nueva entrada en la tabla Lote_Ingrediente
                await insert_lote_ingrediente(connection, id_ingrediente, fecha_adquisicion, fecha_caducidad, cantidad)
                await add_ingrediente_to_proveedor(connection, id_proveedor, id_ingrediente)
                # Actualizar el stock del ingrediente
                await update_ingrediente_stock_new(connection, id_ingrediente, cantidad)

            return jsonify({"success": True, "message": "Ingredientes ingresados con éxito."})

        except Exception as e:
            return jsonify({"error":"Database error: {}".format(e)}),500


async def get_proveedor_id(connection, nombre_proveedor):
    async with connection.cursor() as cursor:
        sql = "SELECT ID_Proveedor FROM Proveedor WHERE Nombre = %s"
        await cursor.execute(sql, (nombre_proveedor,))
        result = await cursor.fetchone()
        return result['ID_Proveedor']


async def get_ingrediente_id(connection, nombre_ingrediente):
    async with connection.cursor() as cursor:
        sql = "SELECT ID_Ingrediente FROM Ingrediente WHERE Nombre = %s"
        await cursor.execute(sql, (nombre_ingrediente,))
        result = await cursor.fetchone()
        return result['ID_Ingrediente']


async def insert_lote_ingrediente(connection, id_ingrediente, fecha_adquisicion, fecha_caducidad, cantidad):
    async with connection.cursor() as cursor:
        sql = """
        INSERT INTO Lote_Ingrediente (ID_Ingrediente, Fecha_Adquisicion, Fecha_Caducidad, Cantidad) 
        VALUES (%s, %s, %s, %s)
        """
        await cursor.execute(sql, (id_ingrediente, fecha_adquisicion, fecha_caducidad, cantidad))
        await connection.commit()


async def update_ingrediente_stock_new(connection, id_ingrediente, cantidad):
    async with connection.cursor() as cursor:
        sql = "UPDATE Ingrediente SET Stock = Stock + %s WHERE ID_Ingrediente = %s"
        await cursor.execute(sql, (cantidad, id_ingrediente))
        await connection.commit()

async def add_ingrediente_to_proveedor(connection, id_proveedor, id_ingrediente):
    async with connection.cursor() as cursor:
        sql = """
        INSERT INTO Ingrediente_Proveedor (ID_Proveedor, ID_Ingrediente) 
        VALUES (%s, %s)
        ON DUPLICATE KEY UPDATE ID_Proveedor=VALUES(ID_Proveedor), ID_Ingrediente=VALUES(ID_Ingrediente)
        """
        await cursor.execute(sql, (id_proveedor, id_ingrediente))
        await connection.commit()

#CON GET
# CREAR PEDIDO 
@app.route('/create_pedido', methods=['POST', 'GET'])
async def create_pedido():
    data = request.get_json()
    cliente_id = data['cliente']['id']
    empleado_id = data['empleado']['id']
    platos = data['platos']

    async with connect_to_database() as connection:
        try:
            # Crear una nueva entrada en la tabla Pedido_Cliente
            pedido_id = await insert_pedido_cliente(connection, cliente_id, empleado_id)

            for plato in platos:
                plato_id = await get_plato_id(connection, plato['nombre'])
                cantidad = plato['cantidad']

                # Crear nuevas entradas en la tabla Pedido_Cliente_Plato
                await insert_pedido_cliente_plato(connection, pedido_id, plato_id, cantidad, plato['precio_vendido'])

                # Actualizar el stock de los ingredientes
                await update_ingrediente_stock(connection, plato_id, cantidad)

            return jsonify({"success": True, "message": "Pedido creado con éxito."})

        except Exception as e:
            return jsonify({"error":"Database error: {}".format(e)}),500


async def insert_pedido_cliente(connection, cliente_id, empleado_id):
    async with connection.cursor() as cursor:
        sql = "INSERT INTO Pedido_Cliente (Fecha, Estado, ID_Cliente, ID_Empleado) VALUES (CURDATE(), 'pendiente', %s, %s)"
        await cursor.execute(sql, (cliente_id, empleado_id))
        await connection.commit()
        return cursor.lastrowid

async def get_plato_id(connection, plato_nombre):
    async with connection.cursor() as cursor:
        sql = "SELECT ID_Plato FROM Plato WHERE Nombre = %s"
        await cursor.execute(sql, (plato_nombre,))
        result = await cursor.fetchone()
        return result['ID_Plato']

async def insert_pedido_cliente_plato(connection, pedido_id, plato_id, cantidad, precio_vendido):
    async with connection.cursor() as cursor:
        sql = "INSERT INTO Pedido_Cliente_Plato (ID_Pedido_Cliente, ID_Plato, Cantidad, Precio_Vendido) VALUES (%s, %s, %s, %s)"
        await cursor.execute(sql, (pedido_id, plato_id, cantidad, precio_vendido))
        await connection.commit()


async def update_ingrediente_stock(connection, plato_id, cantidad):
    async with connection.cursor() as cursor:
        # Obtén la cantidad necesaria de ingredientes para el plato
        sql = "SELECT Cantidad as required_quantity FROM Plato_Ingrediente WHERE ID_Plato = %s"
        await cursor.execute(sql, (plato_id,))
        required_quantity = (await cursor.fetchone())['required_quantity']

        # Verifica si hay suficiente stock antes de restarlo
        sql = """
        SELECT Stock FROM Ingrediente
        WHERE ID_Ingrediente IN (SELECT ID_Ingrediente FROM Plato_Ingrediente WHERE ID_Plato = %s)
        """
        await cursor.execute(sql, (plato_id,))
        available_stock = (await cursor.fetchone())['Stock']

        if required_quantity * cantidad <= available_stock:
            # Si hay suficiente stock, actualiza el stock
            sql = """
            UPDATE Ingrediente
            SET Stock = Stock - %s * required_quantity
            WHERE ID_Ingrediente IN (SELECT ID_Ingrediente FROM Plato_Ingrediente WHERE ID_Plato = %s)
            """
            await cursor.execute(sql, (cantidad, plato_id))
            await connection.commit()
        else:
            # Si no hay suficiente stock, lanza un error
            raise Exception("Not enough stock for the requested quantity of the dish.")
# DASHBOARD
# Usado para la VISTA DASHBOARD cuando piden los platos con stock bajo
@app.route('/inventariolow', methods= ['GET'])
async def inventariolow():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT * FROM PlatoViewPocasUnidades"
                await cursor.execute(sql)
                platos = await cursor.fetchall()

                return jsonify(platos)
        except pymysql.Error as e:
            return jsonify({"error":"Database Error :{}".format(e)}),500
        finally:
            connection.close()

@app.route ('/cantidadproveedores', methods= ['GET'])
async def cantidad_proveedores():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT TotalProveedores() AS Proveedores;"
                await cursor.execute(sql)
                cantidadproveedores = await cursor.fetchone()

                return jsonify(cantidadproveedores)
        except pymysql.Error as e:
            return jsonify({"error":"Database Error :{}".format(e)}),500

# Usado para la VISTA MENU DEL DIA Y PLATOS cuando pide ordenar por disponibilidad
@app.route('/menudeldia/orderedby',methods= ['GET'])
async def menu_del_dia_orderedby_dispo():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT * FROM MENU_DEL_DIA_ORDERED"
                await cursor.execute(sql)
                platos = await cursor.fetchall()

                return jsonify(platos)
        except pymysql.Error as e:
            return jsonify({"error":"Database Error :{}".format(e)}),500
        finally:
            connection.close()



# Usado para obtener los empleados, SIN USO EN NINGUNA DE LAS VISTAS, SOLO PARA PROPOSITOS DE PRUEBA
@app.route('/empleados', methods=['GET'])
async def get_empleados():
    # connection=await connect_to_database()
    # if connection:
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT ID_Empleado, Nombre, Usuario, Contrasena, Rol FROM Empleado"
                await cursor.execute(sql)
                empleados = await cursor.fetchall()

                resultados = [{"id_empleado":empleado['ID_Empleado'],"nombre": empleado['Nombre'], "usuario": empleado['Usuario'], "contrasena": empleado['Contrasena'], "rol": empleado['Rol']} for empleado in empleados]
                return jsonify(resultados)            
        except pymysql.Error as e:
            return jsonify({"error":"DataBase Error :{}".format(e)}),500
        finally:
            connection.close()


# Usado en la VISTA PROVEEDORES EN LA SECCION DE PROVEEDORES

@app.route('/proveedores', methods = ['GET'])
async def get_proveedores():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                # Consulta los nombres de los proveedores y los ingredientes que proporcionan
                sql = """
                SELECT Proveedor.ID_Proveedor, Proveedor.Nombre, Proveedor.Telefono, Proveedor.Direccion, GROUP_CONCAT(Ingrediente.Nombre) as Ingredientes
                FROM Proveedor
                LEFT JOIN Ingrediente_Proveedor ON Proveedor.ID_Proveedor = Ingrediente_Proveedor.ID_Proveedor
                LEFT JOIN Ingrediente ON Ingrediente_Proveedor.ID_Ingrediente = Ingrediente.ID_Ingrediente
                GROUP BY Proveedor.ID_Proveedor;
                """
                await cursor.execute(sql)
                
                # Obtiene los resultados
                proveedores = await cursor.fetchall()
                
                resultados = [{"id_proveedor":proveedor['ID_Proveedor'],"nombre": proveedor['Nombre'], "telefono": proveedor['Telefono'], "direccion": proveedor['Direccion'], "ingredientes": proveedor['Ingredientes']} for proveedor in proveedores]
                return jsonify(resultados)
        
        except pymysql.Error as e:
            return jsonify({"error": "Database error: {}".format(e)}), 500
        finally:
            connection.close()

# Quiero ver cuanto consume cada plato.
@app.route('/platos_ingredientes', methods = ['GET'])
async def get_platos_ingredientes():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                # Consulta los nombres de los clientes
                sql = "SELECT ID_Plato, ID_Ingrediente, Cantidad FROM Plato_Ingrediente;"
                await cursor.execute(sql)
                
                platos_ingredientes = await cursor.fetchall()
                
                return jsonify(platos_ingredientes)
        
        except pymysql.Error as e:
            return jsonify({"error": "Database error: {}".format(e)}), 500
        finally:
            connection.close()
    
# VISTA DESCRIPCION DEL PLATO
@app.route('/platosdescription/<int:plato_id>', methods = ['GET', 'POST'])
async def platos_description(plato_id):
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "CALL GetPlatoDetails(%s);"
                await cursor.execute(sql,(plato_id,))
                plato = await cursor.fetchone()

                return jsonify(plato)
        except pymysql.Error as e:
            return jsonify({"error":"Database error: {}".format(e)}),500
        finally:
            connection.close()






@app.route('/platos',methods=['GET'])
async def get_platos():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql="SELECT ID_Plato, Nombre, Precio, Tiempo_Preparacion, Imagen_URL FROM Plato;"
                await cursor.execute(sql)
                platos=await cursor.fetchall()
                res=[{"id_plato":plato["ID_Plato"],"nombre":plato["Nombre"],"precio":plato["Precio"],"tiempo_preparacion":plato["Tiempo_Preparacion"],"url_image":plato["Imagen_URL"]} for plato in platos]
                return jsonify(res)
        except pymysql.Error as e:
            return jsonify({"error": "Database error: {}".format(e)}), 500
        finally:
            connection.close()


@app.route('/ingredientes',methods=['GET'])
async def get_ingredientes():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql="SELECT ID_Ingrediente, Nombre, Stock, Unidad_Medida FROM Ingrediente;"
                await cursor.execute(sql)
                ingredientes=await cursor.fetchall()
                res=[{"id_ingrediente":ingrediente["ID_Ingrediente"],"nombre":ingrediente["Nombre"],"stock":ingrediente["Stock"],"unidad_medida":ingrediente["Unidad_Medida"]} for ingrediente in ingredientes]
                return jsonify(res)
        except pymysql.Error as e:
            return jsonify({"error": "Database error: {}".format(e)}), 500
        finally:
            connection.close()

@app.route('/clientes', methods=['GET'])
async def get_clientes():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT ID_Cliente, Nombre, Telefono, Direccion FROM Cliente;"
                await cursor.execute(sql)
                clientes = await cursor.fetchall()

                resultados = []
                for cliente in clientes:
                    resultado = {
                        "id_cliente": cliente['ID_Cliente'],
                        "nombre": cliente['Nombre'],
                        "telefono": cliente['Telefono'],
                        "direccion": cliente['Direccion']
                    }
                    resultados.append(resultado)

                return jsonify(resultados)

        except pymysql.Error as e:
            return jsonify({"error": "Database error: {}".format(e)}), 500

        finally:
            connection.close()


@app.route('/menudeldia', methods=['GET'])
async def get_menu():
    async with connect_to_database() as connection:
        try: 
            async with connection.cursor() as cursor:
                sql = "SELECT * FROM PlatoView"
                await cursor.execute(sql)
            
                platos = await cursor.fetchall()
                return jsonify(platos)
    
        except pymysql.Error as e:
            return jsonify({"error": "Database error: {}".format(e)}), 500
        finally:
            connection.close()


@app.route('/adquisicion', methods=['GET'])
async def dynamic_programming():
    inventario_mayonesa= [3,3,3,3]
    demanda_mayonesa = [3, 4, 4, 3]
    costo_pedido_mayonesa = [7.5, 7.5, 7.5, 7.5]
    costo_adquisicion_mayonesa = [70, 65,60,60 ]
    costo_almacenaje_mayonesa = [14,14,14,14]
    resultado_mayonesa = bellman_algorithm(demanda_mayonesa, inventario_mayonesa,costo_pedido_mayonesa, costo_adquisicion_mayonesa,costo_almacenaje_mayonesa)
    inventario_papa= [3,3,3,3]
    demanda_papa = [12,13,15,15]
    costo_pedido_papa = [15,15,15,15]
    costo_adquisicion_papa = [40,40,45,50]
    costo_almacenaje_papa = [27,27,27,27]
    resultado_papa = bellman_algorithm(demanda_papa, inventario_papa,costo_pedido_papa, costo_adquisicion_papa, costo_almacenaje_papa)
    resultados = {
        "mayonesa": resultado_mayonesa.tolist(),
        "papa": resultado_papa.tolist()
    }
    
    return jsonify(resultados)



# @app.route('/ingredientes', methods=['POST'])
# async def crear_ingredientes():
#     try:
#         data = await request.get_json()
#         nombre = data['nombre']
#         stock = data['stock']
#         unidad_medida = data['unidad_medida']
        
#         async with connect_to_database() as connection:
#             async with connection.cursor() as cursor:
#                 sql = "INSERT INTO Ingrediente (Nombre, Stock, Unidad_Medida) VALUES (%s, %s, %s)"
#                 await cursor.execute(sql, (nombre, stock, unidad_medida))
#                 await connection.commit()
#                 id_ingrediente = cursor.lastrowid
#                 return jsonify({"id_ingrediente": id_ingrediente, "mensaje": "Ingrediente creado exitosamente"})
    
#     except pymysql.Error as e:
#         return jsonify({"error": "Database error: {}".format(e)}), 500


@app.route('/ingredientes', methods=['POST'])
async def create_ingrediente():
    try:
        data =  request.get_json()
        nombre = data.get('nombre')
        stock = data.get('stock')
        unidad_medida = data.get('unidad_medida')

        async with connect_to_database() as connection:
            async with connection.cursor() as cursor:
                sql = "INSERT INTO Ingrediente (Nombre, Stock, Unidad_Medida) VALUES (%s, %s, %s)"
                await cursor.execute(sql, (nombre, stock, unidad_medida))
                await connection.commit()
                id_ingrediente = cursor.lastrowid
                return jsonify({"id_ingrediente": id_ingrediente, "mensaje": "Ingrediente creado exitosamente"})
    
    except Exception as e:
        return jsonify({"error": "Error en la solicitud POST: {}".format(str(e))}), 500

@app.route('/platos', methods=['POST'])
async def create_plato():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        precio = data.get('precio')
        tiempo_preparacion = data.get('tiempo_preparacion')
        url_imagen = data.get('url_imagen')

        async with connect_to_database() as connection:
            async with connection.cursor() as cursor:
                sql = "INSERT INTO Plato (Nombre, Precio, Tiempo_Preparacion, Imagen_URL) VALUES (%s, %s, %s, %s)"
                await cursor.execute(sql, (nombre, precio, tiempo_preparacion, url_imagen))
                await connection.commit()
                id_plato = cursor.lastrowid
                return jsonify({"id_plato": id_plato, "mensaje": "Plato creado exitosamente"})

    except Exception as e:
        return jsonify({"error": "Error en la solicitud POST: {}".format(str(e))}), 500

@app.route('/empleados', methods=['POST'])
@jwt_required()
async def create_empleado():
    identity = get_jwt_identity()
    if identity['role'] != 'Admin':
       return jsonify({"error": "Unauthorized"}), 403
    data = request.get_json()
    name = data.get('name')
    user = data.get('user')
    password = data.get('password')
    role = data.get('role')
    hashed_password = generate_password_hash(password)

    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "INSERT INTO Empleado (Nombre, Usuario, Contrasena, Rol) VALUES (%s, %s, %s, %s)"
                await cursor.execute(sql, (name ,user, hashed_password, role))
                await connection.commit()

                return jsonify({"message": "User created successfully"}), 200
          
        except pymysql.Error as e:
            return jsonify({"error":"Create Empleado Failed! :{}".format(e)}),500
        finally:
            connection.close()


@app.route('/proveedores', methods=['POST'])
async def create_proveedor():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        telefono = data.get('telefono')
        direccion = data.get('direccion')

        async with connect_to_database() as connection:
            async with connection.cursor() as cursor:
                sql = "INSERT INTO Proveedor (Nombre, Telefono, Direccion) VALUES (%s, %s, %s)"
                await cursor.execute(sql, (nombre, telefono, direccion))
                await connection.commit()
                id_proveedor = cursor.lastrowid
                return jsonify({"id_proveedor": id_proveedor, "mensaje": "Proveedor creado exitosamente"})

    except Exception as e:
        return jsonify({"error": "Error en la solicitud POST: {}".format(str(e))}), 500
    

@app.route('/clientes', methods=['POST'])
async def create_cliente():
    try:
        data = request.get_json()
        nombre = data.get('nombre')
        telefono = data.get('telefono')
        direccion = data.get('direccion')

        async with connect_to_database() as connection:
            async with connection.cursor() as cursor:
                sql = "INSERT INTO Cliente (Nombre, Telefono, Direccion) VALUES (%s, %s, %s)"
                await cursor.execute(sql, (nombre, telefono, direccion))
                await connection.commit()
                id_cliente = cursor.lastrowid
                return jsonify({"id_cliente": id_cliente, "mensaje": "Cliente creado exitosamente"})

    except Exception as e:
        return jsonify({"error": "Error en la solicitud POST: {}".format(str(e))}), 500


if __name__ == '__main__':
    app.run(debug=True)
