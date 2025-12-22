from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import pymssql
import os

app = FastAPI()

# ----------------------------------------------------
# CORS liberado
# ----------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----------------------------------------------------
# Conexão com SQL Server (Azure) usando pymssql
# ----------------------------------------------------
def conectar_bd():
    conn = pymssql.connect(
        server=os.getenv("DB_SERVER"),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASS"),
        database=os.getenv("DB_NAME"),
        port=1433,
        tds_version='7.4'
    )
    return conn


# ----------------------------------------------------
# /visitas_periodo – puxar registros incrementais
# ----------------------------------------------------
@app.get("/visitas_periodo")
def visitas_periodo(last_date: str = "2000-01-01T00:00:00"):
    try:
        conn = conectar_bd()
        cursor = conn.cursor(as_dict=True)

        query = f"""
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
            WHERE DATA_HORA_INICIO > %s
            ORDER BY DATA_HORA_INICIO ASC
        """

        cursor.execute(query, (last_date,))
        registros = cursor.fetchall()

        cursor.close()
        conn.close()

        return {
            "status": "success",
            "total": len(registros),
            "data": registros
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}


# ----------------------------------------------------
# Rota inicial
# ----------------------------------------------------
@app.get("/")
def home():
    return {"message": "API da Prime Operando no Railway! 🚀"}
