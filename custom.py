import time
import json
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def get_ff():
    # print("get_ff")
    html_doc = "bookmarks.html"
    new_html = "fanfiction2.html"
    html_doc = "test.html"
    new_html = "test2.html"
    writing = False
    with open(html_doc, "r", encoding="utf-8") as og, open(new_html, "w", encoding="utf-8") as new:
        # soup = BeautifulSoup(og, "html.parser")
        # for header in soup.find_all("h3"):
        #     print(header)
        for line in og:
            if "Fanfiction<" in line:
                writing = True
            elif ">ff<" in line:
                writing = False
            if writing:
                new.write(line)
    # with open(new_html, "r", encoding="utf-8") as new:
    #     soup2 = BeautifulSoup(new, "html.parser")
    #     for header in soup2.find_all("h3"):
    #         print(header)
    return new_html


def get_fics(html_doc):
    # print("get_fics")
    fic_list = []
    with open(html_doc, "r", encoding="utf-8") as fp:
        soup = BeautifulSoup(fp, "html.parser")
        for header in soup.find_all("h3"):
            header_title = header.text
            # print(header_title)
            if "fanfiction" in header_title.lower():
                # print(header_title)
                dls = header.find_next_sibling("dl")
                for dl in dls:
                    paras = dl.findChildren("p")
                    for para in paras:
                        links = para.findChildren("a")
                        # print(len(links))
                        for link in links:
                            fic_dict = {"title": link.text, "link": link.get("href"),
                                        "site": str(link.get("href")).split("/")[2]}
                            fic_list.append(fic_dict)
    print(len(fic_list), " fics")

    return fic_list


def sort_sites(fic_list):
    # print("sort_sites")
    ao3_fics = []
    ffn_fics = []
    other_fics = []
    other = []
    for fic in fic_list:
        if "arc" in fic["site"].lower():
            ao3_fics.append(fic)
        elif "fan" in fic["site"].lower():
            ffn_fics.append(fic)
        else:
            other_fics.append(fic)
            if fic["site"] not in other:
                # print(fic["site"])
                other.append(fic["site"])
    return ao3_fics, ffn_fics, other_fics


def get_meta(soup, meta_dict):
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

    # print(f"class list:\n\t{class_list}")
    # j_list = json.dumps(meta_dict, indent=4)
    # print(j_list)
    # print(f"meta dict:\n\t{meta_dict}")
    # print("\n\n")
    return meta_dict


def get_fic_r(site, meta_dict):
    # print("get_fic_r")
    try:
        html_text = requests.get(site["link"]).text
        soup = BeautifulSoup(html_text, 'html.parser')
        soup.findChildren()
        get_meta(soup, meta_dict)
    except Exception as e:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("time: ", current_time, "err ", e)
    return meta_dict


def get_res(site, meta_dict, types, error_list):
    # print("get_res")
    response = requests.get(site["link"])
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("time: ", current_time)
    if str(response) not in types:
        types.append(str(response))
    #     print(response)
    # print(response)
    if "429" in str(response):
        print("sleep: ", response.headers["retry-after"])
        print(response.headers)
        # time.sleep(int(response.headers["retry-after"]))
        # get_res(site, meta_dict, types, error_list)
    elif "404" in str(response):
        print("Fic Not Found")
        error_list.append({f"{site['title']}": str(response)})
    # elif "200" not in str(response):
    #     error_list.append({f"{site['title']}": str(response)})
    #     # print(response)
    # elif "200" in str(response):
    #     get_fic_r(site, meta_dict)
    # return meta_dict


def main():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("started at: ", current_time)

    start = time.time()

    meta_list = []

    err_list = []
    res_types = []
    html_file = get_ff()
    fics = get_fics(html_file)
    lists = sort_sites(fics)

    for bookmark in lists:
        for link in bookmark:
            fic_meta = {}
            if "arc" in link["site"] and "/works/" in link["link"]:
                # response = requests.get(link["link"])
                print(link["title"])
                res = get_res(link, fic_meta, res_types, err_list)
                meta_list.append({f"{link['title']}": res})
    end_1 = time.time()
    j_list = json.dumps(meta_list, indent=4)
    print(j_list)
    with open("final.json", "w", encoding="utf-8") as f:
        json.dump(meta_list, f, indent=4)
    with open("json/error_dict.json", "w", encoding="utf-8") as j:
        json.dump(err_list, j, indent=4)
    with open("json/types.json", "w", encoding="utf-8") as k:
        json.dump(res_types, k, indent=4)

    end_2 = time.time()

    time_1 = end_1 - start
    time_2 = end_2 - start

    print(f"Time 1\n\t{time_1},\nTime 2\n\t{time_2}")
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("finished at: ", current_time)


def test():
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("started at: ", current_time)

    meta_list = []

    links = ["https://archiveofourown.org/works/6870118", "https://archiveofourown.org/works/1042274",
             "https://archiveofourown.org/works/1042278"]
    for i in links:
        fic_meta = {}
        try:
            html_text = requests.get(i).text
            soup = BeautifulSoup(html_text, 'html.parser')
            soup.findChildren()
            get_meta(soup, fic_meta)
        except Exception as e:
            now = datetime.now()
            current_time = now.strftime("%H:%M:%S")
            print("time: ", current_time, "err ", e)
        meta_list.append(fic_meta)

    with open("json/test2.json", "w", encoding="utf-8") as f:
        json.dump(meta_list, f, indent=4)
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("finished at: ", current_time)


if __name__ == '__main__':
    test()
    # main()
