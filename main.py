"""
To install all requirements use `pip3 install -r requirements.txt`

Here in this project we will be working with google maps 
scraping 
name , phone number, address, website of the given search and location
"""

import pandas as pd
from playwright.sync_api import sync_playwright # for browser automation
import openpyxl # for creating excel file
from dataclasses import dataclass, asdict, field
import argparse #cli tool

# we are using chromium as our automating browser `playwright install chromium`

@dataclass #Dataclasses are python classes, but are suited for storing data objects
class Business:
    name: str = None
    address: str = None
    website: str = None
    phoneNumber: str = None
    reviews_count: int = None
    reviews_average: float = None

@dataclass
class BusinessList:
    business_list: list[Business] = field(default_factory=list)

    def dataframe(self):
        return pd.json_normalize((asdict(business) for business in self.business_list), sep="_")

        """pandas.json_normalize(data, record_path=None, meta=None, meta_prefix=None, 
        record_prefix=None, errors='raise', sep='.', max_level=None)"""
        # Normalize semi-structured JSON data into a flat table.
    
    def save_to_excel(self, filename):
        self.dataframe().to_excel(f'{filename}.xlsx', index=False)
    
    def save_to_csv(self, filename):
        self.dataframe().to_csv(f'{filename}.csv', index=False)


def main():
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        page = browser.new_page()

        page.goto("https://www.google.com/maps", timeout=60000)
        page.wait_for_timeout(5000)

        page.locator('//input[@id="searchboxinput"]').fill(search_for)
        page.wait_for_timeout(5000)

        page.keyboard.press('Enter')
        page.wait_for_timeout(5000)

        page.hover('(//a[contains(@href, "https://www.google.com/maps/place")])[1]')

        while True:
            page.mouse.wheel(0, 10000)
            page.wait_for_timeout(3000)
            if page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count() >= total:
                listings = page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').all()[:total]
                print(f'Total scrapped {len(listings)}')
                break
            else:
                print(f'Currently scrapped: ', page.locator('//a[contains(@href, "https://www.google.com/maps/place")]').count())
        

        business_list = BusinessList()

        for listing in listings[:total]:
            listing.click()
            page.wait_for_timeout(5000)

            name_xpath = '//h1[contains(@class, "DUwDvf lfPIob")]'
            address_xpath = '//button[@data-item-id="address"]//div[contains(@class, "fontBodyMedium")]'
            website_xpath = '//a[@data-item-id="authority"]//div[contains(@class, "fontBodyMedium")]'
            phone_number_xpath = '//button[contains(@data-item-id, "phone:tel:")]//div[contains(@class, "fontBodyMedium")]'
            reviews_xpath = '//span[@role="img"]'
            try:
                business = Business()

                if page.locator(name_xpath).count() > 0:
                    business.name = page.locator(name_xpath).inner_text()
                else:
                    business.name = ''

                if page.locator(address_xpath).count() > 0:
                    business.address = page.locator(address_xpath).inner_text()
                else:
                    business.address = ''

                if page.locator(website_xpath).count() > 0:
                    business.website = page.locator(website_xpath).inner_text()
                else:
                    business.website = ''

                if page.locator(phone_number_xpath).count() > 0:
                    business.phoneNumber = page.locator(phone_number_xpath).inner_text()
                else:
                    business.phoneNumber = ''

                if page.locator(reviews_xpath).count() > 0:
                    business.reviews_average = float(
                        page.locator(reviews_xpath).all()[0]
                        .get_attribute("aria-label")
                        .split()[0]
                        .replace(",", ".")
                        .strip()
                    )
# strip() method used to remove extra whitespaces and specified characters 
# from the start and from the end of the strip irrespective of how the parameter is passed.
                    business.reviews_count = int(
                        page.locator(reviews_xpath).all()[0]
                        .get_attribute("aria-label")
                        .split()[2]
                        .replace(',','')
                        .strip()
                    )
                else:
                    business.reviews_average = ""
                    business.reviews_count = ""
                
                business_list.business_list.append(business)
            except:
                print("cannot get full info")
                
        business_list.save_to_csv('google_maps_data')
        business_list.save_to_excel('google_maps_data')
        browser.close()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-s', '--search', type=str, required=True)
    parser.add_argument('-l', '--location', type=str, required=False)
    parser.add_argument('-t', '--total', type=int, default=5, required=False)
    args = parser.parse_args()

    if args.location and args.search:
        search_for = f'{args.search} {args.location}'
    else:
        search_for = 'colleges srinagar'
    if args.total:
        total = args.total
    main()

