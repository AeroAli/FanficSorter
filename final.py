import asyncio
import csv
import time
from datetime import datetime
import json

import extract

import aiohttp as aiohttp
from bs4 import BeautifulSoup


async def get_meta(soup, meta_dict):
    # main div
    div = soup.find("div", {"class": "wrapper", "id": "outer"})

    # meta data
    dl = div.findChild("dl", {"class": "work meta group"})
    meta = dl.findChild("dl")

    # author info
    h3 = div.findChild("h3", {"class": "byline heading"})
    link = h3.findChild("a")

    dd = dl.findChildren("dd")  # tags

    h2 = div.findChild("h2", {"class": "title heading"})  # fic title

    meta_dict["title"] = h2.text.strip()
    meta_dict["Author"] = link.text
    meta_dict["Author Link"] = link.get("href")

    class_list = []
    for child in meta.findChildren():
        try:
            if child["class"][0]:
                if str(child["class"][0]) not in class_list:
                    class_list.append(str(child["class"][0]))
                    # print(child["class"][0])
                else:
                    meta_dict[f"{child['class'][0]}"] = child.text
                    # print(child["class"][0], "\t", child.text)
        except Exception:
            # print(child)
            meta_dict[f"bookmarks"] = child.text
            continue

    for tag in dd:
        # print(child.text)
        if tag.has_attr("class") and tag["class"][0] not in class_list and tag["class"][0] != "stats":
            kid_text = []
            for kid in tag.findChildren("a"):
                # print(kid["class"][0])
                if kid.text != "Next Work →" and kid.text != "← Previous Work":
                    # print(f"\t{kid.text}")
                    if "tag" not in kid.get("href"):
                        kid_text.append([kid.text, kid.get("href")])
                    else:
                        kid_text.append(kid.text)
            meta_dict[f"{tag['class'][0]}"] = kid_text
            if tag["class"][0] == "language":
                # print("\t",tag.text.strip())
                meta_dict[f"{tag['class'][0]}"] = tag.text.strip()

    # print(meta_dict)
    print("meta acquired")


async def scrape(url, meta_dict,err_dict):
    async with aiohttp.ClientSession() as session:
        if "arc" in url and "/works/" in url:
            try:
                print("awaiting soup")
                await asyncio.sleep(0.42069)
                async with session.get(url) as resp:
                    res = resp.status
                    print(res, url)
                    reses = []
                    if res not in reses:
                        reses.append(res)

                    if "429" in str(res):
                        await asyncio.sleep(int(resp.headers["retry-after"]))
                        await scrape(url, meta_dict, err_dict)

                    if "200" in str(res):
                        try:
                            html_text = await resp.text()
                            soup = BeautifulSoup(html_text, 'html.parser')
                            print("soup acquired", url)
                            await get_meta(soup, meta_dict)
                        except Exception as e:
                            await asyncio.sleep(0.5)
                            now = datetime.now()
                            current_time = now.strftime("%H:%M:%S")
                            print("time: ", current_time, "res: ", res, "url: ", url, "err: ", e)
                            try:
                                await asyncio.sleep(0.5)
                                html_text = await resp.text()
                                soup = BeautifulSoup(html_text, 'html.parser')
                                print("soup acquired", url)
                                await get_meta(soup, meta_dict)
                            except Exception as uh:
                                print("time: ", current_time, "res: ", res, "url: ", url, "err: ", uh)
            except Exception as err:
                print(err, url)
                err_dict[url] = [err]
                try:
                    x = 10
                    print(f"sleeping for {x} seconds")
                    await asyncio.sleep(x)
                    await scrape(url, meta_dict, err_dict)
                except Exception as er:
                    print(er, url)
                    err_dict[url] = [err, er]


async def main():
    start_time = time.time()

    # extract.main()

    tasks = []
    with open('../csv/ao3.csv', encoding="utf-8") as file:
        csv_reader = csv.DictReader(file)
        url_num = 0
        meta_list = []
        err_list = []
        for csv_row in csv_reader:
            url_num += + 1
            print(url_num)
            meta_dict = {}
            err_dict = {}
            if url_num % 1000 == 0:
                await asyncio.sleep(5)
                task = asyncio.create_task(scrape(csv_row['link'], meta_dict, err_dict))
                tasks.append(task)
            else:
                meta_dict = {}
                task = asyncio.create_task(scrape(csv_row['link'], meta_dict, err_dict))
                tasks.append(task)
            meta_list.append({csv_row["link"]: meta_dict})
            err_list.append(err_dict)

    print('Saving the output of extracted information')
    await asyncio.gather(*tasks)

    with open("final.json", "w", encoding="utf-8") as f:
        json.dump(meta_list, f, indent=4)
    with open("json/error_dict.json", "w", encoding="utf-8") as j:
        json.dump(err_list, j, indent=4)


    time_difference = time.time() - start_time
    print(f'Scraping time: %.2f seconds.' % time_difference)

asyncio.run(main())
