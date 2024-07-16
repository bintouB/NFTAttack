from web3 import Web3
from moralis import evm_api


#Api key moralis
api_key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJub25jZSI6ImNkOTdhNzJmLWM3OTgtNDM2ZS1hMGIwLTQ1ZDY2ZGJlNjM5YSIsIm9yZ0lkIjoiMzk5NzM3IiwidXNlcklkIjoiNDEwNzQ1IiwidHlwZUlkIjoiMTFmYWM1MmEtMjhlMC00YmUxLTllNzAtZGRiOTA1NThkMzNhIiwidHlwZSI6IlBST0pFQ1QiLCJpYXQiOjE3MjA2OTA4NjMsImV4cCI6NDg3NjQ1MDg2M30.46KLOAC0B4W-7xaQj7MK1heHP8Jduz9wTH3szdUTFyY"

#web3
provider_url = 'https://eth-mainnet.g.alchemy.com/v2/owl6GCftheMeCsV6y1GmaasAoXT9jO3u'
w3 = Web3(Web3.HTTPProvider(provider_url))

#celle ci pas trop de items: https://etherscan.io/token/0x9922638937b99d12dbd1caf84a7eb439bb6222d2
#https://opensea.io/fr/assets/ethereum/0x9922638937b99d12dbd1caf84a7eb439bb6222d2/1
address="0x9922638937B99D12Dbd1Caf84A7EB439Bb6222d2"

#address="0x59325733eb952a92e069c87f0a6168b29e80627f"
threshold=25


#Pas UTILISE Fonction pour faire appel à l'API et récupérer les token id
#Uniquement les 100 premiers token 
def get_NFTs_by_contract1(address):

    params = {
    "chain": "eth",
    "format": "decimal",
    "address": address
    }

    result = evm_api.nft.get_contract_nfts(
    api_key=api_key,
    params=params,
    )
    return result['result']


#Fonction pour la récupértion des token id avec curseur 
#appelé dans def get_NFTs_by_contract(address)
def get_NFTs_by_contract_cursor(address,cursor):

    params = {
    "chain": "eth",
    "format": "decimal",
    "cursor":cursor,
    "address": address
    
    }

    result = evm_api.nft.get_contract_nfts(
    api_key=api_key,
    params=params,
    )
    return result['result']

#A vérifié si sa fonctionne bien
#Fonction pour la récupération des tous les tokens 
def get_NFTs_by_contract(address):
    all_nfts = []
    cursor = None

    while True:
        params = {
            "chain": "eth",
            "format": "decimal",
            "address": address
        }

        result = evm_api.nft.get_contract_nfts(
            api_key=api_key,
            params=params,
        )
        #print(result)
        # Ajout des NFTs récupérés
        all_nfts.extend(result['result'])
        
        # Vérifiez la présence d'un curseur pour la pagination
        if 'cursor' in result and result['cursor']:
            cursor = result['cursor']
            # Récupérer les NFTs de la prochaine page avec le curseur
            all_nfts.extend(get_NFTs_by_contract_cursor(address, cursor))
        else:
            break

    return all_nfts

#fonction pour récupérer la liste des ventes un token 
def get_trades_by_token(address,token_id, to_block):
    params = {
    "chain": "eth",
    "to_block": to_block,
    "address": address,
    "token_id": token_id
    }

    result = evm_api.nft.get_nft_trades_by_token(
    api_key=api_key,
    params=params,
    )

    return result

# Fonction pour calculer le floor price basé sur les transactions précédentes
def calculate_floor_price(transactions):
    floor_price = None
    for tx in transactions:
        try:
            price = float(tx['price_formatted'])
            if floor_price is None or price < floor_price:
                floor_price = price
                
        #Gestion des erreurs
        except KeyError:
            print(f"L'information du prix est manquante dans cette transaction: {tx}")
        except ValueError:
            print(f"Format du prix invalide ici: {tx['price_formatted']}")

    return floor_price


#Récupération de tous les nfts de cette collection
all_nfts= get_NFTs_by_contract(address)

#Pour chaque token
for current_nft in all_nfts:
    token_id=current_nft['token_id']
    print('='*20)
    print(f"Token ID:{token_id}")
    #Récupération des transactions de chaque nft
    sales=get_trades_by_token(address,token_id, "latest")
    for sale in sales['result']:
        block_number=sale['block_number']
        previous_block=int(block_number)-1
        price=float(sale['price_formatted'])
        
        
        previous_sales=get_trades_by_token(address,token_id, str(previous_block))
        floor_price=calculate_floor_price(previous_sales['result'])
        
        if floor_price is None: # potentiellement le cas de la première vente qui n'a pas de floor_price
            #print("Il s'agit de la première vente, ou floor price invalide.")
            continue  # Ignore cette vente et passe à la suivante
        
        if price < (float(floor_price)*threshold)/100: 
            print("Vente suspecte détectée!\n")
            print(f"Le montant de cette vente est inférieur à {threshold}% du floor price")
            print(f"Transaction hash : {sale['transaction_hash']}")
            print(f"Prix de vente : {price} ETH, Floor price : {floor_price} ETH") 
            print(f"Adresse de l'acheteur:{sale['buyer_address']}")
            print('-'*40)
        
        
    