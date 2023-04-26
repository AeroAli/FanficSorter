import asyncio
import aiofiles
import csv
import json
import os
import time
from datetime import datetime

import aiohttp as aiohttp
from bs4 import BeautifulSoup

import fandom_extract


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
        except Exception as err:
            # print(child)
            # print(err)
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
    # print("meta acquired")


async def scrape(url, meta_dict, err_dict, url_num, reses):
    meta_dict[url] = {}
    meta = meta_dict[url]
    async with aiohttp.ClientSession() as session:
        if "arc" in url and "/works/" in url:
            try:
                print("awaiting soup ", url_num)
                await asyncio.sleep(0.42069)
                async with session.get(url) as resp:
                    res = resp.status
                    err_dict[str(url_num)]["res"] = str(res)
                    err_dict[str(url_num)]["resp"] = str(resp)
                    if res not in reses:
                        reses.append(res)
                    if "login?restricted=true" not in str(resp):
                        if "429" in str(res):
                            print(f"st{(url_num)} sleeping for {int(resp.headers['retry-after'])} seconds")
                            await asyncio.sleep(int(resp.headers["retry-after"]))
                            await scrape(url, meta_dict, err_dict, url_num, reses)

                        if "200" in str(res):
                            try:
                                html_text = await resp.text()
                                soup = BeautifulSoup(html_text, 'html.parser')
                                # print("soup acquired")  # , url)
                                await get_meta(soup, meta)
                            except Exception as e:
                                await asyncio.sleep(0.5)
                                now = datetime.now()
                                current_time = now.strftime("%H:%M:%S")
                                print("url num: ", url_num, "time: ", current_time, "url: ", url, "err: ", e)
                                try:
                                    x = 10
                                    print(f"sleeping for {x} seconds")
                                    await asyncio.sleep(x)
                                    html_text = await resp.text()
                                    soup = BeautifulSoup(html_text, 'html.parser')
                                    # print("soup acquired", url)
                                    await get_meta(soup, meta)

                                    err_dict[str(url_num)]["e"] = str(e)
                                except Exception as uh:
                                    print("url num: ", url_num, "time: ", current_time, "url: ", url, "err: ", uh)
                                    err_dict[str(url_num)]["uh"] = str(uh)
                                    # print(err_dict)
                                    if str(uh) == "'NoneType' object has no attribute 'findChild'" and "?view_adult=true" not in str(
                                            url):
                                        if "#" not in str(url) and "?" not in str(url):
                                            url = str(url) + "?view_adult=true"
                                        elif "#" not in str(url) and "?" in str(url):
                                            url = str(url).split("?")[0] + "?view_adult=true&" + str(url).split("?")[1]
                                        await scrape(url, meta_dict, err_dict, url_num, reses)

                    else:
                        meta["Private"] = "yes"
                        err_dict["Private"] = "yes"
            except Exception as err:
                # print(err, url)
                err_dict[str(url_num)]['err'] = str(err)
                # print(err_dict)
                try:
                    x = 10
                    print(f"sleeping for {x} seconds")
                    await asyncio.sleep(x)
                    await scrape(url, meta_dict, err_dict, url_num, reses)
                except Exception as er:
                    print(er, url)
                    err_dict[str(url_num)]["err"] = str(err)
                    err_dict[str(url_num)]["er"] = str(er)


async def get_files():
    files = {
        "ao3": [],
        "fandoms": []
    }
    try:
        current = os.getcwd()
        up = os.path.abspath(os.path.join(current, os.pardir))
        # print(current)
        # print(up)
        mypath = os.path.join(up, "csv\\fandoms")
        for (dirpath, dirnames, filenames) in os.walk(mypath):
            fandom = str(dirpath).split("fandoms\\")[-1]
            # print(fandom)
            files["fandoms"].append(fandom)
            for file in filenames:
                # print(os.path.join(dirpath, file))
                if "ao3" in file:
                    files["ao3"].append(os.path.join(dirpath, file))
        # print(ao3)
    except OSError as Er:
        print(Er)
    return files


async def get_files_dict():
    files = {
        "ao3": [],
        "fandoms": []
    }
    try:
        current = os.getcwd()
        up = os.path.abspath(os.path.join(current, os.pardir))
        # print(current)
        # print(up)
        mypath = os.path.join(up, "csv\\fandoms")
        for (dirpath, dirnames, filenames) in os.walk(mypath):
            fandom = str(dirpath).split("fandoms\\")[-1]
            # print(fandom)
            files["fandoms"].append(fandom)
            for file in filenames:
                # print(os.path.join(dirpath, file))
                if "ao3" in file:
                    files["ao3"].append([f"{fandom}", (os.path.join(dirpath, file))])

        print(json.dumps(files["ao3"], indent=4))
    except OSError as Er:
        print(Er)
    return files


async def folders(folder):
    try:
        folder = f"json\\fandoms\\{folder}"
        current = os.getcwd()
        up = os.path.abspath(os.path.join(current, os.pardir))
        try:
            path = os.path.join(up, folder)
            os.makedirs(path)
        except OSError as Err:
            print(Err, "err")
    except OSError as Er:
        print(Er)


async def private():
    files = await get_files()
    priv = []
    for file in files["ao3"]:
        with open(file, "r", encoding="utf-8") as f, open("keep/old/2/final.json", "r") as j:
            myreader = csv.DictReader(f)
            d = json.load(j)
            for row in myreader:
                l = 0
                for i in d:
                    for v in i.values():
                        for k1, v2 in v.items():
                            for k in v2.keys():
                                if "Private" in k:
                                    l += 1
                                    if row["link"] == k1:
                                        print(row["title"])
                                        priv.append(row)
    print(l)
    return priv


async def main():
    start_time = time.time()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    # with open("time.txt", "a") as t:
    #     t.write(f"\n{now}, ")
    print(now)
    tasks = []
    print("getting fics")
    # fandom_extract.main()
    timings = {
        "start unix time": start_time,
        "start time": current_time
    }
    stuff = {
        "meta_list": [],
        "err_list": [],
        "res_list": [],
        "url_dict": {}
    }

    url_num = 0
    files = await get_files()

    for item in files["ao3"]:
        # print(item)
        j = item.split("csv")
        outfile = j[0] + "json" + j[1].split("ao3")[0] + "meta.json"
        print(outfile)
        fandom = outfile[52:-10]
        print(fandom)
        # await folders(fandom)
        # TODO: write meta to separate files

        meta = []
        with open(item, encoding="utf-8") as fic_file:
            csv_reader = csv.DictReader(fic_file)
            for csv_row in csv_reader:
                stuff["url_dict"][url_num] = str(csv_row['link'])
                print(url_num)
                meta_dict = {}
                err_dict = {str(url_num): {}}

                task = asyncio.create_task(
                    scrape(csv_row['link'], meta_dict, err_dict, url_num, stuff["res_list"])
                )

                tasks.append(task)
                if "\\" in fandom:
                    metafandom = fandom.split("\\")[0]
                    fandom = fandom.split("\\")[1]
                else:
                    metafandom = ""
                fandoms = {metafandom: fandom}
                err_dict[str(url_num)]["url"] = csv_row["link"]
                stuff["meta_list"].append({str(url_num): [{"fandoms":fandoms}, meta_dict]})
                stuff["err_list"].append(err_dict)
                meta.append({str(url_num): meta_dict})

                url_num += 1

        # async with aiofiles.open(outfile, "w") as f:
        #     j = json.dumps(meta, indent=4)
        #     await f.write(j)

    # print('Saving the output of extracted information')
    await asyncio.gather(*tasks)
    # # print(meta)
    with open("stuff.json", "w", encoding="utf-8") as f:
        json.dump(stuff, f, indent=4)

    with open("final.json", "w", encoding="utf-8") as f:
        json.dump(stuff["meta_list"], f, indent=4)
    with open("error_dict.json", "w", encoding="utf-8") as j:
        json.dump(stuff["err_list"], j, indent=4)
    with open("res.json", "w", encoding="utf-8") as j:
        json.dump(stuff["res_list"], j, indent=4)

    end_time = time.time()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    time_difference = end_time - start_time
    print(f'Scraping time: {time_difference} seconds.')

    # timings["end unix time"] = end_time
    # timings["end time"] = current_time
    # timings["length"] = time_difference
    # with open("time.txt", "a") as t:
    #     t.write(f"{now}, {time_difference}")
    # with open("time.json", "w", encoding="utf-8") as j:
    #     json.dump(timings, j, indent=4)


async def get_structure():
    with open("final.json", "r") as j:
        meta_from_file = json.load(j)
        fandoms = {}
        i = 0
        for value in meta_from_file:
            # if i == 0:
            #     print(json.dumps(value, indent=4))
            # i += 1
            for key1, value1 in value.items():
                print(key1+":")
                for value2 in value1:
                    if type(value2) is str:
                        print(f"\t Fandom: {value2}")
                        value2_s = str(value2)
                        if value2_s not in fandoms.keys():
                            fandoms[value2_s] = [value]
                        if value2_s in fandoms.keys():
                            if value not in fandoms[value2_s]:
                                fandoms[value2_s].append(value)
                    # elif type(value2) is dict:
                    #     for key3, value3 in value2.items():
                    #         print("\t",key3)
                    #         for key4, value4 in value3.items():
                    #             print("\t\t", key4+":")
                    #             if type(value4) is str:
                    #                 print("\t\t\t", value4)
                    #             elif type(value4) is list:
                    #                 for value5 in value4:
                    #                     if type(value5) is str:
                    #                         print("\t\t\t", value5)
                    #                     elif type(value5) is list:
                    #                         for value6 in value5:
                    #                             print("\t\t\t\t", value6)
                    # else:
                    #     print(type(value2))
            # with open("ich_weiss_nict.json", "w") as j:
            #     json.dump(fandoms, j, indent=4)
    # for key, value in fandoms.items():
    #     print(key)
    #     for value1 in value:
    #         for key1 in value1.values():
    #             print(json.dumps(key1, indent=4))
    with open("ich_weiss_nict.json", "r") as j:
        fandoms = json.load(j)
        for key, value in fandoms.items():
            k = {}
            print(key)
            for item in value:
                for value2 in item.values():
                    for item1 in value2:
                        if type(item1) is str:
                            # print(item1)
                            value2.remove(item1)
                        else:
                            continue
                k.update(item)
            # print(json.dumps(k, indent=4))
            fandoms[key] = k
            if "\\" in key:
                y = key.split("\\")
                print(y[0])
                print(y[1])
                # fandoms[y[0]]
        # print(json.dumps(fandoms, indent=4))
        with open("help_me.json", "w") as f:
            json.dump(fandoms, f, indent=4)

asyncio.run(main())
# asyncio.run(get_structure())
