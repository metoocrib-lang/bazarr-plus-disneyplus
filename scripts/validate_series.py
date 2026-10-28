"""Validate series_json and preview one episode locally, without network access."""
import argparse
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mapping_provider", ROOT / "provider/provider.py")
provider = importlib.util.module_from_spec(spec)
spec.loader.exec_module(provider)


def validate(raw):
    if len(raw) > 16384:
        raise ValueError("El mapa supera 16.384 caracteres")
    try:
        entries = json.loads(raw)
    except json.JSONDecodeError as error:
        raise ValueError(f"JSON inválido: línea {error.lineno}, columna {error.colno}") from error
    if not isinstance(entries, list) or not 1 <= len(entries) <= 32:
        raise ValueError("Usa una lista de 1 a 32 series")
    seen = set()
    for number, entry in enumerate(entries, 1):
        if not isinstance(entry, dict):
            raise ValueError(f"Serie {number}: se esperaba un objeto")
        if set(entry) - {"tvdb_id", "series_url", "mapping"}:
            raise ValueError(f"Serie {number}: campos desconocidos; solo tvdb_id, series_url y mapping")
        tvdb = entry.get("tvdb_id")
        if type(tvdb) is not int or not 1 <= tvdb <= 2147483647:
            raise ValueError(f"Serie {number}: TVDB debe ser un entero positivo válido")
        if tvdb in seen:
            raise ValueError(f"Serie {number}: TVDB repetido")
        seen.add(tvdb)
        url = entry.get("series_url")
        if not isinstance(url, str) or len(url) > 500 or not provider._valid_disney_url(url):
            raise ValueError(f"Serie {number}: URL de catálogo Disney+ inválida")
        mapping = entry.get("mapping", "")
        if not isinstance(mapping, str):
            raise ValueError(f"Serie {number}: mapping debe ser texto")
        try:
            provider.parse_mapping(mapping)
        except ValueError as error:
            raise ValueError(f"Serie {number}: {error}") from error
    return entries


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", type=Path, help="Archivo que contiene solamente series_json")
    parser.add_argument("--episode", nargs=3, type=int, metavar=("TVDB", "TEMPORADA", "EPISODIO"))
    args = parser.parse_args(argv)
    try:
        # Bound memory as well as the provider's character limit; accept a UTF-8 BOM.
        with args.file.open("r", encoding="utf-8-sig") as stream:
            raw = stream.read(16385)
        entries = validate(raw)
        if args.episode:
            tvdb, season, episode = args.episode
            if not 1 <= tvdb <= 2147483647 or not 0 <= season <= 100 or not 1 <= episode <= 999:
                raise ValueError("Coordenadas del episodio fuera de rango")
            entry = next((e for e in entries if e["tvdb_id"] == tvdb), None)
            if entry is None:
                raise ValueError("El TVDB indicado no está en el mapa")
            destination = provider.map_episode(entry.get("mapping", ""), season, episode)
            if destination is None:
                print("Sin equivalencia: el proveedor omitirá este episodio.")
                return 2
            print(f"Biblioteca T{season}E{episode} -> Disney+ T{destination[0]}E{destination[1]}")
        print(f"Mapa válido: {len(entries)} series. No se consultó Disney+.")
        return 0
    except (ValueError, OSError) as error:
        # Never print file contents, credentials or URLs from the input.
        message = str(error) if isinstance(error, ValueError) and not isinstance(error, UnicodeError) else "No se pudo leer el archivo UTF-8"
        print(f"Error: {message}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
