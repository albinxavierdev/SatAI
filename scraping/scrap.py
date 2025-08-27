import os
import json
import re
from urllib.parse import urljoin, urlparse

"""
Usage:
	- Ensure dependencies: pip install botasaurus botasaurus-requests beautifulsoup4
	- Run:
		python scraping/scrap.py
Output:
	- Per-category folders: scraping/output/<CATEGORY>/<SATELLITE_NAME>/
		- info.json (satellite data)
		- images/* (downloaded images)
	- Per-category index files: scraping/output/<CATEGORY>_index.json
Categories covered:
	- communication (https://www.isro.gov.in/CommunicatioSatellitenNew.html#)
	- earth_observation (https://www.isro.gov.in/EarthObservationSatellites.html)
	- scientific (https://www.isro.gov.in/spacesciexp.html)
	- navigation (https://www.isro.gov.in/satellitenavign.html)
	- experimental (https://www.isro.gov.in/satellitenavign.html)  # same list page contains experimental/older links
	- small (https://www.isro.gov.in/smallsat.html)
	- student (https://www.isro.gov.in/Student_Satellite.html)
"""

# Botasaurus imports
try:
	from botasaurus import browser, Driver
	from botasaurus_requests import requests
except Exception:
	import requests as requests  # type: ignore
	browser = None  # type: ignore
	Driver = None  # type: ignore

SITE_ROOT = "https://www.isro.gov.in/"

CATEGORIES = {
	"communication": "https://www.isro.gov.in/CommunicatioSatellitenNew.html#",
	"earth_observation": "https://www.isro.gov.in/EarthObservationSatellites.html",
	"scientific": "https://www.isro.gov.in/spacesciexp.html",
	"navigation": "https://www.isro.gov.in/satellitenavign.html",
	"experimental": "https://www.isro.gov.in/satellitenavign.html",
	"small": "https://www.isro.gov.in/smallsat.html",
	"student": "https://www.isro.gov.in/Student_Satellite.html",
}

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
os.makedirs(OUTPUT_DIR, exist_ok=True)


def sanitize_filename(name: str) -> str:
	name = re.sub(r"[^A-Za-z0-9_.\- ]+", "_", name).strip()
	return re.sub(r"\s+", "_", name)[:180]


def absolute_url(href: str) -> str:
	if not href:
		return href
	return urljoin(SITE_ROOT, href)


def download_image_to_folder(img_url: str, folder: str, fname_hint: str) -> str | None:
	try:
		if not img_url:
			return None
		resp = requests.get(img_url, timeout=30)
		resp.raise_for_status()
		ext = os.path.splitext(urlparse(img_url).path)[1] or ".jpg"
		filename = sanitize_filename(fname_hint) + ext
		os.makedirs(folder, exist_ok=True)
		path = os.path.join(folder, filename)
		with open(path, "wb") as f:
			f.write(resp.content)
		return path
	except Exception:
		return None


try:
	from bs4 import BeautifulSoup  # type: ignore
except Exception:
	BeautifulSoup = None  # type: ignore


def parse_list_page(html: str) -> list[dict]:
	"""Extract satellite links from any ISRO category page with a list table.
	Works by scanning for table anchors; ignores anchors with href="#".
	"""
	soup = BeautifulSoup(html, "html.parser")
	results: list[dict] = []
	for a in soup.select('table a[href]'):
		name = a.get_text(strip=True)
		href = a.get("href")
		if not name:
			continue
		if not href or href.strip().startswith("#"):
			continue
		url = absolute_url(href)
		if not url.startswith("https://www.isro.gov.in/"):
			continue
		results.append({"name": name, "url": url})
	# Fallback: sometimes pages also list links in cards/paragraphs
	if not results:
		for a in soup.select('a[href*=".html"]'):
			name = a.get_text(strip=True)
			href = a.get("href")
			if name and href and not href.startswith("#"):
				url = absolute_url(href)
				if url.startswith("https://www.isro.gov.in/"):
					results.append({"name": name, "url": url})
	# De-duplicate by URL preserving first occurrence
	seen = set()
	unique = []
	for item in results:
		if item["url"] in seen:
			continue
		seen.add(item["url"])
		unique.append(item)
	return unique


def extract_text(el) -> str:
	return re.sub(r"\s+", " ", el.get_text(" ", strip=True)) if el else ""


def parse_detail_page(html: str, page_url: str) -> dict:
	soup = BeautifulSoup(html, "html.parser")
	title = extract_text(soup.select_one("h1, h2.page-title, .node-title, .title")) or extract_text(soup.select_one("title"))
	intro = extract_text(next((p for p in soup.select("p") if len(p.get_text(strip=True)) > 40), None))
	features: dict[str, str] = {}
	for table in soup.select("table"):
		for row in table.select("tr"):
			cells = [extract_text(td) for td in row.select("th,td")]
			if len(cells) >= 2 and cells[0] and cells[1]:
				features[cells[0]] = cells[1]
	for block in soup.select(".field, .box, .well, .card, .node, .content"):
		text = extract_text(block)
		for m in re.finditer(r"([A-Za-z][A-Za-z /()\-]+)\s*[:\-]\s*([^\n\r]+)", text):
			key = m.group(1).strip()
			val = m.group(2).strip()
			if key and val and key.lower() not in (k.lower() for k in features.keys()):
				features[key] = val
	image_urls = []
	for img in soup.select("img"):
		src = img.get("src") or img.get("data-src")
		src = absolute_url(src) if src else None
		if src and "/themes/" not in src and (src.endswith(".jpg") or src.endswith(".jpeg") or src.endswith(".png") or src.endswith(".webp")):
			image_urls.append(src)
	seen = set()
	ordered_images = []
	for u in image_urls:
		if u in seen:
			continue
		seen.add(u)
		ordered_images.append(u)
	return {
		"title": title,
		"url": page_url,
		"intro": intro,
		"features": features,
		"image_urls": ordered_images,
	}


def fetch_html(url: str) -> str:
	resp = requests.get(url, timeout=60)
	resp.raise_for_status()
	return resp.text


def scrape_category(category: str, base_url: str) -> list[dict]:
	index_html = fetch_html(base_url)
	sat_links = parse_list_page(index_html)
	category_dir = os.path.join(OUTPUT_DIR, category)
	os.makedirs(category_dir, exist_ok=True)
	records: list[dict] = []
	for link in sat_links:
		try:
			detail_html = fetch_html(link["url"])
			record = parse_detail_page(detail_html, link["url"])  # title may differ
			sat_name = record.get("title") or link["name"]
			safe_name = sanitize_filename(sat_name)
			folder = os.path.join(category_dir, safe_name)
			images_folder = os.path.join(folder, "images")
			# Download images into satellite folder
			local_images: list[str] = []
			for idx, u in enumerate(record.get("image_urls", [])):
				local = download_image_to_folder(u, images_folder, f"{safe_name}_{idx+1}")
				if local:
					local_images.append(os.path.basename(local))
			record["local_images"] = [os.path.join("images", p) for p in local_images]
			record["name"] = sat_name
			# Save per-satellite JSON
			os.makedirs(folder, exist_ok=True)
			with open(os.path.join(folder, "info.json"), "w", encoding="utf-8") as f:
				json.dump(record, f, ensure_ascii=False, indent=2)
			records.append({
				"name": sat_name,
				"folder": os.path.relpath(folder, OUTPUT_DIR),
				"url": record.get("url"),
				"cover_image": record.get("local_images", [None])[0],
			})
		except Exception:
			continue
	# Write category index
	with open(os.path.join(OUTPUT_DIR, f"{category}_index.json"), "w", encoding="utf-8") as f:
		json.dump(records, f, ensure_ascii=False, indent=2)
	return records


def run_all_categories() -> dict[str, int]:
	counts: dict[str, int] = {}
	for cat, url in CATEGORIES.items():
		records = scrape_category(cat, url)
		counts[cat] = len(records)
	return counts


if __name__ == "__main__":
	result_counts = run_all_categories()
	print("Scraped categories:")
	for cat, cnt in result_counts.items():
		print(f" - {cat}: {cnt} satellites")
