#!/usr/bin/env python3
import os
import sys
import json
import time
import re
import urllib.request
import urllib.error
from urllib.parse import urlencode
from concurrent.futures import ThreadPoolExecutor, as_completed

import click
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, MofNCompleteColumn, TimeElapsedColumn

# Platform Constants
API_KEY = "HVOd9et3td3SBu7XX2sjz3ZxdHGh7LlI57KMJSiy"
BASE_URL = "https://aikosha-api.indiaai.gov.in/dataset/idp/api/v1/"
DETAIL_URL = BASE_URL + "datasets/detail/"
VERSIONS_URL = BASE_URL + "dataset/{dataset_id}/versions?page=1&size=10"

# Target Keywords for SyntheticTutor
DEFAULT_KEYWORDS = [
    # Education / School / Curriculum
    "education", "school", "ncert", "cbse", "textbook", "student", "teacher",
    "learn", "socratic", "curriculum", "pedagogy", "syllabus", "classroom",
    "academic", "subject", "literacy", "enrollment", "udise", "didactic",
    # Indic Languages & Multilingual
    "indic", "hinglish", "translation", "multilingual", "code-switch", "bilingual",
    "hindi", "tamil", "telugu", "kannada", "malayalam", "marathi", "bengali",
    "gujarati", "odia", "punjabi", "assamese", "sanskrit", "urdu", "manipuri",
    "konkani", "nepali", "santhali", "maithili", "dogri", "bodo", "kashmiri",
    # Socratic & Dialogue / Interaction
    "dialogue", "conversation", "interaction", "tutor", "tutorial", "instructional",
    "misconception", "qa", "question-answering", "question answering", "chat",
    # Core Subjects
    "science", "math", "history", "geography", "civics", "physics", "chemistry", "biology"
]

console = Console()

def fetch_json(url: str, headers: dict = None) -> dict:
    """Helper to fetch JSON data from a URL with retry logic."""
    if headers is None:
        headers = {}
    
    req = urllib.request.Request(url)
    req.add_header("x-api-key", API_KEY)
    req.add_header("Accept", "application/json, text/plain, */*")
    req.add_header("User-Agent", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36")
    for k, v in headers.items():
        req.add_header(k, v)
        
    retries = 3
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                content = response.read().decode("utf-8")
                return json.loads(content)
        except urllib.error.HTTPError as e:
            if e.code == 429: # Rate limit
                time.sleep(2 ** attempt)
                continue
            raise e
        except Exception as e:
            if attempt == retries - 1:
                raise e
            time.sleep(1)
    raise Exception(f"Failed to fetch {url} after {retries} attempts.")

def fetch_all_datasets_metadata() -> list:
    """Fetches all datasets metadata by paginating through the AIKosh API."""
    all_cards = []
    page = 1
    size = 1000  # Optimized size to minimize API calls
    
    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        MofNCompleteColumn(),
        TimeElapsedColumn(),
        console=console
    ) as progress:
        task = progress.add_task("[cyan]Fetching datasets from AIKosh...", total=None)
        
        while True:
            url = f"{BASE_URL}datasets/all?page={page}&size={size}"
            try:
                response_data = fetch_json(url)
                cards_container = response_data.get("data", {}).get("cards", {})
                cards = cards_container.get("data", [])
                total = cards_container.get("total", 0)
                
                progress.update(task, total=total)
                
                if not cards:
                    break
                    
                all_cards.extend(cards)
                progress.advance(task, advance=len(cards))
                
                if len(all_cards) >= total or len(cards) < size:
                    break
                    
                page += 1
            except Exception as e:
                console.print(f"[red]Error fetching page {page}: {e}[/red]")
                break
                
    return all_cards

def fetch_dataset_details(slug_or_id: str) -> dict:
    """Fetches detailed metadata for a specific dataset using its slug or ID."""
    try:
        url = DETAIL_URL + slug_or_id
        response_data = fetch_json(url)
        return response_data.get("data") or {}
    except Exception as e:
        return {"error": str(e)}

def fetch_dataset_versions_and_files(dataset_id: str) -> list:
    """Fetches the versions and files list for a dataset."""
    try:
        url = VERSIONS_URL.format(dataset_id=dataset_id)
        response_data = fetch_json(url)
        data_field = response_data.get("data")
        if isinstance(data_field, dict):
            return data_field.get("versions", {}).get("data", [])
        elif isinstance(data_field, list):
            return data_field
        return []
    except Exception as e:
        return []

def fetch_version_files(dataset_id: str, version_id: str, parent_id: str = None) -> list:
    """Fetches files inside a specific directory/version of a dataset."""
    try:
        url = f"{BASE_URL}dataset/{dataset_id}/version-files/{version_id}?page=1&size=50"
        if parent_id:
            url += f"&parentId={parent_id}"
        response_data = fetch_json(url)
        return response_data.get("data", {}).get("versions", {}).get("data", [])
    except Exception as e:
        return []

def filter_relevant_datasets(datasets: list, keywords: list) -> list:
    """Filters datasets that match the educational and Socratic keywords using word boundaries."""
    relevant = []
    for d in datasets:
        name = d.get("name", "")
        desc = d.get("shortDescription", "") or ""
        tags = d.get("tags", [])
        
        # Combine all text fields for the dataset
        text_to_search = (name + " " + desc + " " + " ".join(tags)).lower()
        
        # Match keywords using word boundary regex to avoid false positives (e.g. 'index' matching 'indic')
        matched_kws = []
        for kw in keywords:
            pattern = r'\b' + re.escape(kw) + r'\b'
            if re.search(pattern, text_to_search):
                matched_kws.append(kw)
                
        if matched_kws:
            d_copy = dict(d)
            d_copy["matched_keywords"] = matched_kws
            relevant.append(d_copy)
            
    return relevant

@click.group()
def cli():
    """Web crawler and scraper utility for AIKosh IndiaAI datasets."""
    pass

@cli.command()
@click.option("--output", "-o", default="output/aikosh_relevant_datasets.json", help="Path to save the output JSON file.")
@click.option("--keywords-file", "-k", default=None, help="Optional text file containing custom keywords (one per line).")
@click.option("--details/--no-details", default=False, help="Whether to fetch deep metadata and files list for matched datasets (warning: slow).")
@click.option("--threads", "-t", default=10, help="Number of concurrent threads for fetching details.")
def crawl(output, keywords_file, details, threads):
    """Crawl and filter relevant datasets from AIKosh."""
    # 1. Load keywords
    kws = DEFAULT_KEYWORDS
    if keywords_file:
        if os.path.exists(keywords_file):
            with open(keywords_file, "r") as f:
                kws = [line.strip().lower() for line in f if line.strip()]
            console.print(f"[green]Loaded {len(kws)} custom keywords from {keywords_file}[/green]")
        else:
            console.print(f"[yellow]Keywords file {keywords_file} not found. Using default keywords.[/yellow]")
            
    console.print(f"[bold green]Starting AIKosh Dataset Crawler[/bold green]")
    console.print(f"Keywords check includes terms like: [italic]{', '.join(kws[:10])}...[/italic]")

    # 2. Fetch all datasets top-level cards
    all_datasets = fetch_all_datasets_metadata()
    console.print(f"[green]Successfully fetched {len(all_datasets)} total datasets metadata from AIKosh.[/green]")

    # 3. Filter relevant datasets locally
    console.print("[cyan]Filtering datasets for project relevance (word-boundary aware)...[/cyan]")
    relevant_datasets = filter_relevant_datasets(all_datasets, kws)
    console.print(f"[bold green]Found {len(relevant_datasets)} relevant educational/Socratic/Indic datasets![/bold green]")

    # 4. Fetch details & files list if requested
    if details and relevant_datasets:
        console.print(f"[cyan]Fetching deep details and files list for {len(relevant_datasets)} datasets using {threads} threads...[/cyan]")
        
        detailed_results = []
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            console=console
        ) as progress:
            task = progress.add_task("Retrieving dataset details...", total=len(relevant_datasets))
            
            with ThreadPoolExecutor(max_workers=threads) as executor:
                # Map futures to dataset items
                future_to_ds = {
                    executor.submit(fetch_dataset_details, ds["slug"]): ds 
                    for ds in relevant_datasets
                }
                
                for future in as_completed(future_to_ds):
                    ds = future_to_ds[future]
                    progress.advance(task)
                    try:
                        detail_data = future.result()
                        if "error" in detail_data:
                            ds["details_error"] = detail_data["error"]
                            detailed_results.append(ds)
                            continue
                            
                        merged = dict(ds)
                        merged["fullDescription"] = detail_data.get("fullDescription")
                        merged["datasetMetadata"] = detail_data.get("datasetMetadata") or {}
                        
                        versions = fetch_dataset_versions_and_files(ds["id"])
                        merged["versions"] = versions
                        
                        files_list = []
                        for v in versions:
                            if v.get("nicFiles"):
                                for nf in v["nicFiles"]:
                                    files_list.append({
                                        "name": nf.get("name"),
                                        "size_bytes": nf.get("size"),
                                        "version": v.get("versionNumber"),
                                        "type": "NIC"
                                    })
                        merged["extracted_files"] = files_list
                        detailed_results.append(merged)
                    except Exception as e:
                        ds["details_error"] = str(e)
                        detailed_results.append(ds)
                        
        relevant_datasets = detailed_results

    # 5. Save results to output
    os.makedirs(os.path.dirname(output), exist_ok=True)
    with open(output, "w", encoding="utf-8") as f:
        json.dump(relevant_datasets, f, indent=2)
    console.print(f"[bold green]Saved {len(relevant_datasets)} datasets to {output}[/bold green]")

    # 6. Display a summary table of the top 15 most viewed/downloaded relevant datasets
    sorted_ds = sorted(
        relevant_datasets,
        key=lambda x: x.get("stats", {}).get("views", 0),
        reverse=True
    )
    
    table = Table(title="Top Relevant AIKosh Datasets for SyntheticTutor", show_header=True, header_style="bold magenta")
    table.add_column("No.", style="dim")
    table.add_column("Dataset Name", width=40)
    table.add_column("Matched Keywords", style="cyan")
    table.add_column("Downloads", justify="right")
    table.add_column("Views", justify="right")
    
    for idx, ds in enumerate(sorted_ds[:15]):
        kws_str = ", ".join(ds.get("matched_keywords", [])[:3])
        downloads = ds.get("stats", {}).get("downloads", 0)
        views = ds.get("stats", {}).get("views", 0)
        table.add_row(
            str(idx+1),
            ds.get("name"),
            kws_str,
            str(downloads),
            str(views)
        )
        
    console.print("\n")
    console.print(table)

@cli.command()
@click.argument("slug_or_id")
def info(slug_or_id):
    """Retrieve detailed metadata and files list for a dataset."""
    console.print(f"[cyan]Retrieving details for: {slug_or_id}...[/cyan]")
    details = fetch_dataset_details(slug_or_id)
    if "error" in details:
        console.print(f"[red]Error fetching details: {details['error']}[/red]")
        sys.exit(1)
        
    name = details.get("name")
    id_val = details.get("id")
    slug = details.get("slug")
    desc = details.get("shortDescription")
    full_desc = details.get("fullDescription") or "No detailed description provided."
    meta = details.get("datasetMetadata") or {}
    tags = details.get("tags") or []
    stats = details.get("stats") or {}
    
    console.print(f"\n[bold magenta]{name}[/bold magenta]")
    console.print(f"ID: [green]{id_val}[/green] | Slug: [green]{slug}[/green]")
    console.print(f"Sector: [cyan]{meta.get('sector', 'N/A')}[/cyan] | License: [yellow]{meta.get('license', 'N/A')}[/yellow]")
    console.print(f"Format: [yellow]{meta.get('datasetType', 'N/A')} ({meta.get('dataType', 'N/A')})[/yellow]")
    console.print(f"Stats: Views={stats.get('views', 0)}, Downloads={stats.get('downloads', 0)}")
    console.print(f"Tags: {', '.join(tags)}")
    console.print(f"\n[bold]Description:[/bold]\n{desc}\n")
    
    # Versions & files
    console.print("[bold cyan]Versions & File Structure:[/bold cyan]")
    versions = fetch_dataset_versions_and_files(id_val)
    if not versions:
        console.print("  No version information available.")
        return
        
    for v in versions:
        v_num = v.get("versionNumber")
        v_id = v.get("id")
        created = v.get("createdDate", "N/A")
        console.print(f"\n[bold green]Version {v_num} (ID: {v_id}, Created: {created})[/bold green]")
        
        # Check NIC/legacy files
        if v.get("nicFiles"):
            console.print("  [bold]Files:[/bold]")
            for nf in v["nicFiles"]:
                size_kb = int(nf.get("size", 0)) / 1024
                console.print(f"  - {nf.get('name')} ({size_kb:.2f} KB)")
        
        # Check modern directory-based versions
        else:
            files_tree = Tree(f"[DIR] Version Root (ID: {v_id})")
            
            def build_tree(parent_tree, parent_id):
                sub_items = fetch_version_files(id_val, v_id, parent_id)
                for item in sub_items:
                    name = item.get("fileName")
                    ftype = item.get("type")
                    size = int(item.get("size") or 0)
                    fid = item.get("id")
                    
                    if ftype == "Directory":
                        sub_tree = parent_tree.add(f"[DIR] {name}")
                        build_tree(sub_tree, fid)
                    else:
                        size_kb = size / 1024
                        parent_tree.add(f"[FILE] {name} ({size_kb:.2f} KB)")
                        
            build_tree(files_tree, None)
            console.print(files_tree)

@cli.command()
@click.argument("slug_or_id")
@click.argument("file_path")
def download(slug_or_id, file_path):
    """Explain how to download or get access link to a dataset file."""
    details = fetch_dataset_details(slug_or_id)
    if "error" in details:
        console.print(f"[red]Error fetching details: {details['error']}[/red]")
        sys.exit(1)
        
    name = details.get("name")
    id_val = details.get("id")
    
    console.print(f"\n[bold green]Dataset: {name}[/bold green]")
    console.print(f"ID: {id_val}")
    console.print(f"File Path: {file_path}")
    console.print("\n[yellow]Direct Download/Preview Link (Web Access Key):[/yellow]")
    
    # We get versions to find the version_id
    versions = fetch_dataset_versions_and_files(id_val)
    if not versions:
        console.print("[red]Could not retrieve version details for this dataset.[/red]")
        return
        
    v_id = versions[0].get("id")
    import urllib.parse
    encoded_path = urllib.parse.quote(file_path)
    preview_url = (
        f"https://aikosha-api.indiaai.gov.in/du/idp/api/v1/dataset-download/"
        f"{id_val}/version/{v_id}/get-pre-login-preview-url?filePath={encoded_path}"
    )
    console.print(f"[cyan]{preview_url}[/cyan]")
    
    console.print("\n[bold cyan]How to download this file:[/bold cyan]")
    console.print("1. Set up the `aikosh` Python SDK in your workspace environment:")
    console.print("   [green]pip install aikosh[/green]")
    console.print("2. Generate your personal API Key from the AIKosh portal:")
    console.print("   Navigate to [bold]Profile > Account Settings > Generate API Key[/bold] on [cyan]https://aikosh.indiaai.gov.in[/cyan]")
    console.print("3. Run python code to download the file securely:")
    console.print(f"   [yellow]import aikosh[/yellow]")
    console.print(f"   [yellow]aikosh.set_api_key('YOUR_API_KEY')[/yellow]")
    console.print(f"   [yellow]aikosh.download({{[/yellow]")
    console.print(f"   [yellow]    'identifier': '{id_val}',[/yellow]")
    console.print(f"   [yellow]    'file_path': '{file_path}'[/yellow]")
    console.print(f"   [yellow]}})[/yellow]")

if __name__ == "__main__":
    cli()
