from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pymssql
import os
from datetime import datetime

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
# Conexão com SQL Server
# ----------------------------------------------------
def conectar_bd():
    return pymssql.connect(
        server=os.getenv("DB_SERVER"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        port=1433,
        tds_version="7.4"
    )

# ----------------------------------------------------
# /visitas_periodo – incremental robusto (DATA + ID)
# ----------------------------------------------------
@app.get("/visitas_periodo")
def visitas_periodo(
    last_date: str = "2000-01-01T00:00:00",
    last_id: int = 0
):
    try:
        last_date_dt = datetime.fromisoformat(
            last_date.replace("Z", "")
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
            WHERE
                (DATA_HORA_INICIO > %s)
                OR (
                    DATA_HORA_INICIO = %s
                    AND ID_OS > %s
                )
            ORDER BY
                DATA_HORA_INICIO ASC,
                ID_OS ASC
        """

        cursor.execute(query, (last_date_dt, last_date_dt, last_id))
        registros = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "total": len(registros),
            "data": registros
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

# ----------------------------------------------------
# /visitas_por_id – BACKFILL CIRÚRGICO POR ID
# ----------------------------------------------------
@app.get("/visitas_por_id")
def visitas_por_id(id_inicio: int, id_fim: int):
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
        """

        cursor.execute(query, (id_inicio, id_fim))
        registros = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "total": len(registros),
            "data": registros
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }



# ----------------------------------------------------
# /visitas_backfill_data – backfill histórico paginado
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

# ----------------------------------------------------
# Health check
# ----------------------------------------------------
@app.get("/")
def home():
    return {"message": "API Prime – OK 🚀"}
