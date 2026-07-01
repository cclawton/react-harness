import csv
import sys


def normalize(input_path, output_path):
    with open(input_path, newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)

    for row in rows:
        row["category"] = row["category"].strip().lower()
        row["notes"] = row["notes"].strip()
        row["amount"] = "{:.2f}".format(float(row["amount"]))

    with open(output_path, "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    normalize(sys.argv[1], sys.argv[2])
