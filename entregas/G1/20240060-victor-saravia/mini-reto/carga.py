#!/usr/bin/env python3
"""Prepara y carga las cuatro tablas Spotify desde los CSV del taller.

Uso desde la raíz del repositorio:
    python3 entregas/G1/20240060-victor-saravia/mini-reto/carga.py

Genera CSV denormalizados en datos_carga/ y los importa con cqlsh COPY.
COPY inserta por las mismas llaves primarias, así que volver a correrlo
actualiza las mismas filas sin duplicarlas.
"""
from __future__ import annotations

import csv
import re
import subprocess
import sys
from collections import defaultdict
from pathlib import Path


CARPETA = Path(__file__).resolve().parent
RAIZ = Path(__file__).resolve().parents[4]
FUENTE = RAIZ / "data/mini-reto/G1-spotify"
DATOS = CARPETA / "datos_carga"
CONTENEDOR = "cassandra2"
KEYSPACE = "spotify_20240060"


def leer(nombre: str) -> list[dict[str, str]]:
    with (FUENTE / nombre).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def escribir(nombre: str, columnas: list[str], filas: list[dict[str, object]]) -> None:
    destino = DATOS / nombre
    with destino.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=columnas, lineterminator="\n")
        writer.writeheader()
        writer.writerows(filas)


def preparar() -> dict[str, int]:
    usuarios = leer("usuarios.csv")
    canciones = {r["cancion_id"]: r for r in leer("canciones.csv")}
    playlists = {r["playlist_id"]: r for r in leer("playlists.csv")}
    membresias = leer("playlist_canciones.csv")
    reproducciones = leer("reproducciones.csv")

    perfil = [
        {k: u[k] for k in ("usuario_id", "nombre", "pais", "plan")}
        for u in usuarios
    ]

    recientes = []
    por_dia = []
    for r in reproducciones:
        cancion = canciones[r["cancion_id"]]
        recientes.append({
            "usuario_id": r["usuario_id"],
            "reproducida_en": r["reproducida_en"] + "+0000",
            "reproduccion_id": r["reproduccion_id"],
            "titulo": cancion["titulo"],
            "artista": cancion["artista"],
        })
        por_dia.append({
            "cancion_id": r["cancion_id"],
            "dia": r["reproducida_en"][:10],
            "reproduccion_id": r["reproduccion_id"],
        })

    playlist_orden = []
    for m in membresias:
        if m["playlist_id"] not in playlists:
            raise ValueError(f"Playlist inexistente en playlist_canciones: {m['playlist_id']}")
        cancion = canciones[m["cancion_id"]]
        playlist_orden.append({
            "playlist_id": m["playlist_id"],
            "posicion": m["posicion"],
            "cancion_id": m["cancion_id"],
            "titulo": cancion["titulo"],
            "artista": cancion["artista"],
        })
    playlist_orden.sort(key=lambda r: (r["playlist_id"], int(str(r["posicion"]))))

    DATOS.mkdir(exist_ok=True)
    escribir("perfil_usuario.csv", ["usuario_id", "nombre", "pais", "plan"], perfil)
    escribir("reproducciones_recientes_por_usuario.csv",
             ["usuario_id", "reproducida_en", "reproduccion_id", "titulo", "artista"], recientes)
    escribir("canciones_por_playlist_orden.csv",
             ["playlist_id", "posicion", "cancion_id", "titulo", "artista"], playlist_orden)
    escribir("reproducciones_por_cancion_dia.csv",
             ["cancion_id", "dia", "reproduccion_id"], por_dia)
    return {
        "perfil_usuario": len(perfil),
        "reproducciones_recientes_por_usuario": len(recientes),
        "canciones_por_playlist_orden": len(playlist_orden),
        "reproducciones_por_cancion_dia": len(por_dia),
    }


def ejecutar(comando: list[str], *, entrada: str | None = None) -> str:
    p = subprocess.run(comando, input=entrada, stdout=subprocess.PIPE,
                       stderr=subprocess.STDOUT, text=True)
    if p.returncode:
        raise RuntimeError(p.stdout)
    return p.stdout


def main() -> int:
    try:
        conteos = preparar()
        # IF NOT EXISTS permite repetir el script sin borrar datos compartidos.
        modelo = (CARPETA / "modelo.cql").read_text(encoding="utf-8")
        print(ejecutar(["docker", "exec", "-i", CONTENEDOR, "cqlsh"], entrada=modelo), end="")

        comandos = [
            ("perfil_usuario", ["usuario_id", "nombre", "pais", "plan"]),
            ("reproducciones_recientes_por_usuario",
             ["usuario_id", "reproducida_en", "reproduccion_id", "titulo", "artista"]),
            ("canciones_por_playlist_orden",
             ["playlist_id", "posicion", "cancion_id", "titulo", "artista"]),
            ("reproducciones_por_cancion_dia", ["cancion_id", "dia", "reproduccion_id"]),
        ]
        for tabla, columnas in comandos:
            cols = ", ".join(columnas)
            csv_texto = (DATOS / f"{tabla}.csv").read_text(encoding="utf-8")
            comando_copy = (
                f"CONSISTENCY QUORUM;\nUSE {KEYSPACE};\n"
                f"COPY {tabla} ({cols}) FROM STDIN "
                "WITH HEADER = true AND MAXATTEMPTS = 5 AND NUMPROCESSES = 4 "
                "AND MAXPARSEERRORS = 0 AND MAXINSERTERRORS = 0;\n"
                + csv_texto + ".\n"
            )
            salida = ejecutar(
                ["docker", "exec", "-i", CONTENEDOR, "cqlsh"], entrada=comando_copy
            )
            print(salida, end="")
            match = re.search(r"(?m)^(\d+) rows? imported from", salida)
            if not match or int(match.group(1)) != conteos[tabla]:
                raise RuntimeError(
                    f"{tabla}: esperaba importar {conteos[tabla]} filas; salida de cqlsh:\n{salida}"
                )
        for tabla, cantidad in conteos.items():
            print(f"Filas preparadas para {tabla}: {cantidad}")
        return 0
    except (OSError, ValueError, RuntimeError, KeyError) as e:
        print(f"Error de carga: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
