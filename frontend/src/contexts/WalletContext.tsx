import React, { createContext, useContext, useEffect, useState } from "react";

declare global {
  interface Window {
    ethereum?: any;
  }
}

type WalletContextType = {
  walletAddress: string;
  balance: string;
  isConnecting: boolean;
  isFetchingBalance: boolean;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  refreshBalance: () => Promise<void>;
};

const WalletContext = createContext<WalletContextType | undefined>(undefined);

const ARC_TESTNET_CONFIG = {
  chainId: "0x4CEF52", // 5042002 in hex
  chainName: "Arc Testnet",
  nativeCurrency: {
    name: "USDC",
    symbol: "USDC",
    decimals: 18,
  },
  rpcUrls: ["https://rpc.testnet.arc.network"],
  blockExplorerUrls: ["https://testnet.arcscan.app"],
};

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [walletAddress, setWalletAddress] = useState("");
  const [balance, setBalance] = useState("0.000000");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isFetchingBalance, setIsFetchingBalance] = useState(false);

  const fetchBalance = async (address: string) => {
    if (!window.ethereum) return;
    try {
      setIsFetchingBalance(true);
      const balanceWei = await window.ethereum.request({
        method: "eth_getBalance",
        params: [address, "latest"],
      });
      const balanceNumber = parseInt(balanceWei, 16) / Math.pow(10, 18);
      setBalance(balanceNumber.toFixed(6));
    } catch (error) {
      console.error("Error fetching balance:", error);
      setBalance("0.000000");
    } finally {
      setIsFetchingBalance(false);
    }
  };

  const connectWallet = async () => {
    try {
      setIsConnecting(true);
      if (!window.ethereum) {
        alert("MetaMask is not installed. Please install it to continue.");
        return;
      }

      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts",
      });

      try {
        await window.ethereum.request({
          method: "wallet_switchEthereumChain",
          params: [{ chainId: ARC_TESTNET_CONFIG.chainId }],
        });
      } catch (switchError: any) {
        if (switchError.code === 4902) {
          await window.ethereum.request({
            method: "wallet_addEthereumChain",
            params: [ARC_TESTNET_CONFIG],
          });
        } else {
          throw switchError;
        }
      }

      setWalletAddress(accounts[0]);
      await fetchBalance(accounts[0]);
    } catch (error: any) {
      console.error("Error connecting wallet:", error);
      alert(error?.message ?? "Failed to connect wallet");
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    setWalletAddress("");
    setBalance("0.000000");
  };

  const refreshBalance = async () => {
    if (walletAddress) {
      await fetchBalance(walletAddress);
    }
  };

  useEffect(() => {
    if (!window.ethereum) {
      return;
    }

    const handleAccountsChanged = (accounts: string[]) => {
      if (accounts.length === 0) {
        disconnectWallet();
      } else if (accounts[0] !== walletAddress) {
        setWalletAddress(accounts[0]);
        fetchBalance(accounts[0]);
      }
    };

    const handleChainChanged = () => {
      window.location.reload();
    };

    window.ethereum.on("accountsChanged", handleAccountsChanged);
    window.ethereum.on("chainChanged", handleChainChanged);

    return () => {
      window.ethereum?.removeListener("accountsChanged", handleAccountsChanged);
      window.ethereum?.removeListener("chainChanged", handleChainChanged);
    };
  }, [walletAddress]);

  return (
    <WalletContext.Provider
      value={{
        walletAddress,
        balance,
        isConnecting,
        isFetchingBalance,
        connectWallet,
        disconnectWallet,
        refreshBalance,
      }}
    >
      {children}
    </WalletContext.Provider>
  );
};

export const useWallet = (): WalletContextType => {
  const context = useContext(WalletContext);
  if (!context) {
    throw new Error("useWallet must be used within a WalletProvider");
  }
  return context;
};

