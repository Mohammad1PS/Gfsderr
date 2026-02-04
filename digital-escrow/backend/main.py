from __future__ import annotations

import json
import os
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from web3 import Web3

APP = FastAPI(title="Digital Escrow Backend")

GOOGLE_PEOPLE_API = "https://people.googleapis.com/v1/people/me"
YOUTUBE_CHANNEL_API = "https://www.googleapis.com/youtube/v3/channels"

DEFAULT_ABI = [
    {
        "inputs": [{"internalType": "uint256", "name": "escrowId", "type": "uint256"}],
        "name": "releaseFunds",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function",
    }
]


class OwnershipVerificationRequest(BaseModel):
    asset_id: str
    new_owner_email: EmailStr
    google_oauth_token: str


class ReleaseRequest(OwnershipVerificationRequest):
    escrow_id: int


class ReleaseResponse(BaseModel):
    tx_hash: str


def load_contract_abi() -> list[dict[str, Any]]:
    abi_path = os.getenv("ESCROW_CONTRACT_ABI_PATH", "")
    if abi_path:
        with open(abi_path, "r", encoding="utf-8") as abi_file:
            return json.load(abi_file)
    return DEFAULT_ABI


def verify_owner_transfer(
    asset_id: str,
    new_owner_email: str,
    google_oauth_token: str,
) -> bool:
    headers = {"Authorization": f"Bearer {google_oauth_token}"}
    people_params = {"personFields": "emailAddresses"}

    with httpx.Client(timeout=15) as client:
        people_response = client.get(GOOGLE_PEOPLE_API, headers=headers, params=people_params)
        if people_response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Failed to verify Google account ownership.",
            )
        people_payload = people_response.json()
        emails = people_payload.get("emailAddresses", [])
        if not emails:
            raise HTTPException(status_code=400, detail="No email found for OAuth user.")
        current_email = emails[0].get("value", "").lower()

        youtube_params = {"part": "id", "mine": "true"}
        youtube_response = client.get(YOUTUBE_CHANNEL_API, headers=headers, params=youtube_params)
        if youtube_response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail="Failed to fetch YouTube channel info for verification.",
            )
        youtube_payload = youtube_response.json()
        channels = youtube_payload.get("items", [])
        channel_ids = {channel.get("id") for channel in channels}

    return current_email == new_owner_email.lower() and asset_id in channel_ids


def release_funds(escrow_id: int) -> str:
    provider_url = os.getenv("WEB3_PROVIDER_URL")
    private_key = os.getenv("ESCROW_SIGNER_PRIVATE_KEY")
    contract_address = os.getenv("ESCROW_CONTRACT_ADDRESS")

    if not provider_url or not private_key or not contract_address:
        raise HTTPException(
            status_code=500,
            detail="Missing WEB3_PROVIDER_URL, ESCROW_SIGNER_PRIVATE_KEY, or ESCROW_CONTRACT_ADDRESS.",
        )

    web3 = Web3(Web3.HTTPProvider(provider_url))
    if not web3.is_connected():
        raise HTTPException(status_code=502, detail="Unable to connect to Web3 provider.")

    signer = web3.eth.account.from_key(private_key)
    contract = web3.eth.contract(address=web3.to_checksum_address(contract_address), abi=load_contract_abi())
    nonce = web3.eth.get_transaction_count(signer.address)
    gas_price = web3.eth.gas_price

    transaction = contract.functions.releaseFunds(escrow_id).build_transaction(
        {
            "from": signer.address,
            "nonce": nonce,
            "gasPrice": gas_price,
        }
    )
    signed_tx = signer.sign_transaction(transaction)
    tx_hash = web3.eth.send_raw_transaction(signed_tx.rawTransaction)
    return web3.to_hex(tx_hash)


@APP.post("/verify-ownership")
async def verify_ownership(payload: OwnershipVerificationRequest) -> dict[str, bool]:
    is_valid = verify_owner_transfer(
        asset_id=payload.asset_id,
        new_owner_email=payload.new_owner_email,
        google_oauth_token=payload.google_oauth_token,
    )
    return {"verified": is_valid}


@APP.post("/release", response_model=ReleaseResponse)
async def release(payload: ReleaseRequest) -> ReleaseResponse:
    is_valid = verify_owner_transfer(
        asset_id=payload.asset_id,
        new_owner_email=payload.new_owner_email,
        google_oauth_token=payload.google_oauth_token,
    )
    if not is_valid:
        raise HTTPException(status_code=403, detail="Ownership transfer not verified.")

    tx_hash = release_funds(payload.escrow_id)
    return ReleaseResponse(tx_hash=tx_hash)
