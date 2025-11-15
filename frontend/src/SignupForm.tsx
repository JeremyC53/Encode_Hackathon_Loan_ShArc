import React, { useState } from "react";
import { useForm } from "react-hook-form";
import { useW3sContext } from "./W3Context"; // import your SDK context
import { createWallet } from "./WalletCreate"; // import wallet creation function

export default function SignupForm() {
  const { register, handleSubmit } = useForm();
  const { client } = useW3sContext();
  const [loading, setLoading] = useState(false);
  const [formMessage, setFormMessage] = useState("");

  // Replace with your real API!
  const onSubmit = async (data) => {
    setLoading(true);
    setFormMessage("");
    try {
      // 1. User registration with backend API
      // const res = await api.signup(data);
      // const challengeId = res.challengeId; // Returned by your backend after signup
      const challengeId = "some-id-from-api"; // replace with real one

      // 2. Wallet creation via Circle SDK
      const walletResult = await createWallet(client, challengeId);

      setFormMessage("Signup and wallet creation successful!");
      setLoading(false);
      // navigate or further logic here
    } catch (err) {
      setFormMessage("Error: " + err.message);
      setLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <input type="email" {...register("email")} placeholder="Email" />
      <input type="password" {...register("password")} placeholder="Password" />
      <button type="submit" disabled={loading}>
        {loading ? "Submitting..." : "Sign Up"}
      </button>
      {formMessage && <div>{formMessage}</div>}
    </form>
  );
}
