import math


def calculate_emi(
    principal: float,
    annual_interest_rate: float,
    tenure_months: int,
):
    """
    Calculates EMI using declining balance method.

    EMI = [P x R x (1+R)^N] / [(1+R)^N - 1]

    Returns:
    - emi_amount (monthly EMI)
    - total_payable (EMI * tenure)
    """

    if principal <= 0 or tenure_months <= 0:
        raise ValueError("Invalid principal or tenure")

    # Convert annual rate (%) to monthly decimal rate
    monthly_rate = (annual_interest_rate / 100) / 12

    # EMI formula
    emi = (
        principal
        * monthly_rate
        * math.pow(1 + monthly_rate, tenure_months)
    ) / (
        math.pow(1 + monthly_rate, tenure_months) - 1
    )

    emi = round(emi, 2)
    total_payable = round(emi * tenure_months, 2)

    return {
        "emi": emi,
        "total_payable": total_payable,
    }


def generate_emi_schedule(
    principal: float,
    annual_interest_rate: float,
    tenure_months: int,
):
    """
    Generates month-wise EMI breakdown showing
    declining principal.
    """

    result = calculate_emi(principal, annual_interest_rate, tenure_months)
    emi = result["emi"]

    monthly_rate = (annual_interest_rate / 100) / 12
    balance = principal

    schedule = []

    for month in range(1, tenure_months + 1):
        interest_component = round(balance * monthly_rate, 2)
        principal_component = round(emi - interest_component, 2)
        balance = round(balance - principal_component, 2)

        if balance < 0:
            balance = 0

        schedule.append(
            {
                "month": month,
                "emi": emi,
                "principal_paid": principal_component,
                "interest_paid": interest_component,
                "remaining_balance": balance,
            }
        )

    return schedule
