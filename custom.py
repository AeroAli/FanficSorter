import time
import json
import math
from datetime import datetime

import requests
from bs4 import BeautifulSoup


def get_ff():
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
                            fic_dict = {"title": link.text, "link": link.get("href"), "site": str(link.get("href")).split("/")[2]}
                            fic_list.append(fic_dict)
    print(len(fic_list))

    return fic_list


def sort_sites(fic_list):
    ao3_fics = []
    ffn_fics = []
    other_fics =[]
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
    div1 = soup.find("div", {"class": "wrapper", "id": "outer"})
    div2 = div1.findChild("div", {"class": "wrapper", "id": "inner"})
    div3 = div2.findChild("div", {"class": "works-show region", "id": "main"})
    div4 = div3.findChild("div", {"class": "wrapper"})
    dl = div4.findChild("dl", {"class": "work meta group"})
    meta = dl.findChild("dl")
    class_list = []
    for child in meta.findChildren():
        try:
            if child["class"][0]:
                if str(child["class"][0]) not in class_list:
                    class_list.append(str(child["class"][0]))
                    # print(child["class"][0])
                else:
                    meta_dict[f"{child['class'][0]}"] = child.text
        except Exception:
            # print(child)
            meta_dict[f"bookmarks"] = child.text
            continue
    # print(meta_dict)
    return meta_dict


def get_fic_r(site, meta_dict):
    try:
        html_text = requests.get(site["link"]).text
        soup = BeautifulSoup(html_text, 'html.parser')
        soup.findChildren()
        get_meta(soup, meta_dict)
    except Exception as e:
        now = datetime.now()
        current_time = now.strftime("%H:%M:%S")
        print("time: ", current_time,"err", e)
    return meta_dict


def get_res(site,  meta_dict, types, error_list):
    response = requests.get(site["link"])
    now = datetime.now()
    current_time = now.strftime("%H:%M:%S")
    print("time: ", current_time)
    if response not in types:
        types.append(response)
        print(response)
    if "429" in str(response):
        print("sleep: ", response.headers["retry-after"])
        time.sleep(int(response.headers["retry-after"]))
        error_list.append(str(response))
        get_res(site,  meta_dict, types, error_list)
    elif "404" in str(response):
        print("Fic Not Found")
        error_list.append(str(response))
    elif "200" not in str(response):
        error_list.append(str(response))
        print(response)
    elif "200" in str(response):
        get_fic_r(site, meta_dict)
    return meta_dict



if __name__ == '__main__':
    meta_list = []
    fic_meta = {}
    authors = []
    err_list = []
    err_types = []
    html_file = get_ff()
    fics = get_fics(html_file)
    lists = sort_sites(fics)
    for bookmark in lists:
        for link in bookmark:
            if "arc" in link["site"] and "/works/" in link["link"]:
                # response = requests.get(link["link"])
                print(link["title"])
                res = get_res(link, fic_meta, err_types, err_list)
                meta_list.append(res)

    with open("test.txt", "w", encoding="utf-8") as f:
        json.dump(meta_list, f)
    with open("error_dict.txt", "w", encoding="utf-8") as j:
        j.writelines(err_list)
    with open("errors.txt", "w", encoding="utf-8") as k:
        k.writelines(err_types)
