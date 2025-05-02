from fiscal.utils.assinatura import assinar_xml_com_signxml as assinar_xml
from fiscal.utils.sefaz_ce import enviar_xml_para_sefaz

from pathlib import Path

def emitir_nfce_cardpayment(cardpayment):
    xml_path = f'/tmp/nfce_{cardpayment.id}.xml'

    # Aqui você gera o XML da nota com os dados do pagamento (salve como xml_path)
    with open(xml_path, 'w') as f:
        f.write(cardpayment.gerar_xml())  # Suponha que cardpayment gere XML

    certificado_path = Path('/caminho/do/certificado.pfx')
    senha_certificado = 'sua_senha'

    xml_assinado = assinar_xml(xml_path, certificado_path, senha_certificado)
    resposta = enviar_xml_para_sefaz(xml_assinado)

    return resposta
