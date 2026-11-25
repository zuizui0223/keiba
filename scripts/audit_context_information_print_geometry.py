"""Query rendered text geometry from Inkscape; no original sources downloaded."""
import csv, itertools, json, subprocess, sys
from pathlib import Path
import xml.etree.ElementTree as ET

def audit(path):
    root=ET.parse(path).getroot()
    ids={x.attrib["id"] for x in root.iter("{http://www.w3.org/2000/svg}text")}
    rows=list(csv.reader(subprocess.check_output(["inkscape",str(path),"--query-all"],text=True).splitlines()))
    boxes={r[0]:tuple(map(float,r[1:])) for r in rows if len(r)==5 and r[0] in ids}
    if set(boxes)!=ids: raise ValueError("HOLD missing text geometry")
    W,H=180*96/25.4,115.3125*96/25.4
    outside=[k for k,(x,y,w,h) in boxes.items() if x < -0.5 or y < -0.5 or x+w > W+0.5 or y+h > H+0.5]
    collisions=[]
    for (a,(x,y,w,h)),(b,(X,Y,U,V)) in itertools.combinations(boxes.items(),2):
        overlap_x=min(x+w,X+U)-max(x,X)
        overlap_y=min(y+h,Y+V)-max(y,Y)
        if overlap_x>1 and overlap_y>1 and overlap_x*overlap_y > 0.05*min(w*h,U*V):
            collisions.append([a,b])
    return {"file":path.name,"labels":len(ids),"outside_canvas":outside,"text_box_overlaps":collisions,
            "status":"REVIEW" if outside or collisions else "PASS_GEOMETRY"}
if __name__=="__main__":
    rows=[audit(p) for p in sorted(Path(sys.argv[1]).glob("*.svg"))]
    if len(rows)!=4: raise ValueError("HOLD figure count")
    print(json.dumps({"status":"REVIEW" if any(r["status"]=="REVIEW" for r in rows) else "PASS_GEOMETRY","figures":rows},indent=2))
    # Preserve QA even when overlap candidates require human review. A rendered
    # box intersection is not itself a final visual-quality verdict.
    if any(r["status"]=="REVIEW" for r in rows): sys.exit(2)
