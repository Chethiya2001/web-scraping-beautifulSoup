from bs4 import BeautifulSoup
import requests
import json
import queue

walmrt_url = "https://www.walmart.com/ip/LG-24-Inch-Full-HD-IPS-Gaming-Monitor-144Hz-1ms-FreeSync-G-Sync-Compatible-24G41WB/20361372472?adsRedirect=true"

OUTPUT_FILE = "walmart_products.jsonl"

HEADERS ={
    "accept": "*/*",
    "accept-encoding": "gzip, deflate, br, zstd",
    "accept-language": "en-US,en;q=0.9,fr;q=0.8,si;q=0.7",
    "content-type": "application/x-www-form-urlencoded",
    "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36"
}

# List of search queries
search_queries = ["computers", "laptops", "desktops", "monitors", "printers", "hard+drives", "usb", "cords", "cameras", 
                  "mouse", "keyboard", "microphones", "speakers", "radio", "tablets", "android", "apple", "watch", "smart+watch", 
                  "fridge", "airconditioning", "wifi", "router", "modem", "desk", "xbox", "playstation", "nintendo"]

# Initialize a queue for product URLs and a set for seen URLs
product_queue = queue.Queue()
seen_urls = set()

def get_product_links(quary,pageNumber=1):
    search_url = f"https://www.walmart.com/search?q={quary}&page={pageNumber}"
    response = requests.get(search_url, headers=HEADERS)
    soup = BeautifulSoup(response.text, "html.parser")
    links = soup.find_all("a", href=True)
    product_links = []

    for link in links:
        link_href = link["href"]
        if "/ip/" in link_href:
            if "https" in link_href:
                full_url = link_href
            else:
                full_url = "https://www.walmart.com" + link_href
            product_links.append(full_url)
    return product_links

def get_product_info(url):
    response = requests.get(url, headers=HEADERS)

    soup = BeautifulSoup(response.text, "html.parser")

    script_tag = soup.find(
            "script", id="__NEXT_DATA__"
        )


    data = json.loads(script_tag.string)
    initial_data = data["props"]["pageProps"]["initialData"]["data"]
    product_data = initial_data["product"]
    reviews_data = initial_data.get("reviews", {})

    product_info = {
                    "price": product_data["priceInfo"]["currentPrice"]["price"],
                    "review_count": reviews_data.get("totalReviewCount", 0),
                    "item_id": product_data["usItemId"],
                    "avg_rating": reviews_data.get("averageOverallRating", 0),
                    "product_name": product_data["name"],
                    "brand": product_data.get("brand", ""),
                    "availability": product_data["availabilityStatus"],
                    "image_url": product_data["imageInfo"]["thumbnailUrl"],
                    "short_description": product_data.get("shortDescription", "")
                }
    print(product_info)
    return product_info


def main():
    with open(OUTPUT_FILE, 'w') as file:
        while search_queries:
            current_query = search_queries.pop(0)
            print("\n\nCURRENT QUERY", current_query, "\n\n")
            page_number = 1

            while True:
                product_links = get_product_links(current_query, page_number)
                if not product_links or page_number > 99:
                    break

                for link in product_links:
                    if link not in seen_urls:
                        product_queue.put(link)
                        seen_urls.add(link)

                while not product_queue.empty():
                    product_url = product_queue.get()
                    product_info = get_product_info(product_url)
                    if product_info:
                        file.write(json.dumps(product_info) + "\n")

                page_number += 1
                print(page_number)


if __name__ == "__main__":
    main()