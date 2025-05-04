import pandas as pd
import xml.etree.ElementTree as ET
import csv
import datetime
import pymupdf
import re


def read_pdf(pdf_doc):
    doc = pymupdf.open("CE/src/Etsy/"+pdf_doc) # open a document
    out = open("output.txt", "wb") # create a text output
    for page in doc: # iterate the document pages
        text = page.get_text()# get plain text (is in UTF-8)
        x = re.search("Invoice: [0-9]*",text)
        span = x.span()
        invoice = text[span[0]+9:span[1]]
    out.close()
    return invoice



def read_csv(file_name):
    with open("CE/src/Etsy/"+file_name, "r") as f:
        reader = csv.reader(f)
        return list(reader)


def make_entry_list(data_list):
    """Returns list of dicts with entries"""
    entry_list = []
    headers = data_list[0]
    for row in data_list[1:]:
        # make dict from headers and first row
        dict = {}
        for i in range(len(headers)):
            dict[headers[i]] = row[i]

        # dict["turnover"] = abs(float(dict["Amount"]))
        # result = dict["Description"]
        # if dict["Payment Reference"]:
        #     result += f" / {dict['Payment Reference']}"
        # if dict["Exchange From"]:
        #     result += f" / {dict['Exchange From']}-{dict['Exchange To']};{dict['Exchange Rate']}"
        # dict["info"] = result
        # if dict["Payee Name"] == "":
        #     dict["Payee Name"] = dict["Merchant"]
        # dict = get_type(dict)
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
        date = datetime.datetime.strptime("January 30, 2025","%B %d, %Y")
        bookdate.text = date.strftime("%Y-%m-%d")
        valuedate =  ET.SubElement(trxset,"ValueDate")
        valuedate.text = date.strftime("%Y-%m-%d") 
        bankref = ET.SubElement(trxset,"BankRef")
        bankref.text = "000"  #Ask
        docno = ET.SubElement(trxset,"DocNo")
        docno.text = "000"  #Ask
        cord  = ET.SubElement(trxset,"CorD")

        if dic_row["Type"] == "SALE":
            typename.text = "INB"
            typecode.text = "INP"
            cord.text = "C"
        else:
            typename.text = "PRV"
            typecode.text = "OUTP"
            cord.text = "D"
        accamt  = ET.SubElement(trxset,"AccAmt")
        if dic_row["Net"] == "--":
            accamt.text = dic_row["Title"][3:8]
        else:
            accamt.text = dic_row["Net"][3:]

        pmtinfo  = ET.SubElement(trxset,"PmtInfo")
        if dic_row["Type"] == "Deposit":
            info_processing = dic_row["Title"][3:] + " / Deposit"
            pmtinfo.text = info_processing
        elif dic_row["Type"] == "Sale":
            info_processing = dic_row["Title"]+ " / Sale" # order different file ---
            pmtinfo.text = info_processing
        elif dic_row["Type"] == "Fee":
            invoice = read_pdf("tax_statement_2025-1.pdf")
            pmtinfo.text = invoice + " / " + dic_row["Info"] + " / " + dic_row["Title"] + " / Fee"
        
            

        cpartyset  = ET.SubElement(trxset,"CPartSet")
        accno_2  = ET.SubElement(cpartyset,"AccNo")
        accholder_2  = ET.SubElement(cpartyset,"AccHolder")
        name_2  = ET.SubElement(accholder_2,"Name")
        legalid_2  = ET.SubElement(accholder_2,"LegalId")
        bankcode  = ET.SubElement(cpartyset,"BankCode")
        ccy_2 = ET.SubElement(cpartyset,"Ccy")
        amt = ET.SubElement(cpartyset,"Amt")





data_list = read_csv("testing123.csv")
entry_list = make_entry_list(data_list)
make_xml = make_xml_list(entry_list)


print(entry_list)







def prepare_list(file_root):
    xml_str = ET.tostring(file_root).decode("utf-8")
    xml_list = xml_str.split(">")
    new_list =[]
    for things in xml_list:
        newthings = things + ">\n"
        new_list.append(newthings)
    new_list.pop(-1)
    return new_list

def prepare_xml(name,file_root):
    with open(name,"w") as file:
        for things in prepare_list(file_root):
            file.writelines(things)
    return


prepare_xml("test2.xml",root)