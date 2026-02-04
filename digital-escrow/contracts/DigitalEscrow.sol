// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

import {IERC20} from "./IERC20.sol";

contract DigitalEscrow {
    enum Status {
        Pending,
        Released,
        Refunded
    }

    struct EscrowDeal {
        address buyer;
        address seller;
        address token;
        uint256 amount;
        Status status;
    }

    mapping(uint256 => EscrowDeal) public escrows;
    uint256 public escrowCount;
    address public owner;

    event EscrowCreated(uint256 indexed escrowId, address indexed buyer, address indexed seller);
    event FundsReleased(uint256 indexed escrowId);
    event FundsRefunded(uint256 indexed escrowId);

    modifier onlyOwner() {
        require(msg.sender == owner, "Only owner");
        _;
    }

    constructor() {
        owner = msg.sender;
    }

    function createEscrow(address seller, address token, uint256 amount) external payable returns (uint256) {
        if (token == address(0)) {
            require(msg.value == amount, "ETH amount mismatch");
        } else {
            require(msg.value == 0, "No ETH when using token");
            IERC20(token).transferFrom(msg.sender, address(this), amount);
        }

        escrowCount += 1;
        escrows[escrowCount] = EscrowDeal({
            buyer: msg.sender,
            seller: seller,
            token: token,
            amount: amount,
            status: Status.Pending
        });

        emit EscrowCreated(escrowCount, msg.sender, seller);
        return escrowCount;
    }

    function releaseFunds(uint256 escrowId) external onlyOwner {
        EscrowDeal storage escrow = escrows[escrowId];
        require(escrow.status == Status.Pending, "Escrow not pending");
        escrow.status = Status.Released;

        if (escrow.token == address(0)) {
            payable(escrow.seller).transfer(escrow.amount);
        } else {
            IERC20(escrow.token).transfer(escrow.seller, escrow.amount);
        }

        emit FundsReleased(escrowId);
    }

    function refund(uint256 escrowId) external onlyOwner {
        EscrowDeal storage escrow = escrows[escrowId];
        require(escrow.status == Status.Pending, "Escrow not pending");
        escrow.status = Status.Refunded;

        if (escrow.token == address(0)) {
            payable(escrow.buyer).transfer(escrow.amount);
        } else {
            IERC20(escrow.token).transfer(escrow.buyer, escrow.amount);
        }

        emit FundsRefunded(escrowId);
    }
}
