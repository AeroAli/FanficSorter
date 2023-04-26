import asyncio
import csv
import json
import os
import time
from datetime import datetime

from bs4 import BeautifulSoup
import aiofiles
import aiocsv


async def get_ff():
    html_doc = "../html/bookmarks.html"
    new_html = ""
    writing = False
    async with aiofiles.open(html_doc, "r", encoding="utf-8") as og:
        async for line in og:
            if "Fanfiction<" in line:
                writing = True
            elif ">ff<" in line:
                writing = False
            if writing:
                new_html += "\n" + line
    return new_html


async def get_parent(item, fandoms):
    try:
        # print(item.name)
        if item.name != "dl":
            item = item.parent
            await get_parent(item, fandoms)
        else:
            fandom = item.find_previous_sibling("h3").text

            fandom = str(fandom)
            if str(fandom) not in fandoms:
                fandoms.append(fandom)
    except Exception as e:
        print(e)


async def get_fics_dict(html_doc):
    soup = BeautifulSoup(html_doc, "html.parser")

    # Get just the right folder.
    base_ff_folder = soup.find("h3")

    results = {}
    fandoms = []

    # Get all the tags for the fics.
    fics = base_ff_folder.find_all_next("a")
    # print(fics)
    for fic in fics:
        await get_parent(fic, fandoms)
        try:
            w = len(fandoms) + 1
            try:
                x = len(fandoms) - 1
                # print(fandoms[x])
                link = str(fic.get("href"))
                # print(link)
                link = str(link.split("#")[0])
                # print(link)
                if "comment" in link:
                    link = str(link.split("show_comments=true&")[0])+str(link.split("show_comments=true&")[1])
                # print(link)
                if fandoms[x] in results:
                    results[fandoms[x]].append({"title": fic.text, "link": link, "fandom": str(fandoms[x]),
                                                "site": str(link).split("/")[2]})
                else:
                    results[fandoms[x]] = [{"title": fic.text, "link": link, "fandom": str(fandoms[x]),
                                            "site": str(link).split("/")[2]}]
            except Exception as e:
                print(e)
        except Exception as E:
            print(E)

    # print(fandoms)
    # print(results.keys())
    # print(json.dumps(results, indent=4))
    return results


async def create_csv_dict(fics):
    for key, value in fics.items():
        folder = key.replace("/", "_&_")
        folder = folder.replace(" ", "_")
        folder = folder.replace(":", "_")

        if "&" in folder and "0Meta_&_Fandom" not in folder:
            folder = f"Crossovers/{folder}"

        metas = {
            "Marvel": ["agents_of_shield", "avengers", "black_panther", "black_widow", "captain_america",
                       "captain_marvel",
                       "daredevil", "deadpool", "doctor_strange", "hawkeye", "irondad", "loki", "shield", "spiderman",
                       "team_red", "thor", "winter_soldier", "xmen"],
            "DC": ["arrow", "batman", "flash", "green_lantern", "smallvile"],
            "NCIS": ["ncis_la"],
            "CSI": ["csi__la"],
            "Tolkien": ["lord_of_the_rings", "hobbit"],
            "Harry_Potter": ["crack"]
        }

        # print(folder)

        for key1, value1 in metas.items():
            for value2 in value1:
                if value2 in folder.lower() and "&" not in folder.lower():
                    folder = f"{key1}/{folder}"
                    # print(folder)

        folder1 = folder

        folder = f"csv/fandoms/{folder}"
        folder1 = f"csv/blanks/fandoms/{folder1}"

        if "&" in folder or "&" in folder1:
            print(folder)
            print(folder1)

        try:
            current = os.getcwd()
            up = os.path.abspath(os.path.join(current, os.pardir))
            path = os.path.join(up, folder)
            os.makedirs(path)
            path = os.path.join(up, folder1)
            os.makedirs(path)
        except OSError as Er:
            print(Er)

        for key1, value1 in value.items():
            keys = value1[0].keys()
            # print(keys)

            async with aiofiles.open(f"../{folder1}/{key1}.csv", "w", encoding="utf-8") as output_file:
                dict_writer = aiocsv.AsyncDictWriter(output_file, keys)
                await dict_writer.writeheader()
                await dict_writer.writerows(value1)

            await stripNewLines(f"../{folder1}/{key1}.csv", f"../{folder}/{key1}.csv")


async def stripNewLines(input_file, output_file):
    async with aiofiles.open(input_file, 'r', encoding='utf-8') as inFile, \
            aiofiles.open(output_file, 'w', encoding='utf-8') as outFile:
        async for line in inFile:
            if line.strip():
                await outFile.write(line)


async def sort_sites_dict(fics):
    for folder, fandom in fics.items():
        categories = {
            "ao3": [],
            "ffn": [],
            "other": [],
            "not fics": [],
            "authors": [],
            "tags": [],
            "series": [],
            "collections": [],
        }
        for fic in fandom:
            # print(fic)
            print(fic.keys())
            if "arc" in fic["site"].lower():
                if "/works/" in fic["link"].lower():
                    categories["ao3"].append(fic)
                elif "/users/" in fic["link"].lower() or "user_id" in fic["link"].lower():
                    categories["authors"].append(fic)
                elif "/tags/" in fic["link"].lower():
                    categories["tags"].append(fic)
                elif "/series/" in fic["link"].lower():
                    categories["series"].append(fic)
                elif "/collections/" in fic["link"].lower():
                    categories["collections"].append(fic)
                else:
                    categories["not fics"].append(fic)
            elif "fan" in fic["site"].lower():
                if "/s/" in fic["link"].lower():
                    categories["ffn"].append(fic)
                elif "/u/" in fic["link"].lower():
                    categories["authors"].append(fic)
                else:
                    categories["not fics"].append(fic)
            else:
                categories["not fics"].append(fic)

        fics[folder] = {key: value for key, value in categories.items() if len(value) > 0}

    # print(json.dumps(fics, indent=4))
    return fics


async def main():
    start_time = time.time()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")

    async with aiofiles.open("time.txt", "a") as t:
        await t.write(f"\n{now}, ")
    print(now)
    tasks = []
    print("getting fics")
    # fandom_extract.main()
    timings = {
        "start unix time": start_time,
        "start time": current_time
    }
    # print(json.dumps(get_fics_dict(get_ff()), indent=4))
    links = sort_sites_dict(get_fics_dict(get_ff()))
    await create_csv_dict(links)
    async with aiofiles.open("fic_dict.json", "w") as f:
        j = json.dumps(links, indent=4)
        await f.write(j)

    end_time = time.time()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    time_difference = end_time - start_time
    print(f'Scraping time: {time_difference} seconds.')

    timings["end unix time"] = end_time
    timings["end time"] = current_time
    timings["length"] = time_difference
    async with aiofiles.open("time.txt", "a") as t:
        await t.write(f"{now}, {time_difference}")
    async with aiofiles.open("time.json", "w", encoding="utf-8") as f:
        j = json.dumps(timings, indent=4)
        await f.write(j)


asyncio.run(main())


