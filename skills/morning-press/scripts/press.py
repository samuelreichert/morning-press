#!/usr/bin/env python3
"""Morning Press CLI. Research and connector access belong to the host agent."""
from __future__ import annotations

import argparse
import copy
import json
import sys
from datetime import datetime
from pathlib import Path

from core import KINDS, SKILL, data_home, private_write, profile_path, read_json, save_profile, timezone, validate_issue, validate_profile, validate_schema


def ask(label, default=""):
    answer = input(f"{label}" + (f" [{default}]" if default != "" else "") + ": ").strip()
    return answer if answer else str(default)


def yes(label, default=False):
    while True:
        answer = ask(label + " (yes/no)", "yes" if default else "no").lower()
        if answer in ("yes", "y", "no", "n"):
            return answer in ("yes", "y")
        print("Please enter yes or no.")


def select(label, values, default):
    while True:
        answer = ask(label + " (" + "/".join(values) + ")", default)
        if answer in values:
            return answer
        print("Choose one of the listed values.")


def number(label, default, low=1, high=20):
    while True:
        try:
            n = int(ask(label, default))
            if low <= n <= high:
                return n
        except ValueError:
            pass
        print(f"Enter a whole number from {low} to {high}.")


def csv(label, current=()):
    value = ask(label + " (comma-separated; '-' clears)", ", ".join(current))
    return [] if value == "-" else [v.strip() for v in value.split(",") if v.strip()]


def new_section(kind):
    return {"id":kind,"kind":kind,"title":kind.title(),"enabled":True,"max_items":3,"regions":[],"topics":[],"exclude":[],"depth":"balanced","sources":{"mode":"open","domains":[]},"options":{}}


def wizard(base, name, replace):
    path = profile_path(base, name)
    if path.exists():
        profile = read_json(path)
        validate_profile(profile)
        if profile["status"] == "ready" and not replace:
            raise ValueError("Profile is already ready. Use setup --replace to edit it.")
        print("Resuming the existing profile. Enter keeps a previous answer.")
    else:
        profile = copy.deepcopy(read_json(SKILL / "assets" / "example-profile.json"))
        profile["status"] = "draft"
        profile["sections"] = [new_section("news")]
    pub = profile["publication"]
    print("\n1. Your newspaper\nAnswers stay in private local storage. No accounts will be connected by this wizard.")
    pub["title"] = ask("Newspaper title", pub["title"])
    pub["subtitle"] = ask("Subtitle ('-' for none)", pub["subtitle"])
    if pub["subtitle"] == "-":
        pub["subtitle"] = ""
    pub["language"] = ask("Newspaper language (e.g. en or pt-BR)", pub["language"])
    while True:
        pub["timezone"] = ask("IANA timezone (e.g. UTC or Asia/Tokyo)", pub["timezone"])
        try:
            timezone(pub["timezone"])
            break
        except ValueError as exc:
            print(exc)
    pub["format"] = select("Output", ("pdf","markdown","both"), pub["format"])
    if pub["format"] != "markdown":
        pub["pages"] = number("PDF pages (content must fit exactly)",pub["pages"],1,12)
        pub["paper"] = select("Paper", ("A4","Letter"),pub["paper"])
        pub["color"] = select("Appearance", ("color","monochrome"),pub["color"])
        pub["body_size"] = number("Body text size in points",pub["body_size"],10,13)
    pub["links"]["clickable"] = yes("Clickable headlines",pub["links"]["clickable"])
    pub["links"]["qr"] = yes("Printed QR codes (PDF only)",pub["links"]["qr"]) if pub["format"] != "markdown" else False

    print("\n2. Sections, in reading order\nEvery section is optional. Add custom categories in conversation with the skill.")
    while True:
        chosen = csv("Choose section kinds in order: " + ", ".join(KINDS),[s["kind"] for s in profile["sections"] if s["enabled"]])
        if chosen and len(chosen) == len(set(chosen)) and set(chosen) <= set(KINDS):
            break
        print("Choose at least one kind, without duplicates. Use conversation for several sections of the same kind.")
    existing = {s["kind"]:s for s in profile["sections"]}
    profile["sections"] = [existing.get(kind,new_section(kind)) for kind in chosen]
    for s in profile["sections"]:
        s["enabled"] = True
        print(f"\n{s['kind'].title()}")
        s["title"] = ask("Section title",s["title"])
        s["max_items"] = number("Maximum items",s["max_items"])
        s["topics"] = csv("Topics / interests",s["topics"])
        s["exclude"] = csv("Topics to avoid",s["exclude"])
        s["depth"] = select("Depth", ("brief","balanced","deep"),s["depth"])
        s["sources"]["mode"] = select("Sources", ("open","allowlist"),s["sources"]["mode"])
        if s["sources"]["mode"] == "allowlist":
            s["sources"]["domains"] = csv("Allowed source domains",s["sources"]["domains"])
        opts, kind = s["options"], s["kind"]
        if kind in ("news","positive","events"):
            s["regions"] = csv("Regions (city/region/country or Worldwide)",s["regions"])
        if kind == "weather":
            locations = csv("Weather locations",[x["name"] for x in opts.get("locations",[])])
            previous = {x["name"]:x["timezone"] for x in opts.get("locations",[])}
            opts["locations"] = [{"name":loc,"timezone":ask(f"Timezone for {loc}",previous.get(loc,pub["timezone"]))} for loc in locations]
            opts["temperature"] = select("Temperature",("celsius","fahrenheit"),opts.get("temperature","celsius"))
            opts["wind"] = select("Wind",("kmh","mph","ms"),opts.get("wind","kmh"))
            opts["weather_format"] = select("Forecast format",("compact","detailed"),opts.get("weather_format","compact"))
        if kind == "calendar":
            print("Choose a provider preference; connection availability is checked by the agent later. Never enter credentials or feed URLs here.")
            provider = select("Calendar provider",("google","apple","outlook","notion","ics","manual","other"),opts.get("providers",[{}])[0].get("provider","manual"))
            mode = select("Access",("connector","manual"),"manual" if provider in ("ics","manual") else "connector")
            opts["providers"] = [{"provider":provider,"mode":mode,"state":"pending" if mode=="connector" else "manual","calendars":csv("Calendar names to include")}]
            opts["calendar_privacy"] = select("Calendar detail",("details","busy-only"),opts.get("calendar_privacy","busy-only"))
        if kind == "economy":
            opts["instruments"] = csv("Instruments and currency pairs (or '-' for topics only)",opts.get("instruments",[]))
            opts["currency"] = ask("Reporting currency (ISO code)",opts.get("currency","USD")).upper()
        if kind in ("books","screen"):
            opts["interests"] = csv("Genres, themes, or favorite creators",opts.get("interests",[]))
            opts["avoid"] = csv("Already read/watched or disliked",opts.get("avoid",[]))
            opts["spoiler_free"] = yes("Avoid spoilers",opts.get("spoiler_free",True))
        if kind == "screen":
            opts["country"] = ask("Streaming catalog country",opts.get("country",""))
            opts["services"] = csv("Streaming services (or '-' for any)",opts.get("services",[]))
        if kind == "events":
            opts["horizon_days"] = number("Event horizon in days",opts.get("horizon_days",14),1,90)
            opts["weekend_plan"] = yes("Include a weekend plan",opts.get("weekend_plan",False))
        if kind == "learning":
            opts["learning_level"] = select("Level",("beginner","intermediate","advanced"),opts.get("learning_level","beginner"))
            opts["learning_format"] = select("Learning format",("concept","challenge","mixed"),opts.get("learning_format","concept"))
        if kind == "language":
            opts["language_target"] = ask("Language to learn",opts.get("language_target",""))
        # Save checkpoints so an interrupted interview can resume.
        profile["status"] = "draft"
        save_profile(base,name,profile,replace=True)

    print("\n3. Editorial preferences and delivery")
    ed = profile["editorial"]
    ed["audience"] = ask("Who is the newspaper for? (no personal names needed)",ed["audience"])
    ed["tone"] = ask("Editorial tone",ed["tone"])
    ed["lookback_hours"] = number("News lookback in hours",ed["lookback_hours"],1,168)
    ed["avoid_repeats_days"] = number("Avoid repeats for days",ed["avoid_repeats_days"],0,90)
    delivery = profile["delivery"]
    delivery["schedule_requested"] = yes("Record an interest in scheduled generation",delivery["schedule_requested"])
    if delivery["schedule_requested"]:
        delivery["time"] = ask("Preferred local time (HH:MM)",delivery["time"] or "07:00")
        delivery["weekdays"] = csv("Days (MO, TU, WE, TH, FR, SA, SU)",delivery["weekdays"])
    else:
        delivery["time"] = None
    delivery["print_requested"] = yes("Record an interest in physical printing",delivery["print_requested"])
    print("These preferences do not create a schedule or send a print job.")
    profile["status"] = "draft"
    save_profile(base,name,profile,replace=True)
    print("\nReview your profile:\n" + json.dumps(profile,ensure_ascii=False,indent=2))
    candidate = copy.deepcopy(profile)
    candidate["status"] = "ready"
    validate_profile(candidate,ready=True)
    if yes("Confirm these choices and finish setup",False):
        profile = candidate
    saved = save_profile(base,name,profile,replace=True)
    print(f"Saved {profile['status']} profile: {saved}")


def next_destination(base, name, issue):
    parent = profile_path(base,name).parent / ("demos" if issue["demo"] else "issues")
    target = parent / issue["date"]
    revision = 1
    while target.exists():
        revision += 1
        target = parent / f"{issue['date']}-r{revision}"
    return target


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir",help="Private data directory, outside the public package")
    parser.add_argument("--profile",default="main",help="Private profile name")
    sub = parser.add_subparsers(dest="command",required=True)
    p = sub.add_parser("setup",help="Guided terminal setup; resumes drafts")
    p.add_argument("--replace",action="store_true")
    p = sub.add_parser("import-profile",help="Save a profile prepared during conversational setup")
    p.add_argument("path",type=Path)
    p.add_argument("--confirm",action="store_true",help="Confirm and mark the reviewed choices ready")
    p.add_argument("--replace",action="store_true")
    sub.add_parser("show",help="Show the private profile")
    p = sub.add_parser("validate",help="Validate profile, and optionally an issue")
    p.add_argument("--issue",type=Path)
    p = sub.add_parser("brief",help="Create an empty editorial JSON for the host agent to research")
    p.add_argument("--date",help="YYYY-MM-DD; defaults to today in the profile timezone")
    p = sub.add_parser("render",help="Render reviewed editorial JSON; no network access")
    p.add_argument("issue",type=Path)
    p = sub.add_parser("demo",help="Render the entirely fictional bundled example without personal setup")
    p.add_argument("--qr",action="store_true")
    args = parser.parse_args(argv)
    try:
        base = data_home(args.data_dir)
        path = profile_path(base,args.profile)
        if args.command == "setup":
            wizard(base,args.profile,args.replace)
        elif args.command == "import-profile":
            profile = read_json(args.path)
            profile["status"] = "ready" if args.confirm else "draft"
            print(save_profile(base,args.profile,profile,replace=args.replace))
        elif args.command == "demo":
            from render import render
            profile = read_json(SKILL / "assets" / "example-profile.json")
            profile["publication"]["links"]["qr"] = args.qr
            issue = read_json(SKILL / "assets" / "demo-issue.json")
            # A named demo never reads or overwrites a real reader profile.
            for output in render(issue,profile,next_destination(base,"sample",issue)):
                print(output)
        else:
            if not path.exists():
                raise ValueError("No profile found. Run setup first, or use demo for a fictional preview.")
            profile = read_json(path)
            validate_profile(profile)
            if args.command == "show":
                print(json.dumps(profile,ensure_ascii=False,indent=2))
            elif args.command == "validate":
                if args.issue:
                    validate_issue(read_json(args.issue),profile)
                print("Valid")
            elif args.command == "brief":
                validate_profile(profile,ready=True)
                day = args.date or datetime.now(timezone(profile["publication"]["timezone"])).date().isoformat()
                existing = list((path.parent / "issues").glob("*/issue.json"))
                previous = [read_json(p) for p in existing]
                same_day = [i for i in previous if i["date"] == day]
                edition_number = same_day[0]["number"] if same_day else max((i["number"] for i in previous),default=0)+1
                issue = {"version":1,"date":day,"number":edition_number,"demo":False,"sections":[{"id":s["id"],"status":"pending","note":"Not researched yet.","items":[]} for s in profile["sections"] if s["enabled"]]}
                validate_schema(issue,"issue")
                draft = path.parent / "drafts" / f"{day}.json"
                if draft.exists():
                    raise ValueError("A draft for this date already exists; resume it instead of overwriting it")
                private_write(draft,json.dumps(issue,ensure_ascii=False,indent=2)+"\n")
                print(draft)
            elif args.command == "render":
                from render import render
                issue = read_json(args.issue)
                for output in render(issue,profile,next_destination(base,args.profile,issue)):
                    print(output)
    except (ValueError, OSError, json.JSONDecodeError) as exc:
        parser.exit(2,f"Error: {exc}\n")


if __name__ == "__main__":
    main()
