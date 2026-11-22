# Plataforma de Rendimiento Deportivo · v1.0

Aplicación Streamlit basada en el formato `Formato_Deportista_Nuevo oficial.xlsx`.

## Instalación (Windows / macOS / Linux)

```bash
python -m venv .venv
# Windows PowerShell:
.venv\Scripts\Activate.ps1
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Flujo de uso

1. **Gestionar deportistas**: crea un perfil con nombre y club.
2. **Importar Excel**: selecciona el perfil y sube el archivo individual del atleta. Revisa la vista previa antes de confirmar.
3. **Registrar evaluación**: introduce nuevas pruebas directamente.
4. **Editar evaluaciones**: corrige registros o elimínalos con confirmación.
5. **Panel del deportista**: explora evolución, perfiles carga-resultado y exporta PDF.
6. **Comparar deportistas**: filtra por club, protocolo y carga.

## Cobertura del Excel original

Importa: `Registro Saltos`, `Registro VBT`, `Registro CMJ Cargado`, `Monitoreo diario press VBT ` y `Monitoreo diario sentadilla VBT`.

Detecta pero **todavía no transforma automáticamente**: `Movilidad `, `Dinamométrica`, `Anamnesis` y `Programación semanal` (sus estructuras son heterogéneas). El resumen se recalcula desde las mediciones y la tabla `%RM` se conserva como referencia metodológica del archivo original, pero **no se aplica automáticamente** sin identificar ejercicio y métrica de velocidad.

**Importante:** en `Registro VBT`, cada par carga/velocidad se almacena como una medición. La regresión se calcula por fecha y ejercicio con al menos tres cargas distintas. La intersección con velocidad cero **no debe tratarse como una 1RM validada**. La fórmula RSI del formato es tiempo de vuelo/tiempo de contacto, no RSI clásico altura/tiempo de contacto. La interpretación de tendencias es descriptiva y no sustituye variabilidad intraindividual ni criterio técnico.

## Persistencia y privacidad

SQLite guarda los datos en `data/rendimiento.sqlite3`, excluido de Git. Haz copias de seguridad de `data/` antes de actualizar o cambiar de servidor. **Streamlit Community Cloud no garantiza persistencia del disco local**: para producción y uso multiusuario migrar a PostgreSQL, añadir autenticación, control de permisos, cifrado y copias de seguridad. No subir datos identificables ni historias de salud al repositorio.

## GitHub

```bash
git init
git add .
git commit -m "Versión inicial plataforma de rendimiento"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```

Crea antes un repositorio vacío en GitHub. Para ejecutar pruebas: `python -m pytest`.

## Próximas mejoras

- Identidad por archivo y cargas masivas de varios deportistas con confirmación y deduplicación robusta.
- Mapeo detallado de movilidad, dinamometría, anamnesis y programación semanal.
- Bibliografía versionada por protocolo, velocidades mínimas individuales y modelos específicos por ejercicio.
- Métricas de confiabilidad (CV, error típico, cambio mínimo detectable), reportes con gráficos y comparación por categorías.
- Autenticación y base de datos remota para clubes y entrenadores.
