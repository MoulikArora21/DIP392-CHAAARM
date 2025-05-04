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
clients = [{"Name":"MARLE SIA","BankAcc":"LV81HABA0551052348489"}]
selected_client = 0 



def read_pdf(pdf_doc):
    doc = pymupdf.open("CE/src/Etsy/"+pdf_doc) # open a document
    out = open("output.txt", "wb") # create a text output
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

                # period_start_date = date_start.strftime("%Y-%m-%d")
                # period_end_date = date_end.strftime("%Y-%m-%d")
                break 
    return invoice, date_start, date_end




def read_csv(file_name):
    with open("CE/src/Etsy/"+file_name, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return list(reader)


def make_entry_list(data_list):
    entry_list = []
    headers = [h.strip('\ufeff') for h in data_list[0]]  # Remove BOM from header keys
    for row in data_list[1:]:
        dict = {}
        for i in range(len(headers)):
            dict[headers[i]] = row[i]
        entry_list.append(dict)
    return entry_list

root = ET.Element('FIDAVISTA')
header = ET.SubElement(root, 'Header')
timestamp = ET.SubElement(header, 'Timestamp')
from_who = ET.SubElement(header, 'From')
statement = ET.SubElement(root, 'Statement')
period = ET.SubElement(statement, 'Period')
startdate = ET.SubElement(period, 'StartDate')
enddate = ET.SubElement(period, 'EndDate')
prepdate = ET.SubElement(period, 'PrepDate')
bankset = ET.SubElement(statement, 'BankSet')
name = ET.SubElement(bankset, 'Name')
legalid = ET.SubElement(bankset, 'LegalId')
address = ET.SubElement(bankset, 'Address')
clientset = ET.SubElement(statement, 'ClientSet')
name = ET.SubElement(clientset, 'Name')
legalid = ET.SubElement(clientset, 'LegalId')
accountset = ET.SubElement(statement, 'AccountSet')
accno = ET.SubElement(accountset, 'AccNo')
ccystmt = ET.SubElement(accountset, 'CcyStmt')
ccy = ET.SubElement(ccystmt, 'Ccy')
openbal = ET.SubElement(ccystmt, 'OpenBal')
closebal = ET.SubElement(ccystmt, 'CloseBal')

def make_xml_list(entry_list):
    xml_list = []
    for dic_row in entry_list:

        trxset = ET.SubElement(ccystmt,"TrxSet")
        typecode = ET.SubElement(trxset,"TypeCode")
        typename = ET.SubElement(trxset,"TypeName")
        # actual_type = ET.SubElement(trxset,"Type") DOUBT


        regdate =  ET.SubElement(trxset,"RegDate")
        bookdate =  ET.SubElement(trxset,"BookDate")
        date = datetime.datetime.strptime(dic_row["Date"],"%B %d, %Y")
        bookdate.text = date.strftime("%Y-%m-%d")
        valuedate =  ET.SubElement(trxset,"ValueDate")
        valuedate.text = date.strftime("%Y-%m-%d") 
        bankref = ET.SubElement(trxset,"BankRef")
        bankref.text = "000"  #Ask
        docno = ET.SubElement(trxset,"DocNo")
        docno.text = "000"  #Ask
        cord  = ET.SubElement(trxset,"CorD")

        if dic_row["Type"] == "Sale":
            typename.text = "INB"
            typecode.text = "INP"
            cord.text = "C"
        else:
            typename.text = "PRV"
            typecode.text = "OUTP"
            cord.text = "D"
        accamt  = ET.SubElement(trxset,"AccAmt")
        if dic_row["Net"] == "--":
            amount = re.search(r"([0-9.,]+)",dic_row["Title"])
            accamt.text = amount.group(1)


        else:
            amount = re.search(r"([0-9.,]+)",dic_row["Net"])
            accamt.text = amount.group(1)

        pmtinfo  = ET.SubElement(trxset,"PmtInfo")
        if dic_row["Type"] == "Deposit":
            info_processing = dic_row["Title"] + " / Deposit"
            pmtinfo.text = info_processing
        elif dic_row["Type"] == "Sale":
            order_number_location = re.search("(\d+)",dic_row["Title"])
            order_number = order_number_location.group(1)
            order_list = make_entry_list(read_csv("EtsySoldOrders2025-1.csv"))
            for orders in order_list:
                if orders["Order ID"] == order_number:
                    country = orders["Ship Country"]
                    customer_name = orders["Full Name"]
                    if is_eu_country(country):
                        vat = "21% indiv."
                    else:
                        vat = "0% indiv."
            info_processing = dic_row["Title"]+ " / Sale / "+vat # order different file ---
            pmtinfo.text = info_processing
        elif dic_row["Type"] == "Fee":
            pdf_data = [read_pdf("tax_statement_2025-1.pdf")]

            for pdf in pdf_data:
                if pdf[1] <= date <= pdf[2]:
                    pmtinfo.text = pdf[0] + " / " + dic_row["Info"] + " / " + dic_row["Title"] + " / Fee"
                else:
                    print("Etsy Rekins is missing! for ")
        elif dic_row["Type"] == "Tax":
            pmtinfo.text = "delete / " + dic_row["Info"] + " / " + dic_row["Title"] + " / Tax"
            # how to know which listing belongs to which pdf
        
            

        cpartyset  = ET.SubElement(trxset,"CPartSet")
        accno_2  = ET.SubElement(cpartyset,"AccNo")
        accholder_2  = ET.SubElement(cpartyset,"AccHolder")
        name_2  = ET.SubElement(accholder_2,"Name")
        legalid_2  = ET.SubElement(accholder_2,"LegalId")
        bankcode  = ET.SubElement(cpartyset,"BankCode")
        ccy_2 = ET.SubElement(cpartyset,"Ccy")
        amt = ET.SubElement(cpartyset,"Amt")

        if dic_row["Type"] == "Deposit":
            accno_2.text = clients[selected_client]["BankAcc"]
            name_2.text = clients[selected_client]["Name"]
        elif dic_row["Type"] == "Fee" or dic_row["Type"] == "Tax" :
            name_2.text = "Etsy Inc."
        elif dic_row["Type"] == "Sale":
            name_2.text = vat + " / " + customer_name

        ccy_2.text = "EUR"
        amt.text = amount.group(1)





data_list = read_csv("testing123.csv")
entry_list = make_entry_list(data_list)
make_xml = make_xml_list(entry_list)


print(entry_list)







def prepare_list(file_root):
    xml_str = ET.tostring(file_root, encoding="unicode")
    xml_list = xml_str.split(">")
    new_list = []
    i = 0
    while i < len(xml_list):
        things = xml_list[i].strip()
        if things == "<TrxSet":
            # Start of TrxSet; collect all parts until </TrxSet
            trx_line = things + ">"
            i += 1
            while i < len(xml_list) and xml_list[i].strip() != "</TrxSet":
                trx_line += xml_list[i].strip() + ">"
                i += 1
            if i < len(xml_list):
                trx_line += xml_list[i].strip() + ">"
                new_list.append(trx_line + "\n")
                i += 1
        else:
            new_list.append(things + ">\n")
            i += 1
    if new_list[-1].strip() == ">":
        new_list.pop(-1)
    return new_list

def prepare_xml(name,file_root):
    with open(name,"w", encoding="utf-8") as file:
        for things in prepare_list(file_root):
            file.write(things)
    return

print("€")  # should print the euro symbol

prepare_xml("test2.xml",root)



