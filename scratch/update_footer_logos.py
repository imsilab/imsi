import re
from pathlib import Path

ROOT = Path(r"c:\Users\임준수\Desktop\imsi_capp")

# Precise regex to match the exact row block and all its 4 nested divs in original state
footer_pattern = re.compile(
    r'<div class="row justify-content-center align-items-center mb-5">\s*'
    r'<div class="col-auto px-4 d-flex align-items-center justify-content-center">\s*'
    r'<img src="/imsi/images/logo/capp\.png"[^>]*>\s*'
    r'</div>\s*'
    r'<div class="col-auto px-4 d-flex align-items-center justify-content-center">\s*'
    r'<img src="/imsi/images/logo/snu\.jpg"[^>]*>\s*'
    r'</div>\s*'
    r'<div class="col-auto px-4 d-flex align-items-center justify-content-center">\s*'
    r'<img src="/imsi/images/logo/smc\.png"[^>]*>\s*'
    r'</div>\s*'
    r'</div>',
    re.DOTALL
)

new_footer = """<div class="d-flex justify-content-center align-items-center flex-wrap mb-5" style="gap: 3rem; margin-top: 2rem;">
        <div class="d-flex align-items-center justify-content-center" style="width: 260px; height: 120px;">
          <img src="/imsi/images/logo/capp.png" alt="CAPP Lab Logo" style="max-height: 120px; max-width: 100%; object-fit: contain;">
        </div>
        <div class="d-flex align-items-center justify-content-center" style="width: 260px; height: 120px;">
          <img src="/imsi/images/logo/snu.jpg" alt="SNU Logo" style="max-height: 120px; max-width: 100%; object-fit: contain;">
        </div>
        <div class="d-flex align-items-center justify-content-center" style="width: 260px; height: 120px;">
          <img src="/imsi/images/logo/smc.png" alt="SMC Logo" style="max-height: 120px; max-width: 100%; object-fit: contain;">
        </div>
      </div>"""

def main():
    html_files = list(ROOT.rglob("*.html"))
    modified_count = 0
    print(f"Found {len(html_files)} HTML files in total.")
    
    for f in html_files:
        if ".git" in f.parts or "node_modules" in f.parts:
            continue
        try:
            content = f.read_text(encoding="utf-8")
        except Exception as e:
            try:
                content = f.read_text(encoding="latin-1")
            except Exception as e2:
                print(f"Could not read {f}: {e2}")
                continue
                
        if footer_pattern.search(content):
            new_content = footer_pattern.sub(new_footer, content)
            f.write_text(new_content, encoding="utf-8")
            modified_count += 1
            print(f"Updated: {f.relative_to(ROOT)}")
            
    print(f"Successfully updated {modified_count} files!")

if __name__ == "__main__":
    main()
