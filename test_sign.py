from fiscal.utils.assinatura import assinar_xml_com_signxml

xml_assinado = assinar_xml_com_signxml(
    'exemplo_nfe.xml',
    'certificados/MONT GRANITOS LTDA EM RECUPERACAO JUDICIAL_01595789000133.pfx',
    '123456'
)

with open('nfe_assinada.xml', 'wb') as f:
    f.write(xml_assinado)

try:
    xml_assinado = assinar_xml_com_signxml(xml_path, pfx_path, pfx_password)
    print("✅ XML assinado com sucesso!\n")
    print(xml_assinado.decode("utf-8"))  # exibe XML em texto
except Exception as e:
    print("❌ Erro ao assinar XML:")
    print(e)
