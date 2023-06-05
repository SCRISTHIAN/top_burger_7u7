import asyncio
import json
from flask import Flask, Response, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import check_password_hash, generate_password_hash
import pymysql
import aiomysql
from contextlib import asynccontextmanager

app = Flask(__name__)
jwt = JWTManager(app)
# app.config['JWT_SECRET_KEY'] = 'IJDLZQVMpvbnBAuOsGBg'



@asynccontextmanager
async def connect_to_database():
    connection = await aiomysql.connect(
        host='containers-us-west-24.railway.app',
        port=5828,
        user='root',
        password='IJDLZQVMpvbnBAuOsGBg',
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

                if not empleado or not check_password_hash(empleado['Contrasena'], password):
                    return jsonify({"error": "Invalid user or password"}), 401
                

                access_token = create_access_token(identity={"user": user, "role": empleado["Rol"]})
                return jsonify(access_token=access_token), 200           
        except pymysql.Error as e:
            return jsonify({"error":"Login failed! :{}".format(e)}),500
        finally:
            connection.close()


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

@app.route('/proveedores', methods = ['GET'])
async def get_proveedores():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                # Consulta los nombres de los clientes
                sql = "SELECT ID_Proveedor, Nombre, Telefono, Direccion FROM Proveedor;"
                await cursor.execute(sql)
                
                # Obtiene los resultados
                proveedores = await cursor.fetchall()
                
                resultados = [{"id_proveedor":proveedor['ID_Proveedor'],"nombre": proveedor['Nombre'], "telefono": proveedor['Telefono'], "direccion": proveedor['Direccion']} for proveedor in proveedores]
                return jsonify(resultados)
        
        except pymysql.Error as e:
            return jsonify({"error": "Database error: {}".format(e)}), 500
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
                res=[{"id_plato":platos["ID_Plato"],"nombre":platos["Nombre"],"precio":platos["Precio"],"tiempo_preparacion":platos["Tiempo_Preparacion"],"url_image":platos["Imagen_URL"]} for plato in platos]
                return jsonify(res)
        except pymysql.Error as e:
            return jsonify({"error": "Database error: {}".format(e)}), 500
        finally:
            connection.close()



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
    #identity = get_jwt_identity()
    #if identity['role'] != 'admin':
    #   return jsonify({"error": "Unauthorized"}), 403
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
    
@app.route('/ingredientes',methods=['GET'])
async def get_ingredientes():
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql="SELECT ID_Ingrediente, Nombre, Stock, Unidad_Medida FROM Ingrediente;"
                await cursor.execute(sql)
                ingredientes=await cursor.fetchall()
                res=[{"id_ingrediente":ingredientes["ID_Ingrediente"],"nombre":ingredientes["Nombre"],"stock":ingredientes["Stock"],"unidad_medida":ingredientes["Unidad_Medida"]} for ingrediente in ingredientes]
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
