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
            ["Eunseob Choi", "Yului Jeong", "Hyunsu Go", "Jooyoung Bae", "Anna Jung", "Minjun Yoo", "Giseong Hwang"],
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

    def test_publication_search_reports_count_and_new_link_actions(self):
        self._navigate("publication/")
        initial = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const deadline = Date.now() + 20000;
            (function poll() {
              const count = document.getElementById('pub-result-count');
              const cards = [...document.querySelectorAll('#publication-dynamic-list .pub-card')];
              if (count && cards.length) {
                done({
                  count: count.innerText,
                  cards: cards.length,
                  labels: [...document.querySelectorAll('#publication-dynamic-list .pub-card-actions > *')]
                    .map(node => node.innerText.trim())
                });
              } else if (Date.now() > deadline) {
                done({error: 'publication archive timed out', body: document.body.innerText});
              } else {
                setTimeout(poll, 100);
              }
            })();
            """
        )
        self.assertNotIn("error", initial)
        self.assertIn(str(initial["cards"]), initial["count"])
        self.assertIn("GDrive", initial["labels"])
        self.assertIn("arXiv", initial["labels"])

        zero = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const input = document.getElementById('pub-search-dynamic');
            input.value = 'definitely-no-such-publication-928374';
            input.dispatchEvent(new Event('input', {bubbles: true}));
            setTimeout(() => done({
              count: document.getElementById('pub-result-count')?.innerText || '',
              cards: document.querySelectorAll('#publication-dynamic-list .pub-card').length
            }), 100);
            """
        )
        self.assertEqual(0, zero["cards"])
        self.assertIn("0", zero["count"])

        lab_filter = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            done({
              personal: IMSI.Publications.isLabPublication(IMSI.Publications.normalize({Remarks: 'PERSONAL'})),
              lab: IMSI.Publications.isLabPublication(IMSI.Publications.normalize({Remarks: 'Lab'}))
            });
            """
        )
        self.assertFalse(lab_filter["personal"])
        self.assertTrue(lab_filter["lab"])

    def test_new_and_updated_profiles_render_required_links_and_assets(self):
        self._navigate("authors/undergraduate_interns/minjun-yoo/")
        minjun = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const image = document.querySelector('#profile img.portrait');
            const deadline = Date.now() + 10000;
            (function poll() {
              if (image?.complete && image.naturalWidth) {
                done({
                  width: image.naturalWidth,
                  text: document.body.innerText,
                  links: [...document.querySelectorAll('a')].map(a => a.getAttribute('href'))
                });
              } else if (Date.now() > deadline) {
                done({error: 'Minjun profile image timed out'});
              } else setTimeout(poll, 100);
            })();
            """
        )
        self.assertNotIn("error", minjun)
        self.assertGreater(minjun["width"], 0)
        self.assertIn("Geuneulro", minjun["text"])
        self.assertTrue(any("apps.apple.com/kr/app/" in link for link in minjun["links"]))

        for route in [
            "authors/undergraduate_interns/eunseob-choi/",
            "authors/research_assistants/kyeonghun-kim/",
        ]:
            self._navigate(route)
            highlight = self._execute_async(
                """
                const done = arguments[arguments.length - 1];
                const link = document.querySelector('a[href="/imsi/news/NEWS-005/"]');
                done({text: document.body.innerText, href: link?.getAttribute('href') || ''});
                """
            )
            self.assertEqual("/imsi/news/NEWS-005/", highlight["href"])
            self.assertIn("Two NeurIPS 2026 Papers Accepted", highlight["text"])

        self._navigate("authors/research_assistants/kyeonghun-kim/")
        kyeonghun = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            done({
              text: document.body.innerText,
              orcid: document.querySelector('a[href="https://orcid.org/0009-0002-9405-8424"]')?.href || '',
              awards: [...document.querySelectorAll('[data-fancybox="blood-donation-awards"]')].map(a => a.getAttribute('href'))
            });
            """
        )
        self.assertTrue(kyeonghun["orcid"])
        self.assertEqual(2, len(kyeonghun["awards"]))
        self.assertIn("Teaching Experience", kyeonghun["text"])

        self._navigate("authors/research_assistants/youngung-han/")
        youngung_orcid = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            done(Boolean(document.querySelector('a[href="https://orcid.org/0009-0008-0596-8367"]')));
            """
        )
        self.assertTrue(youngung_orcid)

    def test_kyeonghun_profile_loads_recent_publications_from_sheet(self):
        self._navigate("authors/research_assistants/kyeonghun-kim/")
        result = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const deadline = Date.now() + 15000;
            (function poll() {
              const root = document.querySelector('[data-author-publications="Kyeonghun Kim"]');
              const items = root ? [...root.querySelectorAll('li')] : [];
              const text = root?.innerText || '';
              if (items.length > 0 && !text.includes('Loading publications')) {
                done({count: items.length, text, actions: root.querySelectorAll('.profile-publication-actions a').length});
              } else if (Date.now() > deadline) {
                done({error: 'publication profile timed out', text});
              } else setTimeout(poll, 100);
            })();
            """
        )
        self.assertNotIn("error", result)
        self.assertGreater(result["count"], 0)
        self.assertNotIn("No publications found", result["text"])
        self.assertGreater(result["actions"], 0)

    def test_people_sheet_normalization_contract(self):
        self._navigate("/")
        result = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            if (typeof normalizePeopleRows !== 'function' ||
                typeof createPeopleLookup !== 'function' ||
                typeof resolveTeamPerson !== 'function') {
              done({error: 'normalization API missing'});
              return;
            }

            const malformed = [
              {
                P_0001: 'P_0002', Professor: 'Researcher', Name_EN_FULL: 'Nam-Joon Kim',
                Column_0: 'P_0002', Column_1: 'Researcher', Column_2: 'Nam-Joon Kim',
                Column_3: '', Column_4: '', Column_5: '', Column_6: 'knj01@snu.ac.kr'
              },
              {
                P_0001: 'P_0003', Professor: 'Researcher', Name_EN_FULL: 'Kyeonghun Kim',
                Column_0: 'P_0003', Column_1: 'Researcher', Column_2: 'Kyeonghun Kim',
                Column_3: 'OUTTA', Column_4: 'AI Research', Column_5: '',
                Column_6: 'kyeonghun.kim@outta.ai', Column_9: 'https://github.com/khkim1729'
              },
              {P_0001: '', Professor: '', Name_EN_FULL: '', Column_0: '', Column_1: '', Column_2: ''}
            ];
            const normalized = normalizePeopleRows(malformed);
            const valid = normalizePeopleRows([
              {Person_ID: 'P_0099', Category: 'Alumni', Name_EN_FULL: 'Valid Person'}
            ]);
            const lookup = createPeopleLookup(normalized);
            const exact = resolveTeamPerson({Person_ID: 'P_0002'}, lookup);
            const fallback = resolveTeamPerson({Person_ID: 'P_0003'}, lookup);
            const byName = resolveTeamPerson({Name_EN_FULL: '  kyeonghun   kim '}, lookup);

            const transitionRows = [];
            for (let number = 2; number <= 31; number += 1) {
              const id = `P_${String(number).padStart(4, '0')}`;
              const name = number === 31 ? 'Sehyun Kim' : `Person ${number}`;
              transitionRows.push({
                P_0001: id, Professor: 'Student', Name_EN_FULL: name,
                Column_0: id, Column_1: 'Student', Column_2: name
              });
            }
            transitionRows.push({
              P_0001: '', Professor: '', Name_EN_FULL: 'Donghyun Seo',
              Column_0: '', Column_1: '', Column_2: 'Donghyun Seo'
            });
            transitionRows.push({
              P_0001: 'P_0032', Professor: 'Alumni', Name_EN_FULL: 'Wongyeong Lee',
              Column_0: 'P_0032', Column_1: 'Alumni', Column_2: 'Wongyeong Lee'
            });
            const transition = normalizePeopleRows(transitionRows).slice(-3);
            done({
              normalized,
              valid,
              exact: exact?.Name_EN_FULL || '',
              fallback: fallback?.Name_EN_FULL || '',
              byName: byName?.Name_EN_FULL || '',
              transition
            });
            """
        )
        self.assertNotIn("error", result)
        self.assertEqual(2, len(result["normalized"]))
        self.assertEqual("P_0001", result["normalized"][0]["Person_ID"])
        self.assertEqual("P_0002", result["normalized"][1]["Person_ID"])
        self.assertEqual("P_0003", result["normalized"][1]["_SheetPerson_ID"])
        self.assertEqual("P_0099", result["valid"][0]["Person_ID"])
        self.assertEqual("Kyeonghun Kim", result["exact"])
        self.assertEqual("Kyeonghun Kim", result["fallback"])
        self.assertEqual("Kyeonghun Kim", result["byName"])
        self.assertEqual(
            [
                ("P_0030", "Sehyun Kim"),
                ("P_0031", "Donghyun Seo"),
                ("P_0032", "Wongyeong Lee"),
            ],
            [(person["Person_ID"], person["Name_EN_FULL"]) for person in result["transition"]],
        )

    def test_teams_and_alumni_render_from_live_sheet(self):
        self._navigate("alumni/")
        result = self._execute_async(
            """
            const done = arguments[arguments.length - 1];
            const deadline = Date.now() + 25000;
            (function poll() {
              const teams = document.getElementById('teams-people-row');
              const alumni = document.getElementById('alumni-people-row');
              const loadedLocalImages = teams
                ? [...teams.querySelectorAll('img')].filter(img =>
                    img.getAttribute('src')?.startsWith('/imsi/authors/') && img.complete && img.naturalWidth > 0
                  )
                : [];
              const alumniText = alumni?.innerText || '';
              if (loadedLocalImages.length && alumniText.includes('Youngung Han')) {
                const teamMembers = teamName => {
                  const heading = [...teams.querySelectorAll('.col-md-12 h2')]
                    .find(node => node.textContent.includes(teamName));
                  const names = [];
                  let card = heading?.parentElement?.nextElementSibling;
                  while (card && !card.classList.contains('col-md-12')) {
                    const name = card.querySelector('.portrait-title h2')?.textContent.trim();
                    if (name) names.push(name);
                    card = card.nextElementSibling;
                  }
                  return names;
                };
                done({
                  teamText: teams.innerText,
                  alumniText,
                  localImageCount: loadedLocalImages.length,
                  haedal: teamMembers('Team HAEDAL'),
                  multimodal: teamMembers('Team MultiModal'),
                  pni: teamMembers('Team PNI')
                });
              } else if (Date.now() > deadline) {
                done({error: 'Teams/Alumni timed out', teamText: teams?.innerText || '', alumniText});
              } else setTimeout(poll, 100);
            })();
            """
        )
        self.assertNotIn("error", result)
        self.assertGreater(result["localImageCount"], 0)
        self.assertIn("Youngung Han", result["alumniText"])
        self.assertNotIn("Name_EN_FULL", result["teamText"] + result["alumniText"])
        self.assertIn("Donghyun Seo", result["haedal"])
        self.assertIn("Sehyun Kim", result["multimodal"])
        self.assertIn("Dohyun Kweon", result["multimodal"])
        self.assertNotIn("Wongyeong Lee", result["haedal"])
        self.assertIn("Wongyeong Lee", result["alumniText"])
        self.assertIn("Seongheon Choi", result["alumniText"])
        self.assertIn("Jihyun Bang", result["alumniText"])


if __name__ == "__main__":
    unittest.main()
