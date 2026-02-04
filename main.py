from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from datetime import datetime
import pymssql
import os

app = FastAPI()

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
# Conexão com SQL Server (BLINDADA)
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

# ----------------------------------------------------
# /visitas_periodo – incremental PAGINADO
# ----------------------------------------------------
@app.get("/visitas_periodo")
def visitas_periodo(
    last_date: str = "2025-01-01T00:00:00",
    last_id: int = 0,
    limit: int = 500
):
    try:
        DATA_INICIO_FIXA = datetime(2025, 1, 1)

        last_date_dt = datetime.fromisoformat(
            last_date.replace("Z", "")
        )

        if last_date_dt < DATA_INICIO_FIXA:
            last_date_dt = DATA_INICIO_FIXA

        conn = conectar_bd()
        cursor = conn.cursor(as_dict=True)

        query = """
            SELECT
                ID_OS,
                CODIGO_OS,
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
            WHERE
                DATA_HORA_INICIO >= %s
                AND (
                    DATA_HORA_INICIO > %s
                    OR (
                        DATA_HORA_INICIO = %s
                        AND ID_OS > %s
                    )
                )
            ORDER BY DATA_HORA_INICIO ASC, ID_OS ASC
            OFFSET 0 ROWS
            FETCH NEXT %s ROWS ONLY
        """

        cursor.execute(
            query,
            (
                DATA_INICIO_FIXA,
                last_date_dt,
                last_date_dt,
                last_id,
                limit
            )
        )

        registros = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "returned": len(registros),
            "limit": limit,
            "data": registros
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ----------------------------------------------------
# /visitas_full – FULL REFRESH (2025 → MAIS RECENTE)
# ----------------------------------------------------
@app.get("/visitas_full")
def visitas_full(
    start_date: str = "2025-01-01T00:00:00",
    limit: int = Query(200000, ge=1, le=500000)
):
    try:
        DATA_MINIMA = datetime(2025, 1, 1)

        start_dt = datetime.fromisoformat(
            start_date.replace("Z", "")
        )

        if start_dt < DATA_MINIMA:
            start_dt = DATA_MINIMA

        conn = conectar_bd()
        cursor = conn.cursor(as_dict=True)

        query = """
            SELECT
                ID_OS,
                CODIGO_OS,
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
            FETCH NEXT %s ROWS ONLY

        """

        cursor.execute(query, (start_dt, limit))
        registros = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "from": start_dt.isoformat(),
            "returned": len(registros),
            "data": registros
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ----------------------------------------------------
# /visitas_por_id – backfill por faixa
# ----------------------------------------------------
@app.get("/visitas_por_id")
def visitas_por_id(
    id_inicio: int,
    id_fim: int,
    limit: int = 500,
    offset: int = 0
):
    try:
        conn = conectar_bd()
        cursor = conn.cursor(as_dict=True)

        query = """
            SELECT
                ID_OS,
                CODIGO_OS,
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
            WHERE ID_OS BETWEEN %s AND %s
            ORDER BY ID_OS ASC
            OFFSET %s ROWS
            FETCH NEXT %s ROWS ONLY
        """

        cursor.execute(
            query,
            (id_inicio, id_fim, offset, limit)
        )

        registros = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "returned": len(registros),
            "limit": limit,
            "offset": offset,
            "data": registros
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ----------------------------------------------------
# /visitas_backfill_data – histórico
# ----------------------------------------------------
@app.get("/visitas_backfill_data")
def visitas_backfill_data(
    data_fim: str,
    limit: int = 500,
    offset: int = 0
):
    try:
        data_fim_dt = datetime.fromisoformat(
            data_fim.replace("Z", "")
        )

        conn = conectar_bd()
        cursor = conn.cursor(as_dict=True)

        query = """
            SELECT
                ID_OS,
                CODIGO_OS,
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
            WHERE DATA_HORA_INICIO < %s
            ORDER BY DATA_HORA_INICIO ASC, ID_OS ASC
            OFFSET %s ROWS
            FETCH NEXT %s ROWS ONLY
        """

        cursor.execute(
            query,
            (data_fim_dt, offset, limit)
        )

        registros = cursor.fetchall()
        cursor.close()
        conn.close()

        return {
            "status": "success",
            "returned": len(registros),
            "limit": limit,
            "offset": offset,
            "data": registros
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

# ----------------------------------------------------
# Health check
# ----------------------------------------------------
@app.get("/")
def home():
    return {"message": "API Prime – OK 🚀"}

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
