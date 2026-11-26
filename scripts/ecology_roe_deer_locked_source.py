"""Fetch the exact previously acquired 2020 public Dryad release.
Use documented endpoints; file content SHA256 is authoritative.
"""
import argparse,json
from pathlib import Path
from ecology_roe_deer_public_source_audit import acquire,SOURCES
ROOT=Path(__file__).resolve().parents[1]
def main():
    p=argparse.ArgumentParser()
    p.add_argument("--private",type=Path,required=True)
    p.add_argument("--output",type=Path,required=True)
    a=p.parse_args()
    a.private.mkdir(parents=True,exist_ok=False);a.private.chmod(0o700)
    old=json.loads((ROOT/"docs/evidence/roe-deer-source-readiness-20261126.json").read_text())["acquisition"]["sources"][0]
    z=acquire("gervais2020",SOURCES["gervais2020"],a.private)
    if z["status"]!="ACQUIRED_FOR_SCHEMA_AUDIT":raise ValueError(z["status"])
    if z["version_id"]!="49679" or z["version_id"]!=old["version_id"] or z["files"]!=old["files"]:
        raise ValueError("HOLD_LOCKED_FILE_CONTENT_OR_RELEASE_DRIFT")
    z["file_content_parity"]=True
    z["archive_byte_parity"]=z["archive_sha256"]==old["archive_sha256"]
    a.output.parent.mkdir(parents=True,exist_ok=True)
    a.output.write_text(json.dumps(z,indent=2)+"\n")
    print(json.dumps(z))
if __name__=="__main__":main()
