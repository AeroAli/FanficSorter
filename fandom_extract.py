import csv
import json
import os

from bs4 import BeautifulSoup


def get_ff():
    html_doc = "../html/bookmarks.html"
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
    fics = base_ff_folder.find_all_next("a")
    # print(fics)
    for fic in fics:
        get_parent(fic, fandoms)
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


def create_csv_dict(fics):
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

            with open(f"../{folder1}/{key1}.csv", "w", encoding="utf-8") as output_file:
                dict_writer = csv.DictWriter(output_file, keys)
                dict_writer.writeheader()
                dict_writer.writerows(value1)

            stripNewLines(f"../{folder1}/{key1}.csv", f"../{folder}/{key1}.csv")

def stripNewLines(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as inFile, \
            open(output_file, 'w', encoding='utf-8') as outFile:
        for line in inFile:
            if line.strip():
                outFile.write(line)


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


def main():
    # print(json.dumps(get_fics_dict(get_ff()), indent=4))
    links = sort_sites_dict(get_fics_dict(get_ff()))
    create_csv_dict(links)
    with open("fic_dict.json", "w") as j:
        json.dump(links, j, indent=4)


if __name__ == '__main__':
    main()
