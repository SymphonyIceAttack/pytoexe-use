from pathlib import Path
import textwrap, zipfile, os, shutil, re

base = Path("/mnt/data/html_a_epub")
if base.exists():
    shutil.rmtree(base)
base.mkdir()

# Python script: converts Word HTML to a minimal EPUB3, preserving underline, highlight, bold, italic.
script = r'''import sys, re, html, zipfile, tempfile, shutil
from pathlib import Path
from html.parser import HTMLParser

class WordHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.out=[]
        self.in_body=False
        self.skip=0
        self.stack=[]
        self.pending=[]
    def handle_starttag(self, tag, attrs):
        tag=tag.lower()
        d={k.lower(): (v or '') for k,v in attrs}
        if tag=="body":
            self.in_body=True; return
        if not self.in_body or self.skip:
            if tag in ("script","style","xml"): self.skip+=1
            return
        if tag in ("script","style","xml"): self.skip+=1; return
        if tag=="p":
            self.out.append("<p>")
        elif tag=="br":
            self.out.append("<br/>")
        elif tag in ("u","b","strong","i","em"):
            m={"u":"u","b":"strong","strong":"strong","i":"em","em":"em"}[tag]
            self.out.append(f"<{m}>"); self.stack.append(m)
        elif tag=="span":
            st=d.get("style","").lower()
            if "background" in st or "mso-highlight" in st:
                color=None
                m=re.search(r'background(?:-color)?\s*:\s*([^;]+)', st)
                if m: color=m.group(1).strip()
                if not color:
                    m=re.search(r'mso-highlight\s*:\s*([^;]+)', st)
                    if m: color=m.group(1).strip()
                if color and color not in ("none","transparent"):
                    self.out.append(f'<span class="highlight" style="background-color:{html.escape(color, quote=True)}">')
                    self.stack.append("highlight")
                    return
            # preserve underline/bold/italic embedded in style
            opened=[]
            if re.search(r'text-decoration\s*:\s*[^;]*underline', st):
                self.out.append("<u>"); opened.append("u")
            if re.search(r'font-weight\s*:\s*(bold|[6-9]00)', st):
                self.out.append("<strong>"); opened.append("strong")
            if re.search(r'font-style\s*:\s*italic', st):
                self.out.append("<em>"); opened.append("em")
            self.stack.extend(opened)
    def handle_endtag(self, tag):
        tag=tag.lower()
        if tag=="body":
            self.in_body=False; return
        if not self.in_body or self.skip:
            if tag in ("script","style","xml") and self.skip: self.skip-=1
            return
        if tag in ("script","style","xml"): 
            if self.skip: self.skip-=1
            return
        if tag=="p":
            self.out.append("</p>")
        elif tag in ("u","b","strong","i","em","span"):
            # close the most recent tag corresponding to this HTML end tag
            target={"u":"u","b":"strong","strong":"strong","i":"em","em":"em"}.get(tag)
            if target and target in self.stack:
                while self.stack:
                    x=self.stack.pop()
                    self.out.append(f"</{x}>")
                    if x==target: break
    def handle_data(self,data):
        if self.in_body and not self.skip:
            # Word's non-breaking placeholder paragraphs
            if data.replace("\xa0","").strip()=="":
                return
            self.out.append(html.escape(data))
    def result(self):
        # best-effort close leftovers
        while self.stack:
            self.out.append("</"+self.stack.pop()+">")
        return "".join(self.out)

def convert(src):
    src=Path(src)
    raw=src.read_text(encoding="cp1252", errors="replace")
    p=WordHTMLParser(); p.feed(raw)
    body=p.result()
    # Remove empty paragraphs caused by Word
    body=re.sub(r'<p>\s*</p>', '', body)
    # Normalize consecutive whitespace, but retain paragraph structure
    body=re.sub(r'[ \t\r\n]+',' ',body)
    body=body.replace("</p> <p>","</p><p>")
    out=src.with_suffix(".epub")
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)
        (root/"META-INF").mkdir()
        (root/"OEBPS").mkdir()
        (root/"mimetype").write_text("application/epub+zip", encoding="ascii")
        (root/"META-INF/container.xml").write_text('''<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
<rootfiles><rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/></rootfiles>
</container>''', encoding="utf-8")
        title=src.stem
        xhtml=f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops">
<head><title>{html.escape(title)}</title><link rel="stylesheet" type="text/css" href="style.css"/></head>
<body><h1>{html.escape(title)}</h1>{body}</body></html>'''
        (root/"OEBPS/content.xhtml").write_text(xhtml, encoding="utf-8")
        (root/"OEBPS/style.css").write_text('''body{font-family:serif;line-height:1.35;margin:5%;}h1{font-size:1.4em;margin-bottom:1em;}p{margin:0 0 .7em 0;}u{text-decoration:underline;}strong{font-weight:bold;}em{font-style:italic;}.highlight{background-color:yellow;}''', encoding="utf-8")
        (root/"OEBPS/content.opf").write_text(f'''<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="bookid">
<metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
<dc:identifier id="bookid">urn:uuid:{abs(hash(str(src.resolve())))} </dc:identifier>
<dc:title>{html.escape(title)}</dc:title><dc:language>es</dc:language>
</metadata>
<manifest><item id="content" href="content.xhtml" media-type="application/xhtml+xml"/><item id="css" href="style.css" media-type="text/css"/></manifest>
<spine><itemref idref="content"/></spine>
</package>''', encoding="utf-8")
        with zipfile.ZipFile(out,"w",zipfile.ZIP_DEFLATED) as z:
            z.write(root/"mimetype","mimetype",compress_type=zipfile.ZIP_STORED)
            for f in (root/"META-INF").rglob("*"):
                z.write(f,f.relative_to(root).as_posix())
            for f in (root/"OEBPS").rglob("*"):
                z.write(f,f.relative_to(root).as_posix())
    return out

if __name__=="__main__":
    if len(sys.argv)<2:
        print("Arrastra un archivo HTML sobre este programa.")
        input("Pulsa ENTER para salir...")
    else:
        try:
            out=convert(sys.argv[1])
            print("EPUB creado:", out)
        except Exception as e:
            print("ERROR:",e)
        input("Pulsa ENTER para salir...")
'''
(base/"html_a_epub.py").write_text(script, encoding="utf-8")

# Create Windows launcher .bat that can be used without Python? We'll package a portable-ish folder + instructions,
# and also generate an EPUB from the user's supplied content for immediate testing.
html_content = r'''<html><body>
<p>Esto es un ejemplo:</p>
<p><u>El fichero ya est� reordenado por orden</u> <span style="background:yellow">pero solo por bloques de meses</span>, <b>dentro de cada mes est� a la inversa</b>.</p>
<p>En la linea anterio hay un trozo subrayado y otro trozo resalatdo de amarillo y otro trozo en negrita</p>
</body></html>'''
(base/"prueba.html").write_text(html_content, encoding="utf-8")
# run converter
import subprocess, sys
subprocess.run([sys.executable, str(base/"html_a_epub.py"), str(base/"prueba.html")], check=True, capture_output=True, text=True)
print(base/"prueba.epub")
