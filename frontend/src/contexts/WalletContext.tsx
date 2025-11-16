import React, { createContext, useContext, useState, useEffect } from "react";

// Extend Window interface for MetaMask
declare global {
  interface Window {
    ethereum?: any;
  }
}

interface WalletContextType {
  walletAddress: string;
  balance: string;
  isConnecting: boolean;
  isFetchingBalance: boolean;
  connectWallet: () => Promise<void>;
  disconnectWallet: () => void;
  refreshBalance: () => Promise<void>;
}

const WalletContext = createContext<WalletContextType | undefined>(undefined);

// Arc Testnet network configuration
const ARC_TESTNET_CONFIG = {
  chainId: "0x4CEF52", // 5042002 in hex
  chainName: "Arc Testnet",
  nativeCurrency: {
    name: "USDC",
    symbol: "USDC",
    decimals: 18,
  },
  rpcUrls: ["https://evocative-patient-dust.arc-testnet.quiknode.pro/106d4e9c481f02b2f523dc3ff495ad3b835e3939"],
  blockExplorerUrls: ["https://testnet.arcscan.app"],
};

export const WalletProvider: React.FC<{ children: React.ReactNode }> = ({
  children,
}) => {
  const [walletAddress, setWalletAddress] = useState<string>("");
  const [balance, setBalance] = useState<string>("");
  const [isConnecting, setIsConnecting] = useState(false);
  const [isFetchingBalance, setIsFetchingBalance] = useState(false);

  const fetchBalance = async (address: string) => {
    try {
      setIsFetchingBalance(true);

      // Get balance in wei
      const balanceWei = await window.ethereum.request({
        method: "eth_getBalance",
        params: [address, "latest"],
      });

      // Convert from wei to USDC (18 decimals)
      const balanceInUsdc = parseInt(balanceWei, 16) / Math.pow(10, 18);
      setBalance(balanceInUsdc.toFixed(6));
    } catch (err: any) {
      console.error("Error fetching balance:", err);
      setBalance("0.000000");
    } finally {
      setIsFetchingBalance(false);
    }
  };

  const connectWallet = async () => {
    try {
      setIsConnecting(true);

      // Check if MetaMask is installed
      if (!window.ethereum) {
        alert(
          "MetaMask is not installed. Please install MetaMask to continue."
        );
        return;
      }

      // Request account access
      const accounts = await window.ethereum.request({
        method: "eth_requestAccounts",
      });

      // Try to switch to Arc Testnet
      try {
        await window.ethereum.request({
          method: "wallet_switchEthereumChain",
          params: [{ chainId: ARC_TESTNET_CONFIG.chainId }],
        });
      } catch (switchError: any) {
        // If the network doesn't exist, add it
        if (switchError.code === 4902) {
          await window.ethereum.request({
            method: "wallet_addEthereumChain",
            params: [ARC_TESTNET_CONFIG],
          });
        } else {
          throw switchError;
        }
      }

      // Set the connected wallet address
      setWalletAddress(accounts[0]);
      console.log("Connected to Arc Testnet with address:", accounts[0]);

      // Fetch balance
      await fetchBalance(accounts[0]);
    } catch (err: any) {
      console.error("Error connecting wallet:", err);
      alert(err.message || "Failed to connect wallet");
    } finally {
      setIsConnecting(false);
    }
  };

  const disconnectWallet = () => {
    setWalletAddress("");
    setBalance("");
  };

  const refreshBalance = async () => {
    if (walletAddress) {
      await fetchBalance(walletAddress);
    }
  };

  // Listen for account changes
  useEffect(() => {
    if (window.ethereum) {
      const handleAccountsChanged = (accounts: string[]) => {
        if (accounts.length === 0) {
          // User disconnected their wallet
          disconnectWallet();
        } else if (accounts[0] !== walletAddress) {
          // User switched accounts
          setWalletAddress(accounts[0]);
          fetchBalance(accounts[0]);
        }
      };

      const handleChainChanged = () => {
        // Reload the page when chain changes
        window.location.reload();
      };

      window.ethereum.on("accountsChanged", handleAccountsChanged);
      window.ethereum.on("chainChanged", handleChainChanged);

      return () => {
        window.ethereum.removeListener(
          "accountsChanged",
          handleAccountsChanged
        );
        window.ethereum.removeListener("chainChanged", handleChainChanged);
      };
    }
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

export const useWallet = () => {
  const context = useContext(WalletContext);
  if (context === undefined) {
    throw new Error("useWallet must be used within a WalletProvider");
  }
  return context;
};


