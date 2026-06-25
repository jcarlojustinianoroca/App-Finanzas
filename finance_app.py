from flask import Flask, render_template, request, redirect, url_for
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)

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
        datos_iniciales = [
            ('ingreso', 'Sueldo', 2500.0, 'Pago mensual'),
            ('gasto', 'Alquiler', 800.0, 'Mes corriente'),
            ('gasto', 'Comida', 150.0, 'Supermercado')
        ]
        cursor.executemany(
            'INSERT INTO transacciones (tipo, categoria, monto, descripcion) VALUES (?, ?, ?, ?)',
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
        conn = conectar_db()
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO transacciones (tipo, categoria, monto, descripcion) VALUES (?, ?, ?, ?)',
            (tipo, categoria, monto, descripcion)
        )
        conn.commit()
        conn.close()
    
    return redirect(url_for('index'))

@app.route('/eliminar/<int:id_transaccion>')
def eliminar_transaccion(id_transaccion):
    conn = conectar_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM transacciones WHERE id = ?', (id_transaccion,))
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

if __name__ == '__main__':
    # Inicializar la base de datos
    inicializar_db()
    # El servidor corre en modo debug y se actualiza solo si haces cambios
    app.run(debug=True, port=5000)