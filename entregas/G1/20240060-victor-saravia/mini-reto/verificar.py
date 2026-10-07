#!/usr/bin/env python3
"""Compara cada consulta del mini-reto: SQL sobre los CSV frente a Cassandra.

Uso desde la raíz del repositorio:
    python3 entregas/G1/20240060-victor-saravia/mini-reto/verificar.py
"""
import csv
import json
import re
import sqlite3
import subprocess
import sys
from pathlib import Path


CARPETA = Path(__file__).resolve().parent
RAIZ = Path(__file__).resolve().parents[4]
FUENTE = RAIZ / "data/mini-reto/G1-spotify"
KEYSPACE = "spotify_20240060"
CONTENEDOR = "cassandra2"


def sentencias(path: Path) -> list[str]:
    texto = re.sub(r"--[^\n]*", "", path.read_text(encoding="utf-8"))
    return [s.strip() for s in texto.split(";") if s.strip()]


def sqlite_esperado() -> list[tuple[list[str], list[tuple]]]:
    db = sqlite3.connect(":memory:")
    db.executescript((FUENTE / "schema.sql").read_text(encoding="utf-8"))
    for nombre in ("usuarios", "canciones", "playlists", "playlist_canciones", "reproducciones"):
        with (FUENTE / f"{nombre}.csv").open(encoding="utf-8-sig", newline="") as f:
            reader = csv.DictReader(f)
            columnas = reader.fieldnames
            marcadores = ",".join("?" for _ in columnas)
            db.executemany(
                f"INSERT INTO {nombre} ({','.join(columnas)}) VALUES ({marcadores})",
                (tuple(fila[c] for c in columnas) for fila in reader),
            )
    consultas = sentencias(FUENTE / "consultas.sql")
    resultados = []
    for consulta in consultas:
        cursor = db.execute(consulta)
        resultados.append((
            [col[0] for col in cursor.description],
            [tuple(fila) for fila in cursor.fetchall()],
        ))
    db.close()
    return resultados


def cql_obtenido(consulta: str, columnas: list[str]) -> list[tuple]:
    consulta_json = re.sub(r"(?i)^\s*SELECT\s+", "SELECT JSON ", consulta, count=1)
    comando = (
        f"CONSISTENCY QUORUM; USE {KEYSPACE}; {consulta_json};"
    )
    p = subprocess.run(
        ["docker", "exec", CONTENEDOR, "cqlsh", "-e", comando],
        capture_output=True, text=True,
    )
    if p.returncode:
        raise RuntimeError(p.stdout + p.stderr)
    filas = []
    for linea in p.stdout.splitlines():
        texto = linea.strip()
        if texto.startswith("{"):
            fila = json.loads(texto)
            filas.append(tuple(fila.get(c) for c in columnas))
    return filas


def normalizar(valor):
    if not isinstance(valor, str):
        return valor
    valor = valor.replace("T", " ")
    valor = re.sub(r"\.\d+(?=Z|[+-]\d\d:?\d\d|$)", "", valor)
    valor = re.sub(r"(?:Z|\+00:?00)$", "", valor)
    return valor


def main() -> int:
    esperados = sqlite_esperado()
    consultas = [s for s in sentencias(CARPETA / "consultas.cql")
                 if re.match(r"(?is)^SELECT\b", s)]
    if len(consultas) != len(esperados):
        raise RuntimeError(f"Hay {len(consultas)} consultas CQL y {len(esperados)} SQL")

    todo_ok = True
    for i, (consulta, (columnas, filas_sql)) in enumerate(zip(consultas, esperados), 1):
        filas_cql = cql_obtenido(consulta, columnas)
        a = [tuple(normalizar(v) for v in fila) for fila in filas_sql]
        b = [tuple(normalizar(v) for v in fila) for fila in filas_cql]
        coincide = a == b
        todo_ok &= coincide
        print(f"C{i}: esperado={len(a)} filas, obtenido={len(b)} filas; "
              f"{'COINCIDE' if coincide else 'DIFIERE'}")
        if not coincide:
            for n, (esperado, obtenido) in enumerate(zip(a, b), 1):
                if esperado != obtenido:
                    print(f"  fila {n}: SQL={esperado!r}; Cassandra={obtenido!r}")
            if len(a) != len(b):
                print(f"  SQL={a!r}\n  Cassandra={b!r}")
    print("Comparación completa: " + ("las cuatro consultas coinciden." if todo_ok
                                        else "hay diferencias por corregir."))
    return 0 if todo_ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, sqlite3.Error, RuntimeError, json.JSONDecodeError) as e:
        print(f"Error de verificación: {e}", file=sys.stderr)
        raise SystemExit(1)
