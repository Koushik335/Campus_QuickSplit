# Campus_QuickSplit
A local-first student expense tracker for splitting group costs, calculating balances, and managing shared campus expenses with minimal friction.

## Screenshots

### Dashboard
<img width="293" height="656" alt="Screenshot 2026-08-30 155054" src="https://github.com/user-attachments/assets/40ef3df3-3ba3-43ca-bbc7-9514f21f5531" />


### Add Expense
<img width="307" height="661" alt="image" src="https://github.com/user-attachments/assets/3db5ccd7-05f3-4e75-8ece-5035f001bb93" />


### Activity Log
<img width="302" height="222" alt="image" src="https://github.com/user-attachments/assets/13670e7c-ba5a-455b-92ec-6388276849c0" />
# Campus QuickSplit

## Frictionless Local-First Peer Expense Tracker

Campus QuickSplit is a lightweight peer expense tracker designed for students to manage shared campus expenses with minimal friction.

The app supports common situations such as:

- Daily auto rides
- Food bills
- Group subscriptions
- Printout costs
- Other shared expenses

## Phase 1 Requirements Covered

- Standard equal distribution
- Expense name and category
- Expense amount
- Participant selection
- Payer selection
- Automatic per-person split calculation
- Aggregated balance dashboard
- Member-wise net balances
- Time-ordered activity log
- Category indicators
- Input validation
- No phone-number login
- Local-first operation
- Local JSON data storage
- Separate payer and participant logic

## Key Expense Logic

### Participants

Participants are selected explicitly.

The current user is **not automatically included**.

To include the current user while typing participant names, use:

```text
ME

