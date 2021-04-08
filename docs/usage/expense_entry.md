# `adjuftments` Expense Entry

## Airtable Form Setup

The `Expenses` table on `airtable` has a view that becomes a public facing form. My best
recommendation is to save the URL and add it to your home screen using
[iOS Safari or Android Chrome](https://natomasunified.org/kb/add-website-to-mobile-device-home-screen/)
.

<img src="../static/airtable_form.png" alt="drawing" width=50%;/>

## Parts of Submitting an Expense

- `Date`: Expense Date
- `Amount`: Expense Amount
- `Transaction`: Expense Transaction
    - This transaction typically has 2 parts and is split with spaces and a
      hypen (` - `): `<vendor> - <description>`
    - Adding an additional field (separated by the hyphen and spaces) enables some functionality on
      certain transaction categories such as savings (`<vendor> - <description> - <bank account>` )
- `Category`: Expense Category
- `Splitwise`: Check this box to create a splitiwse expense
    - the eventual transaction amount will be half of the `Amount` provided

<img src="../static/airtable_form_submission.png" alt="drawing" width=50%;/>

## Entering Expenses

Entering expenses into Adjuftments is pretty straightforward, with a few tips and tricks.
Essentially every entry besides a few categories (`Rent`, `Mortgage`, `Savings`, `Savings Spend`
, `Income`, `Interest`, `Adjustment`) is considered to be an expense. Creating these expenses is
straightforward. Submitting expenses into these other categories can take some getting used to.
Let's begin with some common examples:

1) Submitting a Savings Transaction
    - Did you move money from your `checking` to primary `savings` account?
        - Great, submit the expense like normal. I will usually put something
          like `"Ally - January Savings"` as the transaction. This will move whatever amount you
          indicate from checking to savings

    - Did you move money from your primary `savings` to `checking` account?
        - Awesome. Do what you did above, just make the amount a negative number

    - Moving money to non-standard accounts
        - If you need to move money from Checkings to your Home Savings Acccount, add a third
          transaction item (described above). There are multiple savings accounts available to be
          used (The "Miscellaneous" savings account is always the default if not specified)
            - Home Savings Account - Accepts `Home` / `House`
                - `Ally Bank - Savings - Home`
            - Shared Savings Account - Accepts `Shared` / `Share`
                - `Ally Bank - Savings - Shared`
            - Miscellaneous Savings Account (default) - Accepts `Misc` / `Miscellaneous`
                - `Ally Bank - Savings - Misc`

    - Spending Money Directly from the Savings Account
        - There are times when you would like to spend money directly from your savings account.
          Rather than recording a transfer from savings to checking, and then the actual transaction
          itself, you can submit an expense with the category `Savings Spend`. Using the same
          savings account methodology as above, you can specify which account the money should be
          taken from. This sounds kind of complicated, but it is useful when you would like to buy
          something with saved money, but don't want your monthly spending to be thrown off.

2) Submitting Income Expenses
    - Submitting Income expenses is easy, you just have to remember that you need to put in a
      negative number. Got a $100.00 check from your Uncle? Here's what that transaction would look
      like (with the category as `Income`): `Uncle Joey - Christmas Check` / `$-(100.00)`
    - Getting one of your byweekly paychecks is different. Make sure the transaction includes your
      employer name and the word Salary: `McDonalds - Salary`

3) Getting Interest
    - Receiving interest is just like income, except you can direct it to bank acounts other
      than `checking`. Again, just use the 3rd transaction delimiter (bank account method described
      above) and make sure the amount you enter is negative.

4) Making adjustments to your checking account balance without affecting monthly spending, starting
   balances
    - It happens to all of us. We forget to record an expense, or lose track of something. Realize
      your actual account balance is different from what `adjuftments` is telling you? Use the
      category `Adjustmnent` to create a transaction that will change your account balance but not
      affect your monthly budgeting.