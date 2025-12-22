# debug_jomashop_scraper.py
import time
import traceback
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIG ---
BASE_URL = "https://www.jomashop.com/perfume.html?page={}"
MAX_PAGE = 2            # pages to iterate (increase after testing)
PRODUCTS_PER_PAGE = None  # None => all; otherwise first N products per page (for fast testing)
OUTPUT_CSV = "data/raw/jomashop_perfumes_debug.csv"

# --- SELENIUM SETUP ---
options = webdriver.ChromeOptions()
# options.add_argument("--headless")   # <--- comment out headless while debugging to watch browser
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)

def scrape_single_product_all_variants(url, driver, wait=8):
    """Robust variant scraper for a single product URL (returns list of dicts)."""
    print(f"    ENTER product scraper: {url}")
    try:
        driver.get(url)
    except Exception as e:
        print("    Error loading product URL:", e)
        return []

    # wait for main product header (if it never shows, bail)
    try:
        WebDriverWait(driver, wait).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#product-h1-product-name"))
        )
    except Exception as e:
        print("    Timeout waiting for product header:", e)
        # continue -- some pages might still render variant container; we'll try below

    # collect variant elements (if none, we will treat page as single-variant)
    try:
        variant_elements = driver.find_elements(By.CSS_SELECTOR, "div.child-products-container a.child-product")
    except Exception as e:
        print("    Error collecting variant elements:", e)
        variant_elements = []

    # Build full variant URL list safely
    variant_urls = []
    for ve in variant_elements:
        try:
            href = ve.get_attribute("href")
            if not href:
                continue
            if href.startswith("http"):
                variant_urls.append(href)
            else:
                variant_urls.append("https://www.jomashop.com" + href)
        except Exception as e:
            print("    error reading href for one variant:", e)
    # If no variant URLs found, treat the current product URL as the only variant
    if not variant_urls:
        variant_urls = [driver.current_url]
    print(f"    Found {len(variant_urls)} variant urls for product")

    variants = []
    for variant_url in variant_urls:
        try:
            print("      Visiting variant:", variant_url)
            driver.get(variant_url)

            # Wait for product header to ensure page is loaded
            WebDriverWait(driver, wait).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#product-h1-product-name"))
            )

            # product name & brand
            try:
                product_name = driver.find_element(By.CSS_SELECTOR, "#product-h1-product-name").text.strip()
            except:
                product_name = ""
            try:
                brand = driver.find_element(By.CSS_SELECTOR, ".brand-name").text.strip()
            except:
                brand = ""

            # size (try selected child-product then fallback)
            size = ""
            try:
                size = driver.find_element(By.CSS_SELECTOR, ".child-product.selected .item-size").text.strip()
            except:
                try:
                    # fallback: maybe the .item-size is present in some other container
                    size = driver.find_element(By.CSS_SELECTOR, ".item-size").text.strip()
                except:
                    size = ""

            # discount / now price
            discount_price = ""
            try:
                discount_price = driver.find_element(By.CSS_SELECTOR, ".child-product.selected .item-price").text.strip()
            except:
                try:
                    discount_price = driver.find_element(By.CSS_SELECTOR, ".now-price span").text.strip()
                except:
                    # fallback to any item-price on page
                    try:
                        discount_price = driver.find_element(By.CSS_SELECTOR, ".item-price").text.strip()
                    except:
                        discount_price = ""

            # retail price (exclude label)
            retail_price = ""
            try:
                retail_price = driver.find_element(By.CSS_SELECTOR, ".retail-wrapper span:not(.retail-label)").text.strip()
            except:
                retail_price = ""

            variants.append({
                "brand": brand,
                "product": product_name,
                "size": size,
                "discount_price": discount_price,
                "retail_price": retail_price,
                "url": variant_url
            })

            # polite pause between variant pages
            time.sleep(0.6)

        except Exception as e:
            print("      Exception scraping variant:", variant_url)
            traceback.print_exc()
            continue

    print(f"    EXIT product scraper: collected {len(variants)} variants")
    return variants

# --- MAIN crawling loop with debug prints and incremental saving ---
all_data = []

try:
    for page in range(1, MAX_PAGE + 1):
        list_url = BASE_URL.format(page)
        print(f"\n=== Scraping listing page {page}: {list_url} ===")
        driver.get(list_url)

        # Wait until the listing items render (or timeout)
        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "li.productItem"))
            )
        except Exception as e:
            print("Timeout waiting for listing items:", e)
            # continue anyway to attempt
            time.sleep(2)

        # collect product elements and their hrefs first
        try:
            product_elements = driver.find_elements(By.CSS_SELECTOR, "li.productItem")
            print(" Found product element count:", len(product_elements))
        except Exception as e:
            print(" Error finding product elements:", e)
            product_elements = []

        product_links = []
        for idx, prod in enumerate(product_elements):
            try:
                # try multiple candidate link selectors
                try:
                    link_el = prod.find_element(By.CSS_SELECTOR, "a.productImg-link")
                except:
                    try:
                        link_el = prod.find_element(By.CSS_SELECTOR, "a.productName-link")
                    except:
                        try:
                            link_el = prod.find_element(By.CSS_SELECTOR, "a.itemLink")
                        except:
                            link_el = None
                if link_el:
                    href = link_el.get_attribute("href")
                    if href:
                        product_links.append(href)
            except Exception as e:
                print(f"  error collecting link for product idx {idx}:", e)

        print(f" Collected {len(product_links)} product links on page {page}")
        if not product_links:
            print(" No product links collected for this listing page! Dumping page HTML for inspection...")
            # optional: save page_source to file for offline inspection
            with open(f"debug_page_{page}.html", "w", encoding="utf-8") as fh:
                fh.write(driver.page_source[:200000])  # first chunk
            # continue to next page
            continue

        # Optionally limit products per page (for fast testing)
        to_scrape = product_links if PRODUCTS_PER_PAGE is None else product_links[:PRODUCTS_PER_PAGE]
        print(f" Will scrape {len(to_scrape)} products from listing page {page}")

        for i, product_link in enumerate(to_scrape, 1):
            print(f"\n--> ({i}/{len(to_scrape)}) Scraping product: {product_link}")
            try:
                variants = scrape_single_product_all_variants(product_link, driver)
                if variants:
                    all_data.extend(variants)
                    # incremental save after each product so we don't lose progress
                    pd.DataFrame(all_data).to_csv(OUTPUT_CSV, index=False)
                    print(f"    Saved {len(all_data)} total variants to {OUTPUT_CSV}")
                else:
                    print("    No variants returned for this product.")
            except Exception as e:
                print("    Error scraping product, continuing:", e)
                traceback.print_exc()

            time.sleep(1)  # polite delay between products

finally:
    try:
        driver.quit()
    except:
        pass

print("\n=== FINISHED ===")
print("Total variants scraped:", len(all_data))
print("Final CSV:", OUTPUT_CSV)
