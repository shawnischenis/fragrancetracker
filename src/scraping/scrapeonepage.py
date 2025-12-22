from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import pandas as pd
import time

# --- Setup Selenium ---
#options = webdriver.ChromeOptions()
#options.add_argument("--headless")  # run headless
#driver = webdriver.Chrome(options=options)
'''
def scrape_single_product_all_variants(url, driver):
    driver.get(url)

    # Wait for main product info to load
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#product-h1-product-name"))
    )

    # Collect all variant URLs first (avoid stale references)
    variant_elements = driver.find_elements(By.CSS_SELECTOR, "div.child-products-container a.child-product")
    variant_urls = [ve.get_attribute("href") for ve in variant_elements]

    variants = []

    for variant_url in variant_urls:
        print("Scraping variant:", variant_url)
        driver.get(variant_url)
        time.sleep(2)

        product_name = driver.find_element(By.CSS_SELECTOR, "#product-h1-product-name").text.strip()
        brand = driver.find_element(By.CSS_SELECTOR, ".brand-name").text.strip()
        size = driver.find_element(By.CSS_SELECTOR, ".child-product.selected .item-size").text.strip()
        discount_price = driver.find_element(By.CSS_SELECTOR, ".child-product.selected .item-price").text.strip()

        # Retail price
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
        })

    return variants
'''
def scrape_single_product_all_variants(url, driver):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CSS_SELECTOR, "#product-h1-product-name"))
    )

    variant_elements = driver.find_elements(By.CSS_SELECTOR, "div.child-products-container a.child-product")
    if not variant_elements:
        variant_urls = [driver.current_url]  # single variant
    else:
        variant_urls = [ve.get_attribute("href") for ve in variant_elements]

    variants = []
    for variant_url in variant_urls:
        driver.get(variant_url)
        WebDriverWait(driver, 5).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "#product-h1-product-name"))
        )

        product_name = driver.find_element(By.CSS_SELECTOR, "#product-h1-product-name").text.strip()
        brand = driver.find_element(By.CSS_SELECTOR, ".brand-name").text.strip()

        try:
            size = driver.find_element(By.CSS_SELECTOR, ".child-product.selected .item-size").text.strip()
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
        })

    return variants

# === Example usage ===
#url = "https://www.jomashop.com/sospiro-unisex-vibrato-edp-spray-3-4-oz-tester-fragrances-3700583501402.html"
#data = scrape_single_product_all_variants(url)
#df = pd.DataFrame(data)
#print(df)

#driver.quit()
