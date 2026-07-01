import csv
import sys


def normalize_row(row):
    return {
        "date": row["date"],
        "product": row["product"],
        "amount": f"{float(row['amount']):.2f}",
        "category": row["category"].strip().lower(),
        "notes": row["notes"].strip(),
    }


def main():
    input_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(input_path, newline="") as infile:
        reader = csv.DictReader(infile)
        fieldnames = reader.fieldnames
        rows = [normalize_row(row) for row in reader]

    with open(output_path, "w", newline="") as outfile:
        writer = csv.DictWriter(outfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
