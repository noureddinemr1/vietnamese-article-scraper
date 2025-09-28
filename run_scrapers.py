import os
import time
from Scrapers.VnExpressScraper import VnExpressScraper

def run_full_scraping(input_file,output_file):

    print("VIETNAMESE TEXT DATASET SCRAPER")
    print("=" * 50)
    print("This script will scrape Vietnamese articles from vnexpress.net")
    print("to create a high-quality text dataset for AI training.")
    print()
    
    with open(input_file, 'r', encoding='utf-8') as f:
        total_categories = len([line for line in f if line.strip()])
    
    estimated_articles = total_categories 
    estimated_time_minutes = (estimated_articles * 2.5) / 60
    
    print(f"📊 SCRAPING ESTIMATES:")
    print(f"   • Categories to process: {total_categories}")
    print(f"   • Expected articles: ~{estimated_articles}")
    print(f"   • Estimated time: ~{estimated_time_minutes:.1f} minutes")
    print()
    

    response = input("Do you want to proceed with full scraping? (y/N): ").lower().strip()
    if response != 'y':
        print("Scraping cancelled.")
        return
    
    print("\n🚀 Starting full scraping process...")
    print("⏰ This will take some time. Progress will be shown below.")
    print()
    
    # Initialize scraper
    scraper = VnExpressScraper(delay=1.5)  
    
    # Run scraping
    start_time = time.time()
    
    try:
        scraper.scrape_urls_from_file(
            links_file=input_file,
            output_file=output_file,
            max_categories=None, 
        )
        
        end_time = time.time()
        total_time = (end_time - start_time) / 60
        
        print(f"\n✅ SCRAPING COMPLETED!")
        print(f"   • Total time: {total_time:.1f} minutes")
        print(f"   • Output file: vietnamese_dataset_full.jsonl")
        print()
    except KeyboardInterrupt:
        print("\n⚠️ Scraping interrupted by user.")
        print("Partial results may be saved in vietnamese_dataset_full.jsonl")
        
    except Exception as e:
        print(f"\n❌ Error during scraping: {e}")




input_file = 'data/input.txt'
output_file = 'data/vietnamese_dataset_full.jsonl2'
run_full_scraping(input_file, output_file)