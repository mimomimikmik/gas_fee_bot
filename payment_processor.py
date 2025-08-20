from web3 import Web3
from config import Config
from firebase_service import FirebaseService
import time

class PaymentProcessor:
    def __init__(self, web3_provider):
        self.web3 = Web3(Web3.HTTPProvider(web3_provider))
        self.firebase = FirebaseService()
    
    def validate_payment(self, user_id, tx_hash):
        try:
            tx = self.web3.eth.get_transaction(tx_hash)
            
            if not tx:
                return False, "Transaction not found"
            
            receipt = self.web3.eth.get_transaction_receipt(tx_hash)
            
            if not receipt or receipt.status != 1:
                return False, "Transaction failed"
            
            # Check if transaction is to our wallet
            wallet_address = self.firebase.get_wallet_address()
            if tx.to.lower() != wallet_address.lower():
                return False, "Payment to wrong wallet address"
            
            # Check if amount is sufficient
            value_eth = self.web3.fromWei(tx.value, 'ether')
            if value_eth < Config.SUBSCRIPTION_PRICE_ETH:
                return False, f"Insufficient payment. Required: {Config.SUBSCRIPTION_PRICE_ETH} ETH"
            
            # Check if this is a duplicate payment
            user = self.firebase.get_user(user_id)
            if user and user.get("last_payment_tx") == tx_hash:
                return False, "This payment has already been processed"
            
            # All checks passed
            return True, "Payment validated successfully"
        
        except Exception as e:
            return False, f"Payment validation error: {str(e)}"
    
    def monitor_pending_transactions(self, user_id, from_address):
        # In a real implementation, you would monitor the mempool or use a service like Alchemy or Infura
        # This is a simplified version that checks recent transactions
        
        wallet_address = self.firebase.get_wallet_address()
        
        # Wait for a few blocks to be mined (simplified approach)
        time.sleep(120)  # Wait 2 minutes
        
        # Check the last 100 transactions to the wallet
        block = self.web3.eth.block_number
        for i in range(100):
            try:
                tx_hash = self.web3.eth.get_block(block - i)['transactions']
                for tx in tx_hash:
                    tx_data = self.web3.eth.get_transaction(tx)
                    if (tx_data['from'].lower() == from_address.lower() and 
                        tx_data['to'].lower() == wallet_address.lower()):
                        return tx.hex()
            except:
                continue
        
        return None