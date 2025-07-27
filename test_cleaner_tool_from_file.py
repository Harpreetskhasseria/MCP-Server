from pathlib import Path
from cleaner_tool import CleanerTool

if __name__ == "__main__":
    # Ask user for input path
    html_path_input = input("🔍 Enter the path to the HTML file to clean: ").strip().strip('"')
    html_path = Path(html_path_input)

    # Validate file
    if not html_path.exists():
        print(f"❌ File does not exist: {html_path}")
        exit(1)

    # Load content
    scraped_html = html_path.read_text(encoding="utf-8")
    url = f"file://{html_path.resolve()}"

    # Run tool
    tool = CleanerTool()
    result = tool._run(url=url, scraped_html=scraped_html)

    # Show result
    print("\n✅ Cleaned HTML saved to:", result["cleaned_file"])
