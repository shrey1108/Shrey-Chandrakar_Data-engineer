import requests
import zipfile
import xml.etree.ElementTree as ET
import csv
import boto3

# Step 1: download XML
url = 'https://registers.esma.europa.eu/solr/esma_registers_firds_files/select?q=*&fq=publication_date:%5B2022-03-30T00:00:00Z+TO+2022-03-30T23:59:59Z%5D&wt=xml&indent=true&start=0&rows=100'
response = requests.get(url)
xml_content = response.content

# Step 2: find first download link for DLTINS file type
root = ET.fromstring(xml_content)
download_link = ''
for doc in root.findall('.//doc'):
    file_type = doc.find('.//str[@name="file_type"]')
    if file_type is not None and file_type.text == 'DLTINS':
        download_link = doc.find('.//str[@name="download_link"]')
        break
if download_link == '':
    print('DLTINS file not found')
    exit()

# Step 3: download and extract DLTINS zip file
zip_url = download_link.text
zip_response = requests.get(zip_url)
with open('DLTINS.zip', 'wb') as f:
    f.write(zip_response.content)
with zipfile.ZipFile('DLTINS.zip', 'r') as zip_ref:
    zip_ref.extractall()

# Step 4: parse XML and extract required data
xml_file_path = 'DLTINS_20220330_01of01.xml'
tree = ET.parse(xml_file_path)
root = tree.getroot()
data = []
for instrm in root.findall('.//{urn:iso:std:iso:20022:tech:xsd:auth.036.001.02}FinInstrmGnlAttrbts'):
    instrm_data = {
        'FinInstrmGnlAttrbts.Id': instrm.find('{urn:iso:std:iso:20022:tech:xsd:auth.036.001.02}Id').text,
        'FinInstrmGnlAttrbts.FullNm': instrm.find('{urn:iso:std:iso:20022:tech:xsd:auth.036.001.02}FullNm').text,
        'FinInstrmGnlAttrbts.ClssfctnTp': instrm.find('{urn:iso:std:iso:20022:tech:xsd:auth.036.001.02}ClssfctnTp').text,
        'FinInstrmGnlAttrbts.CmmdtyDerivInd': instrm.find('{urn:iso:std:iso:20022:tech:xsd:auth.036.001.02}CmmdtyDerivInd').text,
        'FinInstrmGnlAttrbts.NtnlCcy': instrm.find('{urn:iso:std:iso:20022:tech:xsd:auth.036.001.02}NtnlCcy').text,
        'Issr': instrm.find('{urn:iso:std:iso:20022:tech:xsd:auth.036.001.02}Issr').text if instrm.find('{urn:iso:std:iso:20022:tech:xsd:auth.036.001.02}Issr') is not None else '',
    }
    data.append(instrm_data)

# Step 5: write data to CSV file
with open('data.csv', 'w', newline='') as csvfile:
    fieldnames = [
        'FinInstrmGnlAttrbts.Id',
        'FinInstrmGnlAttrbts.FullNm',
        'FinInstrmGnlAttrbts.ClssfctnTp',
        'FinInstrmGnlAttrbts.CmmdtyDerivInd',
        'FinInstrmGnlAttrbts.NtnlCcy',
        'Issr',
    ]
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()
    for instrm_data in data:
        writer.writerow(instrm_data)