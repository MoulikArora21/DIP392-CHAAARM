import pandas as pd
from lxml import etree as ET
import os
from datetime import datetime
from lxml import etree  # Use lxml for pretty print and tag formatting

def prepare_xml(file_name, file_root):
    """Write XML with full tags and proper formatting."""
    def force_full_tags(elem):
        # Ensures even empty tags are written as <tag></tag>
        if not elem.text and not len(elem) and elem.tag != file_root.tag:
            elem.text = ''
        for child in elem:
            force_full_tags(child)

    force_full_tags(file_root)
    with open(file_name, "w", encoding="utf-8") as file:
        file.write('<?xml version="1.0" encoding="WINDOWS-1257"?>\n')
        xml_str = etree.tostring(
            etree.ElementTree(file_root).getroot(),
            encoding='unicode',
            method='xml',
            pretty_print=True,
            xml_declaration=False
        )
        file.write(xml_str)

def process(csv_file, output_xml, client, clients, selected_client):
    """Process Revolut CSV and generate FIDAVISTA XML."""
    try:
        # Read CSV
        df = pd.read_csv(csv_file)
        if df.empty:
            raise ValueError("CSV file is empty.")

        # Filter completed transactions for the selected client
        df = df[df['State'] == 'COMPLETED']
        df = df[df['Payer'] == client['Name']]
        if df.empty:
            raise ValueError(f"No completed transactions found for client {client['Name']}.")

        nsmap = {
            None: 'http://www.bankasoc.lv/fidavista/fidavista0101.xsd',
            'xsi': 'http://www.w3.org/2001/XMLSchema-instance'
        }
        root = etree.Element('FIDAVISTA', nsmap=nsmap)
        now = datetime.now()
        header = ET.SubElement(root, "Header")
        ET.SubElement(header, "Timestamp").text = now.strftime("%Y%m%d%H%M%S") + f"{int(now.microsecond / 1000):03d}"
        ET.SubElement(header, "From").text = "Placeholder"

        statement = ET.SubElement(root, "Statement")
        period = ET.SubElement(statement, "Period")

        dates = pd.to_datetime(df['Date completed (UTC)'])
        start_date = dates.min().strftime("%Y-%m-%d") if not dates.empty else now.strftime("%Y-%m-%d")
        end_date = dates.max().strftime("%Y-%m-%d") if not dates.empty else now.strftime("%Y-%m-%d")
        ET.SubElement(period, "StartDate").text = start_date
        ET.SubElement(period, "EndDate").text = end_date
        ET.SubElement(period, "PrepDate").text = now.strftime("%Y-%m-%d")

        bank_set = ET.SubElement(statement, "BankSet")
        ET.SubElement(bank_set, "Name").text = "Revolut"
        ET.SubElement(bank_set, "LegalId").text = ""
        ET.SubElement(bank_set, "Address").text = ""

        client_set = ET.SubElement(statement, "ClientSet")
        ET.SubElement(client_set, "Name").text = client['Name']
        ET.SubElement(client_set, "LegalId").text = client.get('LegalId', '')

        account_set = ET.SubElement(statement, "AccountSet")
        ET.SubElement(account_set, "AccNo").text = client['BankAcc']
        ccy_stmt = ET.SubElement(account_set, "CcyStmt")
        ET.SubElement(ccy_stmt, "Ccy").text = "EUR"
        ET.SubElement(ccy_stmt, "OpenBal").text = "0.00"
        close_bal = round(df['Balance'].iloc[-1], 2) if pd.notna(df['Balance'].iloc[-1]) else 0.00
        ET.SubElement(ccy_stmt, "CloseBal").text = str(close_bal)

        transaction_count = 0
        for _, row in df.iterrows():
            trx_set = ET.SubElement(ccy_stmt, "TrxSet")
            is_topup = row['Type'] == 'TOPUP'
            ET.SubElement(trx_set, "TypeCode").text = "INB" if is_topup else "OUT"
            ET.SubElement(trx_set, "TypeName").text = "INP" if is_topup else "OUT"
            ET.SubElement(trx_set, "Type").text = "03" if is_topup else "04"

            book_date = row['Date started (UTC)'] if pd.notna(row['Date started (UTC)']) else now.strftime("%Y-%m-%d")
            value_date = row['Date completed (UTC)'] if pd.notna(row['Date completed (UTC)']) else now.strftime("%Y-%m-%d")
            ET.SubElement(trx_set, "BookDate").text = book_date
            ET.SubElement(trx_set, "ValueDate").text = value_date

            trans_id = str(row['ID']) if pd.notna(row['ID']) else ''
            ET.SubElement(trx_set, "BankRef").text = trans_id
            ET.SubElement(trx_set, "DocNo").text = trans_id

            amount = row['Amount'] if pd.notna(row['Amount']) else 0.0
            amount = round(float(amount), 2)
            ET.SubElement(trx_set, "CorD").text = "C" if amount > 0 else "D"
            ET.SubElement(trx_set, "AccAmt").text = f"{abs(amount):.2f}"

            description = str(row.get('Description', '')) if pd.notna(row.get('Description')) else ''
            reference = str(row.get('Reference', '')) if pd.notna(row.get('Reference')) else ''
            pmt_info = description + (" " + reference if reference else '')
            ET.SubElement(trx_set, "PmtInfo").text = pmt_info if pmt_info else 'No details'

            cparty_set = ET.SubElement(trx_set, "CPartySet")
            iban = str(row.get('Beneficiary IBAN', '')) if pd.notna(row.get('Beneficiary IBAN')) else ''
            ET.SubElement(cparty_set, "AccNo").text = iban
            acc_holder = ET.SubElement(cparty_set, "AccHolder")
            cp_name = description if not is_topup and description else ''
            ET.SubElement(acc_holder, "Name").text = cp_name
            ET.SubElement(acc_holder, "LegalId").text = ''
            bic = str(row.get('Beneficiary BIC', '')) if pd.notna(row.get('Beneficiary BIC')) else ''
            ET.SubElement(cparty_set, "BankCode").text = bic
            ccy = str(row['Payment currency']) if pd.notna(row['Payment currency']) else 'EUR'
            ET.SubElement(cparty_set, "Ccy").text = ccy
            ET.SubElement(cparty_set, "Amt").text = f"{abs(amount):.2f}"

            transaction_count += 1

        clients[selected_client]['total_transactions'] += transaction_count

        prepare_xml(output_xml, root)

    except Exception as e:
        raise Exception(f"Error processing Revolut CSV: {str(e)}")
