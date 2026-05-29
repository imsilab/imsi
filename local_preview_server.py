from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote
import mimetypes
import os


ROOT = Path(__file__).resolve().parent


class IMSIPreviewHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path: str) -> str:
        path = unquote(path.split("?", 1)[0].split("#", 1)[0])
        if path == "/":
            rel = "index.html"
        elif path.startswith("/imsi/"):
            rel = path[len("/imsi/"):]
        else:
            rel = path.lstrip("/")

        target = (ROOT / rel).resolve()
        try:
            target.relative_to(ROOT)
        except ValueError:
            return str(ROOT)
        return str(target)

    def end_headers(self) -> None:
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def guess_type(self, path):
        mime, _ = mimetypes.guess_type(path)
        if mime:
            return mime
        return "application/octet-stream"


def main() -> None:
    port = int(os.environ.get("IMSI_PREVIEW_PORT", "4000"))
    server = ThreadingHTTPServer(("127.0.0.1", port), IMSIPreviewHandler)
    print(f"Serving IMSI preview at http://127.0.0.1:{port}/imsi/")
    server.serve_forever()


if __name__ == "__main__":
    main()
