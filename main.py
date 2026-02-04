from fastapi import FastAPI, Query
from datetime import datetime

app = FastAPI()

# =========================================================
# ENDPOINT INCREMENTAL (JÁ EXISTENTE – NÃO ALTERADO)
# =========================================================
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
            ORDER BY
                DATA_HORA_INICIO ASC,
                ID_OS ASC
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
        return {
            "status": "error",
            "message": str(e)
        }


# =========================================================
# NOVO ENDPOINT — FULL REFRESH (2025 → MAIS RECENTE)
# =========================================================
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
            WHERE
                DATA_HORA_INICIO >= %s
            ORDER BY
                DATA_HORA_INICIO ASC,
                ID_OS ASC
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
        return {
            "status": "error",
            "message": str(e)
        }
