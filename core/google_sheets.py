
import streamlit as st
import pandas as pd

from google.oauth2 import service_account
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/drive.readonly",
    "https://www.googleapis.com/auth/spreadsheets.readonly",
]


def conectar_google():
    credenciales = service_account.Credentials.from_service_account_info(
        dict(st.secrets["gcp_service_account"]),
        scopes=SCOPES,
    )

    drive = build(
        "drive", "v3",
        credentials=credenciales,
        cache_discovery=False,
    )

    sheets = build(
        "sheets", "v4",
        credentials=credenciales,
        cache_discovery=False,
    )

    return drive, sheets


@st.cache_data(ttl=60, show_spinner=False)
def listar_archivos():
    drive, _ = conectar_google()
    carpeta = st.secrets["google_drive"]["folder_id"]

    archivos = []
    token = None

    while True:
        respuesta = drive.files().list(
            q=(
                f"'{carpeta}' in parents and "
                "mimeType='application/vnd.google-apps.spreadsheet' "
                "and trashed=false"
            ),
            fields="nextPageToken, files(id,name,mimeType)",
            pageSize=100,
            pageToken=token,
        ).execute()

        archivos.extend(respuesta.get("files", []))
        token = respuesta.get("nextPageToken")

        if not token:
            break

    return sorted(archivos, key=lambda x: x["name"].lower())


@st.cache_data(ttl=60, show_spinner=False)
def listar_pestanas(archivo_id):
    _, sheets = conectar_google()

    respuesta = sheets.spreadsheets().get(
        spreadsheetId=archivo_id,
        fields="sheets(properties(title,sheetId))",
    ).execute()

    return [
        hoja["properties"]["title"]
        for hoja in respuesta.get("sheets", [])
    ]


@st.cache_data(ttl=60, show_spinner=False)
def leer_pestana(archivo_id, nombre_pestana):
    _, sheets = conectar_google()

    rango = "'" + nombre_pestana.replace("'", "''") + "'"

    respuesta = sheets.spreadsheets().values().get(
        spreadsheetId=archivo_id,
        range=rango,
    ).execute()

    filas = respuesta.get("values", [])

    if not filas:
        return pd.DataFrame()

    encabezados = [
        str(c).strip() or f"Columna_{i+1}"
        for i, c in enumerate(filas[0])
    ]

    ancho = max(len(encabezados), max(map(len, filas)))

    encabezados += [
        f"Columna_{i+1}"
        for i in range(len(encabezados), ancho)
    ]

    registros = [
        fila + [""] * (ancho - len(fila))
        for fila in filas[1:]
    ]

    return pd.DataFrame(registros, columns=encabezados)
