from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime
import pytz
import requests

app = Flask(__name__)

# Configuración de zona horaria
ZONA_HORARIA = pytz.timezone('America/La_Paz')

# Configuración de Telegram (Reemplaza con tus credenciales)
TELEGRAM_TOKEN = '8838884467:AAHecX5VrBy0a4qAjKycerAfxDIyuc97mqo'
TELEGRAM_CHAT_ID = '1690149604'

# Configuración de la base de datos
DB_PATH = os.path.join(os.path.dirname(__file__), 'finanzas.db')

def conectar_db():
    """Conecta a la base de datos SQLite"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def inicializar_db():
    """Crea la tabla de transacciones si no existe"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS transacciones (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tipo TEXT NOT NULL,
            categoria TEXT NOT NULL,
            monto REAL NOT NULL,
            descripcion TEXT,
            fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Insertar datos de ejemplo si la tabla está vacía
    cursor.execute('SELECT COUNT(*) as count FROM transacciones')
    if cursor.fetchone()['count'] == 0:
        # Obtener fecha/hora actual en zona horaria de Bolivia
        ahora_bolivia = datetime.now(ZONA_HORARIA).strftime('%Y-%m-%d %H:%M:%S')
        
        datos_iniciales = [
            ('ingreso', 'Sueldo', 2500.0, 'Pago mensual', ahora_bolivia),
            ('gasto', 'Alquiler', 800.0, 'Mes corriente', ahora_bolivia),
            ('gasto', 'Comida', 150.0, 'Supermercado', ahora_bolivia)
        ]
        cursor.executemany(
            'INSERT INTO transacciones (tipo, categoria, monto, descripcion, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
            datos_iniciales
        )
    
    conn.commit()
    conn.close()

def obtener_transacciones():
    """Obtiene todas las transacciones de la base de datos"""
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM transacciones ORDER BY fecha_creacion DESC')
    transacciones = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return transacciones

def calcular_totales():
    """Calcula los totales de ingresos, gastos y balance"""
    transacciones = obtener_transacciones()
    ingresos = sum(t["monto"] for t in transacciones if t["tipo"] == "ingreso")
    gastos = sum(t["monto"] for t in transacciones if t["tipo"] == "gasto")
    balance = ingresos - gastos
    return {"ingresos": ingresos, "gastos": gastos, "balance": balance}

def obtener_gastos_hoy():
    """Obtiene gastos de hoy en zona horaria de Bolivia"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Obtener fecha de hoy en Bolivia
    hoy_bolivia = datetime.now(ZONA_HORARIA).strftime('%Y-%m-%d')
    
    cursor.execute(
        'SELECT * FROM transacciones WHERE tipo = "gasto" AND DATE(fecha_creacion) = ?',
        (hoy_bolivia,)
    )
    gastos_hoy = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    total_hoy = sum(t["monto"] for t in gastos_hoy)
    return gastos_hoy, total_hoy

def obtener_gastos_mes():
    """Obtiene gastos del mes actual"""
    conn = conectar_db()
    cursor = conn.cursor()
    
    # Obtener mes y año actual en Bolivia
    ahora = datetime.now(ZONA_HORARIA)
    mes_actual = ahora.strftime('%Y-%m')
    
    cursor.execute(
        'SELECT * FROM transacciones WHERE tipo = "gasto" AND fecha_creacion LIKE ?',
        (f'{mes_actual}%',)
    )
    gastos_mes = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    total_mes = sum(t["monto"] for t in gastos_mes)
    return gastos_mes, total_mes

def enviar_resumen_telegram():
    """Envía resumen de gastos a Telegram"""
    # Validar que están configuradas las credenciales
    if TELEGRAM_TOKEN == 'TU_TOKEN_DE_BOT_AQUI' or TELEGRAM_CHAT_ID == 'TU_CHAT_ID_AQUI':
        print("⚠️ Telegram no configurado. Agrega TELEGRAM_TOKEN y TELEGRAM_CHAT_ID en finance_app.py")
        return False
    
    try:
        gastos_hoy, total_hoy = obtener_gastos_hoy()
        gastos_mes, total_mes = obtener_gastos_mes()
        totales = calcular_totales()
        
        # Construir mensaje formateado
        fecha_hoy = datetime.now(ZONA_HORARIA).strftime('%d/%m/%Y %H:%M:%S')
        
        mensaje = f"""
📊 *Resumen de Finanzas - {fecha_hoy}*

*💰 GASTOS DE HOY*
Total: ${total_hoy:.2f}
Transacciones: {len(gastos_hoy)}

*📈 GASTOS DEL MES*
Total: ${total_mes:.2f}
Transacciones: {len(gastos_mes)}

*💹 BALANCE GENERAL*
Ingresos: ${totales['ingresos']:.2f}
Gastos: ${totales['gastos']:.2f}
Balance: ${totales['balance']:.2f}

_App de Control de Finanzas_
"""
        
        # Enviar a Telegram
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        params = {
            'chat_id': TELEGRAM_CHAT_ID,
            'text': mensaje,
            'parse_mode': 'Markdown'
        }
        
        respuesta = requests.post(url, params=params)
        
        if respuesta.status_code == 200:
            print("✅ Mensaje enviado a Telegram exitosamente")
            return True
        else:
            print(f"❌ Error al enviar a Telegram: {respuesta.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error en enviar_resumen_telegram: {str(e)}")
        return False

@app.route('/')
def index():
    transacciones = obtener_transacciones()
    totales = calcular_totales()
    return render_template('index.html', transacciones=transacciones, totales=totales)

@app.route('/agregar', methods=['POST'])
def agregar_transaccion():
    tipo = request.form.get('tipo')
    categoria = request.form.get('categoria')
    try:
        monto = float(request.form.get('monto', 0))
    except ValueError:
        monto = 0.0
    descripcion = request.form.get('descripcion', '')

    if monto > 0 and categoria:
        # Obtener fecha/hora actual en zona horaria de Bolivia
        ahora_bolivia = datetime.now(ZONA_HORARIA).strftime('%Y-%m-%d %H:%M:%S')
        
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO transacciones (tipo, categoria, monto, descripcion, fecha_creacion) VALUES (?, ?, ?, ?, ?)',
            (tipo, categoria, monto, descripcion, ahora_bolivia)
        )
        conn.commit()
        conn.close()
        
        # Enviar resumen a Telegram si es un gasto
        if tipo == "gasto":
            enviar_resumen_telegram()
    
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id_transaccion>')
def eliminar_transaccion(id_transaccion):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transacciones WHERE id = ?', (id_transaccion,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

@app.route('/ejecutar-resumen-diario')
def ejecutar_resumen_diario():
    """Ruta para ejecutar manualmente el envío del resumen a Telegram"""
    resultado = enviar_resumen_telegram()
    if resultado:
        return "✅ Resumen enviado a Telegram exitosamente"
    else:
        return "❌ Error al enviar el resumen. Verifica las credenciales de Telegram."

if __name__ == '__main__':
    # Inicializar la base de datos
    inicializar_db()
    print("✅ App iniciada - cron-job.org ejecutará el resumen diariamente a las 00:00")
    # El servidor corre en modo debug y se actualiza solo si haces cambios
    app.run(debug=True, port=5000)