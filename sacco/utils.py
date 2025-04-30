def add_saving_transaction(member, amount, note=''):
    last_statement = SavingStatement.objects.filter(member=member).order_by('-date').first()
    opening_balance = last_statement.running_balance if last_statement else 0.00

    running_balance = opening_balance + amount

    # Save the new savings statement record
    SavingStatement.objects.create(
        member=member,
        amount=amount,
        opening_balance=opening_balance,
        running_balance=running_balance,
        note=note
    )


def create_saving_statement(member, amount, category, deposit_type=None, description=None):
    from .models import SavingStatement
    last_statement = SavingStatement.objects.filter(member=member).order_by('-date').first()
    opening_balance = last_statement.running_balance if last_statement else 0
    running_balance = opening_balance + amount
    return SavingStatement.objects.create(
        member=member,
        amount=amount,
        opening_balance=opening_balance,
        running_balance=running_balance,
        category=category,
        deposit_type=deposit_type,
        description=description or f"Saving deposit of {amount}"
    )
