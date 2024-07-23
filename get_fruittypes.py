#! /bin/env python3

import argparse
import csv
from datetime import datetime
from pprint import pprint
import xml.etree.ElementTree as ET
from math import ceil
import tempfile
import shutil
import zipfile
import gzip
import os

DIFFICULTIES = {
    "normal": 1.8
}

def calc_price(per_liter, period_factor, difficulty_factor):
    return ceil(per_liter * 1000 * difficulty_factor * period_factor)

def main(temp):
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument("--output", dest="output", help="Output CSV Path", default="fruits.csv")

    diff_parser = argparse.ArgumentParser(add_help=False)
    diff_parser.add_argument("--difficulty", help="Difficulty", choices=DIFFICULTIES.keys(), default="normal")
    
    xml = subparser.add_parser("xml", help="XML Files", parents=[output_parser, diff_parser])
    xml.add_argument("--fruit-types", dest="fruit_fp", help="Fruit Types XML Path", required=True)
    xml.add_argument("--fill-types", dest="fill_fp", help="Fill Types XML Path", required=True)

    zip_parser = subparser.add_parser("zip", help="ZIP File", parents=[output_parser, diff_parser])
    zip_parser.add_argument("--zip-file", dest="zip_fp", help="Map ZIP File", required=True)

    args = parser.parse_args()

    difficulty_factor = DIFFICULTIES.get(args.difficulty, 1)


    try:
        csv_data = get_zip_data(args.zip_fp, temp, difficulty_factor)
    except AttributeError:
        csv_data = get_data(args.fruit_fp, args.fill_fp, difficulty_factor)
        raise 

    print("Exporting CSV")
    with open(args.output, "w") as csv_file:
        csv_file.truncate()
        writer = csv.DictWriter(csv_file, fieldnames=csv_data[0].keys(), delimiter=";")

        writer.writeheader()
        writer.writerows(csv_data)

def get_zip_data(zip, temp, difficulty_factor):
    print("Extracting ZIP")
    with zipfile.ZipFile(zip, "r") as zip_ref:
        zip_ref.extractall(temp)

    fruit_fp = os.path.join(temp, "maps", "maps_fruitTypes.xml")
    fill_fp = os.path.join(temp, "maps", "maps_fillTypes.xml")

    return get_data(fruit_fp, fill_fp, difficulty_factor)

def get_data(fruit_fp, fill_fp, difficulty_factor):
    print("Loading Fruit Types")
    fruittypes = get_fruittypes(fruit_fp)

    print("Loading Fill Types")
    csv_data = get_filltypes(fill_fp, fruittypes, difficulty_factor)
    return csv_data


def get_fruittypes(filepath):
    xml = ET.parse(filepath)
    fruittypes = xml.find("fruitTypes")

    ret = {}

    for fruittype in fruittypes.findall("fruitType"):
        growth = fruittype.find("growth")
        harvest = fruittype.find("harvest")
        windrow = fruittype.find("windrow")
        name = fruittype.attrib.get("name").lower()
        regrows = growth.attrib.get("regrows", "false")

        if windrow is not None:
            straw = windrow.attrib.get("name", "nostraw") == "straw"
        else:
            straw = False

        ret.update({
            name: {
                "regrows": regrows == "true",
                "liter": float(harvest.attrib.get("literPerSqm", 0)),
                "straw": straw
            }
        })

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
            liter_per_sqm = fruittypes.get(name, {}).get("liter", 0.0)
            row = {
                "Name": name.replace("_", " ").capitalize(),
                "Wächst nach": ("Ja" if fruittypes.get(name, {}).get("regrows", False) == True else "Nein"),
                "Stroh": ("Ja" if fruittypes.get(name, {}).get("straw", False) == True else "Nein"),
                "Liter per Sqm": make_float_excel_friendly(liter_per_sqm)
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

            ertrag = liter_per_sqm * best_value / 1000
            row.update({
                "Bester Monat": best_month,
                "Bester Preis": best_value,
                "Ertrag pro sqm": make_float_excel_friendly(ertrag),
                "Ertrag pro ha": make_float_excel_friendly((ertrag * 10000)),
            })
            ret.append(row)
    return ret


def make_float_excel_friendly(value):
    return str(value).replace(".", ",")



if __name__ == "__main__":
    temp = tempfile.mkdtemp()
    try:
        main(temp)
    except Exception as err:
        raise err
    finally:
        shutil.rmtree(temp)