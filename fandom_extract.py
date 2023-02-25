import csv
import json

from bs4 import BeautifulSoup


def get_ff():
    # print("get_ff")
    html_doc = "../html/bookmarks.html"
    # html_doc = "../html/test.html"
    new_html = ""
    writing = False
    with open(html_doc, "r", encoding="utf-8") as og:
        for line in og:
            if "Fanfiction<" in line:
                writing = True
            elif ">ff<" in line:
                writing = False
            if writing:
                new_html += "\n" + line
    return new_html


def get_parent(item, fandoms):
    try:
        # print(item.name)
        if item.name != "dl":
            item = item.parent
            get_parent(item, fandoms)
        else:
            fandom = item.find_previous_sibling("h3").text

            fandom = str(fandom)
            if str(fandom) not in fandoms:
                fandoms.append(fandom)
    except Exception as e:
        print(e)


def get_fics_dict(html_doc):
    soup = BeautifulSoup(html_doc, "html.parser")

    # Get just the right folder.
    base_ff_folder = soup.find("h3")

    results = {}
    fandoms = []

    # Get all the tags for the fics.
    links = base_ff_folder.find_all_next("a")
    # print(links)
    for link in links:

        get_parent(link, fandoms)
        try:
            w = len(fandoms) + 1
            try:
                x = len(fandoms) - 1
                # print(fandoms[x])
                if fandoms[x] in results:
                    results[fandoms[x]].append({"title": link.text, "link": link.get("href"), "fandom": str(fandoms[x]),
                                                "site": str(link.get("href")).split("/")[2]})
                else:
                    results[fandoms[x]] = [{"title": link.text, "link": link.get("href"), "fandom": str(fandoms[x]),
                                            "site": str(link.get("href")).split("/")[2]}]
            except Exception as e:
                print(e)
        except Exception as E:
            print(E)

    # print(fandoms)
    # print(results.keys())
    # print(json.dumps(results, indent=4))
    return results



def create_csv_dict(fics):
    # TODO: convert to using dict

    folder = fics.keys()
    keys = fics[1].keys()

    with open(f"../csv/blanks/{fics[0]}1.csv", "w", encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        print(fics[0])
        print(keys)
        dict_writer.writerows(fics[1:])

    stripNewLines(f"../csv/blanks/{fics[0]}1.csv", f"../csv/{fics[0]}1.csv")


def stripNewLines(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as inFile, \
            open(output_file, 'w', encoding='utf-8') as outFile:
        for line in inFile:
            if line.strip():
                outFile.write(line)


def sort_sites_list(fic_list):
    ao3_fics = ["ao3"]
    ffn_fics = ["ffn"]
    other_fics = ["other"]
    other = ["not fics"]

    for fic in fic_list:
        if "arc" in fic["link"].lower() and "works" in fic["link"].lower():
            ao3_fics.append(fic)
        elif "fan" in fic["link"].lower() and "/s/" in fic["link"].lower():
            ffn_fics.append(fic)
        else:
            other_fics.append(fic)
            if fic["link"] not in other:
                other.append(fic["link"])
    return ao3_fics, ffn_fics, other_fics


def sort_sites_dict(fics):
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


def main():
    # print(json.dumps(get_fics_dict(get_ff()), indent=4))
    links = sort_sites_dict(get_fics_dict(get_ff()))
    with open("fic_disct.json", "w") as j:
        json.dump(links, j, indent=4)


if __name__ == '__main__':
    main()
