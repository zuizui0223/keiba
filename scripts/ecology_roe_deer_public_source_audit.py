#!/usr/bin/env python3
"""One-pass public Dryad release acquisition and safe schema-audit staging.
No login, access-barrier bypass, source script execution, or raw artifact upload.
"""
from __future__ import annotations
import argparse
import hashlib
import io
import json
import re
import tarfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from pathlib import Path

ROOT="https://datadryad.org"
SOURCES={
    "gervais2020":{"doi":"10.5061/dryad.dbrv15dxg","published":"2020-01-23",
        "files":["data_movement_roedeer.csv","data_spaceuse_roedeer.csv","grm_readytouse.Rdata","README.txt","space_use.R"]},
    "gervais2022":{"doi":"10.5061/dryad.6wwpzgn1j","published":"2022-02-22",
        "files":["bodymass_ID.Rdata","dailyaveragespeed_ID.Rdata","data_spaceuse_ID.Rdata","grm_full_ID.Rdata","grm_reduced_n293_ID.Rdata","hindfoot_ID.Rdata","README.txt","sim_envi_for456month_ID.Rdata","sim_envi_MONTH_FULL_ID.Rdata"]},
}
MAX_BYTES=30_000_000
META_BYTES=2_000_000
class Hold(Exception): pass

def sha(b): return hashlib.sha256(b).hexdigest()

def get(url,limit,receipt,label):
    """Public GET only. Record bounded status; never print signed redirect URLs."""
    if not url.startswith(ROOT+"/api/v2/"): raise Hold("UNEXPECTED_INITIAL_ENDPOINT")
    try:
        req=urllib.request.Request(url,headers={"User-Agent":"EcologicalResearchSourceAudit/1.0","Accept":"application/json" if limit==META_BYTES else "*/*"})
        with urllib.request.urlopen(req,timeout=40) as f:
            if urllib.parse.urlparse(f.geturl()).scheme!="https":raise Hold("NON_HTTPS_REDIRECT")
            b=f.read(limit+1)
            receipt["requests"].append({"stage":label,"status":f.status,"bytes":len(b),"sha256":sha(b),"final_host":urllib.parse.urlparse(f.geturl()).hostname})
            if len(b)>limit:raise Hold("RESPONSE_SIZE_LIMIT")
            return b
    except urllib.error.HTTPError as e:
        receipt["requests"].append({"stage":label,"status":e.code})
        raise Hold("HTTP_"+str(e.code)+"_"+label) from None
    except (urllib.error.URLError,TimeoutError,OSError) as e:
        receipt["requests"].append({"stage":label,"status":type(e).__name__})
        raise Hold("NETWORK_"+label) from None

def metadata(url,r,label):
    b=get(url,META_BYTES,r,label)
    try:z=json.loads(b)
    except (UnicodeDecodeError,json.JSONDecodeError):raise Hold("NOT_JSON_"+label) from None
    if not isinstance(z,dict):raise Hold("UNEXPECTED_METADATA_"+label)
    return z

def embedded(z,kind):
    v=z.get("_embedded",{})
    if not isinstance(v,dict):raise Hold("METADATA_EMBEDDED")
    candidates=[v[k] for k in ("stash:"+kind,kind) if k in v]
    if len(candidates)!=1 or not isinstance(candidates[0],list):raise Hold("MISSING_"+kind.upper()+"_LIST")
    items=candidates[0]
    total=z.get("total",len(items))
    if isinstance(total,int) and total!=len(items):raise Hold("PAGINATED_"+kind.upper())
    return items

def version_id(v):
    links=v.get("_links",{})
    for key in ("self","stash:version"):
        val=links.get(key,{})
        href=val.get("href","") if isinstance(val,dict) else ""
        m=re.fullmatch(r"(?:https://datadryad\.org)?/api/v2/versions/([0-9]+)",href)
        if m:return m.group(1)
    for key in ("id","versionId"):
        x=v.get(key)
        if str(x).isdigit():return str(x)
    raise Hold("NO_VERSION_IDENTIFIER")

def unpack(b,expected,out):
    """Accept only listed ordinary files, never extract a path from the archive."""
    blobs={}
    count=0
    def add(name,size,reader):
        nonlocal count
        name=Path(name).name
        if name not in expected:return
        if name in blobs or size<0 or size>MAX_BYTES or count+size>MAX_BYTES:raise Hold("ARCHIVE_DUPLICATE_OR_SIZE")
        raw=reader()
        if len(raw)!=size:raise Hold("ARCHIVE_TRUNCATED")
        count+=size;blobs[name]=raw
    if zipfile.is_zipfile(io.BytesIO(b)):
        with zipfile.ZipFile(io.BytesIO(b)) as z:
            for i in z.infolist():
                if not i.is_dir():add(i.filename,i.file_size,lambda:z.read(i))
    else:
        try:
            with tarfile.open(fileobj=io.BytesIO(b),mode="r:*") as t:
                for i in t:
                    if i.isfile():add(i.name,i.size,lambda:t.extractfile(i).read())
        except tarfile.TarError:raise Hold("NOT_SUPPORTED_ARCHIVE") from None
    if set(blobs)!=set(expected):raise Hold("ARCHIVE_EXPECTED_FILES_MISSING")
    out.mkdir(parents=True,exist_ok=False)
    out.chmod(0o700)
    rows=[]
    for k,v in sorted(blobs.items()):
        p=out/k;p.write_bytes(v);p.chmod(0o600)
        rows.append({"name":k,"bytes":len(v),"sha256":sha(v)})
    return rows

def acquire(name,spec,private):
    doi=spec["doi"]
    r={"source":name,"doi":doi,"published_listing":spec["published"],"requests":[],"status":"HOLD","source_rights_basis":"Dryad public dataset terms, CC0; cite DOI; no source redistribution here"}
    url=ROOT+"/api/v2/datasets/"+urllib.parse.quote("doi:"+doi,safe="")
    try:
        d=metadata(url,r,"dataset")
        identifier=str(d.get("identifier",d.get("doi",""))).lower()
        if identifier.removeprefix("doi:")!=doi.lower():raise Hold("DOI_NOT_VERIFIED")
        r["dataset_identifier"]=identifier
        # Published data only. Provider's public DOI listing is known; reject
        # contradictory access or license metadata rather than assume rights.
        for k in ("sharingLink","private","embargoed"):
            if d.get(k) is True:raise Hold("NONPUBLIC_METADATA")
        explicit={k:d[k] for k in ("license","licenseName","licenseURI","rights","rightsList") if k in d and d[k]}
        if explicit:
            rights=json.dumps(explicit).lower()
            if not any(x in rights for x in ("cc0","publicdomain/zero","public domain")):raise Hold("REVIEW_EXPLICIT_LICENSE")
            r["explicit_cc0_in_metadata"]=True
        else:r["explicit_cc0_in_metadata"]=False
        vs=embedded(metadata(url+"/versions",r,"versions"),"versions")
        if len(vs)!=1:raise Hold("RELEASE_SELECTION_REQUIRES_REVIEW")
        vid=version_id(vs[0]);r["version_id"]=vid
        r["version_publication_fields"]={k:vs[0][k] for k in ("versionNumber","version","publicationDate","versionDate","lastModificationDate") if k in vs[0] and isinstance(vs[0][k],(str,int,float))}
        base=ROOT+"/api/v2/versions/"+vid
        files=embedded(metadata(base+"/files",r,"files"),"files")
        listed=[]
        for item in files:
            name0=item.get("path",item.get("name",""))
            if not isinstance(name0,str) or not name0:raise Hold("FILE_NAME_METADATA")
            listed.append(Path(name0).name)
        if sorted(listed)!=sorted(spec["files"]):raise Hold("RELEASE_FILE_LIST_DIFFERS")
        r["listed_files"]=sorted(listed)
        b=get(base+"/download",MAX_BYTES,r,"download")
        r["archive_sha256"]=sha(b)
        r["files"]=unpack(b,spec["files"],private/name)
        r["status"]="ACQUIRED_FOR_SCHEMA_AUDIT"
    except Hold as e:r["status"]="HOLD_"+str(e)
    return r

def self_test():
    x=io.BytesIO()
    with zipfile.ZipFile(x,"w") as z:z.writestr("nested/a.csv","id,year\nx,2001\n")
    import tempfile
    with tempfile.TemporaryDirectory() as t:
        d=Path(t)
        a=unpack(x.getvalue(),["a.csv"],d/"a")
        assert a[0]["bytes"]==15 and (d/"a"/"a.csv").is_file()
        try:unpack(x.getvalue(),["missing.csv"],d/"b")
        except Hold:pass
        else:raise AssertionError("expected missing-file HOLD")
    assert version_id({"_links":{"self":{"href":"/api/v2/versions/123"}}})=="123"
    assert embedded({"_embedded":{"stash:files":[{"path":"a"}]}},"files")[0]["path"]=="a"
    print("Synthetic source gates passed")

def main():
    a=argparse.ArgumentParser()
    a.add_argument("--self-test",action="store_true")
    a.add_argument("--private",type=Path);a.add_argument("--output",type=Path)
    z=a.parse_args()
    if z.self_test:self_test();return
    if not z.private or not z.output:a.error("private and output required")
    z.private.mkdir(parents=True,exist_ok=False);z.private.chmod(0o700)
    result={"status":"SOURCE_ACQUISITION_ATTEMPTS_NOT_ANALYSIS","sources":[acquire(k,v,z.private) for k,v in SOURCES.items()],"no_credentials_or_access_bypass":True,"no_source_data_uploaded":True}
    z.output.parent.mkdir(parents=True,exist_ok=True)
    z.output.write_text(json.dumps(result,indent=2)+"\n")
    print(json.dumps(result))
if __name__=="__main__":main()
