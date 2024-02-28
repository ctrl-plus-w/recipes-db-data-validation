# from sentence_transformers import SentenceTransformer, util
#
# model = SentenceTransformer("all-MiniLM-L6-v2")
#
# sentences = [
#     "A man is eating food.",
#     "A man is eating a piece of bread.",
#     "The girl is carrying a baby.",
#     "A man is riding a horse.",
#     "A woman is playing violin.",
#     "Two men pushed carts through the woods.",
#     "A man is riding a white horse on an enclosed ground.",
#     "A monkey is playing drums.",
#     "Someone in a gorilla costume is playing a set of drums.",
# ]
#
# # Encode all sentences
# embeddings = model.encode(sentences)
#
# # Compute cosine similarity between all pairs
# cos_sim = util.cos_sim(embeddings, embeddings)
#
# # Add all pairs to a list with their cosine similarity score
# all_sentence_combinations = []
# for i in range(len(cos_sim) - 1):
#     for j in range(i + 1, len(cos_sim)):
#         all_sentence_combinations.append([cos_sim[i][j], i, j])
#
# # Sort list by the highest cosine similarity score
# all_sentence_combinations = sorted(all_sentence_combinations, key=lambda x: x[0], reverse=True)
# print(all_sentence_combinations)
#
# print("Top-5 most similar pairs:")
# for score, i, j in all_sentence_combinations[0:5]:
#     print("{} \t {} \t {:.4f}".format(sentences[i], sentences[j], cos_sim[i][j]))

import csv
import argparse
import xlsxwriter
import re

from sentence_transformers import SentenceTransformer, util
from datetime import datetime


class Ingredient:
    uuid: str
    name: str
    shelf_life: int
    opened_shelf_life: int
    created_at: datetime

    def __init__(self, uuid: str, name: str, shelf_life: int, opened_shelf_life: int, created_at: datetime):
        self.uuid = uuid
        self.name = name
        self.shelf_life = shelf_life
        self.opened_shelf_life = opened_shelf_life
        self.created_at = created_at

    def __str__(self):
        return str({"id": self.uuid, "name": self.name, "shelf_life": self.shelf_life,
                    "opened_shelf_life": self.opened_shelf_life, "created_at": self.created_at.isoformat()})


def int_or_none(val):
    try:
        return int(val)
    except ValueError:
        return None


def get_ingredients(filename: str):
    ingredients = []

    with open(filename, newline='') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=",")

        for row in reader:
            ingredient = Ingredient(row["id"], row["name"], int_or_none(row["shelf_life"]),
                                    int_or_none(row["opened_shelf_life"]), datetime.fromisoformat(row["created_at"]))
            ingredients.append(ingredient)

    return ingredients


def main():
    # Arg parser for the CLI
    parser = argparse.ArgumentParser(
        prog='Ingredients data validation program',
        description='Inputs a csv file of the ingredients row and output and excel file summarizing the analysed rows.'
    )
    parser.add_argument('filename')
    args = parser.parse_args()

    # Get the ingredients as class instances from the filename
    ingredients = get_ingredients(args.filename)
    names = list(map(lambda ingredient: ingredient.name, ingredients))
    print(f"Retrieved {len(ingredients)} from the file ({args.filename}).")

    # Generate the Excel filename
    date_prefix = re.sub(r'-|:|T', '_', datetime.now().isoformat().split('.')[0])
    ext = 'xlsx'
    excel_filename = f'{date_prefix}_INGREDIENTS_DATA_VALIDATION.{ext}'
    print(f"Creating Excel workbook with name '{excel_filename}'")

    # Create the workbook
    workbook = xlsxwriter.Workbook(excel_filename)
    worksheet = workbook.add_worksheet()

    border_format = workbook.add_format({"border": 1})

    worksheet.write(0, 0, 0, border_format)

    # Initialise the columns and rows headers
    for i in range(len(names) - 1):
        worksheet.write(0, i + 1, names[i + 1], border_format)
        worksheet.write(i + 1, i, names[i], border_format)

    print("Initialized the columns and rows headers.")

    # Initialise the text embedding model
    model = SentenceTransformer("all-MiniLM-L6-v2")
    embeddings = model.encode(names)
    print("Encoded the names.")
    cos_sim = util.cos_sim(embeddings, embeddings)
    print("Calculating the cosinus similarities.")

    # Fill the similarity values
    for i in range(len(cos_sim) - 1):
        for j in range(i + 1, len(cos_sim)):
            worksheet.write_number(i + 1, j, round(cos_sim[i][j].item(), 2), border_format)
    print("Filling the similarity values into the sheet.")

    # Add the conditional rendering
    worksheet.conditional_format(1, 1, len(names) - 1, len(names) - 1, {
        'type': '3_color_scale',
        'min_color': "green",
        'mid_color': "yellow",
        'max_color': "red",
        'mid_type': "num"
    })
    print("Added the conditional rendering.")

    worksheet.autofit()
    workbook.close()
    print("Finished. Created the worksheet.")


if __name__ == '__main__':
    main()
