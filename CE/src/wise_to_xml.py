import csv
import lxml.etree as etree
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

def get_xml_list(entry_list, client, clients, selected_client):
    """Returns XML tree with FIDAVISTA structure"""
    nsmap = {
        None: 'http://www.bankasoc.lv/fidavista/fidavista0101.xsd',
        'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
    }
    root = etree.Element('FIDAVISTA', nsmap=nsmap)
    
    # Header
    header = etree.SubElement(root, 'Header')
    timestamp = etree.SubElement(header, 'Timestamp')
    now = datetime.datetime.now()
    timestamp.text = now.strftime("%Y%m%d%H%M%S") + f"{int(now.microsecond / 1000):03d}"
    from_who = etree.SubElement(header, 'From')
    from_who.text = "Swedbank, business.swedbank.lv, Customer support Tel. +371 67444444"
    
    # Statement
    statement = etree.SubElement(root, 'Statement')
    period = etree.SubElement(statement, 'Period')
    startdate = etree.SubElement(period, 'StartDate')
    enddate = etree.SubElement(period, 'EndDate')
    prepdate = etree.SubElement(period, 'PrepDate')
    prepdate.text = datetime.datetime.now().strftime("%Y-%m-%d")
    
    # BankSet
    bankset = etree.SubElement(statement, 'BankSet')
    name = etree.SubElement(bankset, 'Name')
    name.text = "Wise Europe SA"
    legalid = etree.SubElement(bankset, 'LegalId')
    address = etree.SubElement(bankset, 'Address')
    
    # ClientSet
    clientset = etree.SubElement(statement, 'ClientSet')
    client_name = etree.SubElement(clientset, 'Name')
    client_name.text = client["Name"]
    legalid = etree.SubElement(clientset, 'LegalId')
    legalid.text = client.get("LegalId", "")
    
    # AccountSet
    accountset = etree.SubElement(statement, 'AccountSet')
    accno = etree.SubElement(accountset, 'AccNo')
    accno.text = client["BankAcc"]
    ccystmt = etree.SubElement(accountset, 'CcyStmt')
    ccy = etree.SubElement(ccystmt, 'Ccy')
    ccy.text = "EUR"
    openbal = etree.SubElement(ccystmt, 'OpenBal')
    openbal.text = "0.00"
    closebal = etree.SubElement(ccystmt, 'CloseBal')
    closebal.text = "0.00"
    
    # Calculate date range
    mindate = None
    maxdate = None
    current_doc_no = client["total_transactions"]
    
    for row in entry_list:
        date = datetime.datetime.strptime(row["Date"], '%d-%m-%Y')
        if mindate is None or date < mindate:
            mindate = date
        if maxdate is None or date > maxdate:
            maxdate = date
    
    if mindate and maxdate:
        startdate.text = mindate.strftime("%Y-%m-%d")
        enddate.text = maxdate.strftime("%Y-%m-%d")
    else:
        startdate.text = ""
        enddate.text = ""
    
    # Transactions
    for row in entry_list:
        current_doc_no += 1
        trx_set = etree.SubElement(ccystmt, "TrxSet")
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

    clients[selected_client]["total_transactions"] = current_doc_no
    return root

def read_csv(file_name):
    with open(file_name, "r", encoding="utf-8") as f:
        reader = csv.reader(f)
        return list(reader)

def prepare_xml(file_name, file_root):
    """Write XML with full tags and proper formatting"""
    def force_full_tags(elem):
        if not elem.text and not len(elem) and elem.tag != file_root.tag:
            elem.text = ''
        for child in elem:
            force_full_tags(child)

    force_full_tags(file_root)
    with open(file_name, "w", encoding="utf-8") as file:
        file.write('<?xml version="1.0" encoding="WINDOWS-1257"?>\n')
        xml_str = etree.tostring(
            file_root,
            encoding='unicode',
            method='xml',
            pretty_print=True,
            xml_declaration=False
        )
        file.write(xml_str)

def process(csv_file, output_xml, client, clients, selected_client):
    data_list = read_csv(csv_file)
    entry_list = make_entry_list(data_list)
    xml_root = get_xml_list(entry_list, client, clients, selected_client)
    prepare_xml(output_xml, xml_root)