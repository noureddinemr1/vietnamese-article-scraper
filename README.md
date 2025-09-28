# Vietnamese Text Dataset Scraper for VnExpress.net

This project scrapes Vietnamese news articles from vnexpress.net to create a high-quality text dataset for AI language model training.

## Features

- ✅ **Automated article discovery**: Crawls category pages to find individual article URLs
- ✅ **Smart content extraction**: Uses multiple selectors to extract clean article content
- ✅ **Vietnamese language validation**: Ensures content is primarily Vietnamese (>85% purity)
- ✅ **Quality filtering**: Only includes articles with 200+ words
- ✅ **Clean text processing**: Removes HTML, ads, navigation, and unnecessary elements
- ✅ **Structured output**: Generates JSONL format ready for AI training
- ✅ **Respectful scraping**: Includes delays to avoid overwhelming the server

## Requirements

- Python 3.8+
- Virtual environment (recommended)

## Installation

1. Clone or download this project
2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage
```bash
python main.py
```

This will:
1. Read category URLs from `links.txt`
2. Find article URLs from each category page
3. Scrape article content and metadata
4. Filter for Vietnamese content with 200+ words
5. Save results to `vietnamese_dataset.jsonl`

### Configuration

You can modify the scraper behavior in the `main()` function:

```python
scraper.scrape_urls_from_file(
    links_file="links.txt", 
    output_file="vietnamese_dataset.jsonl",
    max_categories=None,  # Limit number of categories (None = all)
    articles_per_category=20  # Articles per category
)
```

### Customizing for Other Sites

To adapt this scraper for other Vietnamese news sites:

1. Update `find_article_urls()` method with new URL patterns
2. Modify `extract_article_content()` with new CSS selectors
3. Adjust `is_vietnamese_text()` validation if needed

## Output Format

Each line in the output JSONL file contains one article:

```json
{
  "id": "uuid-string",
  "language": "vi",
  "source_url": "https://vnexpress.net/article-url.html",
  "title": "Article Title",
  "text": "Clean Vietnamese text content...",
  "clean_status": "clean",
  "category": "news"
}
```

## Data Quality Standards

- **Minimum word count**: 200 words per article
- **Language purity**: >85% Vietnamese content
- **Clean text**: No HTML, ads, navigation, or special characters
- **Unique content**: Duplicate articles are automatically filtered
- **Structured format**: Ready for AI training pipelines

## Example Results

From the test run with 3 categories and 5 articles each:
- **Total articles found**: 15 unique URLs
- **Successfully scraped**: 10 high-quality articles
- **Average word count**: 800+ words per article
- **Content quality**: Clean Vietnamese text suitable for language model training

## Ethical Considerations

- **Respectful scraping**: 1-second delay between requests
- **Content attribution**: Original URLs are preserved
- **Fair use**: For research and educational purposes
- **Server-friendly**: Reasonable request rate and error handling

## Troubleshooting

### Common Issues

1. **403/406 errors**: The site may block requests. Try:
   - Increasing delay between requests
   - Using different User-Agent headers
   - Running during off-peak hours

2. **No content extracted**: Check if site structure changed:
   - Update CSS selectors in `extract_article_content()`
   - Test with individual article URLs

3. **Language detection issues**: 
   - Adjust Vietnamese validation in `is_vietnamese_text()`
   - Check for mixed-language content

### Logs and Debugging

The scraper provides detailed logging:
- ✓ Successfully scraped articles with word counts
- ⚠ Skipped articles (short content, wrong language)
- ❌ Error messages for failed requests

## Performance

- **Speed**: ~2-3 seconds per article (including delays)
- **Memory**: Low memory usage with streaming JSONL output
- **Scalability**: Can process thousands of articles
- **Resumability**: Append-only output allows restarting

## License

This tool is for educational and research purposes. Please respect vnexpress.net's terms of service and robots.txt file.

## Contributing

To improve the scraper:
1. Test with different Vietnamese news sites
2. Enhance language detection accuracy
3. Add support for additional content types
4. Improve error handling and recovery