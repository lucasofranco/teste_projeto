import asyncio
from pysnmp.hlapi.v3arch.asyncio import (
    SnmpEngine, CommunityData, UdpTransportTarget, ContextData,
    ObjectType, ObjectIdentity, next_cmd
)

IP = '127.0.0.1'
PORTA = 1024
COMMUNITY = 'switch1'

# OIDs base de cada coluna da tabela de interfaces (ifTable)
OID_NOME = '1.3.6.1.2.1.2.2.1.2'     # ifDescr
OID_STATUS = '1.3.6.1.2.1.2.2.1.8'   # ifAdminStatus (1=up, 2=down)
OID_TRAFEGO = '1.3.6.1.2.1.2.2.1.10' # ifInOctets

async def walk(engine, transport, oid_base):
    """Pergunta todos os valores de uma coluna da tabela (todas as portas de uma vez)."""
    resultados = {}
    oid_atual = ObjectIdentity(oid_base)
    while True:
        err_ind, err_status, err_idx, var_binds = await next_cmd(
            engine, CommunityData(COMMUNITY), transport, ContextData(),
            ObjectType(oid_atual)
        )
        if err_ind or err_status or not var_binds:
            break
        nome_oid, valor = var_binds[0]
        nome_oid_str = str(nome_oid)
        if not nome_oid_str.startswith(oid_base):
            break
        if nome_oid_str == str(oid_atual):
            # Chegou no fim da tabela simulada - encerra
            break
        indice = nome_oid_str.split('.')[-1]
        resultados[indice] = valor.prettyPrint()
        oid_atual = ObjectIdentity(nome_oid_str)
    return resultados

async def monitorar_uma_vez():
    engine = SnmpEngine()
    transport = await UdpTransportTarget.create((IP, PORTA))
    nomes = await walk(engine, transport, OID_NOME)
    status = await walk(engine, transport, OID_STATUS)
    trafego = await walk(engine, transport, OID_TRAFEGO)
    engine.close_dispatcher()

    print('--- Status do switch ---')
    for indice in sorted(nomes, key=int):
        nome = nomes[indice]
        st = 'ONLINE' if status.get(indice) == '1' else 'OFFLINE'
        traf = trafego.get(indice, '0')
        print(f'{nome}: {st} | trafego acumulado: {traf} bytes')
    print()

async def main():
    while True:
        await monitorar_uma_vez()
        await asyncio.sleep(5)  # espera 5 segundos antes de perguntar de novo

if __name__ == '__main__':
    asyncio.run(main())