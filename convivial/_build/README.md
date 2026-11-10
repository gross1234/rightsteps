# Convivial Concierge: SEO / AEO site generator

`build.py` turns the Homebase *Family Offices Investing in CRE* list into a static site in `convivial/`:

| Output | Indexed? | Purpose |
|---|---|---|
| `index.html`, `family-offices/` | yes | Pillar pages for "concierge for family office real estate" |
| `solutions/<type>/` (8) | yes | One page per property type: multifamily, mixed-use, hotels, office, senior, student, life science / medical, retail |
| `markets/<metro>/` (25) | yes | One page per metro where 5 or more listed offices are based or invest |
| `for/<family-office>/` (1 per office) | **no** (`noindex`, blocked in robots.txt) | Private proposal page linked from outreach emails |
| `for/<office>/<property>/` | **no** | One page per building, from `properties.csv` |
| `sitemap.xml`, `robots.txt`, `llms.txt` | | Crawl and answer-engine files |

Every indexable page opens with a quoted-style "short answer", uses question-shaped FAQ headings, and carries
Organization, Service, FAQPage and BreadcrumbList JSON-LD so search engines and AI answer engines can quote it.

## Run

```bash
python3 convivial/_build/build.py --csv path/to/family_offices.csv --outreach ~/outreach.csv
```

* Edit `config.json` first (`base_url`, `contact_email`, optional `booking_url`).
* Edit the copy in `SEGMENTS` in `build.py` so it only promises services you deliver.
* Add buildings to `properties.csv` (`family_office` must match the name in the list) to get a page per property.
* Keep the source CSV and the outreach CSV **out of this repo**: they contain contact details and the repo is public.
