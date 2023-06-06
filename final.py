import asyncio
import csv
import json
import os
import time
from datetime import datetime

import aiocsv
import aiofiles
import aiohttp as aiohttp
import bs4.element
from bs4 import BeautifulSoup
from markdownify import MarkdownConverter

import fandom_extract


# Create shorthand method for conversion
def md(soup: BeautifulSoup, **options: dict):
    return MarkdownConverter(**options).convert_soup(soup)


async def download_fic(soup: BeautifulSoup, session: aiohttp.ClientSession, fic_id: str):
    halp = soup.find("li", {"class": "download"}).find_all("li")
    for li in halp:
        if "PDF" in li.text:
            url = "https://archiveofourown.org" + li.find("a").get("href")
            async with session.get(url) as resp:
                content = await resp.read()
                async with aiofiles.open(f"../pdf/{fic_id}.pdf", "wb") as f:
                    await f.write(content)


async def get_meta_fic(soup: BeautifulSoup, meta_dict: dict, session: aiohttp.ClientSession, fic_id):
    # main main_div
    main_div = soup.find("div", {"class": "wrapper", "id": "outer"})

    # meta data
    main_meta_block = main_div.find("dl", {"class": "work meta group"})
    meta_block = main_meta_block.find("dl")
    tags_block = main_meta_block.find_all("dd")
    author_block = main_div.find("h3", {"class": "byline heading"})

    fic_title = main_div.find("h2", {"class": "title heading"})  # fic title
    meta_dict["title"] = fic_title.text.strip()

    summary = main_div.find("div", {"class": "summary module"}).find_all("p")
    if summary is not None:
        summary_text = "\n\n".join((md(para) if "<br" in str(para) else para.text) for para in summary)
        meta_dict["Summary"] = summary_text
        meta_dict["sum length"] = len(summary_text)
    else:
        meta_dict["Summary"] = ""
        meta_dict["sum length"] = 0

    # author info
    meta_dict["authors"] = {}
    kount = 0
    if author_block is not None:
        authors = author_block.find_all("a", {"rel": "author"})
        for author in authors:
            meta_dict["authors"][kount] = {}
            author_link = author.get("href")
            author_name = author.text
            if "users" in author_link:
                meta_dict["authors"][kount]["author_name"] = author_name
                meta_dict["authors"][kount]["author_link"] = author_link
            kount += 1

    class_list = []
    child_position = 0
    children = meta_block.find_all()
    for child in children:
        if child.text == children[child_position - 1].text:
            continue
        if child_position % 2 == 0:
            # print(child.text.strip(":").lower())
            if child.text.strip(":").lower() not in class_list:
                class_list.append(child.text.strip(":").lower())
        else:
            if children[child_position - 1].text.strip(":").lower() in class_list:
                meta_dict[children[child_position - 1].text.strip(":").lower()] = child.text
        child_position += 1

    for tag in tags_block:
        if tag.has_attr("class") and tag["class"][0] not in class_list and tag["class"][0] != "stats":
            kid_text = []
            counter = 0
            position = []
            if "part" in str(tag.text).lower():
                series_span = tag.find_all("span", {"class": "position"})
                for span in series_span:
                    position.append(span.text)

            for kid in tag.find_all("a"):
                if kid.text != "Next Work →" and kid.text != "← Previous Work":
                    # print(f"\t{kid.text}")
                    try:
                        if "tag" not in kid.get("href"):
                            kid_text.append([position[counter], kid.text, kid.get("href")])
                            counter += 1
                        else:
                            kid_text.append(kid.text)
                    except Exception as e:
                        print(e)
            # if tag["class"][0] not in longform:
            #     kid_text = kid_text[:3]
            meta_dict[f"{tag['class'][0]}"] = kid_text
            if tag["class"][0] == "language":
                # print("\t",tag.text.strip())
                meta_dict[f"{tag['class'][0]}"] = tag.text.strip()

    meta_dict["fic id"] = fic_id
    # await download_fic(soup, session, fic_id)
    # print(json.dumps(meta_dict, indent=4))
    print("meta acquired fic")

async def get_meta_series(soup: BeautifulSoup, meta_dict: dict):
    # main div
    main_div = soup.find("div", {"class": "wrapper", "id": "outer"})
    series_title = main_div.find("h2").text.strip()
    meta_dict["series title"] = series_title

    series_meta = main_div.find("dl", {"class": "series meta group"})
    if series_meta is not None:
        children_dd = series_meta.find_all("dd")
        children_dt = series_meta.find_all("dt")
        k = 0
        for i in children_dd:
            meta_dict[children_dt[k].text.lower().strip(":")] = i.text
            k += 1
        links = series_meta.find_all("a")
        if links is not None:
            for link in links:
                # print(link)
                if "book" in link.get("href"):
                    series_link = link.get("href").split("bookmarks")[0]
                    if series_link is not None:
                        # print(series_link)
                        meta_dict["series link"] = series_link
    # Series Summary
    series_summary = series_meta.find("blockquote")
    if series_summary is not None:
        series_summary = series_summary.find_all("p")
        series_summary = "\n\n".join([md(child) if "<br" in str(child) else child.text for child in series_summary])
        meta_dict["series summary"] = series_summary
        meta_dict["sum length"] = len(series_summary)
    else:
        meta_dict["series summary"] = ""
        meta_dict["sum length"] = 0

    # series authors
    heading1 = main_div.find("dl", {"class": "series meta group"})
    series_authors = heading1.find_all("a", {"rel": "author"})

    meta_dict["authors"] = {}
    kount = 0
    for author in series_authors:
        meta_dict["authors"][kount] = {}
        author_link = author.get("href")
        author_name = author.text
        if "users" in author_link:
            meta_dict["authors"][kount]["author_name"] = author_name
            meta_dict["authors"][kount]["author_link"] = author_link
            kount += 1

    # series fics
    fics = main_div.find("ul", {"class": "series work index group"}).find_all("li", {"role": "article"})

    meta_dict["fics"] = []
    await get_series_fic_meta(fics, meta_dict)

    # print(json.dumps(meta_dict, indent=4))  # print("meta acquired")
    print("meta acquired series", meta_dict["series link"], meta_dict["series title"])


async def get_series_fic_meta(fics: bs4.element.ResultSet, meta_dict: dict):
    c = 0
    for fic in fics:
        fic_meta = {}

        num = fic.find("ul", {"class": "series"}).find("li").find("strong").text
        fic_meta[num] = {}

        fic_meta[num]["soup"] = str(fic)

        heading = fic.find("div", {"class": "header module"})
        if heading is not None:
            link = heading.find("a").get("href")
            title = heading.find("a").text
            if "works" in link:
                fic_meta[num]["title"] = title
                fic_meta[num]["link"] = link

            authors = heading.find_all("a", {"rel": "author"})
            fic_meta[num]["authors"] = {}
            count = 0
            for author in authors:
                fic_meta[num]["authors"][count] = {}
                author_link = author.get("href")
                author_name = author.text
                if "users" in author_link:
                    fic_meta[num]["authors"][count]["author_name"] = author_name
                    fic_meta[num]["authors"][count]["author_link"] = author_link
                    count += 1

        chapters = fic.find("dd", {"class": "chapters"})
        if chapters is not None:
            fic_meta[num]["chapters"] = chapters.text
            if str(fic_meta[num]["chapters"]).split("/")[0] == str(fic_meta[num]["chapters"]).split("/")[1]:
                fic_meta[num]["complete"] = "Yes"
            else:
                fic_meta[num]["complete"] = "No"

        fic_summary = fic.find_all("blockquote", {"class": "userstuff summary"})
        if fic_summary is not None:
            fic_summary = "\n\n".join([md(child) if "<br" in str(child) else child.text for child in fic_summary])
            fic_meta[num]["fic summary"] = fic_summary
            fic_meta[num]["fic summary len"] = len(fic_summary)
        else:
            meta_dict["fic summary"] = ""
            meta_dict["fic summary len"] = 0

        fandoms = fic.find("h5", {"class": "fandoms heading"})
        if fandoms is not None:
            fic_fandoms = [fandom.text for fandom in fandoms.find_all("a")]
            if len(fic_fandoms) > 0:
                fic_meta[num]["fic fandoms"] = fic_fandoms

        # all tags - warnings, relationships, characters, freeform
        tags = fic.find("ul", {"class": "tags commas"}).find_all("li")
        for tag in tags:
            if tag.has_attr("class"):
                if tag["class"][0] not in fic_meta[num].keys():
                    fic_meta[num][tag["class"][0]] = [tag.text]
                else:
                    fic_meta[num][tag["class"][0]].append(tag.text)

        if len(fic_meta) > 0:
            meta_dict["fics"].append(fic_meta)
        c += 1


async def scrape(url: str, meta_dict: dict, url_num: int, session: aiohttp.ClientSession, slep_len: int):
    meta_dict[url] = {}
    if "arc" in url.lower():
        fic_id = url.split("/")[-1].split("?")[0]
        print(fic_id)
        try:
            await asyncio.sleep(0.42069)
            async with session.get(url) as resp:
                res = resp.status
                if "login?restricted=true" not in str(resp):
                    # print("not res")
                    if "429" in str(res):
                        if slep_len < int(resp.headers['retry-after']):
                            slep_len = int(resp.headers['retry-after'])
                        print(f"\t{url_num} is sleeping for {int(resp.headers['retry-after'])} seconds")
                        await asyncio.sleep(int(resp.headers["retry-after"]))
                        await scrape(url, meta_dict, url_num, session, slep_len)
                    if "200" in str(res):
                        try:
                            html_text = await resp.text()
                            soup = BeautifulSoup(html_text, 'html.parser')
                            if "/works/" in url:
                                await get_meta_fic(soup, meta_dict[url], session, fic_id)
                            if "/series/" in url:
                                await get_meta_series(soup, meta_dict[url])
                            if "/tags/" in url or "/works" in url and "/works/" not in url:
                                await get_fics(soup, meta_dict, url_num, session, slep_len, url)
                        except Exception as e:
                            await asyncio.sleep(0.5)
                            now = datetime.now()
                            current_time = now.strftime("%H:%M:%S")
                            # print("time: ", current_time, "url: ", url, "e: ", e)
                            try:
                                html_text = await resp.text()
                                soup = BeautifulSoup(html_text, 'html.parser')
                                if "/works/" in url:
                                    print("try works")
                                    await get_meta_fic(soup, meta_dict[url], session, fic_id)
                                if "/series/" in url:
                                    print("try series")
                                    await get_meta_series(soup, meta_dict[url])
                                if "/tags/" in url or "/works?" in url:
                                    print("try tags")
                                    await get_fics(soup, meta_dict, url_num, session, slep_len, url)
                            except Exception as uh:
                                now = datetime.now()
                                current_time = now.strftime("%H:%M:%S")
                                # print("time: ", current_time, "url: ", url, "uh: ", uh)
                                if "'NoneType' object has no attribute 'find'" in str(
                                        uh) and "?view_adult=true" not in str(url):
                                    # print(uh)
                                    if "#" not in str(url) and "?" not in str(url):
                                        # print(url)
                                        new_url = str(url) + "?view_adult=true"
                                        await scrape(new_url, meta_dict, url_num, session, slep_len)
                                    elif "#" not in str(url) and "?" in str(url):
                                        # print(url)
                                        new_url = str(url).split("?")[0] + "?view_adult=true&" + str(url).split("?")[1]
                                        await scrape(new_url, meta_dict, url_num, session, slep_len)

                    elif "302" in str(res):
                        meta_dict[url]["Private"] = "yes"
                else:
                    # print("res")
                    meta_dict[url]["Private"] = "yes"
        except Exception as err:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("time: ", current_time, "url: ", url, "err: ", err)


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


async def folders(folder: str):
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
        with aiofiles.open(file, "r", encoding="utf-8") as f, open("keep/old/2/final.json", "r") as j:
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


async def get_fics(soup: BeautifulSoup, meta_dict: dict, url_num: int, reses: list, session: aiohttp.ClientSession,
                   slep_len: int, url: str):
    # run main_div
    print("hi")
    meta_dict[str(url)] = []
    fic_list = soup.find("ol", {"class": "work index group"})
    fics = fic_list.find_all("li", {"role": "article"})
    a = 0
    for fic in fics:
        # print(fic.find("h4", {"class": "heading"}).find("a"))
        # print("aye")
        fic_dict = {}
        fic_dict["authors"] = []
        main_info = fic.find("h4", {"class": "heading"}).find_all("a")
        for link in main_info:
            if "/works/" in link.get("href"):
                fic_dict["title"] = link.text
                fic_dict["fic link"] = link.get("href")
            if "/users/" in link.get("href"):
                author_info = {"link": link.get("href"), "author": link.text}
                fic_dict["authors"].append(author_info)
        summary = fic.find("blockquote", {"class": "userstuff summary"}).find_all("p")
        if summary is not None:
            summary_text = "\n\n".join((md(para) if "<br" in str(para) else para.text) for para in summary)
            fic_dict["Summary"] = summary_text
        else:
            fic_dict["Summary"] = ""
        series_meta = fic.find("dl", {"class": "stats"})
        if series_meta is not None:
            children_dd = series_meta.find_all("dd")
            children_dt = series_meta.find_all("dt")
            k = 0
            for i in children_dd:
                fic_dict[children_dt[k].text.lower().strip(":")] = i.text
                k += 1
        a += 1
        # print(json.dumps(fic_dict, indent=4))
        print(fic_dict["fic link"])
        meta_dict[str(url)].append(fic_dict)
    print(a)
    next_link = soup.find("ol", {"class": "pagination actions", "role": "navigation", "title": "pagination"})
    if next_link is not None or next_link:
        next_link = next_link.find("a", {"rel": "next"}).get("href")
        next_link = "https://archiveofourown.org" + next_link
        try:
            await scrape(next_link, meta_dict, url_num, session, slep_len)
        except Exception as E:
            print(E)


async def main():
    start_time = time.time()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    slep_len = 0
    async with aiofiles.open("time.txt", "a") as t:
        await t.write(f"\n{now}, ")
    print(now)
    tasks = []
    print("getting fics")
    fandom_extract.main()
    timings = {
        "start unix time": start_time,
        "start time": current_time
    }
    stuff = {
        "meta_list": [],
        "res_list": [],
        "url_dict": {}
    }

    url_num = 0
    files = await get_files()

    # for item in files["fandoms"]:
    #     await folders(item)  # TODO: write meta to separate files

    async with aiohttp.ClientSession() as session:
        for item in files["ao3"]:
            j = item.split("csv")
            outfile = j[0] + "json" + j[1].split("ao3")[0] + "meta.json"

            fandom = j[1].split("ao3")[0].split("\\")[-2]
            meta = []
            # print('open is assigned to %r' % open)
            async with aiofiles.open(item, encoding="utf-8") as fic_file:
                csv_reader = aiocsv.AsyncDictReader(fic_file)
                async for csv_row in csv_reader:
                    if "\\" in fandom:
                        metafandom = fandom.split("\\")[0]
                        fandom = fandom.split("\\")[1]
                        fandoms = {metafandom: fandom}
                    else:
                        fandoms = {fandom: ""}

                    stuff["url_dict"][url_num] = [fandom, str(csv_row['link'])]
                    print(url_num)
                    meta_dict = {}
                    err_dict = {str(url_num): {}}

                    task = asyncio.create_task(
                        scrape(csv_row['link'], meta_dict, url_num, session, slep_len)
                    )

                    tasks.append(task)

                    err_dict[str(url_num)]["url"] = csv_row["link"]
                    stuff["meta_list"].append({str(url_num): [{"fandoms": fandoms}, meta_dict]})
                    stuff["err_list"].append(err_dict)
                    meta.append({str(url_num): meta_dict})

                    url_num += + 1

            async with aiofiles.open(outfile, "w") as f:
                j = json.dumps(meta, indent=4)
                await f.write(j)

        print('Saving the output of extracted information')
        await asyncio.gather(*tasks)
        print(slep_len)

    async with aiofiles.open("stuff.json", "w", encoding="utf-8") as f:
        j = json.dumps(stuff, indent=4)
        await f.write(j)

    async with aiofiles.open("final.json", "w", encoding="utf-8") as f:
        j = json.dumps(stuff["meta_list"], indent=4)
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


async def test():
    start_time = time.time()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    slep_len = 0
    print(now)

    url_num = 0

    async with aiohttp.ClientSession() as session:
        link = "https://archiveofourown.org/works/38372884/chapters/95888881"
        meta_dict = {}
        try:
            await scrape(link, meta_dict, url_num, session, slep_len)
        except Exception as e:
            print(e)
        async with aiofiles.open("final_tag.json", "w", encoding="utf-8") as f:
            j = json.dumps(meta_dict, indent=4)
            await f.write(j)

    end_time = time.time()
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    time_difference = end_time - start_time
    print(f'Scraping time: {time_difference} seconds.')


asyncio.run(main())
# asyncio.run(test())
