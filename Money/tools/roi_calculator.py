"""
HVAC AI Dispatch — Premium Client ROI Calculator
HOUSTON SHOP EDITION — 2026
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text
from rich import box

console = Console()

def calculate_roi(
    weekly_calls: int = 60,
    missed_call_pct: float = 0.20,
    avg_ticket_usd: float = 350.0,
    monthly_retainer: float = 397.0,
    setup_fee: float = 1997.0,
    dispatch_savings_hrs_per_week: float = 12.0,
    owner_hourly_value: float = 75.0,
) -> dict:
    monthly_calls       = weekly_calls * 4.34
    missed_calls_mo     = monthly_calls * missed_call_pct
    revenue_captured    = missed_calls_mo * avg_ticket_usd
    time_savings_mo     = dispatch_savings_hrs_per_week * 4.34 * owner_hourly_value
    total_monthly_value = revenue_captured + time_savings_mo
    net_roi_monthly     = total_monthly_value - monthly_retainer
    
    payback_days = (setup_fee / (net_roi_monthly / 30.4)) if net_roi_monthly > 0 else 9999
    annual_net   = (net_roi_monthly * 12) - setup_fee

    return {
        "revenue_mo": f"${revenue_captured:,.0f}",
        "time_mo": f"${time_savings_mo:,.0f}",
        "total_mo": f"${total_monthly_value:,.0f}",
        "net_mo": f"${net_roi_monthly:,.0f}",
        "payback": f"{payback_days:.0f} days",
        "year_1": f"${annual_net:,.0f}",
        "ratio": f"{total_monthly_value/monthly_retainer:.1f}x"
    }

def display_industrial_roi_matrix():
    console.print(Panel(
        Text("HOUSTON DISPATCH NODE // REVENUE RECOVERY MATRIX", justify="center", style="bold blue"),
        subtitle="COBALT INDUSTRIAL PROTOCOL // 2026",
        box=box.SQUARE
    ))

    scenarios = [
        ("Fleet_Alpha (1-3 Units)", 40, 0.25, 280),
        ("Fleet_Beta (4-8 Units)", 80, 0.20, 350),
        ("Fleet_Gamma (9+ Units)", 160, 0.15, 420),
    ]

    table = Table(title="Node Projection Matrix: Houston Market v1.1", box=box.SIMPLE_HEAVY, header_style="bold blue")
    table.add_column("Operation Vector", style="dim", width=25)
    table.add_column("Monthly Delta", justify="right", style="green")
    table.add_column("Net Operational Profit", justify="right", style="bold blue")
    table.add_column("Amortization", justify="center", style="dim italic")
    table.add_column("Annual Net Yield", justify="right", style="bold white")
    table.add_column("Efficiency Ratio", justify="center", style="bold cyan")

    for label, calls, pct, tkt in scenarios:
        res = calculate_roi(weekly_calls=calls, missed_call_pct=pct, avg_ticket_usd=tkt)
        table.add_row(
            label, 
            res['revenue_mo'], 
            res['net_mo'], 
            res['payback'], 
            res['year_1'], 
            res['ratio']
        )

    console.print(table)
    console.print("\n[dim]*Industrial parameters: $397_Retainer // $1,997_Setup // Houston-Market-Adjusted.[/]")
    console.print("[bold blue]STATUS:[/] Ready for Fleet Integration. [bold white]Execute Node Deployment.[/]\n")

if __name__ == "__main__":
    display_industrial_roi_matrix()
