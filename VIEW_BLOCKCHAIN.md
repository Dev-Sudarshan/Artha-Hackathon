# View Blockchain Data - Quick Commands

## View All Loans on Blockchain
cd "C:\Users\Ujjwal Shrestha\Downloads\multichain-windows-2.3.3"
.\multichain-cli.exe artha-chain liststreamitems loan_storage

## View Specific Loan by ID
.\multichain-cli.exe artha-chain liststreamkeyitems loan_storage "loan_LN-2B8D4391"

## View All Repayments
.\multichain-cli.exe artha-chain liststreamitems loan_repayments

## View Transaction Details
.\multichain-cli.exe artha-chain gettxout "c9bce3083a7bccaf8978cdd9a21c6c03f5e8fd0d8ffa939e067f41fb2c771b80" 0

## View Blockchain Info
.\multichain-cli.exe artha-chain getinfo

## Count Total Loans on Chain
(.\multichain-cli.exe artha-chain liststreamitems loan_storage | ConvertFrom-Json).Count
