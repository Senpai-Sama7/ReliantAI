
import json
import csv
import os

# ── AR DOCUMENT ──────────────────────────────────────────────────────────────

ar_csv_rows = [
    ["SWIFT HAUL TRANSPORT - ACCOUNTS RECEIVABLE STATEMENT"],
    ["Statement Date", "2026-03-02"],
    ["Account Number", "AR-2026-1142"],
    ["Prepared By", "Lisa Nguyen, AR Specialist"],
    [],
    ["CUSTOMER INFORMATION"],
    ["Account Name", "Lone Star Distribution LLC"],
    ["Contact", "David Garza, AP Manager"],
    ["Address", "3300 Miller Road, Dallas, TX 75217"],
    ["Phone", "(214) 555-0411"],
    ["Email", "dgarza@lonestardist.com"],
    [],
    ["ACCOUNT SUMMARY"],
    ["Category", "Amount"],
    ["Current (0-30 Days)", "$12,400.00"],
    ["30 Days Past Due", "$18,750.00"],
    ["60 Days Past Due", "$9,325.50"],
    ["90+ Days Past Due", "$34,820.00"],
    ["TOTAL OUTSTANDING", "$75,295.50"],
    [],
    ["INVOICE AGING DETAIL"],
    ["Invoice #", "Invoice Date", "Due Date", "Original Amount", "Paid", "Balance", "Days Past Due", "Status"],
    ["SHT-2025-4401", "2025-09-15", "2025-10-15", "$34,820.00", "$0.00", "$34,820.00", "138", "OVERDUE"],
    ["SHT-2025-4887", "2025-11-20", "2025-12-20", "$9,325.50", "$0.00", "$9,325.50", "72", "OVERDUE"],
    ["SHT-2026-0091", "2026-01-10", "2026-02-09", "$18,750.00", "$0.00", "$18,750.00", "21", "OVERDUE"],
    ["SHT-2026-0204", "2026-02-01", "2026-03-03", "$12,400.00", "$0.00", "$12,400.00", "0", "CURRENT"],
    [],
    ["LATE FEES"],
    ["Late Fee Rate", "2.5% monthly on balances 60+ days"],
    ["Late Fee Assessed", "$1,103.64"],
    ["Credit Hold Status", "ACTIVE as of 2026-02-20"],
    [],
    ["PAYMENT DEADLINE", "2026-03-15"],
    ["Next Action", "Escalate to collections if no payment plan by deadline"],
]

with open("AR_SwiftHaul_LoneStarDist.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(ar_csv_rows)

ar_json = {
    "documentType": "Accounts Receivable Statement",
    "priority": 5,
    "issuer": {
        "company": "Swift Haul Transport",
        "address": "7800 Freight Corridor Drive, Fort Worth, TX 76104",
        "phone": "(817) 555-0300",
        "email": "ar@swifthaul.com"
    },
    "customer": {
        "accountName": "Lone Star Distribution LLC",
        "accountNumber": "AR-2026-1142",
        "contact": "David Garza, AP Manager",
        "address": "3300 Miller Road, Dallas, TX 75217",
        "phone": "(214) 555-0411",
        "email": "dgarza@lonestardist.com"
    },
    "statementDate": "2026-03-02",
    "paymentDeadline": "2026-03-15",
    "accountSummary": {
        "current_0_30": "$12,400.00",
        "pastDue_30": "$18,750.00",
        "pastDue_60": "$9,325.50",
        "pastDue_90plus": "$34,820.00",
        "totalOutstanding": "$75,295.50",
        "lateFeeAssessed": "$1,103.64",
        "creditHoldStatus": "ACTIVE",
        "creditHoldDate": "2026-02-20"
    },
    "invoices": [
        {"invoiceNumber": "SHT-2025-4401", "invoiceDate": "2025-09-15", "dueDate": "2025-10-15", "originalAmount": "$34,820.00", "paid": "$0.00", "balance": "$34,820.00", "daysPastDue": 138, "status": "OVERDUE"},
        {"invoiceNumber": "SHT-2025-4887", "invoiceDate": "2025-11-20", "dueDate": "2025-12-20", "originalAmount": "$9,325.50", "paid": "$0.00", "balance": "$9,325.50", "daysPastDue": 72, "status": "OVERDUE"},
        {"invoiceNumber": "SHT-2026-0091", "invoiceDate": "2026-01-10", "dueDate": "2026-02-09", "originalAmount": "$18,750.00", "paid": "$0.00", "balance": "$18,750.00", "daysPastDue": 21, "status": "OVERDUE"},
        {"invoiceNumber": "SHT-2026-0204", "invoiceDate": "2026-02-01", "dueDate": "2026-03-03", "originalAmount": "$12,400.00", "paid": "$0.00", "balance": "$12,400.00", "daysPastDue": 0, "status": "CURRENT"}
    ],
    "communications": [
        {"date": "2026-02-14", "from": "David Garza", "note": "Disputes invoice SHT-2025-4401 – claims freight was delivered late causing $12,000 in downstream losses. Requesting credit memo."},
        {"date": "2026-02-22", "from": "AR Manager Tom Willis", "note": "Customer provided signed delivery receipts showing 4-day delay. Reviewing against SLA contract. Late delivery penalty clause may apply both ways."},
        {"date": "2026-03-01", "from": "David Garza", "note": "Will not pay any invoices until oldest dispute is resolved. Requests meeting with account manager this week."}
    ],
    "entities": {
        "amount": "$75,295.50",
        "dueDate": "2026-03-15",
        "accountName": "Lone Star Distribution LLC",
        "actionRequired": "Schedule dispute resolution meeting. Verify SLA terms on SHT-2025-4401. Maintain credit hold."
    },
    "summary": "Lone Star Distribution owes $75,295.50 across four invoices, with $34,820 over 138 days past due. Customer is withholding all payments pending resolution of a late delivery dispute on the oldest invoice. Credit hold is active. Deadline for payment plan is March 15 or account moves to external collections.",
    "recommendedAction": "Schedule immediate meeting with customer to address SLA dispute. Pull delivery logs and contract SLA terms for invoice SHT-2025-4401. If late delivery confirmed, assess partial credit before escalating remaining balance.",
    "requiresHumanReview": True,
    "escalationReasons": [
        {"type": "Payment Withholding", "description": "Customer refusing all payments pending oldest invoice dispute resolution", "triggeringField": "communications"},
        {"type": "SLA Dispute", "description": "Late delivery claim on $34,820 invoice may trigger contractual penalty clause in either direction", "triggeringField": "invoices[0]"},
        {"type": "High Balance + Credit Hold", "description": "Total exposure $75,295.50 with active credit hold and approaching external collections deadline", "triggeringField": "accountSummary.totalOutstanding"}
    ]
}

with open("AR_SwiftHaul_LoneStarDist.json", "w") as f:
    json.dump(ar_json, f, indent=2)

ar_txt = """
================================================================================
         SWIFT HAUL TRANSPORT — ACCOUNTS RECEIVABLE STATEMENT
================================================================================
Statement Date : March 2, 2026
Account Number : AR-2026-1142
Prepared By    : Lisa Nguyen, AR Specialist

REMIT TO:
  Swift Haul Transport
  7800 Freight Corridor Drive
  Fort Worth, TX 76104
  ar@swifthaul.com | (817) 555-0300

--------------------------------------------------------------------------------
CUSTOMER ACCOUNT
--------------------------------------------------------------------------------
  Account Name : Lone Star Distribution LLC
  Contact      : David Garza, AP Manager
  Address      : 3300 Miller Road, Dallas, TX 75217
  Phone        : (214) 555-0411
  Email        : dgarza@lonestardist.com

--------------------------------------------------------------------------------
ACCOUNT SUMMARY
--------------------------------------------------------------------------------
  Current (0-30 Days)       $12,400.00
  30 Days Past Due          $18,750.00
  60 Days Past Due           $9,325.50
  90+ Days Past Due         $34,820.00
                           -----------
  TOTAL OUTSTANDING         $75,295.50
  Late Fee Assessed          $1,103.64
  Credit Hold Status        ACTIVE (since 2026-02-20)

--------------------------------------------------------------------------------
INVOICE AGING DETAIL
--------------------------------------------------------------------------------
  Invoice #        Date        Due Date    Amount      Paid    Balance    Days  Status
  SHT-2025-4401   09/15/2025  10/15/2025  $34,820.00  $0.00  $34,820.00  138  OVERDUE
  SHT-2025-4887   11/20/2025  12/20/2025   $9,325.50  $0.00   $9,325.50   72  OVERDUE
  SHT-2026-0091   01/10/2026  02/09/2026  $18,750.00  $0.00  $18,750.00   21  OVERDUE
  SHT-2026-0204   02/01/2026  03/03/2026  $12,400.00  $0.00  $12,400.00    0  CURRENT

--------------------------------------------------------------------------------
COMMUNICATIONS LOG
--------------------------------------------------------------------------------
  02/14/2026 – David Garza (Customer):
    Disputes invoice SHT-2025-4401. Claims freight arrived 4 days late causing
    $12,000 in downstream warehouse losses. Requesting credit memo before any
    payment is made.

  02/22/2026 – Tom Willis (AR Manager):
    Customer provided signed delivery receipts confirming 4-day delay. Reviewing
    SLA contract terms — late delivery penalty clause may apply in either direction.

  03/01/2026 – David Garza (Customer):
    Confirming they will not pay any invoices until oldest dispute is resolved.
    Requesting in-person meeting with account manager this week.

--------------------------------------------------------------------------------
URGENT NOTICES
--------------------------------------------------------------------------------
  *** CREDIT HOLD ACTIVE — No new shipments authorized ***
  *** PAYMENT DEADLINE: March 15, 2026 ***
  *** No payment plan = referral to external collections ***

--------------------------------------------------------------------------------
NEXT ACTIONS REQUIRED
--------------------------------------------------------------------------------
  1. Schedule dispute resolution meeting with David Garza re: SHT-2025-4401
  2. Pull GPS/delivery logs to verify late delivery date
  3. Legal review of SLA contract Section 4.2 (delivery penalty clause)
  4. If partial credit approved — issue credit memo and reissue aging statement
  5. Escalate to Collections Manager if no resolution by March 10

================================================================================
  PREPARED BY: Lisa Nguyen, AR Specialist
  APPROVED BY: [PENDING REVIEW]
  GENERATED  : 2026-03-02 06:00 PM CST
================================================================================
""".strip()

with open("AR_SwiftHaul_LoneStarDist.txt", "w") as f:
    f.write(ar_txt)


# ── COLLECTIONS NOTICE ───────────────────────────────────────────────────────

col_csv_rows = [
    ["IRONCLAD RECEIVABLES GROUP - COLLECTIONS NOTICE"],
    ["Notice Type", "Final Demand Before Legal Action"],
    ["Notice Date", "2026-03-02"],
    ["Reference #", "IRG-2026-TX-7731"],
    [],
    ["ORIGINAL CREDITOR"],
    ["Company", "Swift Haul Transport"],
    ["Original Account #", "SHT-AR-2025-0093"],
    ["Charge-Off Date", "2026-02-01"],
    [],
    ["DEBTOR INFORMATION"],
    ["Company", "Panhandle Freight Brokers Inc."],
    ["Contact", "Robert Vega, CFO"],
    ["Address", "510 Commerce Street, Amarillo, TX 79101"],
    ["Phone", "(806) 555-0214"],
    ["Email", "rvega@panhandlefreight.com"],
    [],
    ["AMOUNT DEMANDED"],
    ["Description", "Amount"],
    ["Original Principal Balance", "$52,300.00"],
    ["Accrued Interest (16% APR)", "$4,612.44"],
    ["Late Fees", "$1,569.00"],
    ["Collection Agency Costs", "$1,200.00"],
    ["TOTAL AMOUNT DUE", "$59,681.44"],
    [],
    ["PAYMENT DEADLINE", "2026-03-09 17:00 CST"],
    [],
    ["SETTLEMENT OPTIONS"],
    ["Option", "Terms", "Deadline"],
    ["A - Pay in Full", "$59,681.44", "2026-03-09"],
    ["B - Lump Sum Settlement", "$44,000.00", "2026-03-06 (written agreement required)"],
    ["C - Payment Plan", "$15,000 down + $5,500/mo x 9 months", "2026-03-09 (secured payment method required)"],
    [],
    ["DISPUTES LOG"],
    ["Date", "Party", "Note"],
    ["2026-02-10", "Robert Vega (Debtor)", "Claims $28,000 of principal relates to disputed loads never delivered. Has BOL discrepancies as evidence."],
    ["2026-02-17", "Collections Agent Ana Torres", "Reviewed BOLs provided. Two loads show signed POD by debtor's own warehouse — delivery confirmed. Third load ($8,400) has no POD on file from creditor. Escalated to Swift Haul for documentation."],
    ["2026-02-24", "Swift Haul (Original Creditor)", "Provided POD for two loads. Third load POD still missing — driver retired and GPS records show delivery location matches debtor warehouse."],
]

with open("Collections_IroncladsRG_PanhandleFreight.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(col_csv_rows)

col_json = {
    "documentType": "Collections Notice - Final Demand",
    "priority": 5,
    "collectionAgency": {
        "company": "Ironclad Receivables Group",
        "license": "TX-COL-3341-2025",
        "address": "1600 Main Street, Suite 900, Houston, TX 77002",
        "tollFree": "1-888-555-0741",
        "direct": "(713) 555-0741",
        "fax": "(713) 555-0742"
    },
    "originalCreditor": {
        "company": "Swift Haul Transport",
        "originalAccountNumber": "SHT-AR-2025-0093",
        "chargeOffDate": "2026-02-01"
    },
    "debtor": {
        "company": "Panhandle Freight Brokers Inc.",
        "contact": "Robert Vega, CFO",
        "address": "510 Commerce Street, Amarillo, TX 79101",
        "phone": "(806) 555-0214",
        "email": "rvega@panhandlefreight.com"
    },
    "referenceNumber": "IRG-2026-TX-7731",
    "noticeDate": "2026-03-02",
    "paymentDeadline": "2026-03-09T17:00:00-06:00",
    "amountDemanded": {
        "principalBalance": "$52,300.00",
        "accruedInterest_16pct_APR": "$4,612.44",
        "lateFees": "$1,569.00",
        "collectionCosts": "$1,200.00",
        "totalDue": "$59,681.44"
    },
    "settlementOptions": [
        {"option": "A", "description": "Pay in full", "amount": "$59,681.44", "deadline": "2026-03-09"},
        {"option": "B", "description": "Lump sum settlement", "amount": "$44,000.00", "deadline": "2026-03-06", "notes": "Written agreement required"},
        {"option": "C", "description": "Payment plan", "downPayment": "$15,000.00", "monthlyPayment": "$5,500.00", "months": 9, "totalPayable": "$64,500.00", "deadline": "2026-03-09", "notes": "Secured payment method required"}
    ],
    "disputesLog": [
        {"date": "2026-02-10", "party": "Robert Vega (Debtor)", "note": "Claims $28,000 of principal relates to loads never delivered. Providing BOL discrepancy evidence."},
        {"date": "2026-02-17", "party": "Collections Agent Ana Torres", "note": "Two disputed loads confirmed delivered per debtor-signed PODs. Third load ($8,400) has no POD from creditor. Escalated to Swift Haul."},
        {"date": "2026-02-24", "party": "Swift Haul (Creditor)", "note": "POD provided for two loads. Third load POD still missing. GPS records support delivery to debtor's warehouse."}
    ],
    "legalTimeline": [
        {"date": "2026-03-09", "event": "Payment deadline 5:00 PM CST"},
        {"date": "2026-03-10", "event": "Legal filing recommendation submitted if no payment"},
        {"date": "2026-03-17", "event": "Estimated civil lawsuit filing, Harris County District Court"},
        {"date": "post-filing", "event": "Additional court costs, attorney fees up to 35% of balance, judgment interest applies"}
    ],
    "entities": {
        "amount": "$59,681.44",
        "dueDate": "2026-03-09 17:00 CST",
        "accountName": "Panhandle Freight Brokers Inc.",
        "actionRequired": "Debtor must pay or confirm settlement by deadline. One load ($8,400) has missing POD — resolve before filing."
    },
    "summary": "Final collections demand for $59,681.44 against Panhandle Freight Brokers with a March 9 deadline before lawsuit. Debtor disputes $28,000 in charges claiming non-delivery. Two of three disputed loads are confirmed delivered via signed PODs. The third load ($8,400) has no proof of delivery on file — this is the critical unresolved item that must be addressed before legal action can be confidently pursued.",
    "recommendedAction": "Obtain GPS records and attempt to retrieve POD for third disputed load ($8,400) before March 9. If POD cannot be found, assess risk of litigating disputed portion. Confirm debtor's willingness to pay undisputed balance ($51,281.44) as partial settlement.",
    "requiresHumanReview": True,
    "escalationReasons": [
        {"type": "Missing Proof of Delivery", "description": "One load ($8,400) has no POD — weak legal position if debtor contests delivery in court", "triggeringField": "disputesLog[1]"},
        {"type": "Imminent Legal Deadline", "description": "Payment deadline March 9 at 5PM CST with lawsuit filing scheduled March 17", "triggeringField": "paymentDeadline"},
        {"type": "Partial Dispute Validity", "description": "Debtor's dispute partially valid — weakens full claim amount in court proceedings", "triggeringField": "amountDemanded.principalBalance"}
    ]
}

with open("Collections_IroncladsRG_PanhandleFreight.json", "w") as f:
    json.dump(col_json, f, indent=2)

col_txt = """
================================================================================
    IRONCLAD RECEIVABLES GROUP — FINAL NOTICE BEFORE LEGAL ACTION
================================================================================
License        : TX-COL-3341-2025
Notice Date    : March 2, 2026
Reference #    : IRG-2026-TX-7731

  Ironclad Receivables Group
  1600 Main Street, Suite 900
  Houston, TX 77002
  Toll-Free: 1-888-555-0741 | Direct: (713) 555-0741

--------------------------------------------------------------------------------
ORIGINAL CREDITOR
--------------------------------------------------------------------------------
  Company          : Swift Haul Transport
  Original Acct #  : SHT-AR-2025-0093
  Charge-Off Date  : February 1, 2026

--------------------------------------------------------------------------------
DEBTOR
--------------------------------------------------------------------------------
  Company  : Panhandle Freight Brokers Inc.
  Contact  : Robert Vega, CFO
  Address  : 510 Commerce Street, Amarillo, TX 79101
  Phone    : (806) 555-0214
  Email    : rvega@panhandlefreight.com

--------------------------------------------------------------------------------
AMOUNT DEMANDED
--------------------------------------------------------------------------------
  Original Principal Balance       $52,300.00
  Accrued Interest (16% APR)        $4,612.44
  Late Fees                         $1,569.00
  Collection Agency Costs           $1,200.00
                                  -----------
  TOTAL AMOUNT DUE                 $59,681.44

  *** PAYMENT DEADLINE: March 9, 2026 at 5:00 PM CST ***

--------------------------------------------------------------------------------
LEGAL TIMELINE
--------------------------------------------------------------------------------
  March 9, 2026  — Payment deadline. Payment or settlement must be confirmed.
  March 10, 2026 — Legal filing recommendation submitted to attorney.
  March 17, 2026 — Estimated civil lawsuit filing, Harris County District Court.
  Post-Filing    — Court costs + attorney fees (up to 35% of balance) added.

--------------------------------------------------------------------------------
SETTLEMENT OPTIONS (if resolved by deadline)
--------------------------------------------------------------------------------
  Option A: Pay in full              $59,681.44    Deadline: March 9
  Option B: Lump-sum settlement      $44,000.00    Deadline: March 6 (written agreement)
  Option C: Payment plan             $15,000 down + $5,500/month x 9 months
                                     (Total: $64,500 | Secured payment required)

--------------------------------------------------------------------------------
DISPUTES LOG
--------------------------------------------------------------------------------
  02/10/2026 – Robert Vega (Debtor):
    Disputes $28,000 of principal. Claims three loads were never delivered.
    Submitting BOL discrepancy documents as evidence.

  02/17/2026 – Ana Torres (Collections Agent):
    Reviewed BOLs. Two loads confirmed delivered — debtor's own warehouse signed
    the PODs. Third load ($8,400) has no POD on creditor's file. Escalated to
    Swift Haul Transport for documentation.

  02/24/2026 – Swift Haul Transport (Original Creditor):
    Provided POD for two confirmed loads. Third load POD remains missing.
    Retired driver cannot be reached. GPS records show truck was at debtor's
    warehouse address at delivery time.

--------------------------------------------------------------------------------
LEGAL NOTICES (FDCPA)
--------------------------------------------------------------------------------
  This is an attempt to collect a debt. Any information obtained will be
  used for that purpose. You have the right to dispute this debt within
  30 days and request verification.

  *** INTERNAL FLAG: Third load ($8,400) lacks POD. Do NOT file lawsuit
  until legal team reviews strength of this claim. ***

--------------------------------------------------------------------------------
CONTACT
--------------------------------------------------------------------------------
  Collections Agent : Ana Torres | atorres@ironclad-rg.com | (713) 555-0743
  Legal Department  : (713) 555-0744 | Fax: (713) 555-0742

================================================================================
  PREPARED BY: Ana Torres, Senior Collections Agent
  SUPERVISED BY: Mark Ellison, Collections Director
  ACCOUNT STATUS: ACTIVE COLLECTIONS — LEGAL REVIEW PENDING
================================================================================
""".strip()

with open("Collections_IroncladsRG_PanhandleFreight.txt", "w") as f:
    f.write(col_txt)


# ── INVOICE ──────────────────────────────────────────────────────────────────

inv_csv_rows = [
    ["SWIFT HAUL TRANSPORT - FREIGHT INVOICE"],
    ["Invoice Number", "SHT-2026-0388"],
    ["Invoice Date", "2026-02-20"],
    ["Due Date", "2026-03-22"],
    ["PO Number", "LST-PO-20260210"],
    [],
    ["BILL TO"],
    ["Company", "Lone Star Distribution LLC"],
    ["Attention", "David Garza, AP Manager"],
    ["Address", "3300 Miller Road, Dallas, TX 75217"],
    ["Phone", "(214) 555-0411"],
    ["Email", "dgarza@lonestardist.com"],
    [],
    ["SHIP FROM / TO"],
    ["Origin", "Fort Worth Distribution Hub, 7800 Freight Corridor Dr, Fort Worth TX 76104"],
    ["Destination", "Lone Star Distribution Center, 3300 Miller Road, Dallas TX 75217"],
    ["Pickup Date", "2026-02-10"],
    ["Delivery Date", "2026-02-12"],
    ["BOL Number", "BOL-2026-0388-A"],
    ["Driver", "James Ortega"],
    ["Truck #", "SHT-TRK-047"],
    [],
    ["LINE ITEMS"],
    ["Line", "Description", "Quantity", "Unit", "Unit Price", "Extended", "Notes"],
    ["1", "LTL Freight – Fort Worth to Dallas (22 pallets)", "22", "pallets", "$138.00", "$3,036.00", ""],
    ["2", "Fuel Surcharge (11.5%)", "—", "—", "—", "$349.14", "Rate effective 2/1/2026"],
    ["3", "Residential/Limited Access Delivery Fee", "1", "stop", "$175.00", "$175.00", "Customer warehouse has height restriction"],
    ["4", "Pallet Exchange", "22", "pallets", "$12.00", "$264.00", "Per tariff section 3.4"],
    ["5", "Liftgate Service", "1", "stop", "$95.00", "$95.00", "Requested day-of by receiver"],
    ["6", "Detention – Driver Wait Time", "1.5", "hours", "$75.00", "$112.50", "Gate closed at scheduled arrival"],
    ["7", "Insurance – Declared Value ($85,000)", "—", "—", "—", "$68.00", "Standard cargo coverage"],
    [],
    ["TOTALS"],
    ["Subtotal", "$4,099.64"],
    ["Early Payment Discount (2% if paid by 3/2/2026)", "-$82.00"],
    ["Subtotal After Discount", "$4,017.64"],
    ["Sales Tax (8.25%)", "$331.46"],
    ["TOTAL AMOUNT DUE", "$4,349.10"],
    [],
    ["PAYMENT TERMS"],
    ["Terms", "Net 30"],
    ["Early Payment Discount", "2% if paid by 2026-03-02 (EXPIRED)"],
    ["Late Penalty", "1.5% per month on overdue balance"],
    ["Accepted Methods", "ACH, Wire Transfer, Check, Credit Card (+3.5% fee)"],
    [],
    ["PAYMENT STATUS", "UNPAID"],
    ["Customer Dispute", "Liftgate charge ($95) disputed — claims was not requested"],
    ["Detention Dispute", "Detention time ($112.50) disputed — claims gate was open"],
]

with open("Invoice_SwiftHaul_LoneStarDist.csv", "w", newline="") as f:
    writer = csv.writer(f)
    writer.writerows(inv_csv_rows)

inv_json = {
    "documentType": "Freight Invoice",
    "priority": 3,
    "invoiceNumber": "SHT-2026-0388",
    "invoiceDate": "2026-02-20",
    "dueDate": "2026-03-22",
    "poNumber": "LST-PO-20260210",
    "bolNumber": "BOL-2026-0388-A",
    "issuer": {
        "company": "Swift Haul Transport",
        "address": "7800 Freight Corridor Drive, Fort Worth, TX 76104",
        "phone": "(817) 555-0300",
        "email": "billing@swifthaul.com",
        "dotNumber": "DOT-1847293",
        "mcNumber": "MC-774821"
    },
    "billTo": {
        "company": "Lone Star Distribution LLC",
        "contact": "David Garza, AP Manager",
        "address": "3300 Miller Road, Dallas, TX 75217",
        "phone": "(214) 555-0411",
        "email": "dgarza@lonestardist.com"
    },
    "shipment": {
        "origin": "Fort Worth Distribution Hub, 7800 Freight Corridor Dr, Fort Worth TX 76104",
        "destination": "Lone Star Distribution Center, 3300 Miller Road, Dallas TX 75217",
        "pickupDate": "2026-02-10",
        "deliveryDate": "2026-02-12",
        "pallets": 22,
        "driver": "James Ortega",
        "truckNumber": "SHT-TRK-047",
        "deliverySignedBy": "Maria Castillo, Receiving Supervisor"
    },
    "lineItems": [
        {"line": 1, "description": "LTL Freight – Fort Worth to Dallas (22 pallets)", "qty": 22, "unit": "pallets", "unitPrice": "$138.00", "extended": "$3,036.00"},
        {"line": 2, "description": "Fuel Surcharge (11.5%)", "qty": None, "unit": None, "unitPrice": None, "extended": "$349.14", "notes": "Rate effective 2/1/2026"},
        {"line": 3, "description": "Residential/Limited Access Delivery Fee", "qty": 1, "unit": "stop", "unitPrice": "$175.00", "extended": "$175.00", "notes": "Customer warehouse height restriction"},
        {"line": 4, "description": "Pallet Exchange", "qty": 22, "unit": "pallets", "unitPrice": "$12.00", "extended": "$264.00", "notes": "Per tariff section 3.4"},
        {"line": 5, "description": "Liftgate Service", "qty": 1, "unit": "stop", "unitPrice": "$95.00", "extended": "$95.00", "notes": "Requested day-of by receiver — DISPUTED"},
        {"line": 6, "description": "Detention – Driver Wait Time", "qty": 1.5, "unit": "hours", "unitPrice": "$75.00/hr", "extended": "$112.50", "notes": "Gate closed at scheduled arrival — DISPUTED"},
        {"line": 7, "description": "Insurance – Declared Value $85,000", "qty": None, "unit": None, "unitPrice": None, "extended": "$68.00"}
    ],
    "calculations": {
        "subtotal": "$4,099.64",
        "earlyPaymentDiscount_2pct": "-$82.00",
        "discountExpiry": "2026-03-02",
        "discountStatus": "EXPIRED",
        "subtotalAfterDiscount": "$4,017.64",
        "salesTax_8_25pct": "$331.46",
        "totalAmountDue": "$4,349.10"
    },
    "paymentTerms": {
        "terms": "Net 30",
        "dueDate": "2026-03-22",
        "latePenalty": "1.5% per month",
        "acceptedMethods": ["ACH", "Wire Transfer", "Check", "Credit Card (3.5% fee)"]
    },
    "disputes": [
        {"charge": "Liftgate Service", "amount": "$95.00", "customerClaim": "Liftgate was not requested — receiver says standard dock was available"},
        {"charge": "Detention Time", "amount": "$112.50", "customerClaim": "Gate was open at arrival time — driver may have arrived early"}
    ],
    "entities": {
        "amount": "$4,349.10",
        "dueDate": "2026-03-22",
        "accountName": "Lone Star Distribution LLC",
        "actionRequired": "Verify liftgate and detention charges with driver logs before customer dispute escalates"
    },
    "summary": "Freight invoice for a Fort Worth to Dallas LTL shipment of 22 pallets delivered February 12. Total due $4,349.10 by March 22. Customer disputes two charges: liftgate service ($95) and driver detention ($112.50), totaling $207.50. Early payment discount has expired. Delivery confirmed by signed BOL.",
    "recommendedAction": "Pull driver's electronic log and gate timestamp records to verify detention start time. Confirm liftgate request via dispatch records or driver notes. If both charges verified, provide documentation to customer. If detention arrival was early, adjust charge accordingly.",
    "requiresHumanReview": False,
    "escalationReasons": [
        {"type": "Minor Charge Disputes", "description": "Customer disputes liftgate ($95) and detention ($112.50) — verifiable via driver logs", "triggeringField": "disputes"}
    ]
}

with open("Invoice_SwiftHaul_LoneStarDist.json", "w") as f:
    json.dump(inv_json, f, indent=2)

inv_txt = """
================================================================================
              SWIFT HAUL TRANSPORT — FREIGHT INVOICE
================================================================================
Invoice Number : SHT-2026-0388
Invoice Date   : February 20, 2026
Due Date       : March 22, 2026
PO Number      : LST-PO-20260210
BOL Number     : BOL-2026-0388-A
DOT Number     : DOT-1847293 | MC: MC-774821

FROM (Issuer):
  Swift Haul Transport
  7800 Freight Corridor Drive
  Fort Worth, TX 76104
  (817) 555-0300 | billing@swifthaul.com

BILL TO:
  Lone Star Distribution LLC
  Attn: David Garza, AP Manager
  3300 Miller Road, Dallas, TX 75217
  (214) 555-0411 | dgarza@lonestardist.com

--------------------------------------------------------------------------------
SHIPMENT DETAILS
--------------------------------------------------------------------------------
  Origin     : Fort Worth Distribution Hub, Fort Worth TX 76104
  Destination: Lone Star Distribution Center, Dallas TX 75217
  Pickup     : February 10, 2026
  Delivery   : February 12, 2026
  Pallets    : 22
  Driver     : James Ortega (Truck #SHT-TRK-047)
  Signed By  : Maria Castillo, Receiving Supervisor
  Commodity  : General freight — auto parts (non-hazmat)

--------------------------------------------------------------------------------
LINE ITEMS
--------------------------------------------------------------------------------
  Ln  Description                              Qty    Unit    Unit $   Extended
  --  ---------------------------------------  -----  ------  -------  --------
   1  LTL Freight – Ft Worth to Dallas          22    pallets $138.00  $3,036.00
   2  Fuel Surcharge (11.5%)                     —       —       —      $349.14
   3  Limited Access Delivery Fee                1    stop    $175.00    $175.00
   4  Pallet Exchange (Tariff §3.4)             22    pallets  $12.00    $264.00
   5  Liftgate Service *DISPUTED*                1    stop     $95.00     $95.00
   6  Detention – Driver Wait (1.5 hrs) *DISP*  1.5  hours    $75.00    $112.50
   7  Insurance – Declared Value $85,000         —       —       —       $68.00
                                                                       --------
                                                          SUBTOTAL   $4,099.64

  Early Payment Discount (2% — EXPIRED 3/2/2026)                      -$82.00
  Subtotal After Discount                                            $4,017.64
  Sales Tax (8.25%)                                                    $331.46
                                                                       --------
  TOTAL AMOUNT DUE                                                   $4,349.10

  *** DUE DATE: March 22, 2026 ***
  *** Late penalty: 1.5% per month on overdue balance ***

--------------------------------------------------------------------------------
CUSTOMER DISPUTES
--------------------------------------------------------------------------------
  DISPUTE 1 — Liftgate Service ($95.00)
    Customer claim: Liftgate was not requested. Standard dock was available.
    Our position: Day-of request confirmed by driver James Ortega in dispatch log.
    STATUS: Pending verification — driver log review required.

  DISPUTE 2 — Detention Time ($112.50)
    Customer claim: Gate was open at arrival — driver may have arrived early.
    Our position: Gate closed timestamp on facility log from 2/12 at 07:15 AM.
    STATUS: Pending verification — cross-reference driver ELD + facility logs.

  TOTAL DISPUTED: $207.50
  UNDISPUTED AMOUNT CUSTOMER AGREES TO PAY: $4,141.60

--------------------------------------------------------------------------------
PAYMENT OPTIONS
--------------------------------------------------------------------------------
  ACH / Wire Transfer : Bank details on remittance page 2
  Check               : Mail to Swift Haul Transport, PO Box 7844, Fort Worth TX 76113
  Credit Card         : 3.5% processing fee applies

--------------------------------------------------------------------------------
QUESTIONS / DISPUTES:
  Billing Dept: (817) 555-0301 | billing@swifthaul.com
  Account Mgr : Rachel Torres | (817) 555-0315

================================================================================
  PREPARED BY : Jennifer Hale, Billing Specialist
  APPROVED BY : Rachel Torres, Account Manager
  STATUS      : UNPAID — MINOR DISPUTE PENDING
  GENERATED   : 2026-02-20
================================================================================
""".strip()

with open("Invoice_SwiftHaul_LoneStarDist.txt", "w") as f:
    f.write(inv_txt)

print("All 9 files created successfully:")
for fn in sorted(os.listdir(".")):
    if any(fn.endswith(ext) for ext in [".csv", ".json", ".txt"]) and ("AR_" in fn or "Collections_" in fn or "Invoice_" in fn):
        size = os.path.getsize(fn)
        print(f"  {fn}  ({size:,} bytes)")
