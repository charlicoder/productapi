#!/usr/bin/env python
"""
Enrich a products JSON file with polished English + Arabic copy, using Claude.

For every product it adds:
    title_en, subtitle_en   - short, professional, engaging, SEO-friendly copy generated from
                              the original title / full_title / subtitle (step 1)
    title_ar, subtitle_ar   - Arabic translation of the NEW English copy (step 2)

Usage (from productapi/):
    export ANTHROPIC_API_KEY=sk-ant-...          # or put it in .env
    python scripts/enrich_products.py sample/001_products.json
    python scripts/enrich_products.py in.json --out out.json     # don't touch the input
    python scripts/enrich_products.py in.json --limit 5 --dry-run

Safe to re-run: products that already have all four fields are skipped (use --force to redo).
The file is saved after every batch, so an interrupted run loses nothing. The input is backed up
to <file>.bak the first time it is modified in place. Then import with:
    python manage.py import_products <file>        (or Admin -> Products -> Import JSON)
"""
import argparse
import json
import os
import re
import shutil
import sys
from pathlib import Path

DEFAULT_MODEL = "claude-haiku-5-5"
FIELDS = ("title_en", "subtitle_en", "title_ar", "subtitle_ar")
TITLE_MAX = 80
SUBTITLE_MAX = 180

EN_SYSTEM = f"""You are a senior e-commerce copywriter and SEO specialist writing for a modern online store.
For each product, write fresh English copy from the raw marketplace data you are given.

title_en:
- Professional, natural, easy to read; at most 70 characters (hard limit {TITLE_MAX}).
- Start with the brand, then the product type, then 1-3 of the most valuable attributes (material, fit, style, use).
- Put the most-searched keyword (the product type) early. Title Case. No ALL CAPS, emoji, symbols, or keyword stuffing.
- Do not repeat words; drop marketplace noise (years, "Fall Outfits", "Trendy", sizes, color lists, "for Women" only if useful).

subtitle_en:
- One engaging sentence, {SUBTITLE_MAX} characters maximum, ideally 90-140. Benefit-led, mentions 2-3 real features, friendly and confident.

Rules: use ONLY facts present in the input - never invent materials, certifications, discounts, or claims.
No prices. No quotation marks around the text. Plain text only.

Return ONLY a JSON array, one object per input product, in the same order:
[{{"asin": "...", "title_en": "...", "subtitle_en": "..."}}]"""

AR_SYSTEM = """You are a professional English-to-Arabic e-commerce translator and copywriter.
Translate each product's title_en and subtitle_en into natural, fluent Modern Standard Arabic suitable for an online store.
- Do a marketing-quality adaptation, not a word-for-word translation; keep it concise and engaging, similar length to the English.
- Keep brand names in Latin letters exactly as written. Keep model names/numbers as-is.
- Never mix Arabic and Latin letters inside one word (e.g. not "بلazer"): translate product words fully into Arabic (بليزر), leaving only brand/model names in Latin.
- Use Arabic punctuation naturally (the Arabic comma "،"). No emoji. No diacritics (tashkeel). Plain text only.

Return ONLY a JSON array, one object per input product, in the same order:
[{"asin": "...", "title_ar": "...", "subtitle_ar": "..."}]"""


def load_env():
    try:
        from dotenv import load_dotenv

        load_dotenv(Path(__file__).resolve().parent.parent / ".env")
    except ImportError:
        pass


def extract_json_array(text: str):
    text = text.strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    start, end = text.find("["), text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("no JSON array in model output")
    return json.loads(text[start : end + 1])


def ask(client, model, system, items, attempts=3):
    """Send items as JSON, return the parsed JSON array (retries on malformed output)."""
    last = None
    for _ in range(attempts):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=8000,
                system=system,
                messages=[{"role": "user", "content": json.dumps(items, ensure_ascii=False)}],
            )
            text = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")
            out = extract_json_array(text)
            if isinstance(out, list):
                return out
        except Exception as e:  # malformed JSON, API hiccup... the SDK already retries transient errors
            last = e
    raise RuntimeError(f"model call failed after {attempts} attempts: {last}")


def clean(s):
    return re.sub(r"\s+", " ", (s or "").strip().strip('"“”'))


def source_view(p):
    return {
        "asin": p["asin"],
        "brand": p.get("brand"),
        "title": p.get("title"),
        "full_title": p.get("full_title"),
        "subtitle": p.get("subtitle"),
        "tags": p.get("tags"),
        "category": p.get("category_path"),
    }


def step_english(client, model, batch):
    res = {r["asin"]: r for r in ask(client, model, EN_SYSTEM, [source_view(p) for p in batch]) if "asin" in r}
    ok = {}
    for p in batch:
        r = res.get(p["asin"])
        t, s = clean(r and r.get("title_en")), clean(r and r.get("subtitle_en"))
        if t and s and len(t) <= TITLE_MAX and len(s) <= SUBTITLE_MAX:
            ok[p["asin"]] = (t, s)
    return ok


def step_arabic(client, model, english):
    payload = [{"asin": a, "title_en": t, "subtitle_en": s} for a, (t, s) in english.items()]
    res = {r["asin"]: r for r in ask(client, model, AR_SYSTEM, payload) if "asin" in r}
    ok = {}
    for a in english:
        r = res.get(a)
        t, s = clean(r and r.get("title_ar")), clean(r and r.get("subtitle_ar"))
        if t and s:
            ok[a] = (t, s)
    return ok


def save(path: Path, data):
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    tmp.replace(path)


def main(argv=None, client=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("file", type=Path)
    ap.add_argument("--out", type=Path, help="write here instead of updating the input file in place")
    ap.add_argument("--model", default=os.environ.get("ENRICH_MODEL", DEFAULT_MODEL))
    ap.add_argument("--batch", type=int, default=8, help="products per model call (default 8)")
    ap.add_argument("--limit", type=int, help="only process the first N products that need work")
    ap.add_argument("--force", action="store_true", help="regenerate even if the 4 fields already exist")
    ap.add_argument("--dry-run", action="store_true", help="print what would be sent, change nothing")
    args = ap.parse_args(argv)

    data = json.loads(args.file.read_text(encoding="utf-8"))
    items = data if isinstance(data, list) else [data]

    todo = [
        p for p in items
        if isinstance(p, dict) and p.get("asin") and not p.get("error") and (p.get("title") or p.get("full_title"))
        and (args.force or not all(p.get(f) for f in FIELDS))
    ]
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(items)} products in file, {len(todo)} to process (model: {args.model})")
    if args.dry_run or not todo:
        for p in todo[:3]:
            print(json.dumps(source_view(p), ensure_ascii=False)[:300])
        return 0

    if client is None:
        load_env()
        if not os.environ.get("ANTHROPIC_API_KEY"):
            sys.exit("ANTHROPIC_API_KEY is not set (export it or add it to productapi/.env)")
        import anthropic

        client = anthropic.Anthropic(max_retries=4)

    dest = args.out or args.file
    if dest == args.file:
        bak = args.file.with_suffix(args.file.suffix + ".bak")
        if not bak.exists():
            shutil.copy2(args.file, bak)
    if args.out and not args.out.exists():
        save(args.out, data)  # start from the full file so unprocessed items are kept

    done = failed = 0
    for i in range(0, len(todo), args.batch):
        batch = todo[i : i + args.batch]
        try:
            english = step_english(client, args.model, batch)
            arabic = step_arabic(client, args.model, english) if english else {}
        except Exception as e:
            print(f"  ✖ batch {i // args.batch + 1}: {e}")
            failed += len(batch)
            continue
        for p in batch:
            a = p["asin"]
            if a in english and a in arabic:
                p["title_en"], p["subtitle_en"] = english[a]
                p["title_ar"], p["subtitle_ar"] = arabic[a]
                done += 1
                print(f"  ✔ {a}  {p['title_en']}  |  {p['title_ar']}")
            else:
                failed += 1
                print(f"  ✖ {a}: invalid or missing output (re-run to retry)")
        save(dest, data)  # checkpoint

    print(f"Done: {done} enriched, {failed} failed -> {dest}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
