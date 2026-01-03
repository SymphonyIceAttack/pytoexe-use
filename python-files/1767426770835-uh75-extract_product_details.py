"""
Extract Product Details - Simple Approach (like Step 1)
1. Open Chrome
2. Setup pincode
3. Navigate to product URL
4. Extract details from HTML using XPath selectors (like Step 2)
"""
import os
import time
import re
import json
from datetime import datetime
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from bs4 import BeautifulSoup


def wait_until_element_load_click(driver, locator, timeout=30):
    """Wait for element and click it - same as test_pincode_simple.py"""
    element = WebDriverWait(driver, timeout).until(
        EC.element_to_be_clickable(locator))
    element.click()
    return element


def setup_pincode_first(driver, pincode):
    """Setup pincode first - EXACT SAME as test_pincode_simple.py"""
    try:
        home_url = 'https://www.dmart.in/'
        print(f"[EXTRACT] Loading homepage...")
        driver.get(home_url)
        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(5)  # Same as test_pincode_simple.py
        
        # Find pincode input field
        print(f"[EXTRACT] Looking for pincode input field...")
        el = driver.find_elements(By.XPATH, '//*[@id="pincodeInput"]')
        
        if not el:
            print(f"[EXTRACT] Input field not found, clicking pincode button...")
            time.sleep(4)  # Same as test_pincode_simple.py
            lt = (By.XPATH, '//*[@class="header_pincode__KryhE"]')
            wait_until_element_load_click(driver, lt, 30)
            time.sleep(4)  # Same as test_pincode_simple.py
            el = driver.find_elements(By.XPATH, '//*[@id="pincodeInput"]')
        
        if not el:
            raise Exception("Could not find pincode input field")
        
        # Enter pincode
        print(f"[EXTRACT] Entering pincode {pincode}...")
        el[0].clear()
        el[0].send_keys(str(pincode))
        WebDriverWait(driver, 180).until(
            lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(4)  # Same as test_pincode_simple.py
        
        # Try to find and click suggestion - use same strategies as test_pincode_simple.py
        print(f"[EXTRACT] Looking for clickable elements...")
        suggestion_clicked = False
        
        # Strategy 1: NEW STRUCTURE - button elements inside li
        try:
            print(f"[EXTRACT] Strategy 1: Looking for first button in search results list...")
            element = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, 
                    '//p[text()="SEARCH RESULT"]/following-sibling::ul//li[1]//button')))
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", element)
            time.sleep(0.5)
            driver.execute_script("arguments[0].click();", element)
            print(f"[EXTRACT] ✅ Clicked first suggestion button!")
            suggestion_clicked = True
        except Exception as e1:
            print(f"[EXTRACT] Strategy 1 failed: {str(e1)[:80]}")
        
        # Strategy 2: Alternative - find any button in the list structure
        if not suggestion_clicked:
            try:
                print(f"[EXTRACT] Strategy 2: Finding any button in list structure...")
                elements = driver.find_elements(By.XPATH, 
                    '//p[contains(text(), "SEARCH RESULT")]/following-sibling::ul//button')
                if elements:
                    print(f"[EXTRACT] ✅ Found {len(elements)} buttons in search results!")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", elements[0])
                    print(f"[EXTRACT] ✅ Clicked first button in search results!")
                    suggestion_clicked = True
            except Exception as e2:
                print(f"[EXTRACT] Strategy 2 failed: {str(e2)[:80]}")
        
        # Strategy 3: Last resort - find any button in a list structure
        if not suggestion_clicked:
            try:
                print(f"[EXTRACT] Strategy 3: Finding any button in any list...")
                elements = driver.find_elements(By.XPATH, '//ul[.//button]//button[1]')
                if elements:
                    print(f"[EXTRACT] ✅ Found {len(elements)} buttons in lists!")
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", elements[0])
                    time.sleep(0.5)
                    driver.execute_script("arguments[0].click();", elements[0])
                    print(f"[EXTRACT] ✅ Clicked first button found!")
                    suggestion_clicked = True
            except Exception as e3:
                print(f"[EXTRACT] Strategy 3 failed: {str(e3)[:80]}")
        
        if not suggestion_clicked:
            raise Exception("Could not find or click any pincode suggestion")
        
        WebDriverWait(driver, 180).until(
            lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(2)
        
        # Get location
        try:
            location = driver.find_element(By.XPATH,
                '(//*[@class="pincode-widget_pincode-area__gc_HT"])[1]').text
            print(f"[EXTRACT] Found location: {location}")
        except:
            location = ""
            print(f"[EXTRACT] Could not get location text, continuing...")
        
        # Click confirm button - use same method as test_pincode_simple.py
        print(f"[EXTRACT] Clicking CONFIRM LOCATION button...")
        lt = (By.XPATH, "//*[contains(text(), 'CONFIRM LOCATION')]")
        wait_until_element_load_click(driver, lt, 30)
        time.sleep(5)  # Same as test_pincode_simple.py
        
        print(f"[EXTRACT] ✅ Pincode {pincode} setup completed successfully!")
        # Return location if we got it, otherwise return pincode as success indicator
        return location if location else str(pincode)
        
    except Exception as e:
        print(f"[EXTRACT] ❌ Error setting up pincode: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


def extract_product_details_from_page(driver, url, pincode=None):
    """
    Extract product details - SIMPLE APPROACH like Step 1:
    1. Setup pincode
    2. Navigate to product URL
    3. Extract details from HTML using XPath selectors (like Step 2)
    4. If variants exist, click each variant and extract details for all variants
    
    Returns: List of product_data dictionaries (one per variant, or one if no variants)
    """
    # First, extract details for the current/default variant
    all_variants_data = []
    
    # Helper function to extract product details for current page state
    def extract_current_variant_details(current_url, current_pincode):
        product_data = {
            'Pin': '',
            'Location': '',
            'Dmart_category': '',
            'Dmart_Subcategory': '',
            'Demart_sub_subcategory': '',
            'Manufacturer': '',
            'Product Name': '',
            'Variant': '',
            'MRP': '',
            'Dmart Price': '',
            'save': '',
            'Bulk': 'No',
            'Bulk quantity': '',
            'Marketer': '',
            'overview': '',
            'key features': '',
            'Free': '',
            'SKUs': current_url,
            'Home Delivery': '',
            'Pick Up Point': '',
            'Image Repository': '',
            'Date_Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'in stock': 'No'
        }
        
        try:
            # Set pincode if provided
            if current_pincode:
                product_data['Pin'] = str(current_pincode)
            
            # STEP 2.5: Try to extract from JSON/__NEXT_DATA__ first (faster and more reliable)
            try:
                json_data = driver.execute_script("""
                    try {
                        // Try to get __NEXT_DATA__
                        var scripts = document.querySelectorAll('script[id="__NEXT_DATA__"]');
                        if (scripts.length > 0) {
                            return JSON.parse(scripts[0].textContent);
                        }
                        return null;
                    } catch(e) {
                        return null;
                    }
                """)
                
                if json_data:
                    try:
                        # Extract from JSON structure (like step2_parallel.py)
                        pdp_data = json_data.get('props', {}).get('pageProps', {}).get('pdpData', {})
                        dynamic_pdp = pdp_data.get('dynamicPDP', {})
                        product_data_json = dynamic_pdp.get('data', {}).get('productData', {})
                        
                        if not product_data_json:
                            product_data_json = pdp_data.get('productData', {})
                        
                        if product_data_json:
                            # Extract Manufacturer from JSON (like step2_parallel.py line 147)
                            manufacturer = product_data_json.get('manufacturer', '')
                            if manufacturer:
                                product_data['Manufacturer'] = manufacturer
                            
                            # Extract Prices from JSON (like step2_parallel.py lines 158-166)
                            price_mrp = product_data_json.get('priceMRP')
                            if price_mrp is not None:
                                product_data['MRP'] = str(price_mrp).replace('₹', '').replace(',', '').strip()
                            
                            price_sale = product_data_json.get('priceSALE')
                            if price_sale is not None:
                                product_data['Dmart Price'] = str(price_sale).replace('₹', '').replace(',', '').strip()
                            
                            # Extract Variant (unit) from JSON (like step2_parallel.py lines 204-208)
                            skus = product_data_json.get('sKUs', [])
                            if skus:
                                sku = skus[0]  # Use first SKU
                                variant_text = sku.get('variantTextValue', '')
                                if not variant_text:
                                    # Try to extract from name
                                    sku_name = sku.get('name', '')
                                    if ':' in sku_name:
                                        variant_text = sku_name.split(':')[-1].strip()
                                if variant_text:
                                    product_data['Variant'] = variant_text
                            
                            # Extract Variant (unit) from JSON (like step2_parallel.py lines 204-208)
                            if not product_data.get('Variant'):
                                skus = product_data_json.get('sKUs', [])
                                if skus:
                                    sku = skus[0]  # Use first SKU
                                    variant_text = sku.get('variantTextValue', '')
                                    if not variant_text:
                                        # Try to extract from name
                                        sku_name = sku.get('name', '')
                                        if ':' in sku_name:
                                            variant_text = sku_name.split(':')[-1].strip()
                                    if variant_text:
                                        product_data['Variant'] = variant_text
                            
                            # Extract Overview from descriptionTabs (JSON method - fastest)
                            if not product_data.get('overview'):
                                skus = product_data_json.get('sKUs', [])
                                if skus:
                                    sku = skus[0]  # Use first SKU
                                    description_tabs = sku.get('descriptionTabs', [])
                                    for tab in description_tabs:
                                        if tab.get('title', '').lower() == 'description':
                                            desc_html = tab.get('description', '')
                                            if desc_html:
                                                # Parse HTML to get text
                                                desc_soup = BeautifulSoup(desc_html, 'html.parser')
                                                overview_text = desc_soup.get_text(separator=' ', strip=True)
                                                # Overview contains key features too (as per user requirement)
                                                if overview_text:
                                                    product_data['overview'] = overview_text
                                                    product_data['key features'] = ''  # Leave empty, overview contains it
                                                    break
                            
                            # Extract Marketer from descriptionTabs (JSON method - fastest)
                            if not product_data.get('Marketer'):
                                skus = product_data_json.get('sKUs', [])
                                if skus:
                                    sku = skus[0]  # Use first SKU
                                    description_tabs = sku.get('descriptionTabs', [])
                                    for tab in description_tabs:
                                        if tab.get('title', '').lower() == 'more info':
                                            more_info_html = tab.get('description', '')
                                            if more_info_html:
                                                # Parse HTML to find Marketer
                                                more_info_soup = BeautifulSoup(more_info_html, 'html.parser')
                                                # Look for "Marketer :" in strong tag, then get next span
                                                strong_tags = more_info_soup.find_all('strong')
                                                for strong in strong_tags:
                                                    if 'Marketer :' in strong.get_text() or 'Marketer:' in strong.get_text():
                                                        # Get next span sibling
                                                        next_span = strong.find_next_sibling('span')
                                                        if next_span:
                                                            product_data['Marketer'] = next_span.get_text(strip=True)
                                                            break
                                                break
                    except Exception as json_error:
                        print(f"[EXTRACT] ⚠️ JSON extraction error: {str(json_error)[:50]}")
            except:
                pass
            
            # STEP 3: Extract details from HTML using XPath selectors (exactly like Step 2)
            # Product Name
            try:
                item_name = driver.find_element(By.XPATH,
                    '//*[@class="text-label-component_title__Qk1fy"]').text
                # Remove ": 1 Unit" suffix if present
                if ': 1 Unit' in item_name:
                    item_name = item_name.replace(': 1 Unit', '').strip()
                product_data['Product Name'] = item_name
            except:
                try:
                    h1 = driver.find_element(By.TAG_NAME, 'h1')
                    name_text = h1.text.strip()
                    if ': 1 Unit' in name_text:
                        name_text = name_text.replace(': 1 Unit', '').strip()
                    product_data['Product Name'] = name_text
                except:
                    pass
            
            # Manufacturer - try multiple methods (only if not already extracted from JSON)
            if not product_data.get('Manufacturer'):
                try:
                    # Primary: Use provided XPath
                    brand = driver.find_element(By.XPATH,
                        '//*[@id="app"]/div[1]/main/div/div/div[2]/div[3]/div[1]/div/div').text.strip()
                    if brand and brand not in ['Bags & More', 'Accessories', 'Clothing & Accessories']:  # Exclude generic categories
                        product_data['Manufacturer'] = brand
                except:
                    try:
                        # Fallback 1: Original class-based selector
                        brand = driver.find_element(By.XPATH,
                            '//*[@class="common_brand-link-horizontal__MCanP"]').text.strip()
                        if brand and brand not in ['Bags & More', 'Accessories', 'Clothing & Accessories']:
                            product_data['Manufacturer'] = brand
                    except:
                        try:
                            brand = driver.find_element(By.XPATH,
                                '//*[@class="common_brand-link-horizontal__Mzcqn"]').text.strip()
                            if brand and brand not in ['Bags & More', 'Accessories', 'Clothing & Accessories']:
                                product_data['Manufacturer'] = brand
                        except:
                            try:
                                # Fallback 2: Alternative selector
                                brand_elem = driver.find_elements(By.XPATH, '//a[contains(@class, "brand")]')
                                for elem in brand_elem:
                                    brand_text = elem.text.strip()
                                    if brand_text and brand_text not in ['Bags & More', 'Accessories', 'Clothing & Accessories']:
                                        product_data['Manufacturer'] = brand_text
                                        break
                            except:
                                pass
            
            # Prices - Use provided XPath selectors first, then fallback methods
            if not product_data.get('Dmart Price') or not product_data.get('MRP'):
                try:
                    # Method 1: Use provided XPath selectors (most reliable)
                    if not product_data.get('Dmart Price'):
                        try:
                            dmart_price_elem = driver.find_element(By.XPATH,
                                '/html/body/div[1]/main/div/div/div[2]/div[3]/div[3]/div[1]/div[1]/span/span')
                            dmart_price_text = dmart_price_elem.text.replace('₹', '').replace(',', '').strip()
                            product_data['Dmart Price'] = re.sub(r'[^\d.]', '', dmart_price_text)
                        except:
                            pass
                    
                    if not product_data.get('MRP'):
                        try:
                            mrp_elem = driver.find_element(By.XPATH,
                                '/html/body/div[1]/main/div/div/div[2]/div[3]/div[3]/div[1]/div[2]/span')
                            mrp_text = mrp_elem.text.replace('₹', '').replace(',', '').replace('MRP', '').strip()
                            product_data['MRP'] = re.sub(r'[^\d.]', '', mrp_text)
                        except:
                            pass
                    
                    # Method 2: Fallback to class-based XPath (original method)
                    if not product_data.get('Dmart Price') or not product_data.get('MRP'):
                        price_ele = driver.find_elements(By.XPATH,
                            '//*[@class="price-details-component_value__IvVER"]')
                        
                        if len(price_ele) > 1:
                            # IMPORTANT: index 0 is Dmart Price, index 1 is MRP
                            if not product_data.get('Dmart Price'):
                                dmart_price_text = price_ele[0].text.replace('₹', '').replace(',', '').strip()
                                product_data['Dmart Price'] = re.sub(r'[^\d.]', '', dmart_price_text)
                            if not product_data.get('MRP'):
                                mrp_text = price_ele[1].text.replace('₹', '').replace(',', '').replace('MRP', '').strip()
                                product_data['MRP'] = re.sub(r'[^\d.]', '', mrp_text)
                        elif len(price_ele) == 1:
                            if not product_data.get('Dmart Price'):
                                dmart_price_text = price_ele[0].text.replace('₹', '').replace(',', '').strip()
                                product_data['Dmart Price'] = re.sub(r'[^\d.]', '', dmart_price_text)
                            # Try to find MRP separately (strikethrough price)
                            if not product_data.get('MRP'):
                                try:
                                    mrp_elem = driver.find_element(By.XPATH, '//span[contains(@class, "line-through")]')
                                    mrp_text = mrp_elem.text.replace('₹', '').replace(',', '').replace('MRP', '').strip()
                                    if mrp_text:
                                        product_data['MRP'] = re.sub(r'[^\d.]', '', mrp_text)
                                except:
                                    pass
                
                    # Method 2: Use JavaScript to find prices if XPath didn't work
                    if not product_data.get('Dmart Price') or not product_data.get('MRP'):
                        prices_js = driver.execute_script("""
                    var prices = {
                        dmartPrice: '',
                        mrp: ''
                    };
                    
                    // Method 1: Find by class name
                    var priceElements = document.querySelectorAll('.price-details-component_value__IvVER');
                    if (priceElements.length > 1) {
                        prices.dmartPrice = priceElements[0].textContent.trim();
                        prices.mrp = priceElements[1].textContent.trim();
                    } else if (priceElements.length === 1) {
                        prices.dmartPrice = priceElements[0].textContent.trim();
                    }
                    
                    // Method 2: Find MRP by strikethrough if not found
                    if (!prices.mrp) {
                        var strikethrough = document.querySelector('span.line-through');
                        if (strikethrough) {
                            prices.mrp = strikethrough.textContent.trim();
                        }
                    }
                    
                    // Method 3: Find all price-like spans and extract
                    if (!prices.dmartPrice || !prices.mrp) {
                        var allSpans = document.querySelectorAll('span');
                        var priceSpans = [];
                        for (var i = 0; i < allSpans.length; i++) {
                            var text = allSpans[i].textContent.trim();
                            if (text.includes('₹') && /₹\\s*[\\d,]+/.test(text)) {
                                var priceNum = text.replace(/[₹,\\s]/g, '').replace(/[^\\d.]/g, '');
                                if (priceNum && !isNaN(priceNum)) {
                                    var isStrikethrough = window.getComputedStyle(allSpans[i]).textDecoration.includes('line-through') ||
                                                          allSpans[i].closest('[style*="line-through"]') ||
                                                          allSpans[i].classList.contains('line-through');
                                    priceSpans.push({
                                        value: priceNum,
                                        text: text,
                                        isStrikethrough: isStrikethrough
                                    });
                                }
                            }
                        }
                        
                        // Sort: non-strikethrough first (Dmart Price), strikethrough second (MRP)
                        priceSpans.sort(function(a, b) {
                            if (a.isStrikethrough && !b.isStrikethrough) return 1;
                            if (!a.isStrikethrough && b.isStrikethrough) return -1;
                            return 0;
                        });
                        
                        if (priceSpans.length > 0 && !prices.dmartPrice) {
                            prices.dmartPrice = priceSpans[0].value;
                        }
                        if (priceSpans.length > 1 && !prices.mrp) {
                            prices.mrp = priceSpans[1].value;
                        } else if (priceSpans.length === 1 && priceSpans[0].isStrikethrough && !prices.mrp) {
                            prices.mrp = priceSpans[0].value;
                        }
                    }
                    
                        return prices;
                        """)
                        
                        if prices_js:
                            if prices_js.get('dmartPrice'):
                                dmart_clean = prices_js['dmartPrice'].replace('₹', '').replace(',', '').strip()
                                if dmart_clean:
                                    product_data['Dmart Price'] = re.sub(r'[^\d.]', '', dmart_clean)
                            
                            if prices_js.get('mrp'):
                                mrp_clean = prices_js['mrp'].replace('₹', '').replace(',', '').replace('MRP', '').strip()
                                if mrp_clean:
                                    product_data['MRP'] = re.sub(r'[^\d.]', '', mrp_clean)
                    
                    # Method 3: Fallback - find prices by visible text using Selenium
                    if not product_data.get('Dmart Price') or product_data.get('Dmart Price') == '0' or not product_data.get('MRP') or product_data.get('MRP') == '0':
                        try:
                            all_spans = driver.find_elements(By.XPATH, "//span[contains(text(), '₹')]")
                            prices_found = []
                            for span in all_spans:
                                try:
                                    price_text = span.text.strip()
                                    if '₹' in price_text:
                                        price_num = re.sub(r'[^\d.]', '', price_text)
                                        if price_num and price_num.replace('.', '').isdigit() and float(price_num) > 0:
                                            # Check if strikethrough
                                            is_strikethrough = False
                                            try:
                                                style = span.get_attribute('style') or ''
                                                class_attr = span.get_attribute('class') or ''
                                                parent = span.find_element(By.XPATH, './..')
                                                parent_style = parent.get_attribute('style') or ''
                                                parent_class = parent.get_attribute('class') or ''
                                                is_strikethrough = ('line-through' in style or 
                                                                  'line-through' in class_attr or
                                                                  'line-through' in parent_style or
                                                                  'line-through' in parent_class)
                                            except:
                                                pass
                                            prices_found.append((price_num, is_strikethrough))
                                except:
                                    continue
                            
                            # Sort: non-strikethrough first, strikethrough second
                            prices_found.sort(key=lambda x: x[1])
                            
                            if prices_found:
                                if not product_data.get('Dmart Price') or product_data.get('Dmart Price') == '0':
                                    product_data['Dmart Price'] = prices_found[0][0]
                                if len(prices_found) > 1 and (not product_data.get('MRP') or product_data.get('MRP') == '0'):
                                    product_data['MRP'] = prices_found[1][0]
                                elif len(prices_found) == 1 and prices_found[0][1] and (not product_data.get('MRP') or product_data.get('MRP') == '0'):
                                    product_data['MRP'] = prices_found[0][0]
                        except Exception as fallback_error:
                            print(f"[EXTRACT] ⚠️ Fallback price extraction failed: {str(fallback_error)[:100]}")
                    
                    # Final validation: ensure prices are not "0" or empty (but keep valid prices)
                    if product_data.get('Dmart Price') == '0':
                        product_data['Dmart Price'] = ''
                    if product_data.get('MRP') == '0':
                        product_data['MRP'] = ''
                            
                except Exception as price_error:
                    print(f"[EXTRACT] ⚠️ Price extraction error: {str(price_error)[:100]}")
                    import traceback
                    traceback.print_exc()
                    product_data['MRP'] = ''
                    product_data['Dmart Price'] = ''
            
            # Extract Save - try provided XPath first, then calculate
            if not product_data.get('save'):
                try:
                    # Primary: Use provided XPath for save
                    save_elem = driver.find_element(By.XPATH,
                        '/html/body/div[1]/main/div/div/div[2]/div[3]/div[3]/div[1]/div[1]/div')
                    save_text = save_elem.text.strip()
                    # Extract number from save text (e.g., "You Save ₹251" -> "251")
                    save_match = re.search(r'(\d+)', save_text)
                    if save_match:
                        product_data['save'] = save_match.group(1)
                except:
                    pass
            
            # Calculate save if not extracted - exactly like Step 2 does (using int(float(...)))
            if not product_data.get('save'):
                mrp_str = str(product_data.get('MRP', '')).strip()
                dmart_price_str = str(product_data.get('Dmart Price', '')).strip()
                
                if mrp_str and dmart_price_str and mrp_str != '0' and dmart_price_str != '0':
                    try:
                        mrp_val = float(mrp_str.replace(',', ''))
                        sale_val = float(dmart_price_str.replace(',', ''))
                        if mrp_val > 0 and sale_val > 0:
                            save_val = int(mrp_val) - int(sale_val)  # Step 2 uses int(float(...))
                            product_data['save'] = str(save_val)
                        else:
                            product_data['save'] = ''
                    except Exception as save_error:
                        print(f"[EXTRACT] ⚠️ Save calculation error: {str(save_error)[:50]}")
                        product_data['save'] = ''
                else:
                    product_data['save'] = ''
            
            # Stock status - comprehensive check using Selenium
            try:
                in_stock = False
                
                # Method 1: Check for cart icon (like Step 2)
                try:
                    avail_ele = driver.find_elements(By.XPATH,
                        '//i[@class="dmart-icon-cart cart-action_icon__Xxc_3"]')
                    if avail_ele:
                        in_stock = True
                except:
                    pass
                
                # Method 2: Check if "ADD TO CART" button exists and is enabled
                # Also check for disabled button (out of stock)
                if not in_stock:
                    try:
                        cart_btn = driver.find_elements(By.XPATH, "//button[contains(text(), 'ADD TO CART')]")
                        if cart_btn:
                            for btn in cart_btn:
                                try:
                                    # Check if button is disabled (has Mui-disabled class)
                                    btn_class = btn.get_attribute('class') or ''
                                    if 'Mui-disabled' in btn_class:
                                        # Button exists but is disabled = out of stock
                                        in_stock = False
                                        break
                                    elif btn.is_enabled() and btn.is_displayed():
                                        in_stock = True
                                        break
                                except:
                                    continue
                    except:
                        pass
                
                # Method 3: Use JavaScript to check if button is clickable or disabled
                if not in_stock:
                    try:
                        stock_check = driver.execute_script("""
                            // Check for ADD TO CART button
                            var cartButtons = document.querySelectorAll('button');
                            for (var i = 0; i < cartButtons.length; i++) {
                                var btn = cartButtons[i];
                                var btnText = btn.textContent || btn.innerText || '';
                                if (btnText.toUpperCase().includes('ADD TO CART')) {
                                    // Check if button has Mui-disabled class (out of stock)
                                    var btnClass = btn.className || '';
                                    if (btnClass.includes('Mui-disabled') || btn.disabled) {
                                        return false; // Out of stock
                                    }
                                    // Check if button is enabled and visible
                                    if (!btn.disabled && btn.offsetParent !== null) {
                                        return true; // In stock
                                    }
                                }
                            }
                            
                            // Check for cart icon
                            var cartIcons = document.querySelectorAll('i.dmart-icon-cart, i[class*="cart"]');
                            if (cartIcons.length > 0) {
                                return true;
                            }
                            
                            // Check for "Out of Stock" message
                            var outOfStock = document.body.innerText.toUpperCase();
                            if (outOfStock.includes('OUT OF STOCK') || outOfStock.includes('NOT AVAILABLE')) {
                                return false;
                            }
                            
                            // If we have prices and no out of stock message, assume in stock
                            var prices = document.querySelectorAll('.price-details-component_value__IvVER');
                            if (prices.length > 0) {
                                return true;
                            }
                            
                            return false;
                        """)
                        if stock_check is True:
                            in_stock = True
                        elif stock_check is False:
                            in_stock = False  # Explicitly out of stock
                    except Exception as js_error:
                        pass
                
                # Method 4: Check for explicit "Out of Stock" indicators
                if in_stock:
                    try:
                        # Double-check: look for out of stock messages
                        out_of_stock_indicators = driver.find_elements(By.XPATH, 
                            "//*[contains(text(), 'Out of Stock') or contains(text(), 'Not Available') or contains(text(), 'Sold Out')]")
                        if out_of_stock_indicators:
                            # If we find out of stock message, override
                            in_stock = False
                    except:
                        pass
                
                product_data['in stock'] = 'Yes' if in_stock else 'No'
                
            except Exception as stock_error:
                print(f"[EXTRACT] ⚠️ Stock detection error: {str(stock_error)[:100]}")
                # Default to checking if prices exist - if prices exist, likely in stock
                try:
                    prices_exist = driver.find_elements(By.XPATH, '//*[@class="price-details-component_value__IvVER"]')
                    product_data['in stock'] = 'Yes' if prices_exist else 'No'
                except:
                    product_data['in stock'] = 'No'
            
            # Variant - should be the unit (like "1 Unit", "500g", etc.) - only if not already extracted from JSON
            if not product_data.get('Variant'):
                try:
                    # Primary: Use provided XPath
                    variant_elem = driver.find_element(By.XPATH,
                        '/html/body/div[1]/main/div/div/div[2]/div[3]/div[2]/div[1]/div/div')
                    variant_text = variant_elem.text.strip()
                    if variant_text:
                        product_data['Variant'] = variant_text
                except:
                    try:
                        # Fallback 1: Original class-based selectors
                        variant_elem = driver.find_elements(By.XPATH,
                            '//*[@class="horizontal-single-variants-component__volume__PCe8w"]')
                        if not variant_elem:
                            variant_elem = driver.find_elements(By.XPATH,
                                '//*[@class="horizontal-single-variants-component__volume__MDoJs"]')
                        if variant_elem:
                            variant_text = variant_elem[0].text.strip()
                            product_data['Variant'] = variant_text
                    except:
                        # Fallback 2: Try to extract from product name (if it has unit info)
                        if product_data.get('Product Name'):
                            name = product_data['Product Name']
                            # Look for unit patterns like "1 Unit", "500g", "1kg", etc.
                            unit_match = re.search(r'(\d+\s*(?:Unit|kg|g|ml|l|pack|pcs?))', name, re.IGNORECASE)
                            if unit_match:
                                product_data['Variant'] = unit_match.group(1)
            
            # SKUs is already set in product_data initialization
            
            # Extract Overview using direct XPath (NO TAB CLICKING - saves 2 seconds!)
            if not product_data.get('overview'):
                try:
                    # Use provided XPath for overview
                    overview_elem = driver.find_element(By.XPATH,
                        '/html/body/div[1]/main/div/div/div[4]/div/div[2]')
                    overview_text = overview_elem.text.strip()
                    if overview_text:
                        product_data['overview'] = overview_text
                        # Key features will be included in overview text (as per user requirement)
                        product_data['key features'] = ''  # Leave empty, overview contains it
                except:
                    pass
            
            # Extract Marketer using direct XPath (NO TAB CLICKING - saves 2 seconds!)
            if not product_data.get('Marketer'):
                marketer = ''
                try:
                    # Check if "Marketer :" text is in strong tag under the provided XPath
                    marketer_container = driver.find_element(By.XPATH,
                        '/html/body/div[1]/main/div/div/div[3]/div/div[4]/div/span')
                    
                    # Check if "Marketer :" text exists in strong tag within this span
                    strong_tags = marketer_container.find_elements(By.XPATH, './/strong')
                    for strong in strong_tags:
                        strong_text = strong.text.strip()
                        if 'Marketer :' in strong_text or 'Marketer:' in strong_text:
                            # Get the next span sibling
                            try:
                                next_span = strong.find_element(By.XPATH, './following-sibling::span[1]')
                                marketer = next_span.text.strip()
                                break
                            except:
                                # Try alternative: get next sibling element
                                try:
                                    parent = strong.find_element(By.XPATH, './..')
                                    next_span = parent.find_element(By.XPATH, './span[2]')  # Second span in parent
                                    marketer = next_span.text.strip()
                                    break
                                except:
                                    pass
                except:
                    pass
                
                product_data['Marketer'] = marketer if marketer else ''
            
            # Extract Bulk - exactly like step2_optimized.py lines 444-456
            bulk_val = 'N'
            try:
                bulk_elem = driver.find_element(By.XPATH,
                    '//*[@class="image-gallery_component_preview__lTTL_"]//div[@class="image-gallery_component_ribbon___43Nw"]')
                bulk_string = bulk_elem.text
                matches = re.findall(r'\d+', bulk_string)
                if matches:
                    bulk_val = matches[0]
            except:
                pass
            product_data['Bulk'] = 'No' if bulk_val == 'N' else 'Yes'
            product_data['Bulk quantity'] = bulk_val
            
            # Extract Free offers
            try:
                free_elem = driver.find_element(By.XPATH,
                    '//*[@class="common_product-info__Y2P8l"]/div[@class="offers_widget_offer__YJrlT"]/p')
                product_data['Free'] = free_elem.text
            except:
                pass
            
            # Extract Image URLs
            try:
                img_elements = driver.find_elements(By.TAG_NAME, 'img')
                image_urls = []
                for img in img_elements:
                    src = img.get_attribute('src')
                    if src and 'cdn.dmart.in/images/products' in src:
                        if src not in image_urls:
                            image_urls.append(src)
                if image_urls:
                    product_data['Image Repository'] = ' | '.join(image_urls[:10])  # Limit to 10 images
            except:
                pass
            
            # Extract categories from breadcrumb - get ALL breadcrumb items properly
            try:
                breadcrumb_links = driver.find_elements(By.XPATH, '//nav[@aria-label="breadcrumb"]//a')
                if not breadcrumb_links:
                    # Try alternative breadcrumb selector
                    breadcrumb_links = driver.find_elements(By.XPATH, '//*[@class="MuiBreadcrumbs-root"]//a')
                
                if breadcrumb_links:
                    # Filter to get only category links (exclude home page)
                    category_items = []
                    for link in breadcrumb_links:
                        href = link.get_attribute('href') or ''
                        text = link.text.strip()
                        # Only include category links, not home
                        if '/category/' in href and text:
                            category_items.append(text)
                    
                    # Assign categories
                    if len(category_items) >= 1:
                        product_data['Dmart_category'] = category_items[0]
                    if len(category_items) >= 2:
                        product_data['Dmart_Subcategory'] = category_items[1]
                    if len(category_items) >= 3:
                        product_data['Demart_sub_subcategory'] = category_items[2]
                
                # FALLBACK: If subcategory is still empty, try extracting from URL or JSON
                if not product_data.get('Dmart_Subcategory'):
                    try:
                        # Method 1: Try to extract from JSON/__NEXT_DATA__
                        json_data = driver.execute_script("""
                            try {
                                var scripts = document.querySelectorAll('script[id="__NEXT_DATA__"]');
                                if (scripts.length > 0) {
                                    return JSON.parse(scripts[0].textContent);
                                }
                                return null;
                            } catch(e) {
                                return null;
                            }
                        """)
                        
                        if json_data:
                            # Try to get category from breadcrumbList in JSON
                            breadcrumb_list = json_data.get('props', {}).get('pageProps', {}).get('breadcrumbList', {})
                            if breadcrumb_list:
                                item_list = breadcrumb_list.get('itemListElement', [])
                                if len(item_list) >= 2:
                                    subcat_name = item_list[1].get('item', {}).get('name', '')
                                    if subcat_name:
                                        product_data['Dmart_Subcategory'] = subcat_name
                    except:
                        pass
                    
                    # Method 2: Try to extract from structured data (schema.org)
                    if not product_data.get('Dmart_Subcategory'):
                        try:
                            schema_scripts = driver.find_elements(By.XPATH, '//script[@type="application/ld+json"]')
                            for script in schema_scripts:
                                try:
                                    schema_data = json.loads(script.get_attribute('innerHTML'))
                                    if schema_data.get('@type') == 'BreadcrumbList':
                                        items = schema_data.get('itemListElement', [])
                                        if len(items) >= 2:
                                            subcat_name = items[1].get('item', {}).get('name', '')
                                            if subcat_name:
                                                product_data['Dmart_Subcategory'] = subcat_name
                                                break
                                except:
                                    continue
                        except:
                            pass
                    
                    # Method 3: Try to extract from page URL if available
                    if not product_data.get('Dmart_Subcategory'):
                        try:
                            current_url = driver.current_url
                            # URL pattern: /category/category-name-subcategory-name
                            if '/category/' in current_url:
                                url_parts = current_url.split('/category/')
                                if len(url_parts) > 1:
                                    category_path = url_parts[1].split('?')[0].split('#')[0]
                                    # Try to extract subcategory from path
                                    path_parts = category_path.split('-')
                                    if len(path_parts) > 1:
                                        # This is a heuristic - might not always work
                                        pass  # Skip URL method as it's unreliable
                        except:
                            pass
            except:
                pass
            
            # Extract Pin and Location from header if not already extracted
            if not product_data['Pin']:
                if current_pincode:
                    product_data['Pin'] = str(current_pincode)
                else:
                    try:
                        pincode_elems = driver.find_elements(By.XPATH, "//span[contains(@class, 'font-bold') and contains(@class, 'text-primaryColor')]")
                        for elem in pincode_elems:
                            pin_text = elem.text.strip()
                            if pin_text and len(pin_text) == 6 and pin_text.isdigit():
                                product_data['Pin'] = pin_text
                                break
                    except:
                        pass
            
            if not product_data['Location']:
                try:
                    location_elem = driver.find_element(By.XPATH, "//div[@title]")
                    if location_elem:
                        location_title = location_elem.get_attribute('title')
                        if location_title:
                            product_data['Location'] = location_title
                except:
                    pass
            
            # Extract Home Delivery info if not already extracted - default to "Yes"
            if not product_data['Home Delivery']:
                try:
                    # Look for home delivery section in header
                    delivery_elem = driver.find_elements(By.XPATH, 
                        '//*[@class="MuiGrid-root MuiGrid-item MuiGrid-grid-xs-12 MuiGrid-grid-md-5 header_sepBorder__eD530 mui-style-1r482s6"]')
                    if delivery_elem:
                        delivery_text = delivery_elem[0].text.strip()
                        if 'Home Delivery' in delivery_text:
                            # Extract time if available
                            time_match = re.search(r'(\d{2}:\d{2}\s*[AP]M\s*-\s*\d{2}:\d{2}\s*[AP]M|Today.*?PM|Tomorrow.*?AM)', delivery_text, re.IGNORECASE)
                            if time_match:
                                product_data['Home Delivery'] = time_match.group(1)
                            else:
                                product_data['Home Delivery'] = 'Yes'  # Default to Yes
                        else:
                            product_data['Home Delivery'] = 'Yes'  # Default to Yes
                    else:
                        # Check if delivery info exists anywhere
                        delivery_check = driver.find_elements(By.XPATH, "//*[contains(text(), 'Home Delivery')]")
                        if delivery_check:
                            product_data['Home Delivery'] = 'Yes'
                        else:
                            product_data['Home Delivery'] = 'Yes'  # Default to Yes (as per user requirement)
                except:
                    product_data['Home Delivery'] = 'Yes'  # Default to Yes
            
            product_data['Pick Up Point'] = 'NA'
            
            # Set default for Free if not extracted
            if not product_data.get('Free'):
                product_data['Free'] = 'N'
            
            return product_data
            
        except Exception as e:
            print(f"[EXTRACT] ❌ Error extracting variant details: {str(e)}")
            import traceback
            traceback.print_exc()
            return product_data
    
    # Main extraction logic starts here
    try:
        # STEP 1: Setup pincode ONLY if provided (skip if already set up!)
        # If pincode=None, it means the driver already has pincode configured (via CategoryWorker.setup())
        location = ''
        if pincode:
            # Only setup if pincode is explicitly provided
            location = setup_pincode_first(driver, pincode)
            if location:
                location = location if location != str(pincode) else ''
        else:
            # Pincode already set up via CategoryWorker.setup() (cookies loaded)
            # Skip verification - just go directly to product page (saves ~1 second)
            pass
        
        # STEP 2: Navigate to product URL
        driver.get(url)
        WebDriverWait(driver, 20).until(
            lambda d: d.execute_script('return document.readyState') == 'complete')
        time.sleep(1.5)  # Reduced from 2 seconds
        
        # STEP 3: Check for variant buttons (like Size S, Size XXL, etc.)
        variant_buttons = []
        try:
            # Find all variant buttons - they have class containing "mt-6 mr-4" and contain variant text
            variant_containers = driver.find_elements(By.XPATH,
                '//div[contains(@class, "mt-6") and contains(@class, "mr-4") and contains(@class, "cursor-pointer")]')
            
            for container in variant_containers:
                try:
                    # Get the variant text from the inner div
                    variant_div = container.find_element(By.XPATH, './/div[contains(@class, "font-mulish")]')
                    variant_text = variant_div.text.strip()
                    # Accept ALL variant types (Size, Color, Weight, Pack, etc.) - not just "Size"
                    if variant_text:
                        variant_buttons.append((container, variant_text))
                except:
                    continue
        except Exception as variant_error:
            print(f"[EXTRACT] ⚠️ Error finding variants: {str(variant_error)[:50]}")
        
        # STEP 4: Extract details for each variant (or just once if no variants)
        if variant_buttons and len(variant_buttons) > 1:
            print(f"[EXTRACT] Found {len(variant_buttons)} variants, extracting details for each...")
            for idx, (variant_button, variant_name) in enumerate(variant_buttons):
                try:
                    print(f"[EXTRACT] Processing variant {idx+1}/{len(variant_buttons)}: {variant_name}")
                    
                    # Click the variant button
                    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", variant_button)
                    time.sleep(0.5)
                    variant_button.click()
                    time.sleep(2)  # Wait for page to update with new variant data
                    
                    # Extract details for this variant
                    variant_data = extract_current_variant_details(url, pincode)
                    variant_data['Variant'] = variant_name  # Set the variant name
                    variant_data['Location'] = location  # Set location from pincode setup
                    all_variants_data.append(variant_data)
                    
                except Exception as variant_extract_error:
                    print(f"[EXTRACT] ⚠️ Error extracting variant {variant_name}: {str(variant_extract_error)[:50]}")
                    # Still try to extract with default variant
                    if idx == 0:
                        variant_data = extract_current_variant_details(url, pincode)
                        variant_data['Variant'] = variant_name
                        variant_data['Location'] = location
                        all_variants_data.append(variant_data)
        else:
            # No variants or only one variant, extract once
            product_data = extract_current_variant_details(url, pincode)
            product_data['Location'] = location
            all_variants_data.append(product_data)
        
        return all_variants_data if all_variants_data else [extract_current_variant_details(url, pincode)]
        
    except Exception as e:
        print(f"[EXTRACT] ❌ Error in main extraction: {str(e)}")
        import traceback
        traceback.print_exc()
        # Return at least one empty product data
        try:
            return [extract_current_variant_details(url, pincode)]
        except:
            return [{
                'Pin': str(pincode) if pincode else '',
                'Location': '',
                'Dmart_category': '',
                'Dmart_Subcategory': '',
                'Demart_sub_subcategory': '',
                'Manufacturer': '',
                'Product Name': '',
                'Variant': '',
                'MRP': '',
                'Dmart Price': '',
                'save': '',
                'Bulk': 'No',
                'Bulk quantity': '',
                'Marketer': '',
                'overview': '',
                'key features': '',
                'Free': 'N',
                'SKUs': url,
                'Home Delivery': '',
                'Pick Up Point': '',
                'Image Repository': '',
                'Date_Time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'in stock': 'No'
            }]


def test_extract_product_details():
    """Test function to extract product details from a sample URL"""
    chrome_options = Options()
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument('--disable-dev-shm-usage')
    chrome_options.add_argument('--disable-blink-features=AutomationControlled')
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)
    
    driver = webdriver.Chrome(options=chrome_options)
    
    try:
        # Test URL
        test_url = "https://www.dmart.in/product/sabhyata-mandala-design-sw4-07-womens-wallet-(yellow)-pbag0sabh31xx20724?selectedProd=1588526"
        
        print(f"[TEST] Extracting product details from: {test_url}")
        product_data_list = extract_product_details_from_page(driver, test_url, pincode='400001')
        
        print(f"\n[TEST] ========================================")
        print(f"[TEST] Found {len(product_data_list)} variant(s)")
        print(f"[TEST] ========================================")
        for idx, product_data in enumerate(product_data_list):
            print(f"\n[TEST] Variant {idx+1}:")
            for key, value in product_data.items():
                display_value = str(value)
                if len(display_value) > 100:
                    display_value = display_value[:100] + "..."
                print(f"[TEST]   {key}: {display_value}")
        print(f"[TEST] ========================================\n")
        
        return product_data_list
        
    finally:
        driver.quit()


if __name__ == "__main__":
    test_extract_product_details()
