# fiscal/utils/sefaz_ce.py
import os
import xmlsec
import zeep
from lxml import etree

def assinar_xml(xml_path, cert_pfx_path, cert_password):
    # Carregar XML
    xml = etree.parse(xml_path)
    # Localizar nó da assinatura
    signature_node = xmlsec.template.create(
        xml, xmlsec.Transform.EXCL_C14N, xmlsec.Transform.RSA_SHA1
    )
    xml.getroot().insert(0, signature_node)

    # Carregar chave
    manager = xmlsec.KeysManager()
    manager.load_pkcs12(cert_pfx_path, cert_password)

    # Assinar
    ctx = xmlsec.SignatureContext(manager)
    ctx.sign(signature_node)
    return etree.tostring(xml)

def enviar_xml_para_sefaz(xml_assinado, ambiente='homologacao'):
    # Carregar o WSDL da SEFAZ-CE
    if ambiente == 'homologacao':
        wsdl = 'https://nfce.sefaz.ce.gov.br/nfce/services/NfeAutorizacao?wsdl'
    else:
        wsdl = 'https://nfce.sefaz.ce.gov.br/nfce/services/NfeAutorizacao?wsdl'

    client = zeep.Client(wsdl=wsdl)
    result = client.service.nfeAutorizacaoLote(xml_assinado)
    return result
