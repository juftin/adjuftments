<p align="center">
  <img src="docs/static/juftin.png" width="250" height="250"  alt="juftin logo">
  <img src="docs/static/adjuftments.png" width="500" alt="adjuftments">
</p>

## What is `adjuftments`?

`adjuftments` is a financial application that tracks expenses, income, and more. Ultimately, the
goal of `adjuftments` is to be mindful of spending, and to plan around maximizing savings at the end
of each month. So what makes `adjuftments` different than your Excel spreadsheet? Mainly, at any
given point during the month you can compare your spending with where you planned to be. Secondly,
`adjuftments` is built on top of `splitwise` and `airtable`, which helps it do some pretty cool
stuff.

## How does `adjuftments` integrate with `airtable`?

`adjuftments` is built on top of airtable, every expense that you import into the application is
actually a record inside of `airtable`. This allows a couple of cool things:

- Record Access: At any time you can go back and modify, delete, or create historic expenses.
  `airtable` has mobile apps, and a responsive WebUI that makes data management easy.
- Record Entry: Creating new expenses is really easy using `airtable`'s native form functionality.

## How does `adjuftments` integrate with `splitwise`?

`adjuftments` performs a two way sync with records in `splitwise`. This means that after you
designate a financial partner (a friend in Splitwise and someone who you share expenses with), you
can create Splitwise expenses directly from `adjuftments`, and also auto sync with expenses created
inside of `splitwise`. Your ongoing balance with your financial partner is also tracked.

## How do I set up `adjuftments` for myself?

`adjuftments` set up is relatively straightforward. All credentials are set using
a [`.env`](example.env) file. Inside of this `.env` file you will store information like your
timezone, local directory path, and API credentials to the various services `adjuftments` integrates
with:

- `airtable`: frontend and data management
- `splitwise`: expense sharing integration
- `imgur`: temporary image hosting intermediary
- `pushover`: mobile push notifications

More details on the initial setup can be found in
the [documentation](docs/configuration/initial_setup.md).

* * *

* * *

<br/>
<br/>
<br/>

###### Cool stuff happens in Denver, CO [<img src="https://upload.wikimedia.org/wikipedia/commons/thumb/6/61/Flag_of_Denver%2C_Colorado.svg/800px-Flag_of_Denver%2C_Colorado.svg.png" width="25" alt="Denver">](https://denver-devs.slack.com/)