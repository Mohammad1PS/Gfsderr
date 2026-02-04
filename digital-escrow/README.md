# Digital Escrow System

This directory provides a reference implementation of a digital escrow system:

- **Solidity Smart Contract** (`contracts/`) to hold ETH or ERC-20 tokens (USDT compatible).
- **FastAPI backend** (`backend/`) to verify ownership transfer via Google APIs and release funds.
- **React frontend** (`frontend/`) to connect MetaMask and trigger backend actions.

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:APP --reload
```

Environment variables required by the backend:

- `WEB3_PROVIDER_URL`
- `ESCROW_SIGNER_PRIVATE_KEY`
- `ESCROW_CONTRACT_ADDRESS`
- `ESCROW_CONTRACT_ABI_PATH` (optional, defaults to a minimal ABI with `releaseFunds` only)

The backend uses Google OAuth access tokens to verify ownership. The OAuth token must be created
with scopes that allow `people.googleapis.com` and YouTube Data API access.

## Frontend

Serve the static files from the `frontend` folder:

```bash
cd frontend
python -m http.server 5173
```

Then open `http://localhost:5173` in a browser.

The FastAPI interactive docs are available at `http://localhost:8000/docs`.

## Smart Contract

Compile and deploy `contracts/DigitalEscrow.sol` with your preferred tooling (Hardhat, Foundry, etc.).
Update the backend environment variables with the deployed contract details.
