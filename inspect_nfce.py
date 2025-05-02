import inspect
from pynfe.entidades.notafiscal import NotaFiscal

nf = NotaFiscal()
nf.uf = 'SP'  # define um estado válido

print("Métodos disponíveis na classe NotaFiscal:")
for name, func in inspect.getmembers(nf, predicate=inspect.ismethod):
    if not name.startswith('_'):
        print(name)
