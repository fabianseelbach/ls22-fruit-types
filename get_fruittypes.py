#! /bin/env python3

import argparse
import csv
from datetime import datetime
from pprint import pprint
import xml.etree.ElementTree as ET
from math import ceil

def calc_price(per_liter, period_factor, difficulty_factor):
    return ceil(per_liter * 1000 * difficulty_factor * period_factor)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--fruit-types", dest="fruit_fp", help="Fruit Types XML Path", required=True)
    parser.add_argument("--fill-types", dest="fill_fp", help="Fill Types XML Path", required=True)
    parser.add_argument("--output", dest="output", help="Output CSV Path", default="fruits.csv")

    args = parser.parse_args()

    difficulty_factor = 1.8

    print("Loading Fruit Types")
    fruittypes = get_fruittypes(args.fruit_fp)

    print("Loading Fill Types")
    csv_data = get_filltypes(args.fill_fp, fruittypes, difficulty_factor)

    print("Exporting CSV")
    with open("fruits.csv", "w") as csv_file:
        csv_file.truncate()
        writer = csv.DictWriter(csv_file, fieldnames=csv_data[0].keys(), delimiter=";")

        writer.writeheader()
        writer.writerows(csv_data)


def get_fruittypes(filepath):
    xml = ET.parse(filepath)
    fruittypes = xml.find("fruitTypes")

    ret = {}

    for fruittype in fruittypes.findall("fruitType"):
        growth = fruittype.find("growth")
        harvest = fruittype.find("harvest")
        name = fruittype.attrib.get("name").lower()
        regrows = growth.attrib.get("regrows", "false")
        ret.update({name: {"regrows": regrows == "true", "liter": float(harvest.attrib.get("literPerSqm", 0))}})

    return ret

def get_filltypes(filepath, fruittypes, difficulty_factor):
    xml = ET.parse(filepath)

    filltypes = xml.find("fillTypes")

    ret = []

    for filltype in filltypes.findall("fillType"):
        if filltype.attrib.get("showOnPriceTable", "false") == "true":
            name = filltype.attrib.get("name").lower()
            economy = filltype.find("economy")
            price_per_liter = float(economy.attrib.get("pricePerLiter"))
            row = {
                "Name": name.replace("_", " ").capitalize(),
                "Wächst nach": ("Ja" if fruittypes.get(name, {}).get("regrows", False) == True else "Nein"),
                "Liter per Sqm": fruittypes.get(name, {}).get("liter", 0.0)
            }
            factors = economy.find("factors")
            if factors is None:
                for period in range(1,13):
                    month = datetime.strptime(str(period), "%m").strftime("%B")
                    price = calc_price(price_per_liter, 1, difficulty_factor)
                    row.update({month: price})

                best_month = "All"
                best_value = price
            else:
                best_month = None
                best_value = 0
                for factor in factors.findall("factor"):
                    month = datetime.strptime(factor.attrib.get("period"), "%m").strftime("%B")
                    price = calc_price(price_per_liter, float(factor.attrib.get("value")), difficulty_factor)
                    if price > best_value:
                        best_month = month
                        best_value = price
                    row.update({month: price})

            row.update({"Bester Monat": best_month, "Bester Preis": best_value})
            ret.append(row)
    return ret






if __name__ == "__main__":
    main()