import functools
import http.server
import json
import socket
import subprocess
import threading
import time
import unittest
import urllib.error
import urllib.request
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
FIREFOX = Path("/snap/firefox/current/usr/lib/firefox/firefox")
GECKODRIVER = Path("/snap/firefox/current/usr/lib/firefox/geckodriver")


def free_port():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, _format, *_args):
        pass


@unittest.skipUnless(FIREFOX.exists() and GECKODRIVER.exists(), "Firefox WebDriver is unavailable")
class BrowserSmokeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.web_port = free_port()
        handler = functools.partial(QuietHandler, directory=str(ROOT.parent))
        cls.web_server = http.server.ThreadingHTTPServer(("127.0.0.1", cls.web_port), handler)
        cls.web_thread = threading.Thread(target=cls.web_server.serve_forever, daemon=True)
        cls.web_thread.start()

        cls.driver_port = free_port()
        cls.driver = subprocess.Popen(
            [str(GECKODRIVER), "--port", str(cls.driver_port)],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        cls.driver_url = f"http://127.0.0.1:{cls.driver_port}"
        cls._wait_for_driver()

        response = cls._request(
            "POST",
            "/session",
            {
                "capabilities": {
                    "alwaysMatch": {
                        "browserName": "firefox",
                        "moz:firefoxOptions": {
                            "binary": str(FIREFOX),
                            "args": ["-headless"],
                        },
                    }
                }
            },
        )
        cls.session_id = response["value"]["sessionId"]
        cls._request("POST", f"/session/{cls.session_id}/timeouts", {"script": 30000})

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "session_id", None):
            try:
                cls._request("DELETE", f"/session/{cls.session_id}")
            except Exception:
                pass
        if getattr(cls, "driver", None):
            cls.driver.terminate()
            try:
                cls.driver.wait(timeout=5)
            except subprocess.TimeoutExpired:
                cls.driver.kill()
        if getattr(cls, "web_server", None):
            cls.web_server.shutdown()
            cls.web_server.server_close()

    @classmethod
    def _wait_for_driver(cls):
        deadline = time.time() + 15
        while time.time() < deadline:
            try:
                cls._request("GET", "/status")
                return
            except (urllib.error.URLError, ConnectionError):
                time.sleep(0.1)
        raise RuntimeError("geckodriver did not become ready")

    @classmethod
    def _request(cls, method, path, payload=None):
        data = None if payload is None else json.dumps(payload).encode("utf-8")
        request = urllib.request.Request(
            cls.driver_url + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json; charset=utf-8"},
        )
        with urllib.request.urlopen(request, timeout=35) as response:
            body = response.read()
        return json.loads(body) if body else {}

    @classmethod
    def _navigate(cls, path):
        cls._request(
            "POST",
            f"/session/{cls.session_id}/url",
            {"url": f"http://127.0.0.1:{cls.web_port}/imsi/{path.lstrip('/')}"},
        )

    @classmethod
    def _execute_async(cls, script):
        result = cls._request(
            "POST",
            f"/session/{cls.session_id}/execute/async",
            {"script": script, "args": []},
        )
        return result["value"]

    def test_sheet_and_local_news_merge_and_render_across_routes(self):
        self._navigate("/")
        merged_ids = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            getNews().then(rows => done(rows.map(row =>
              String(row.News_ID || row.Column_0 || '').replaceAll('_', '-').toUpperCase()
            ))).catch(error => done({error: String(error)}));
            """
        )
        self.assertIn("NEWS-001", merged_ids, "Google Sheet news should be retained")
        self.assertIn("NEWS-005", merged_ids)
        self.assertIn("NEWS-006", merged_ids)

        home_result = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const deadline = Date.now() + 20000;
            (function poll() {
              const root = document.getElementById('home-news-list');
              const text = root ? root.innerText : '';
              if (text.includes('NeurIPS 2026') && text.includes('2027년 1월')) {
                done({text, hrefs: [...root.querySelectorAll('a')].map(a => a.getAttribute('href'))});
              } else if (Date.now() > deadline) {
                done({error: 'home news timed out', text});
              } else {
                setTimeout(poll, 100);
              }
            })();
            """
        )
        self.assertNotIn("error", home_result)
        self.assertIn("/imsi/news/NEWS-005/index.html", home_result["hrefs"])
        self.assertIn("/imsi/news/NEWS-006/index.html", home_result["hrefs"])

        self._navigate("news/NEWS-005/")
        detail_result = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const deadline = Date.now() + 20000;
            (function poll() {
              const title = document.getElementById('news-title')?.innerText || '';
              const content = document.getElementById('news-content');
              const text = content?.innerText || '';
              if (title.includes('NeurIPS 2026') && text.includes('Auditing Capsule Vision 2024')) {
                done({title, text, links: [...content.querySelectorAll('a')].map(a => a.getAttribute('href'))});
              } else if (Date.now() > deadline) {
                done({error: 'detail timed out', title, text});
              } else {
                setTimeout(poll, 100);
              }
            })();
            """
        )
        self.assertNotIn("error", detail_result)
        self.assertTrue(any("1nDVguFzOGEUAD3mXIiqLD5wUfmn01ipk" in link for link in detail_result["links"]))
        for route in [
            "/imsi/authors/undergraduate_interns/eunseob-choi/",
            "/imsi/authors/research_assistants/kyeonghun-kim/",
            "/imsi/authors/investigators/hyukjae-lee/",
            "/imsi/authors/investigators/nam-joon-kim/",
        ]:
            self.assertIn(route, detail_result["links"])

        self._navigate("news/NEWS-006/")
        interview_result = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const deadline = Date.now() + 20000;
            (function poll() {
              const text = document.getElementById('news-content')?.innerText || '';
              if (text.includes('참석 확정자에게 별도 안내')) {
                done({text, links: [...document.querySelectorAll('#news-content a')].map(a => a.getAttribute('href'))});
              } else if (Date.now() > deadline) {
                done({error: 'interview timed out', text});
              } else {
                setTimeout(poll, 100);
              }
            })();
            """
        )
        self.assertNotIn("error", interview_result)
        self.assertNotIn("입구비번", interview_result["text"])
        self.assertNotIn("2층입구비번", interview_result["text"])
        self.assertIn("http://capp.snu.ac.kr/imsi/", interview_result["links"])
        self.assertIn("NVIDIA San Jose", interview_result["text"])

    def test_people_order_and_yului_profile_render(self):
        self._navigate("/")
        names = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const heading = [...document.querySelectorAll('#people h2')]
              .find(node => node.textContent.trim() === 'Undergraduate Interns');
            const names = [];
            let node = heading?.parentElement?.nextElementSibling;
            while (node && !node.querySelector('h2.mb-4')) {
              const name = node.querySelector('.portrait-title h2')?.textContent.trim();
              if (name) names.push(name);
              node = node.nextElementSibling;
            }
            done(names);
            """
        )
        self.assertEqual(
            ["Eunseob Choi", "Yului Jeong", "Hyunsu Go", "Jooyoung Bae", "Anna Jung", "Giseong Hwang"],
            names,
        )

        self._navigate("authors/undergraduate_interns/yului-jeong/")
        profile = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const image = document.querySelector('#profile img.portrait');
            const deadline = Date.now() + 10000;
            (function poll() {
              if (image?.complete && image.naturalWidth) {
                done({width: image.naturalWidth, text: document.body.innerText});
              } else if (Date.now() > deadline) {
                done({error: 'profile image timed out'});
              } else {
                setTimeout(poll, 100);
              }
            })();
            """
        )
        self.assertNotIn("error", profile)
        self.assertEqual(512, profile["width"])
        self.assertIn("Global Track Silver Award", profile["text"])
        self.assertIn("Scheduled for October 26, 2026", profile["text"])


if __name__ == "__main__":
    unittest.main()
