from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, PrivateFormat, NoEncryption
from cryptography.hazmat.backends import default_backend
from signxml import XMLSigner, methods
from lxml import etree
from signxml import XMLSigner

def assinar_xml_com_signxml(xml_path, pfx_path, pfx_password):
    # Carrega o arquivo PFX
    with open(pfx_path, 'rb') as f:
        pfx_data = f.read()

    # Extrai chave privada e certificado
    private_key, cert, _ = pkcs12.load_key_and_certificates(
        pfx_data, pfx_password.encode(), backend=default_backend()
    )

    # Exporta como PEM
    private_key_pem = private_key.private_bytes(
        Encoding.PEM,
        PrivateFormat.TraditionalOpenSSL,
        NoEncryption()
    )

    cert_pem = cert.public_bytes(Encoding.PEM)

    # Carrega XML
    with open(xml_path, 'rb') as f:
        xml_data = f.read()

    # Faz o parse
    root = etree.fromstring(xml_data)

    # Assinador
    

    signer = XMLSigner(
        method=methods.enveloped,
        signature_algorithm='rsa-sha1',
        digest_algorithm='sha1'
    )





    # Assina
    signed_root = signer.sign(
        root,
        key=private_key_pem,
        cert=cert_pem,
        reference_uri=""
    )

    # Serializa
    return etree.tostring(signed_root, pretty_print=True, encoding="utf-8")
