import pandas as pd
from argparse import ArgumentParser
import asyncio
from ebay_scrapper import EbayScrapper
import operator

output_file = "output.csv"

async def consume_ebay_product_generator(ebay_bot: EbayScrapper, product_name: str, index: int, max_ammount: int = 5):
    top_products = []
    async for product_info in ebay_bot.ebay_get_products_generator(product_name, ebay_bot.choose_proxy()):
        if product_info is not None:
            if len(top_products) < max_ammount:
                top_products.append(product_info)
            else:
                top_products = sorted(top_products, key=lambda k: k["item_price"])
                if  top_products[-1]["item_price"] > product_info["item_price"]:
                    top_products.pop()
                    top_products.append(product_info)
    top_products = sorted(top_products, key=lambda k: k["item_price"])
    return (product_name, index), top_products
            

async def algorhitm_first(products_path: str, ebay_bot: EbayScrapper):
    global output_file
    df = pd.read_csv(products_path)
    product_names = []
    column_names =  ["first_product", "second_product", "third_product", "fourth_product", "fifth_product"]
    for index, row in df.iterrows():
        product_names.append((row['product_name'].replace(" ", "+"), index))
        if len(product_names) == ebay_bot.max_coroutines:
            top_products = await asyncio.gather(
                *[consume_ebay_product_generator(ebay_bot, product_name, index) for product_name, index in product_names]
            )
            for top_product in top_products:
                product_info = top_product[0]
                products = top_product[1]
                for i in range(len(products)):
                    df.at[product_info[1], column_names[i]] = products[i]["item_url"]
            product_names.clear()
    if len(product_names):
        top_products = await asyncio.gather(
                *[consume_ebay_product_generator(ebay_bot, product_name, index) for product_name, index in product_names]
            )
        for top_product in top_products:
            product_info = top_product[0]
            products = top_product[1]
            for i in range(len(products)):
                df.at[product_info[1], column_names[i]] = products[i]["item_url"]
    df.to_csv(output_file)
async def algorhitm_second(products_path: str, ebay_bot: EbayScrapper):
    global output_file
    df = pd.read_csv(products_path)
    product_names = []
    column_names =  ["first_product", "second_product", "third_product", "fourth_product", "fifth_product"]
    for index, row in df.iterrows():
        product_names.append((row['product_name'].replace(" ", "+"), index))
        if len(product_names) == ebay_bot.max_coroutines:
            top_products = await asyncio.gather(
                *[consume_ebay_product_generator(ebay_bot, product_name, index) for product_name, index in product_names]
            )
            
            for top_product in top_products:
                product_info = top_product[0]
                products = top_product[1]
                while len(products) >= 2:
                    if products[0]["item_price"]*2 < products[-1]["item_price"]:
                        products.pop() 
                    else:
                        break
                for i in range(len(products)):
                    df.at[product_info[1], column_names[i]] = products[i]["item_url"]
            product_names.clear()
    if len(product_names):
        top_products = await asyncio.gather(
                *[consume_ebay_product_generator(ebay_bot, product_name, index) for product_name, index in product_names]
            )
        for top_product in top_products:
            product_info = top_product[0]
            products = top_product[1]
            while len(products) >= 2:
                    if products[0]["item_price"]*2 < products[-1]["item_price"]:
                        products.pop() 
                    else:
                        break
            for i in range(len(products)):
                df.at[product_info[1], column_names[i]] = products[i]["item_url"]
    df.to_csv(output_file)

if __name__ == '__main__':
    
    parser = ArgumentParser()
    parser.add_argument("-i", "--input", type=str, help="Path to csv file with containing ebay product keywords", 
                        required=True)
    parser.add_argument("-a2", "--algo_second", action='store_true', help="Second algorhitm of choosing the best products", default=False)
    parser.add_argument("-p", "--proxies_path", type=str, help="Path to csv file containing http proxies", required=False, default=None)
    parser.add_argument("-c", "--coroutines", type=int, help="Maximum ammount of coroutines for searching products concurrently", default=10)
    parser.add_argument("-r", "--refresh_rate", type=int, help="Refresh rate of each coroutine", default= 1.0)
    parser.add_argument("-o", "--output", type=str, help="Path to csv output file", default="output.csv")
    parser.add_argument("-s", "--ship", action='store_true', help="Adds shipping price to full item price", default=False)
    args = parser.parse_args()
    output_file = args.output
    proxies_list = None
    if args.proxies_path:
        pl = []
        with open(args.proxies_path, "r") as file:
            for line in file.readlines():
                pl.append(line)
        if len(pl) != 0:
            proxies_list = pl 
    ebay_bot = EbayScrapper(args.coroutines, proxies_list, refresh_rate=args.refresh_rate, shipping_cost=args.ship)
    if args.algo_second:
        asyncio.run(algorhitm_second(args.input, ebay_bot))
    else:
        asyncio.run(algorhitm_first(args.input, ebay_bot))