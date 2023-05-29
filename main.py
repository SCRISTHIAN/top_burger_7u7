import asyncio
from flask import Flask, jsonify, request
import pymysql
import aiomysql
from contextlib import asynccontextmanager

app = Flask(__name__)
# jwt = JWTManager(app)
# app.config['JWT_SECRET_KEY'] = 'IJDLZQVMpvbnBAuOsGBg'

# @app.route('/create_empleado', methods=['POST'])
# #@jwt_required()
# async def create_empleado():
#     #identity = get_jwt_identity()
#     #if identity['role'] != 'admin':
#     #   return jsonify({"error": "Unauthorized"}), 403
#     data = request.get_json()
#     result = await create_user(data)
    
#     if "error" in result:
#         return jsonify({"error": result["error"]}), 500
#     else:
#         return jsonify({"message": result["message"]}), 200

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


    
@app.route('/empleados', methods=['GET'])
async def get_empleados():
    # connection=await connect_to_database()
    # if connection:
    async with connect_to_database() as connection:
        try:
            async with connection.cursor() as cursor:
                sql = "SELECT ID_Empleado, Nombre, Usuario, Contrasenia, Rol FROM Empleado"
                await cursor.execute(sql)
                empleados = await cursor.fetchall()

                resultados = [{"id_empleado":empleado['ID_Empleado'],"nombre": empleado['Nombre'], "usuario": empleado['Usuario'], "contrasena": empleado['Contrasenia'], "rol": empleado['Rol']} for empleado in empleados]
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
    



if __name__ == '__main__':
    async def main():
        app.run(debug=True)

loop = asyncio.get_event_loop()
loop.run_until_complete(main())
