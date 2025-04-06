# Read file from csv statement_22950315_EUR_2023-08-18_2023-10-15.csv

import csv
import xml.etree.ElementTree as etree
import os
import sys

# from xml import etree

import datetime #edit

def get_type(dict):
    """Returns dict with type, type_name and CorD added"""
    amount = float(dict["Amount"])
    #if dict["Total fees"] and float(dict["Total fees"]) > 0:
    #    type = "KOM"
    #    type_name = "OTHR"
    #    cor_d = "D"
    #elif amount > 0:
    if amount > 0:
        type = "INB"
        type_name = "INP"
        cor_d = "C"
    elif amount < 0:
        type = "OUTP"
        type_name = "PRV"
        cor_d = "D"
    else:
        print("something went wrong, missing transaction type?")
    dict["type"] = type
    dict["type_name"] = type_name
    dict["CorD"] = cor_d
    return dict


def make_entry_list(data_list):
    """Returns list of dicts with entries"""
    entry_list = []
    headers = data_list[0]
    for first_row in data_list[1:]:
        # make dict from headers and first row
        dict = {}
        for i in range(len(headers)):
            dict[headers[i]] = first_row[i]

        dict["turnover"] = abs(float(dict["Amount"]))
        result = dict["Description"]
        if dict["Payment Reference"]:
            result += f" / {dict['Payment Reference']}"
        if dict["Exchange From"]:
            result += f" / {dict['Exchange From']}-{dict['Exchange To']};{dict['Exchange Rate']}"
        dict["info"] = result
        if dict["Payee Name"] == "":
            dict["Payee Name"] = dict["Merchant"]
        dict = get_type(dict)
        entry_list.append(dict)
    return entry_list


def get_xml_list(entry_list):
    """Returns list of xml strings"""
    xml_list = []
    for row in entry_list:
        # Create root element for the transaction
        trx_set = etree.Element("TrxSet")

        # Populate fields
        etree.SubElement(trx_set, "TypeCode").text = row["type"]
        etree.SubElement(trx_set, "TypeName").text = row["type_name"]
        # if type == 'INB' then '03', else ''
        if row["type"] == "INB":
            etree.SubElement(trx_set, "Type").text = "03"
        else:
            etree.SubElement(trx_set, "Type").text = ""
        etree.SubElement(trx_set, "BookDate").text = datetime.datetime.strptime(row["Date"], '%d-%m-%Y').strftime('%Y-%m-%d') #edit date format
        etree.SubElement(trx_set, "ValueDate").text = datetime.datetime.strptime(row["Date"], '%d-%m-%Y').strftime('%Y-%m-%d') #edit date format
        etree.SubElement(trx_set, "BankRef").text = str(row["TransferWise ID"])[0:25] #edit limit string to max 25 chars
        etree.SubElement(trx_set, "DocNo").text = str(row["TransferWise ID"])[0:25] #edit limit string to max 25 chars
        etree.SubElement(trx_set, "CorD").text = row[
            "CorD"
        ]  # Double check logic is right
        etree.SubElement(trx_set, "AccAmt").text = str(row["Amount"]).replace("-","") #edit to absolute value
        etree.SubElement(trx_set, "PmtInfo").text = row["info"]

        # Add CPartySet
        cparty_set = etree.SubElement(trx_set, "CPartySet")
        etree.SubElement(cparty_set, "AccNo").text = row["Payee Account Number"]
        acc_holder = etree.SubElement(cparty_set, "AccHolder")
        etree.SubElement(acc_holder, "Name").text = row["Payee Name"]
        etree.SubElement(
            acc_holder, "LegalId"
        ).text = ""  # Generally seems to be blank?
        etree.SubElement(
            cparty_set, "BankCode"
        ).text = ""  # Generally seems to be blank?
        etree.SubElement(cparty_set, "Ccy").text = row["Currency"]
        etree.SubElement(cparty_set, "Amt").text = str(row["Amount"]).replace("-","") #edit to absolute value

        # Serialize to string
        xml_str = etree.tostring(trx_set).decode("utf-8")
        xml_list.append(xml_str)
    return xml_list


def read_csv(file_name):
    with open(file_name, "r") as f:
        reader = csv.reader(f)
        return list(reader)


def write_xml(file_name, xml_list):
    # Use this function if you don't need one entry per line
    with open(file_name, "w") as f:
        for xml_str in xml_list:
            f.write(xml_str)


def write_xml_stripped(file_name, xml_list):
    with open(file_name, "w") as f:
        for xml_str in xml_list:
            single_line_xml = " ".join(xml_str.split())
            f.write(single_line_xml + "\n")


import os


# def get_csv_files():
#     return [f for f in os.listdir() if f.endswith(".csv")]


# def select_csv_file():
#     csv_files = get_csv_files()

#     if not csv_files:
#         print("No CSV files found.")
#         return None

#     print("Available CSV files:")
#     for i, f in enumerate(csv_files, 1):
#         print(f"{i}. {f}")

#     while True:
#         choice = input("Select the number of the CSV file: ")
#         try:
#             return csv_files[int(choice) - 1]
#         except (ValueError, IndexError):
#             print("Invalid choice. Please try again.")


def get_output_filename(input_filename):
    return input_filename.rsplit(".", 1)[0] + ".xml"


def main():
    try:
        csv_file = "statement_71034669_EUR_test.csv"
        data_list = read_csv(csv_file)
    except FileNotFoundError:
        print(f"File {csv_file} not found.")
        return

    entry_list = make_entry_list(data_list)
    xml_list = get_xml_list(entry_list)

    try:
        if csv_file:
            output_file = get_output_filename(csv_file)
        write_xml_stripped(output_file, xml_list)
        print(f"XML data written to {output_file}")
    except Exception as e:
        print(f"An error occurred while writing to {output_file}: {e}")


if __name__ == "__main__":
    main()
