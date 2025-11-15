// W3sContext.js
import React, { createContext, useContext, useEffect, useState } from "react";
import { W3SSdk } from "@circle-fin/w3s-pw-web-sdk";

const W3sContext = createContext({ client: undefined });

export const W3sProvider = ({ children }) => {
  const [client, setClient] = useState();

  useEffect(() => {
    if (!client) {
	const sdk = new W3SSdk({
		appSettings: {
		  appId: '4510e8a7-4278-554b-9166-d31f6d7842de'
		},
	   })
      // Optional: set app settings and resources here
      setClient(sdk);
    }
  }, [client]);

  return (
    <W3sContext.Provider value={{ client }}>
      {children}
    </W3sContext.Provider>
  );
};

export const useW3sContext = () => useContext(W3sContext);
