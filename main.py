from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime, timedelta
import pymssql
import os

app = FastAPI(title="API Supervisores")

# ----------------------------------------------------
# CORS
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Configuração base
# ----------------------------------------------------
DATA_MINIMA = datetime(2025, 1, 1)

# ----------------------------------------------------
# Conexão com SQL Server
# ----------------------------------------------------
def conectar_bd():
    return pymssql.connect(
        server=os.getenv("DB_SERVER"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        port=1433,
        tds_version="7.4",
        login_timeout=5,
        timeout=30
    )

# ====================================================
# 🔁 INCREMENTAL – janela móvel (últimos 2 dias)
# ====================================================
@app.get("/visitas_supervisor_sync")
def visitas_supervisor_sync():
    try:
        agora = datetime.now()
        inicio_janela = agora - timedelta(days=2)

        if inicio_janela < DATA_MINIMA:
            inicio_janela = DATA_MINIMA

        conn = conectar_bd()
        cursor = conn.cursor(as_dict=True)

        query = """
            SELECT
                ID_OS,
                CODIGO_OS,
                CODIGO_CLIENTE,
                SUPERVISOR,
                CLIENTE,
                DATA_HORA_FIM,
                DATA_HORA_INICIO,
                STATUS_OS,
                GRUPO_CLIENTE,
                DATA_HORA_AGENDAMENTO,
                STATUS_VISITA,
                LOCALIZACAO_INICIO,
                MOTIVO_NAO_VISITA,
                OUTRO_MOTIVO_NAO_VISITA,
                ENDERECO,
                NUMERO_ENDERECO,
                BAIRRO,
                CIDADE,
                UF,
                COMPLEMENTO,
                CEP,
                TIPO_CHECKIN
            FROM TAB_REGISTRO_VISITA_SUPERVISAO_CABECALHO
            WHERE DATA_HORA_INICIO BETWEEN %s AND %s
            ORDER BY DATA_HORA_INICIO ASC, ID_OS ASC
        """

        cursor.execute(query, (inicio_janela, agora))
        registros = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "mode": "incremental_sync",
            "from": inicio_janela.isoformat(),
            "to": agora.isoformat(),
            "returned": len(registros),
            "data": registros
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ====================================================
# 🔥 FULL – correção de histórico
# ====================================================
@app.get("/visitas_supervisor_full")
def visitas_supervisor_full(
    start_date: str = "2025-01-01T00:00:00",
    limit: int = Query(300000, ge=1, le=600000)
):
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", ""))

        if start_dt < DATA_MINIMA:
            start_dt = DATA_MINIMA

        conn = conectar_bd()
        cursor = conn.cursor(as_dict=True)

        query = f"""
            SELECT
                ID_OS,
                CODIGO_OS,
                CODIGO_CLIENTE,
                SUPERVISOR,
                CLIENTE,
                DATA_HORA_FIM,
                DATA_HORA_INICIO,
                STATUS_OS,
                GRUPO_CLIENTE,
                DATA_HORA_AGENDAMENTO,
                STATUS_VISITA,
                LOCALIZACAO_INICIO,
                MOTIVO_NAO_VISITA,
                OUTRO_MOTIVO_NAO_VISITA,
                ENDERECO,
                NUMERO_ENDERECO,
                BAIRRO,
                CIDADE,
                UF,
                COMPLEMENTO,
                CEP,
                TIPO_CHECKIN
            FROM TAB_REGISTRO_VISITA_SUPERVISAO_CABECALHO
            WHERE DATA_HORA_INICIO >= %s
            ORDER BY DATA_HORA_INICIO ASC, ID_OS ASC
            OFFSET 0 ROWS
            FETCH NEXT {limit} ROWS ONLY
        """

        cursor.execute(query, (start_dt,))
        registros = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "mode": "full_refresh",
            "from": start_dt.isoformat(),
            "returned": len(registros),
            "data": registros
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}





#-----------------------------------------------------
# Endpoint de contratos (FULL)
#-----------------------------------------------------

@app.get("/contratos")
def contratos(
    start_date: str = "2025-01-01T00:00:00",
    limit: int = Query(500000, ge=1, le=600000)
):
    try:
        start_dt = datetime.fromisoformat(start_date.replace("Z", ""))

        if start_dt < DATA_MINIMA:
            start_dt = DATA_MINIMA

        conn = conectar_bd()
        cursor = conn.cursor(as_dict=True)

        query = """
            SELECT
                ID_OS,
                CODIGO_CLIENTE,
                CLIENTE,
                SUPERVISOR,
                DATA_HORA_INICIO
            FROM TAB_REGISTRO_VISITA_SUPERVISAO_CABECALHO
            WHERE DATA_HORA_INICIO >= %s
            ORDER BY DATA_HORA_INICIO ASC, ID_OS ASC
            OFFSET 0 ROWS FETCH NEXT %s ROWS ONLY
        """

        cursor.execute(query, (start_dt, limit))
        registros = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "mode": "contratos_full",
            "returned": len(registros),
            "data": registros
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }


# ----------------------------------------------------
# Health check
# ----------------------------------------------------
@app.get("/")
def home():
    return {"message": "API Supervisores – OK 🚀"}

# ----------------------------------------------------
# Startup Railway
# ----------------------------------------------------
if __name__ == "__main__":
    import uvicorn

    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        log_level="info"
    )
