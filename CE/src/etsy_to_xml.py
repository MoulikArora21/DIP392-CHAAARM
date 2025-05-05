import pandas as pd
import xml.etree.ElementTree as ET
import csv
import datetime
import pymupdf
import re
import pycountry

eu_countries = {
    "Austria", "Belgium", "Bulgaria", "Croatia", "Republic of Cyprus", "Czechia",
    "Denmark", "Estonia", "Finland", "France", "Germany", "Greece", "Hungary",
    "Ireland", "Italy", "Latvia", "Lithuania", "Luxembourg", "Malta",
    "Netherlands", "Poland", "Portugal", "Romania", "Slovakia", "Slovenia",
    "Spain", "Sweden"
}

def is_eu_country(country_name):
    try:
        country = pycountry.countries.lookup(country_name)
        return country.name in eu_countries
    except LookupError:
        return False

def read_pdf(pdf_path):
    doc = pymupdf.open(pdf_path)
    for page in doc:
        text = page.get_text()
        invoice_match = re.search(r"Invoice:\s*(\d+)", text)
        period_match = re.search(r"Invoice Period:\s*([0-9a-zA-Z, ]+)\s*-\s*([0-9a-zA-Z, ]+)", text)
        if invoice_match and period_match:
            invoice = invoice_match.group(1)
            period_start_txt = period_match.group(1).strip()
            period_end_txt = period_match.group(2).strip()
            date_start = datetime.datetime.strptime(period_start_txt, "%d %B, %Y")
            date_end = datetime.datetime.strptime(period_end_txt, "%d %B, %Y")
            doc.close()
            return invoice, date_start, date_end
    doc.close()
    raise ValueError("Could not extract invoice or period from PDF")

def read_csv(file_path):
    with open(file_path, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return list(reader)

def make_entry_list(data_list):
    entry_list = []
    headers = [h.strip('\ufeff') for h in data_list[0]]  # Remove BOM from header keys
    for row in data_list[1:]:
        dict_row = {}
        for i in range(len(headers)):
            dict_row[headers[i]] = row[i] if i < len(row) else ""
        entry_list.append(dict_row)
    return entry_list

def make_xml_list(entry_list, sales_files, pdf_files, client, clients, selected_client):
    # Get current transaction count for the selected client
    current_doc_no = client["total_transactions"]

    root = ET.Element('FIDAVISTA')
    header = ET.SubElement(root, 'Header')
    timestamp = ET.SubElement(header, 'Timestamp')
    timestamp.text = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S").strip()
    from_who = ET.SubElement(header, 'From')
    from_who.text = "PayBaltic SIA"
    statement = ET.SubElement(root, 'Statement')
    period = ET.SubElement(statement, 'Period')
    startdate = ET.SubElement(period, 'StartDate')
    enddate = ET.SubElement(period, 'EndDate')
    prepdate = ET.SubElement(period, 'PrepDate')
    prepdate.text = datetime.datetime.now().strftime("%Y-%m-%d")
    bankset = ET.SubElement(statement, 'BankSet')
    name = ET.SubElement(bankset, 'Name')
    name.text = client["Name"]
    legalid = ET.SubElement(bankset, 'LegalId')
    address = ET.SubElement(bankset, 'Address')
    clientset = ET.SubElement(statement, 'ClientSet')
    client_name = ET.SubElement(clientset, 'Name')
    client_name.text = client["Name"]
    legalid = ET.SubElement(clientset, 'LegalId')
    accountset = ET.SubElement(statement, 'AccountSet')
    accno = ET.SubElement(accountset, 'AccNo')
    accno.text = client["BankAcc"]
    ccystmt = ET.SubElement(accountset, 'CcyStmt')
    ccy = ET.SubElement(ccystmt, 'Ccy')
    ccy.text = "EUR"
    openbal = ET.SubElement(ccystmt, 'OpenBal')
    openbal.text = "0.00"
    closebal = ET.SubElement(ccystmt, 'CloseBal')
    closebal.text = "0.00"

    # Read sales data
    sales_entries = []
    for sales_file in sales_files:
        sales_data = read_csv(sales_file) if sales_file else []
        sales_entries.extend(make_entry_list(sales_data) if sales_data else [])

    # Read PDF data if provided
    pdf_data_list = []
    for pdf_file in pdf_files:
        pdf_data = read_pdf(pdf_file) if pdf_file else None
        pdf_data_list.append(pdf_data)

    for dic_row in entry_list:
        current_doc_no += 1  # Increment for each transaction
        date = datetime.datetime.strptime(dic_row["Date"], "%B %d, %Y")
        trxset = ET.SubElement(ccystmt, "TrxSet")
        typecode = ET.SubElement(trxset, "TypeCode")
        typename = ET.SubElement(trxset, "TypeName")
        regdate = ET.SubElement(trxset, "RegDate")
        bookdate = ET.SubElement(trxset, "BookDate")
        bookdate.text = date.strftime("%Y-%m-%d")
        valuedate = ET.SubElement(trxset, "ValueDate")
        valuedate.text = date.strftime("%Y-%m-%d")
        bankref = ET.SubElement(trxset, "BankRef")
        bankref.text = f"{current_doc_no:03d}"
        docno = ET.SubElement(trxset, "DocNo")
        docno.text = f"{current_doc_no:03d}"  # Three-digit string
        cord = ET.SubElement(trxset, "CorD")

        if dic_row["Type"] == "Sale":
            typename.text = "INB"
            typecode.text = "INP"
            cord.text = "C"
        else:
            typename.text = "PRV"
            typecode.text = "OUTP"
            cord.text = "D"

        accamt = ET.SubElement(trxset, "AccAmt")
        if dic_row["Net"] == "--":
            amount = re.search(r"([0-9.,]+)", dic_row["Title"])
            accamt.text = amount.group(1) if amount else "0.00"
        else:
            amount = re.search(r"([0-9.,]+)", dic_row["Net"])
            accamt.text = amount.group(1) if amount else "0.00"

        pmtinfo = ET.SubElement(trxset, "PmtInfo")
        if dic_row["Type"] == "Deposit":
            info_processing = dic_row["Title"] + " / Deposit"
            pmtinfo.text = info_processing
        elif dic_row["Type"] == "Sale":
            order_number_location = re.search(r"(\d+)", dic_row["Title"])
            order_number = order_number_location.group(1) if order_number_location else ""
            customer_name = "Unknown"
            vat = "0% indiv."
            for order in sales_entries:
                if order["Order ID"] == order_number:
                    country = order["Ship Country"]
                    customer_name = order["Full Name"]
                    vat = "21% indiv." if is_eu_country(country) else "0% indiv."
                    break
            info_processing = f"{dic_row['Title']} / Sale / {vat}"
            pmtinfo.text = info_processing
        elif dic_row["Type"] == "Fee" and pdf_data_list:
            for pdf_data in pdf_data_list:
                if pdf_data[1] <= date <= pdf_data[2]:
                    pmtinfo.text = f"{pdf_data[0]} / {dic_row['Info']} / {dic_row['Title']} / Fee"
                else:
                    pmtinfo.text = f"No matching PDF for {dic_row['Title']} / Fee"
        elif dic_row["Type"] == "Tax":
            pmtinfo.text = f"delete / {dic_row['Info']} / {dic_row['Title']} / Tax"

        cpartyset = ET.SubElement(trxset, "CPartSet")
        accno_2 = ET.SubElement(cpartyset, "AccNo")
        accholder_2 = ET.SubElement(cpartyset, "AccHolder")
        name_2 = ET.SubElement(accholder_2, "Name")
        legalid_2 = ET.SubElement(accholder_2, "LegalId")
        bankcode = ET.SubElement(cpartyset, "BankCode")
        ccy_2 = ET.SubElement(cpartyset, "Ccy")
        amt = ET.SubElement(cpartyset, "Amt")

        if dic_row["Type"] == "Deposit":
            accno_2.text = client["BankAcc"]
            name_2.text = client["Name"]
        elif dic_row["Type"] == "Fee" or dic_row["Type"] == "Tax":
            name_2.text = "Etsy Inc."
        elif dic_row["Type"] == "Sale":
            name_2.text = f"{vat} / {customer_name}"

        ccy_2.text = "EUR"
        amt.text = accamt.text

    # Update client's total_transactions
    clients[selected_client]["total_transactions"] = current_doc_no

    return root

import xml.etree.ElementTree as ET

def prepare_list(file_root):
    xml_str = ET.tostring(file_root, encoding="unicode")
    xml_list = xml_str.split("><")
    new_list = []
    i = 0
    while i < len(xml_list):
        current_segment = xml_list[i].strip()
        if current_segment.startswith("TrxSet"):
            trx_line = current_segment + "><"  # Start with the <TrxSet tag
            i += 1
            while i < len(xml_list) and not xml_list[i].strip().startswith("/TrxSet"):
                trx_line += xml_list[i].strip() + "><"
                i += 1
            if i < len(xml_list) and xml_list[i].strip().startswith("/TrxSet"):
                trx_line += xml_list[i].strip() + ">"  # Include the </TrxSet>
                new_list.append(trx_line + "\n<")
                i += 1
        else:
            # For non-<TrxSet> segments, append with >\n<, but ensure no duplicate ><
            if current_segment.endswith(">"):
                current_segment = current_segment.rstrip(">")
            new_list.append(current_segment + ">\n<")
            i += 1
    # Clean up the last element if it ends with >\n<
    if new_list and new_list[-1].strip().endswith(">\n<"):
        new_list[-1] = new_list[-1].rstrip("\n<")
    return new_list

def prepare_xml(name, file_root):
    with open(name, "w", encoding="utf-8") as file:
        for things in prepare_list(file_root):
            file.write(things)

def process(transaction_file, sales_file, pdf_file, client, clients, selected_client, output_xml):
    data_list = read_csv(transaction_file)
    entry_list = make_entry_list(data_list)
    xml_root = make_xml_list(entry_list, sales_file, pdf_file, client, clients, selected_client)
    prepare_xml(output_xml, xml_root)