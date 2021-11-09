import balpy
import sys
import os
import json
import webbrowser

from os.path import join, dirname
from dotenv import load_dotenv
# Load .env file
dotenv_path = join(dirname(__file__), '..', '.env')
load_dotenv(dotenv_path)

def main():
	
	if len(sys.argv) < 2:
		print("Usage: python3", sys.argv[0], "/path/to/pool.json");
		quit();

	pathToPool = sys.argv[1];
	if not os.path.isfile(pathToPool):
		print("Path", pathToPool, "does not exist. Please enter a valid path.")
		quit();

	with open(pathToPool) as f:
		pool = json.load(f)

	gasFactor = 1.05;
	gasSpeed = "fast";
	gasPriceGweiOverride = -1; # -1 uses etherscan price at speed for gasSpeed, all other values will override

	bal = balpy.balpy.balpy(pool["network"]);

	print();
	print("==============================================================")
	print("================ Step 1: Check Token Balances ================")
	print("==============================================================")
	print();
	
	tokens = list(pool["tokens"].keys());
	initialBalances = [pool["tokens"][token]["initialBalance"] for token in tokens];
	if not bal.erc20HasSufficientBalances(tokens, initialBalances):
		print("Please fix your insufficient balance before proceeding.");
		print("Quitting...");
		quit();

	print();
	print("==============================================================")
	print("============== Step 2: Approve Token Allowance ==============")
	print("==============================================================")
	print();

	(tokensSorted, allowancesSorted) = bal.erc20GetTargetAllowancesFromPoolData(pool);
	initialBalancesSorted = [pool["tokens"][token]["initialBalance"] for token in tokensSorted];
	# Async: Do [Approve]*N then [Wait]*N instead of [Approve, Wait]*N
	bal.erc20AsyncEnforceSufficientVaultAllowances(tokensSorted, allowancesSorted, initialBalancesSorted, gasFactor, gasSpeed, gasPriceGweiOverride=gasPriceGweiOverride);

	print();
	print("==============================================================")
	print("=============== Step 3: Create Pool in Factory ===============")
	print("==============================================================")
	print();

	if not "poolId" in pool.keys():
		txHash = bal.balCreatePoolInFactory(pool, gasFactor, gasSpeed, gasPriceGweiOverride=gasPriceGweiOverride);
		if not txHash:
			quit();
		poolId = bal.balGetPoolIdFromHash(txHash);
		pool["poolId"] = poolId;
		with open(pathToPool, 'w') as f:
			json.dump(pool, f, indent=4);
	else:
		print("PoolId found in pool description. Skipping the pool factory!");
		poolId = pool["poolId"];

	poolLink = bal.balGetLinkToFrontend(poolId);
	if not poolLink == "":
		webbrowser.open_new_tab(poolLink);

	print();
	print("==================================================================")
	print("=============== Step 4: Add Initial Tokens to Pool ===============")
	print("==================================================================")
	print();
	try:
		txHash = bal.balJoinPoolInit(pool, poolId, gasPriceGweiOverride=gasPriceGweiOverride);
	except:
		print("Joining pool failed! Are you the owner?");

	print();
	print("============================================================")
	print("=============== Step 5: Verify Pool Contract ===============")
	print("============================================================")
	print();

	command = bal.balGeneratePoolCreationArguments("0x" + poolId);
	print()
	print(command)
	print()
	print("If you need more complete instructions on what to do with this command, go to:");
	print("\thttps://dev.balancer.fi/resources/pools/verification");

if __name__ == '__main__':
	main();
