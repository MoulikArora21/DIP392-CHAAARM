import csv
import xml.etree.ElementTree as etree
import os
import datetime

def get_type(dict):
    """Returns dict with type, type_name and CorD added"""
    amount = float(dict["Amount"])
    if amount > 0:
        type = "INB"
        type_name = "INP"
        cor_d = "C"
    elif amount < 0:
        type = "OUTP"
        type_name = "PRV"
        cor_d = "D"
    else:
        raise ValueError("Missing or invalid transaction amount")
    dict["type"] = type
    dict["type_name"] = type_name
    dict["CorD"] = cor_d
    return dict

def make_entry_list(data_list):
    """Returns list of dicts with entries"""
    entry_list = []
    headers = data_list[0]
    for first_row in data_list[1:]:
        dict = {}
        for i in range(len(headers)):
            dict[headers[i]] = first_row[i] if i < len(first_row) else ""
        
        dict["turnover"] = abs(float(dict["Amount"]))
        result = dict["Description"]
        if dict.get("Payment Reference"):
            result += f" / {dict['Payment Reference']}"
        if dict.get("Exchange From"):
            result += f" / {dict['Exchange From']}-{dict['Exchange To']};{dict['Exchange Rate']}"
        dict["info"] = result
        if dict.get("Payee Name") == "":
            dict["Payee Name"] = dict.get("Merchant", "")
        dict = get_type(dict)
        entry_list.append(dict)
    return entry_list

def get_xml_list(entry_list):
    """Returns list of xml strings"""
    xml_list = []
    for row in entry_list:
        trx_set = etree.Element("TrxSet")
        etree.SubElement(trx_set, "TypeCode").text = row["type"]
        etree.SubElement(trx_set, "TypeName").text = row["type_name"]
        etree.SubElement(trx_set, "Type").text = "03" if row["type"] == "INB" else ""
        etree.SubElement(trx_set, "BookDate").text = datetime.datetime.strptime(row["Date"], '%d-%m-%Y').strftime('%Y-%m-%d')
        etree.SubElement(trx_set, "ValueDate").text = datetime.datetime.strptime(row["Date"], '%d-%m-%Y').strftime('%Y-%m-%d')
        etree.SubElement(trx_set, "BankRef").text = str(row["TransferWise ID"])
        etree.SubElement(trx_set, "DocNo").text = str(row["TransferWise ID"])
        etree.SubElement(trx_set, "CorD").text = row["CorD"]
        etree.SubElement(trx_set, "AccAmt").text = str(abs(float(row["Amount"])))
        etree.SubElement(trx_set, "PmtInfo").text = row["info"]

        cparty_set = etree.SubElement(trx_set, "CPartySet")
        etree.SubElement(cparty_set, "AccNo").text = row.get("Payee Account Number", "")
        acc_holder = etree.SubElement(cparty_set, "AccHolder")
        etree.SubElement(acc_holder, "Name").text = row.get("Payee Name", "")
        etree.SubElement(acc_holder, "LegalId").text = ""
        etree.SubElement(cparty_set, "BankCode").text = ""
        etree.SubElement(cparty_set, "Ccy").text = row["Currency"]
        etree.SubElement(cparty_set, "Amt").text = str(abs(float(row["Amount"])))

        xml_str = etree.tostring(trx_set).decode("utf-8")
        xml_list.append(xml_str)
    return xml_list

def read_csv(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return list(reader)

def write_xml_stripped(file_name, xml_list):
    with open(file_name, "w", encoding="utf-8") as f:
        for xml_str in xml_list:
            single_line_xml = " ".join(xml_str.split())
            f.write(single_line_xml + "\n")

def process(csv_file, output_xml):
    data_list = read_csv(csv_file)
    entry_list = make_entry_list(data_list)
    xml_list = get_xml_list(entry_list)
    write_xml_stripped(output_xml, xml_list)