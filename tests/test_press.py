import copy
import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT / "skills" / "morning-press" / "scripts"))
sys.path.insert(0,str(ROOT / "tools"))
from core import PUBLIC_ROOT, SKILL, data_home, profile_path, public_url, read_json, save_profile, validate_issue, validate_profile
from render import markdown, pdf_bytes, render
from press import main, wizard
from check_public import findings, scan
from pypdf import PdfReader


class PressTests(unittest.TestCase):
    def setUp(self):
        self.profile = read_json(SKILL / "assets" / "example-profile.json")
        self.issue = read_json(SKILL / "assets" / "demo-issue.json")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def test_example_satisfies_contract(self):
        validate_issue(self.issue,self.profile)

    def test_profiles_are_isolated_and_private(self):
        first = save_profile(self.base,"first",self.profile)
        other = copy.deepcopy(self.profile)
        other["publication"]["title"] = "Another Edition"
        second = save_profile(self.base,"second",other)
        self.assertNotEqual(read_json(first)["publication"]["title"],read_json(second)["publication"]["title"])
        if os.name != "nt":
            self.assertEqual(first.stat().st_mode & 0o777,0o600)
        with self.assertRaises(ValueError):
            save_profile(self.base,"first",other)

    def test_package_cannot_hold_private_data(self):
        for location in (PUBLIC_ROOT, PUBLIC_ROOT / "profiles"):
            with self.assertRaises(ValueError):
                data_home(location)
        with self.assertRaises(ValueError):
            profile_path(self.base,"../outside")

    def test_bad_timezone_and_unknown_fields_rejected(self):
        self.profile["publication"]["timezone"] = "Nowhere/City"
        with self.assertRaises(ValueError):
            validate_profile(self.profile)
        self.profile["publication"]["timezone"] = "UTC"
        self.profile["password"] = "not-a-real-password"
        with self.assertRaises(ValueError):
            validate_profile(self.profile)

    def test_draft_cannot_produce_real_edition(self):
        self.profile["status"] = "draft"
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)

    def test_no_sections_rejected(self):
        for s in self.profile["sections"]:
            s["enabled"] = False
        with self.assertRaises(ValueError):
            validate_profile(self.profile)

    def test_weather_and_screen_need_branch_answers(self):
        s = self.profile["sections"][0]
        s["kind"] = "weather"
        with self.assertRaises(ValueError):
            validate_profile(self.profile)
        s["options"] = {"locations":[{"name":"Example City","timezone":"UTC"}],"temperature":"fahrenheit","wind":"mph","weather_format":"detailed"}
        validate_profile(self.profile)
        s["kind"] = "screen"
        s["options"] = {}
        with self.assertRaises(ValueError):
            validate_profile(self.profile)

    def test_markdown_only_cannot_promise_printed_qr(self):
        self.profile["publication"]["format"] = "markdown"
        self.profile["publication"]["links"]["qr"] = True
        with self.assertRaises(ValueError):
            validate_profile(self.profile)

    def test_duplicate_section_ids_rejected(self):
        self.profile["sections"][1]["id"] = self.profile["sections"][0]["id"]
        with self.assertRaises(ValueError):
            validate_profile(self.profile)

    def test_disabled_sections_cannot_leak_into_issue(self):
        self.profile["sections"][-1]["enabled"] = False
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)
        self.issue["sections"].pop()
        validate_issue(self.issue,self.profile)
        self.assertNotIn("A small discovery",markdown(self.issue,self.profile))

    def test_item_cap_enforced(self):
        self.profile["sections"][0]["max_items"] = 1
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)

    def test_pending_and_unexplained_missing_data_rejected(self):
        s = self.issue["sections"][0]
        s.update(status="pending",items=[])
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)
        s.update(status="unavailable",note="")
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)
        s["note"] = "Source could not be reached."
        validate_issue(self.issue,self.profile)

    def test_real_copy_needs_provenance(self):
        self.issue["demo"] = False
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)

    def test_source_allowlist_and_timestamp(self):
        self.issue["demo"] = False
        for s in self.issue["sections"]:
            for item in s["items"]:
                item["source"] = {"publisher":"Example Publisher","url":item["url"],"published_at":None,"checked_at":"2000-01-01T07:00:00Z"}
        validate_issue(self.issue,self.profile)
        self.profile["sections"][0]["sources"] = {"mode":"allowlist","domains":["example.com"]}
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)
        self.profile["sections"][0]["sources"]["domains"] = ["example.org"]
        self.issue["sections"][0]["items"][0]["source"]["checked_at"] = "2000-01-02T07:00:00Z"
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)

    def test_calendar_has_no_printable_private_urls(self):
        self.profile["sections"] = self.profile["sections"][:1]
        p = self.profile["sections"][0]
        p["kind"] = "calendar"
        p["options"] = {"providers":[{"provider":"apple","mode":"manual","state":"manual","calendars":[]}],"calendar_privacy":"busy-only"}
        self.issue["sections"] = self.issue["sections"][:1]
        for item in self.issue["sections"][0]["items"]:
            item["url"] = None
        validate_issue(self.issue,self.profile)
        self.issue["sections"][0]["items"][0]["url"] = "https://example.org/"
        with self.assertRaises(ValueError):
            validate_issue(self.issue,self.profile)

    def test_private_and_tokenized_destinations_rejected(self):
        for url in ("http://example.org/", "https://example.org/?token=fictional", "https://user:pass" + "@" + "example.org/", "https://127.0.0.1/", "https://localhost/", "https://meet.google.com/example", "https://a.zoom.us/example", "https://example.org/#secret"):
            with self.subTest(url=url), self.assertRaises(ValueError):
                public_url(url)
        public_url("https://example.org/article")

    def test_pdf_text_links_and_demo_labels(self):
        data,layout = pdf_bytes(self.issue,self.profile)
        reader = PdfReader(io.BytesIO(data))
        self.assertEqual(len(reader.pages),2)
        self.assertEqual(len(layout["digital_links"]),5)
        self.assertEqual(layout["qr_codes"],[])
        text = "\n".join(page.extract_text() for page in reader.pages)
        self.assertEqual(text.count("DEMONSTRATION - FICTIONAL CONTENT"),2)
        self.assertIn("verified scientific result",text)
        self.assertNotIn("calendar account",text)

    def test_qr_and_digital_links_are_independent(self):
        self.profile["publication"]["links"] = {"qr":True,"clickable":False}
        data,layout = pdf_bytes(self.issue,self.profile)
        self.assertEqual(len(layout["qr_codes"]),5)
        self.assertEqual(layout["digital_links"],[])
        self.assertFalse(any(page.get("/Annots") for page in PdfReader(io.BytesIO(data)).pages))
        self.assertTrue(all(r["rect"][2]-r["rect"][0] >= 64 for r in layout["qr_codes"]))
        self.assertTrue(all(r["module_mm"] >= 0.4 for r in layout["qr_codes"]))

    def test_overdense_qr_destination_fails_clearly(self):
        self.profile["publication"]["links"]["qr"] = True
        self.issue["sections"][0]["items"][0]["url"] = "https://example.org/" + "long" * 400
        with self.assertRaisesRegex(ValueError,"QR destination is too long"):
            pdf_bytes(self.issue,self.profile)

    def test_news_only_letter_monochrome_has_no_optional_sections(self):
        self.profile["publication"].update(pages=1,paper="Letter",color="monochrome",body_size=10)
        self.profile["sections"] = self.profile["sections"][:1]
        self.issue["sections"] = self.issue["sections"][:1]
        validate_issue(self.issue,self.profile)
        data,layout = pdf_bytes(self.issue,self.profile)
        page = PdfReader(io.BytesIO(data)).pages[0]
        self.assertEqual(layout["pages"],1)
        self.assertEqual(round(float(page.mediabox.width)),612)
        self.assertNotIn("Between the pages",page.extract_text())
        self.assertNotIn("A small discovery",page.extract_text())

    def test_pdf_page_budget_failure_leaves_no_output(self):
        for pages in (1,12):
            self.profile["publication"]["pages"] = pages
            target = self.base / str(pages)
            with self.assertRaises(ValueError):
                render(self.issue,self.profile,target)
            self.assertFalse(target.exists())

    def test_markdown_works_without_fixed_pagination(self):
        self.profile["publication"].update(format="markdown",pages=12)
        paths = render(self.issue,self.profile,self.base / "edition")
        self.assertEqual([p.name for p in paths],["edition.md"])
        self.assertIn("DEMONSTRATION",paths[0].read_text())
        self.assertTrue((paths[0].parent / "profile.json").exists())

    def test_unicode_failure_is_explicit(self):
        self.issue["sections"][0]["items"][0]["title"] = "新聞"
        with self.assertRaisesRegex(ValueError,"font does not cover"):
            pdf_bytes(self.issue,self.profile)

    def test_revision_preserves_original_files(self):
        with redirect_stdout(io.StringIO()):
            main(["--data-dir",str(self.base),"demo"])
        original = self.base / "profiles/sample/demos/2000-01-01/edition.pdf"
        before = original.read_bytes()
        with redirect_stdout(io.StringIO()):
            main(["--data-dir",str(self.base),"demo"])
        self.assertEqual(original.read_bytes(),before)
        self.assertTrue((original.parent.parent / "2000-01-01-r2/edition.pdf").exists())
        self.assertFalse((self.base / "profiles/main/profile.json").exists())

    def test_import_confirmation_and_brief_pending(self):
        path = self.base / "draft.json"
        path.write_text(json.dumps(self.profile))
        args = ["--data-dir",str(self.base),"import-profile",str(path)]
        with redirect_stdout(io.StringIO()):
            main(args)
        self.assertEqual(read_json(profile_path(self.base,"main"))["status"],"draft")
        with redirect_stdout(io.StringIO()):
            main(args + ["--confirm","--replace"])
            main(["--data-dir",str(self.base),"brief","--date","2000-01-01"])
        draft = read_json(self.base / "profiles/main/drafts/2000-01-01.json")
        self.assertEqual(draft["sections"][0]["status"],"pending")
        with self.assertRaises(ValueError):
            validate_issue(draft,self.profile)

    def test_terminal_interview_news_only(self):
        answers = ["", "", "", "UTC", "markdown", "yes", "news", "News", "3", "science", "-", "balanced", "open", "Worldwide", "An adult reader", "Clear and calm", "36", "7", "no", "no", "yes"]
        with patch("builtins.input",side_effect=answers),redirect_stdout(io.StringIO()):
            wizard(self.base,"main",False)
        p = read_json(profile_path(self.base,"main"))
        self.assertEqual(p["status"],"ready")
        self.assertEqual([s["kind"] for s in p["sections"]],["news"])
        self.assertFalse(p["delivery"]["schedule_requested"])

    def test_interrupted_setup_keeps_resumable_draft(self):
        answers = ["My Edition", "", "", "UTC", "markdown", "yes", "news", "News", "3", "science", "-", "balanced", "open", "Worldwide"]
        with patch("builtins.input",side_effect=answers),redirect_stdout(io.StringIO()),self.assertRaises(StopIteration):
            wizard(self.base,"main",False)
        p = read_json(profile_path(self.base,"main"))
        self.assertEqual(p["status"],"draft")
        self.assertEqual(p["publication"]["title"],"My Edition")


class PublicGuardTests(unittest.TestCase):
    def test_sensitive_patterns_without_echoing_data(self):
        self.assertIn("email address",findings("reader" + "@" + "example.org"))
        self.assertIn("absolute home path",findings("/" + "Users/ExampleReader/private"))
        self.assertIn("credential-like token",findings("ghp" + "_" + "x"*30))
        self.assertEqual(findings("A fictional story about a public library."),[])

    def test_index_and_deleted_historical_data_are_checked(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            subprocess.run(["git","init","-q",str(root)],check=True)
            (root / "public-files.json").write_text(json.dumps(["public-files.json","story.txt"]))
            (root / "story.txt").write_text("A fictional public story")
            subprocess.run(["git","-C",str(root),"add","public-files.json","story.txt"],check=True)
            scan(root,True)
            (root / "story.txt").write_text("private reader" + "@" + "example.org")
            subprocess.run(["git","-C",str(root),"add","story.txt"],check=True)
            with self.assertRaises(ValueError):
                scan(root)
            subprocess.run(["git","-C",str(root),"-c","user.name=Test Contributor","-c","user.email=test.invalid","commit","-qm","Synthetic history"],check=True)
            (root / "story.txt").write_text("Clean current story")
            subprocess.run(["git","-C",str(root),"add","story.txt"],check=True)
            scan(root)
            with self.assertRaises(ValueError):
                scan(root,True)
            (root / "private.json").write_text("{}")
            subprocess.run(["git","-C",str(root),"add","private.json"],check=True)
            with self.assertRaises(ValueError):
                scan(root)


if __name__ == "__main__":
    unittest.main()
