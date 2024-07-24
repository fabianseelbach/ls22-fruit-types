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
from matplotlib import pyplot as plt
import os
from operator import itemgetter
from deep_translator import GoogleTranslator

class LS22Calculator():
    temp = tempfile.mkdtemp()
    data = []

    DIFFICULTIES = {
        "normal": 1.8
    }

    TRANSLATION = {}

    translator = None

    def __init__(self, difficulty, language):
        self.difficulty_factor = self.DIFFICULTIES.get(difficulty, 1)
        self.language = language
        if self.language != "default":
            self.translator = GoogleTranslator(source='auto', target=self.language)


    def calc_price(self, per_liter, period_factor):
        return ceil(per_liter * 1000 * self.difficulty_factor * period_factor)
    
    def make_float_excel_friendly(self, value):
        return str(value).replace(".", ",")

    def translate_table_generate(self):
        if not os.path.exists(self.translation_fp):
            self.translation_fp = None

        if self.translation_fp is None:
            print("Warning: No Translation XML found, will not translate!")
        else:
            xml = ET.parse(self.translation_fp)
            l10n = xml.getroot()
            texts = l10n.find("texts")

            for text in texts.findall("text"):
                name = text.attrib.get("name")
                translation = text.attrib.get("text")
                self.TRANSLATION.update({
                    name: translation,
                    f"${l10n.tag}_{name}": translation
                })

    def translate(self, key, text):
        if key in self.TRANSLATION:
            ret = self.TRANSLATION.get(key)
        elif self.translator is not None:
            ret = self.translator.translate(text=text)
        else:
            ret = text

        return ret


    def get_fruittypes(self, filepath):
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

    def get_filltypes(self, filepath, fruittypes):
        xml = ET.parse(filepath)

        filltypes = xml.find("fillTypes")

        ret = []

        for filltype in filltypes.findall("fillType"):
            if filltype.attrib.get("showOnPriceTable", "false") == "true":
                name = filltype.attrib.get("name").lower()
                economy = filltype.find("economy")
                price_per_liter = float(economy.attrib.get("pricePerLiter"))
                liter_per_sqm = fruittypes.get(name, {}).get("liter", 0.0)

                translation_key = filltype.attrib.get("title", f"fillType_{name}".lower())
                title = self.translate(translation_key, name.replace("_", " ").capitalize())

                row = {
                    "Name": title,
                    "Wächst nach": ("Ja" if fruittypes.get(name, {}).get("regrows", False) == True else "Nein"),
                    "Stroh": ("Ja" if fruittypes.get(name, {}).get("straw", False) == True else "Nein"),
                    "Liter per Sqm": liter_per_sqm,
                }
                factors = economy.find("factors")
                if factors is None:
                    for period in range(1,13):
                        month = datetime.strptime(str(period), "%m").strftime("%B")
                        price = self.calc_price(price_per_liter, 1)
                        row.update({month: price})

                    best_month = "All"
                    best_value = price
                else:
                    best_month = None
                    best_value = 0
                    for factor in factors.findall("factor"):
                        month = datetime.strptime(factor.attrib.get("period"), "%m").strftime("%B")
                        price = self.calc_price(price_per_liter, float(factor.attrib.get("value")))
                        if price > best_value:
                            best_month = month
                            best_value = price
                        row.update({month: price})

                ertrag = liter_per_sqm * best_value / 1000
                row.update({
                    "Bester Monat": best_month,
                    "Bester Preis": best_value,
                    "Ertrag pro sqm": ertrag,
                    "Ertrag pro ha": (ertrag * 10000),
                })
                ret.append(row)
        return ret

    def get_zip_data(self, zip):
        print("Extracting ZIP")
        with zipfile.ZipFile(zip, "r") as zip_ref:
            zip_ref.extractall(self.temp)

        self.fruit_fp = os.path.join(self.temp, "maps", "maps_fruitTypes.xml")
        self.fill_fp = os.path.join(self.temp, "maps", "maps_fillTypes.xml")
        self.translation_fp = os.path.join(self.temp, "translations", f"translation_{self.language}.xml")

        return self.get_data()

    def get_xml_data(self, fruit_fp, fill_fp, translation_fp=None):
        self.fruit_fp = fruit_fp
        self.fill_fp = fill_fp
        self.translation_fp = translation_fp

        return self.get_data()

    def get_data(self):
        print("Loading Translations")
        self.translate_table_generate()

        print("Loading Fruit Types")
        fruittypes = self.get_fruittypes(self.fruit_fp)

        print("Loading Fill Types")
        self.data = self.get_filltypes(self.fill_fp, fruittypes)
    
    def export_graph(self, output):
        name = [i["Name"] for i in sorted(self.data, key=itemgetter("Ertrag pro ha"), reverse=True) if i["Liter per Sqm"] > 0]
        price = [i["Ertrag pro ha"] for i in sorted(self.data, key=itemgetter("Ertrag pro ha"), reverse=True) if i["Liter per Sqm"] > 0]
        # Figure Size
        fig, ax = plt.subplots(figsize =(16, 9))

        # Horizontal Bar Plot
        ax.barh(name, price)

        # Remove axes splines
        for s in ['top', 'bottom', 'left', 'right']:
            ax.spines[s].set_visible(False)

        # Remove x, y Ticks
        ax.xaxis.set_ticks_position('none')
        ax.yaxis.set_ticks_position('none')

        # Add padding between axes and labels
        ax.xaxis.set_tick_params(pad = 5)
        ax.yaxis.set_tick_params(pad = 10)

        # Add x, y gridlines
        ax.grid(color ='grey',
                linestyle ='-.', linewidth = 0.5,
                alpha = 0.2)

        # Show top values 
        ax.invert_yaxis()

        # Add annotation to bars
        for i in ax.patches:
            plt.text(i.get_width()+0.2, i.get_y()+0.5, 
                    f"{ceil(i.get_width())} €",
                    fontsize = 10, fontweight ='bold',
                    color ='grey')

        # Add Plot Title
        ax.set_title('Ertrag pro Hektar [€/ha]',
                    loc ='center', )
        
        # Add Text watermark
        fig.text(0.9, 0.15, 'Nur Annährungswerte', fontsize = 12,
            color ='grey', ha ='right', va ='bottom',
            alpha = 0.7)

        plt.savefig(output)

    def export_csv(self, output):
        print("Exporting CSV")
        rows = []
        for d in self.data:
            for k,v in d.items():
                if isinstance(v, float):
                    d[k] = self.make_float_excel_friendly(v)
            rows.append(d)

        with open(output, "w") as csv_file:
            csv_file.truncate()
            writer = csv.DictWriter(csv_file, fieldnames=rows[0].keys(), delimiter=";")

            writer.writeheader()
            writer.writerows(rows)

    def __del__(self):
        if os.path.exists(self.temp):
            shutil.rmtree(self.temp)

def main():
    args = parse_cmd_args()

    calculator = LS22Calculator(args.difficulty, args.lang)

    if args.run_type == "zip":
        calculator.get_zip_data(args.zip_fp)
    else:
        calculator.get_data(args.fruit_fp, args.fill_fp)

    calculator.export_graph(args.output.replace("csv", "png"))
    calculator.export_csv(args.output)

def parse_cmd_args():
    parser = argparse.ArgumentParser()
    subparser = parser.add_subparsers()

    output_parser = argparse.ArgumentParser(add_help=False)
    output_parser.add_argument("--output", dest="output", help="Output CSV Path", default="fruits.csv")

    diff_parser = argparse.ArgumentParser(add_help=False)
    diff_parser.add_argument("--difficulty", help="Difficulty", choices=LS22Calculator.DIFFICULTIES.keys(), default="normal")
    
    xml = subparser.add_parser("xml", help="XML Files", parents=[output_parser, diff_parser])
    xml.add_argument("--fruit-types", dest="fruit_fp", help="Fruit Types XML Path", required=True)
    xml.add_argument("--fill-types", dest="fill_fp", help="Fill Types XML Path", required=True)
    xml.add_argument("--translation", dest="translation_fp", help="Translation XML Path")

    zip_parser = subparser.add_parser("zip", help="ZIP File", parents=[output_parser, diff_parser])
    zip_parser.add_argument("--zip-file", dest="zip_fp", help="Map ZIP File", required=True)
    zip_parser.add_argument("--lang", help="Language", default="default")
    
    zip_parser.set_defaults(run_type="zip")
    xml.set_defaults(run_type="xml")
    
    
    return parser.parse_args()

if __name__ == "__main__":
    main()