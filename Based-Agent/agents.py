import json
from swarm import Agent
from cdp import *
from typing import List, Dict, Any
import os
from openai import OpenAI
from decimal import Decimal
from typing import Union
from web3 import Web3
from web3.exceptions import ContractLogicError
# Configure the CDP SDK
Cdp.configure_from_json("./examples/based_agent/cdp_api_key.json")

# If you want to create a wallet on Base Mainnet, use Wallet.create(network_id="base-mainnet") and comment out the faucet line
agent_wallet = Wallet.create()
faucet = agent_wallet.faucet()
print(f"Faucet transaction: {faucet}")
print(f"Agent wallet address: {agent_wallet.default_address.address_id}")



def create_token(name, symbol, initial_supply):
    """Create a new ERC-20 token."""
    deployed_contract = agent_wallet.deploy_token(name, symbol, initial_supply)
    deployed_contract.wait()
    return f"Token {name} ({symbol}) created with initial supply of {initial_supply} and contract address {deployed_contract.contract_address}"

def transfer_asset(amount, asset_id, destination_address):
    """Transfer an asset to a specific address.
    
    Args:
        amount: Amount to transfer
        asset_id: Asset identifier ("eth", "usdc" are the only supported values) or contract address of another ERC-20 token. Unless the asset is ETH or USDC, you must use the contract address of the token.
        destination_address: Recipient's address
    """
    transfer = agent_wallet.transfer(amount, asset_id, destination_address)
    transfer.wait()
    return f"Transferred {amount} {asset_id} to {destination_address}"

def get_balance(asset_id):
    """Get the balance of a specific asset in the agent's wallet.
    
    Args:
        asset_id: Asset identifier ("eth", "usdc" are the only supported values) or contract address of another ERC-20 token. If you're unsure, use the contract address of the token.
        
    Returns:
        Current balance of the specified asset
    """
    balance = agent_wallet.balance(asset_id)
    return f"Current balance of {asset_id}: {balance}"


def request_eth_from_faucet():
    """Request ETH from the Base Sepolia testnet faucet.
    
    Returns:
        Status message about the faucet request
    """
    # if the agent is on mainnet, this will not work
    if agent_wallet.network_id == "base-mainnet":
        return "Error: The faucet is only available on Base Sepolia testnet."
    
    faucet_tx = agent_wallet.faucet()
    return f"Requested ETH from faucet. Transaction: {faucet_tx}"


def generate_art(prompt):
    """Generate art using DALL-E based on a text prompt.
    
    Args:
        prompt: Text description of the desired artwork
        
    Returns:
        Status message about the art generation
    """
    try:
        # Note: This requires OpenAI API key to be configured separately
        client = OpenAI()

        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size="1024x1024",
            quality="standard",
            n=1,
        )
        
        image_url = response.data[0].url
        return f"Generated artwork available at: {image_url}"
        
    except Exception as e:
        return f"Error generating artwork: {str(e)}"
    

def deploy_nft(name, symbol, base_uri):
    """Deploy an ERC-721 NFT contract.
    
    Args:
        name: Name of the NFT collection
        symbol: Symbol of the NFT collection
        base_uri: Base URI for token metadata
        
    Returns:
        Status message about the NFT deployment
    """
    try:
        # Deploy the NFT contract
        deployed_nft = agent_wallet.deploy_nft(name, symbol, base_uri)
        deployed_nft.wait()
        contract_address = deployed_nft.contract_address
        
        return f"Successfully deployed NFT contract '{name}' ({symbol}) at address {contract_address} with base URI: {base_uri}"
        
    except Exception as e:
        return f"Error deploying NFT contract: {str(e)}"

def mint_nft(contract_address, mint_to):
    """Mint an NFT to a specified address.
    
    Args:
        contract_address: Address of the NFT contract
        mint_to: Address to mint NFT to
        
    Returns:
        Status message about the NFT minting
    """
    try:
        # Call mint function on the NFT contract
        mint_args = {
            "to": mint_to,
            "quantity": "1"  # Changed to string to match working example
        }
        
        mint_invocation = agent_wallet.invoke_contract(
            contract_address=contract_address,
            method="mint", 
            args=mint_args
        )
        mint_invocation.wait()
        
        return f"Successfully minted NFT to {mint_to}"
        
    except Exception as e:
        return f"Error minting NFT: {str(e)}"

def swap_assets(amount: Union[int, float, Decimal], from_asset_id: str, to_asset_id: str):
    """
    Swap one asset for another using the trade function.
    This function only works on Base Mainnet.

    Args:
        amount: Amount of the source asset to swap
        from_asset_id: Source asset identifier ("eth", "usdc" are the only supported values) or contract address of another ERC-20 token. Unless the asset is ETH or USDC, you must use the contract address of the token.
        to_asset_id: Destination asset identifier ("eth", "usdc" are the only supported values) or contract address of another ERC-20 token. Unless the asset is ETH or USDC, you must use the contract address of the token.

    Returns:
        Status message about the swap
    """
    if agent_wallet.network_id != "base-mainnet":
        return "Error: Asset swaps are only available on Base Mainnet. Current network is not Base Mainnet."

    try:
        trade = agent_wallet.trade(amount, from_asset_id, to_asset_id)
        trade.wait()
        return f"Successfully swapped {amount} {from_asset_id} for {to_asset_id}"
    except Exception as e:
        return f"Error swapping assets: {str(e)}"



# Contract addresses
BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_MAINNET = "0x4cCb0BB02FCABA27e82a56646E81d8c5bC4119a5"
BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET = "0x49aE3cC2e3AA768B1e5654f5D3C6002144A59581"
L2_RESOLVER_ADDRESS_MAINNET = "0xC6d566A56A1aFf6508b41f6c90ff131615583BCD"
L2_RESOLVER_ADDRESS_TESTNET = "0x6533C94869D28fAA8dF77cc63f9e2b2D6Cf77eBA"

def create_register_contract_method_args(base_name: str, address_id: str, is_mainnet: bool) -> dict:
    """
    Create registration arguments for Basenames.
    
    Args:
        base_name (str): The Basename (e.g., "example.base.eth" or "example.basetest.eth")
        address_id (str): The Ethereum address
        is_mainnet (bool): True if on mainnet, False if on testnet
        
    Returns:
        dict: Formatted arguments for the register contract method
    """
    w3 = Web3()
    
    # Create contract instances
    resolver_contract = w3.eth.contract(abi=l2_resolver_abi)
    
    # Get namehash of the domain
    name_hash = w3.ens.namehash(base_name)
    
    # Encode function data for setAddr and setName
    address_data = resolver_contract.encode_abi(
        "setAddr",
        args=[name_hash, address_id]
    )
    
    name_data = resolver_contract.encode_abi(
        "setName",
        args=[name_hash, base_name]
    )
    
    # Create register arguments
    register_args = {
        "request": [
            base_name.replace(".base.eth" if is_mainnet else ".basetest.eth", ""),
            address_id,
            "31557600",  # 1 year in seconds
            L2_RESOLVER_ADDRESS_MAINNET if is_mainnet else L2_RESOLVER_ADDRESS_TESTNET,
            [address_data, name_data],
            True
        ]
    }
    
    return register_args

def register_basename(basename: str, amount: float = 0.002):
    """Register a basename for the agent's wallet.
    
    Args:
        basename: The basename to register (e.g. "myname.base.eth" or "myname.basetest.eth")
        amount: Amount of ETH to pay for registration (default 0.002)
        
    Returns:
        Status message about the basename registration
    """
    address_id = agent_wallet.default_address.address_id
    is_mainnet = agent_wallet.network_id == "base-mainnet"

    # Ensure the basename ends with the correct suffix
    suffix = ".base.eth" if is_mainnet else ".basetest.eth"
    if not basename.endswith(suffix):
        basename += suffix

    register_args = create_register_contract_method_args(basename, address_id, is_mainnet)

    try:
        # Determine the correct contract address based on the network
        contract_address = (
            BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_MAINNET if is_mainnet
            else BASENAMES_REGISTRAR_CONTROLLER_ADDRESS_TESTNET
        )

        # Invoke register function on registrar contract
        invocation = agent_wallet.invoke_contract(
            contract_address=contract_address,
            method="register", 
            args=register_args,
            abi=registrar_abi,
            amount=amount,
            asset_id="eth",
        )
        invocation.wait()
        return f"Successfully registered basename {basename} for address {address_id}"
    except ContractLogicError as e:
        return f"Error registering basename: {str(e)}"
    except Exception as e:
        return f"Unexpected error registering basename: {str(e)}"


# Add the new functions to the based_agent
based_agent = Agent(
    name="Based Agent",
    instructions="You are a helpful agent that can interact onchain on the Base Layer 2 using the Coinbase Developer Platform SDK. You can create tokens, transfer assets, generate art, deploy NFTs, mint NFTs, register basenames, and swap assets (on mainnet only). If you ever need to know your address, it is {agent_wallet.default_address.address_id}. If you ever need funds, you can request them from the faucet. You can also deploy your own ERC-20 tokens, NFTs, and interact with them. If someone asks you to do something you can't do, you can say so, and encourage them to implement it themselves using the CDP SDK, recommend they go to docs.cdp.coinbase.com for more informaton. You can also offer to help them implement it by writing the function and telling them to add it to the agents.py file and within your list of callable functions.",
    functions=[
        create_token, 
        transfer_asset, 
        get_balance, 
        request_eth_from_faucet, 
        #generate_art, 
        deploy_nft, 
        mint_nft,
        swap_assets,  # Add the new function here
        register_basename
    ],
)

l2_resolver_abi = [
    {
        "inputs": [
            {"internalType": "bytes32", "name": "node", "type": "bytes32"},
            {"internalType": "address", "name": "a", "type": "address"}
        ],
        "name": "setAddr",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "bytes32", "name": "node", "type": "bytes32"},
            {"internalType": "string", "name": "newName", "type": "string"}
        ],
        "name": "setName",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    }
]

registrar_abi = [
    {
        "inputs": [
            {
                "components": [
                    {"internalType": "string", "name": "name", "type": "string"},
                    {"internalType": "address", "name": "owner", "type": "address"},
                    {"internalType": "uint256", "name": "duration", "type": "uint256"},
                    {"internalType": "address", "name": "resolver", "type": "address"},
                    {"internalType": "bytes[]", "name": "data", "type": "bytes[]"},
                    {"internalType": "bool", "name": "reverseRecord", "type": "bool"}
                ],
                "internalType": "struct RegistrarController.RegisterRequest",
                "name": "request",
                "type": "tuple"
            }
        ],
        "name": "register",
        "outputs": [],
        "stateMutability": "payable",
        "type": "function"
    }
]
