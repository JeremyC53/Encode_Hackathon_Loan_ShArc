// walletCreate.js or inline in your SignupForm
export async function createWallet(client, challengeId) {
	return new Promise((resolve, reject) => {
	  if (!client || !challengeId) {
	    reject(new Error("Missing client or challengeId"));
	    return;
	  }
	  client.execute(challengeId, (error, result) => {
	    if (error) reject(error);
	    else resolve(result);
	  });
	});
   }
   