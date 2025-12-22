import time
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# --- CONFIG ---
BASE_URL = "https://www.jomashop.com/fragrances.html?p={}"
MAX_PAGE = 20
OUTPUT_CSV = "data/raw/jomashop_perfumes.csv"

# --- SELENIUM SETUP ---
options = webdriver.ChromeOptions()
#options.add_argument("--headless")
options.add_argument("--disable-gpu")
options.add_argument("--no-sandbox")
driver = webdriver.Chrome(options=options)


def load_all_products_on_page(driver, pause_time=2, max_attempts=3):
    """
    Scrolls down the page slowly until no new products load.
    """
    last_height = driver.execute_script("return document.body.scrollHeight")
    attempts = 0

    while attempts < max_attempts:
        # Scroll down a bit (instead of all the way)
        driver.execute_script("window.scrollBy(0, 600);")
        time.sleep(pause_time)  # wait for JS to load products

        new_height = driver.execute_script("return document.body.scrollHeight")

        if new_height == last_height:
            attempts += 1  # no new content after scroll
        else:
            attempts = 0   # reset if new content appeared
            last_height = new_height


def scrape_single_product_all_variants(url, driver, wait=8):
    """Scrape all variants for a single product URL."""
    try:
        driver.get(url)
        WebDriverWait(driver, wait).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#product-h1-product-name"))
        )
    except:
        return []

    variant_elements = driver.find_elements(By.CSS_SELECTOR, "div.child-products-container a.child-product")
    variant_urls = [ve.get_attribute("href") for ve in variant_elements if ve.get_attribute("href")]
    if not variant_urls:
        variant_urls = [driver.current_url]

    variants = []
    for variant_url in variant_urls:
        try:
            driver.get(variant_url)
            WebDriverWait(driver, wait).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "#product-h1-product-name"))
            )

            product_name = driver.find_element(By.CSS_SELECTOR, "#product-h1-product-name").text.strip()
            brand = driver.find_element(By.CSS_SELECTOR, ".brand-name").text.strip()

            try:
                size = driver.find_element(By.CSS_SELECTOR, ".child-product.selected .item-size").text.strip()
            except:
                try:
                    size = driver.find_element(By.CSS_SELECTOR, ".item-size").text.strip()
                except:
                    size = ""

            try:
                discount_price = driver.find_element(By.CSS_SELECTOR, ".child-product.selected .item-price").text.strip()
            except:
                try:
                    discount_price = driver.find_element(By.CSS_SELECTOR, ".now-price span").text.strip()
                except:
                    discount_price = ""

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

        except:
            continue

    return variants


# --- MAIN LOOP ---
all_data = []
seen_links = set()  # prevent duplicates

for page in range(1, MAX_PAGE + 1):
    list_url = BASE_URL.format(page)
    print(f"🔎 Scraping listing page {page}: {list_url}")

    driver.get(list_url)
    load_all_products_on_page(driver)
    try:
        WebDriverWait(driver, 10).until(
            EC.presence_of_all_elements_located((By.CSS_SELECTOR, "li.productItem"))
        )
    except:
        print(f"⚠️ Page {page} did not load products")
        continue

    product_elements = driver.find_elements(By.CSS_SELECTOR, "li.productItem")
    product_links = []

    for prod in product_elements:
        try:
            link_el = prod.find_element(By.CSS_SELECTOR, "a.productImg-link, a.productName-link, a.itemLink")
            href = link_el.get_attribute("href")
            if href and href not in seen_links:
                seen_links.add(href)
                product_links.append(href)
        except:
            continue

    print(f" → Found {len(product_links)} new products on page {page}")

    for product_link in product_links:
        variants = scrape_single_product_all_variants(product_link, driver)
        if variants:
            all_data.extend(variants)
        time.sleep(1)  # polite delay

driver.quit()

# --- SAVE ---
df = pd.DataFrame(all_data).drop_duplicates()
df.to_csv(OUTPUT_CSV, index=False)
print(f"✅ Done! Scraped {len(df)} unique variants in total.")
