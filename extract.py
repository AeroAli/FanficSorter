import csv
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


def get_fics(html_doc):
    fic_list = []
    soup = BeautifulSoup(html_doc, "html.parser")
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


def create_csv(fics):
    keys = fics[1].keys()

    with open(f"../csv/blanks/{fics[0]}.csv", "w", encoding="utf-8") as output_file:
        dict_writer = csv.DictWriter(output_file, keys)
        dict_writer.writeheader()
        print(fics[0])
        print(keys)
        dict_writer.writerows(fics[1:])

    stripNewLines(f"../csv/blanks/{fics[0]}.csv", f"../csv/{fics[0]}.csv")


def stripNewLines(input_file, output_file):
    with open(input_file, 'r', encoding='utf-8') as inFile, \
            open(output_file, 'w', encoding='utf-8') as outFile:
        for line in inFile:
            if line.strip():
                outFile.write(line)


def sort_sites(fic_list):
    ao3_fics = ["ao3"]
    ffn_fics = ["ffn"]
    other_fics = ["other"]
    other = ["not fics"]

    for fic in fic_list:
        if "arc" in fic["site"].lower():
            ao3_fics.append(fic)
        elif "fan" in fic["site"].lower():
            ffn_fics.append(fic)
        else:
            other_fics.append(fic)
            if fic["site"] not in other:
                other.append(fic["site"])
    return ao3_fics, ffn_fics, other_fics


def main():
    links = sort_sites(get_fics(get_ff()))
    [create_csv(link) for link in links if len(link) > 1]


if __name__ == '__main__':
    main()
