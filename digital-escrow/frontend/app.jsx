const { useState } = React;

function App() {
  const [walletAddress, setWalletAddress] = useState("");
  const [assetId, setAssetId] = useState("");
  const [newOwnerEmail, setNewOwnerEmail] = useState("");
  const [escrowId, setEscrowId] = useState("");
  const [googleToken, setGoogleToken] = useState("");
  const [status, setStatus] = useState("");

  const connectWallet = async () => {
    if (!window.ethereum) {
      setStatus("MetaMask not detected.");
      return;
    }

    const accounts = await window.ethereum.request({ method: "eth_requestAccounts" });
    setWalletAddress(accounts[0]);
  };

  const verifyAndRelease = async () => {
    setStatus("Verifying ownership...");

    const response = await fetch("http://localhost:8000/release", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        asset_id: assetId,
        new_owner_email: newOwnerEmail,
        escrow_id: Number(escrowId),
        google_oauth_token: googleToken,
      }),
    });

    if (!response.ok) {
      const error = await response.json();
      setStatus(error.detail || "Release failed.");
      return;
    }

    const payload = await response.json();
    setStatus(`Funds released. Tx hash: ${payload.tx_hash}`);
  };

  return (
    <main className="container">
      <header>
        <h1>Digital Escrow</h1>
        <p>Connect MetaMask and trigger escrow release after ownership verification.</p>
      </header>

      <section className="card">
        <button type="button" onClick={connectWallet}>
          {walletAddress ? "Wallet Connected" : "Connect MetaMask"}
        </button>
        {walletAddress && <p className="muted">Connected: {walletAddress}</p>}
      </section>

      <section className="card">
        <label>
          Asset ID (YouTube Channel ID)
          <input value={assetId} onChange={(event) => setAssetId(event.target.value)} />
        </label>
        <label>
          New Owner Email
          <input value={newOwnerEmail} onChange={(event) => setNewOwnerEmail(event.target.value)} />
        </label>
        <label>
          Escrow ID
          <input value={escrowId} onChange={(event) => setEscrowId(event.target.value)} />
        </label>
        <label>
          Google OAuth Token
          <input value={googleToken} onChange={(event) => setGoogleToken(event.target.value)} />
        </label>
        <button type="button" onClick={verifyAndRelease}>
          Verify Ownership &amp; Release Funds
        </button>
      </section>

      {status && (
        <section className="card status">
          <strong>Status</strong>
          <p>{status}</p>
        </section>
      )}
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")).render(<App />);
