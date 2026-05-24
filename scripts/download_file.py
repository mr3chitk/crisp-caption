from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import tempfile
import urllib.request
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def resolve_under_root(raw: str) -> Path:
    target = (ROOT / raw).resolve()
    if ROOT.resolve() != target and ROOT.resolve() not in target.parents:
        raise SystemExit(f"Refusing to write outside project root: {raw}")
    return target


def download(url: str, target: Path, expected_sha256: str = "") -> None:
    if not url or "TODO" in url:
        raise SystemExit("Download URL is not configured yet. Edit the manifest or BAT file first.")
    if not url.startswith("https://"):
        raise SystemExit(f"Refusing non-HTTPS URL: {url}")
    target.parent.mkdir(parents=True, exist_ok=True)
    if target.exists() and expected_sha256:
        actual = sha256_file(target)
        if actual.lower() == expected_sha256.lower():
            print(f"[OK] {target} already exists")
            return
        print(f"[WARN] Existing file hash mismatch, replacing: {target}")
    elif target.exists():
        print(f"[OK] {target} already exists")
        return

    with tempfile.NamedTemporaryFile(delete=False, suffix=target.suffix or ".download") as tmp:
        temp_path = Path(tmp.name)
    try:
        print(f"[GET] {url}")
        urllib.request.urlretrieve(url, temp_path)
        if expected_sha256:
            actual = sha256_file(temp_path)
            if actual.lower() != expected_sha256.lower():
                raise SystemExit(f"sha256 mismatch for {target}\nexpected {expected_sha256}\nactual   {actual}")
        else:
            print(f"[WARN] No sha256 configured for {target.name}; downloaded without hash verification.")
        shutil.move(str(temp_path), target)
        print(f"[OK] Wrote {target}")
    finally:
        temp_path.unlink(missing_ok=True)


def extract_zip(archive: Path, dest: Path, strip_top_level: bool) -> None:
    if not archive.is_file():
        raise SystemExit(f"Archive not found: {archive}")
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive) as zf:
        members = zf.infolist()
        top_parts = {Path(member.filename).parts[0] for member in members if Path(member.filename).parts}
        strip_prefix = next(iter(top_parts)) if strip_top_level and len(top_parts) == 1 else ""
        for member in members:
            parts = Path(member.filename).parts
            if not parts:
                continue
            relative = Path(*parts[1:]) if strip_prefix and parts[0] == strip_prefix else Path(*parts)
            if not str(relative):
                continue
            target = (dest / relative).resolve()
            if dest.resolve() != target and dest.resolve() not in target.parents:
                raise SystemExit(f"Refusing unsafe zip member: {member.filename}")
            if member.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(member) as src, target.open("wb") as out:
                shutil.copyfileobj(src, out)


def load_manifest(path: Path) -> list[dict[str, str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    artifacts = data.get("artifacts")
    if not isinstance(artifacts, list):
        raise SystemExit(f"Manifest must contain an artifacts list: {path}")
    return artifacts


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(dest="cmd", required=True)

    one = sub.add_parser("one")
    one.add_argument("--url", required=True)
    one.add_argument("--target", required=True)
    one.add_argument("--sha256", default="")

    manifest = sub.add_parser("manifest")
    manifest.add_argument("--manifest", required=True)

    extract = sub.add_parser("extract")
    extract.add_argument("--archive", required=True)
    extract.add_argument("--dest", required=True)
    extract.add_argument("--strip-top-level", action="store_true")
    extract.add_argument("--delete-archive", action="store_true")

    args = parser.parse_args(argv)
    if args.cmd == "one":
        download(args.url, resolve_under_root(args.target), args.sha256)
    elif args.cmd == "manifest":
        manifest_path = resolve_under_root(args.manifest)
        for artifact in load_manifest(manifest_path):
            download(
                str(artifact.get("url") or ""),
                resolve_under_root(str(artifact.get("path") or "")),
                str(artifact.get("sha256") or ""),
            )
    elif args.cmd == "extract":
        archive = resolve_under_root(args.archive)
        extract_zip(archive, resolve_under_root(args.dest), args.strip_top_level)
        if args.delete_archive:
            archive.unlink(missing_ok=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
